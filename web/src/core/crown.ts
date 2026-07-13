// Heuristic crown and DIALux geometry layer.
//
// PROVENANCE: nothing here comes from the source workbook (which estimates
// height only). These are engineering heuristics from general urban-forestry
// literature, adjusted by crown architecture. They are NOT species-specific
// published allometric coefficients and are NOT regression-tested. Mirrors
// src/urban_tree_geometry/crown.py.
import { CONSTANTS, CrownGroup, PalmRule } from "./params";

export const CROWN_BAND_REL = CONSTANTS.crown_band_rel;
export const CROWN_BAND_MIN_M = CONSTANTS.crown_band_min_m;

/** Heuristic crown diameter for non-palm trees: min(factor*trunk, limit*H). */
export function crownDiameterDbhScaled(
  trunkDiameterM: number,
  heightM: number,
  group: CrownGroup,
): number {
  const dRaw = group.crown_dbh_factor * trunkDiameterM;
  const dLimit = group.crown_height_limit_fraction * heightM;
  return Math.max(0.0, Math.min(dRaw, dLimit));
}

/** Heuristic palm crown diameter: clip(factor*H, min, max). Always low confidence. */
export function crownDiameterPalm(heightM: number, rule: PalmRule): number {
  const d = rule.palm_crown_height_factor * heightM;
  return Math.min(rule.palm_crown_max_m, Math.max(rule.palm_crown_min_m, d));
}

/** Heuristic crown base height and depth: depth = frac*H, base = H - depth. */
export function crownBaseAndDepth(heightM: number, group: CrownGroup): [number, number] {
  const depth = group.crown_depth_fraction * heightM;
  const base = heightM - depth;
  return [Math.max(0.0, base), Math.max(0.0, depth)];
}

/** Projected crown area assuming a circular projection: A = pi*D^2/4. */
export function crownProjectedArea(crownDiameterM: number): number {
  return (Math.PI * crownDiameterM * crownDiameterM) / 4.0;
}

/** Operational crown-diameter sensitivity band: uncertainty = max(0.20*D, 1.5). */
export function crownBand(crownDiameterM: number): [number, number] {
  const uncertainty = Math.max(CROWN_BAND_REL * crownDiameterM, CROWN_BAND_MIN_M);
  const lower = Math.max(0.0, crownDiameterM - uncertainty);
  const upper = crownDiameterM + uncertainty;
  return [lower, upper];
}
