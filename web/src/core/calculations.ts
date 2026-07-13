// Faithful reproduction of the source-workbook height model.
// Mirrors src/urban_tree_geometry/calculations.py cell-for-cell, including
// the exact rounding conventions. See docs/methodology.md.
import { CONSTANTS } from "./params";

export const BREAST_HEIGHT_M = CONSTANTS.breast_height_m;
export const BAND_LOWER_FACTOR = CONSTANTS.band_lower_factor;
export const BAND_UPPER_FACTOR = CONSTANTS.band_upper_factor;
export const BAND_LOWER_FLOOR_M = CONSTANTS.band_lower_floor_m;
export const ROUND_STEP_M = CONSTANTS.round_step_m;

export class UnitError extends Error {}

/**
 * Round to the nearest multiple of `step`, half away from zero.
 * Matches Python calculations.round_to_step (spreadsheet ROUND(x*2,0)/2).
 */
export function roundToStep(value: number, step: number = ROUND_STEP_M): number {
  if (step <= 0) throw new Error("step must be positive");
  const scaled = value / step;
  const rounded = scaled >= 0 ? Math.floor(scaled + 0.5) : Math.ceil(scaled - 0.5);
  return rounded * step;
}

/**
 * Round to `ndigits` decimals using round-half-to-even (banker's rounding),
 * reproducing CPython's built-in round() exactly. Used for the display fields
 * (DBH 1 dp, trunk 4 dp, crown 2 dp).
 *
 * Exact binary ties DO occur in this pipeline: e.g. crown_depth =
 * crown_depth_fraction * H with fraction 0.75 and H on a 0.5 m grid gives
 * values like 5.625, which is exactly representable in binary. Python rounds
 * such a tie to even (5.62); a naive away-from-zero rounder (toFixed / value*m
 * + Math.round) would give 5.63. We therefore operate on the double's EXACT
 * decimal expansion, obtained via toFixed with extra guard digits (toFixed is
 * spec'd to be correctly rounded, and 25 guard digits capture the full exact
 * value of any double for ndigits <= 4), then apply decimal half-to-even. This
 * agrees with Python value-for-value; the 135-case equivalence fixture
 * (web/test/equivalence.test.ts) verifies it end-to-end.
 */
export function roundDecimal(value: number, ndigits: number): number {
  if (!Number.isFinite(value)) return value;
  const neg = value < 0;
  // Exact-enough decimal expansion of |value| (guard digits avoid FP drift).
  const guard = Math.min(100, ndigits + 25);
  const s = Math.abs(value).toFixed(guard);
  const dot = s.indexOf(".");
  const intPart = s.slice(0, dot);
  const frac = s.slice(dot + 1);
  const keep = frac.slice(0, ndigits);
  const rest = frac.slice(ndigits);

  // Integer string of the digits we keep (intPart followed by kept fraction).
  let digits = (intPart + keep).replace(/^0+(?=\\d)/, "");
  const firstDropped = rest.length ? rest[0] : "0";
  const remainderNonZero = /[1-9]/.test(rest.slice(1));

  let roundUp = false;
  if (firstDropped > "5") {
    roundUp = true;
  } else if (firstDropped === "5") {
    if (remainderNonZero) {
      roundUp = true; // > half -> up
    } else {
      // exact tie -> round to even on the last kept digit
      const lastKept = digits.length ? digits.charCodeAt(digits.length - 1) - 48 : 0;
      roundUp = lastKept % 2 === 1;
    }
  }

  if (roundUp) {
    digits = incrementDecimalString(digits);
  }

  // Reinsert the decimal point ndigits from the right.
  let out: number;
  if (ndigits === 0) {
    out = Number(digits);
  } else {
    const padded = digits.padStart(ndigits + 1, "0");
    const cut = padded.length - ndigits;
    out = Number(`${padded.slice(0, cut)}.${padded.slice(cut)}`);
  }
  if (neg && out !== 0) out = -out;
  return out + 0; // normalise -0 to 0
}

/** Add 1 to a non-negative integer represented as a decimal string. */
function incrementDecimalString(s: string): string {
  const arr = s.split("");
  let i = arr.length - 1;
  while (i >= 0) {
    if (arr[i] === "9") {
      arr[i] = "0";
      i -= 1;
    } else {
      arr[i] = String(Number(arr[i]) + 1);
      return arr.join("");
    }
  }
  return "1" + arr.join("");
}

/** DBH (cm) from trunk perimeter (cm): DBH = P / pi. */
export function dbhFromPerimeter(perimeterCm: number | null | undefined): number {
  if (perimeterCm === null || perimeterCm === undefined || Number.isNaN(perimeterCm)) {
    throw new UnitError("perimeter is missing");
  }
  if (perimeterCm <= 0) {
    throw new UnitError(`perimeter must be positive, got ${perimeterCm} cm`);
  }
  return perimeterCm / Math.PI;
}

/** Trunk diameter in metres from DBH in centimetres (/100). */
export function dbhCmToTrunkDiameterM(dbhCm: number): number {
  return dbhCm / 100.0;
}

/**
 * Asymptotic (monomolecular) height model, rounded to 0.5 m.
 * H = 1.30 + (H_inf - 1.30) * (1 - exp(-DBH / k)).
 */
export function heightFromDbh(dbhCm: number, heightAsymptoteM: number, shapeKCm: number): number {
  if (heightAsymptoteM <= BREAST_HEIGHT_M) {
    throw new Error(`height_asymptote_m must exceed ${BREAST_HEIGHT_M} m, got ${heightAsymptoteM}`);
  }
  if (shapeKCm <= 0) throw new Error(`shape_k_cm must be positive, got ${shapeKCm}`);
  if (dbhCm <= 0) throw new UnitError(`dbh must be positive, got ${dbhCm}`);
  const raw =
    BREAST_HEIGHT_M + (heightAsymptoteM - BREAST_HEIGHT_M) * (1.0 - Math.exp(-dbhCm / shapeKCm));
  return roundToStep(raw);
}

/** Operational +/-20% sensitivity band (2 m floor), each rounded to 0.5 m. */
export function heightBand(heightM: number): [number, number] {
  const lower = roundToStep(Math.max(BAND_LOWER_FLOOR_M, heightM * BAND_LOWER_FACTOR));
  const upper = roundToStep(heightM * BAND_UPPER_FACTOR);
  return [lower, upper];
}
