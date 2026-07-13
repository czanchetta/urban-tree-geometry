// Orchestration: turn a TreeInput into a TreeGeometryResult.
// Mirrors src/urban_tree_geometry/pipeline.py exactly, including warning
// text, confidence downgrades, extrapolation flag and rounding precision.
import * as calc from "./calculations";
import * as crownmod from "./crown";
import { CONSTANTS, Confidence, getCrownGroup, getSpecies, PALM_RULE } from "./params";

export const DBH_EXTRAPOLATION_CM = CONSTANTS.dbh_extrapolation_cm;

const CONFIDENCE_ORDER: Record<Confidence, number> = { low: 0, medium: 1, high: 2 };

function minConfidence(a: Confidence, b: Confidence): Confidence {
  return CONFIDENCE_ORDER[a] <= CONFIDENCE_ORDER[b] ? a : b;
}

function norm(name: string): string {
  return name.trim().toLowerCase().split(/\s+/).join(" ");
}

export interface TreeInput {
  tree_id: string;
  common_name: string;
  scientific_name?: string | null;
  perimeter_cm: number | null;
}

export interface TreeGeometryResult {
  tree_id: string;
  common_name: string;
  scientific_name: string | null;
  perimeter_cm: number | null;
  dbh_cm: number | null;
  trunk_diameter_m: number | null;
  height_m: number | null;
  height_min_m: number | null;
  height_max_m: number | null;
  crown_diameter_x_m: number | null;
  crown_diameter_y_m: number | null;
  crown_base_height_m: number | null;
  crown_depth_m: number | null;
  crown_projected_area_m2: number | null;
  crown_min_m: number | null;
  crown_max_m: number | null;
  crown_group: string | null;
  confidence: Confidence;
  warnings: string[];
}

function emptyResult(t: TreeInput): TreeGeometryResult {
  return {
    tree_id: t.tree_id,
    common_name: t.common_name,
    scientific_name: t.scientific_name ?? null,
    perimeter_cm: t.perimeter_cm,
    dbh_cm: null,
    trunk_diameter_m: null,
    height_m: null,
    height_min_m: null,
    height_max_m: null,
    crown_diameter_x_m: null,
    crown_diameter_y_m: null,
    crown_base_height_m: null,
    crown_depth_m: null,
    crown_projected_area_m2: null,
    crown_min_m: null,
    crown_max_m: null,
    crown_group: null,
    confidence: "medium",
    warnings: [],
  };
}

export interface Overrides {
  heightAsymptoteM?: number;
  shapeKCm?: number;
}

export function processTree(
  tree: TreeInput,
  overrides: Overrides = {},
): TreeGeometryResult {
  const warnings: string[] = [];
  const result = emptyResult(tree);

  const species = getSpecies(tree.common_name);
  if (species === null) {
    warnings.push(
      `Species '${tree.common_name}' not found in parameter set; ` +
        "height and crown cannot be estimated. Provide parameters or overrides.",
    );
    result.confidence = "low";
    result.warnings = warnings;
    return result;
  }

  if (
    tree.scientific_name &&
    species.scientific_name &&
    norm(tree.scientific_name) !== norm(species.scientific_name)
  ) {
    warnings.push(
      `Recorded scientific name '${tree.scientific_name}' diverges from the ` +
        `reference '${species.scientific_name}' for '${tree.common_name}'; ` +
        "estimate is based on the common name.",
    );
  }

  let confidence: Confidence = species.confidence;
  result.crown_group = species.crown_group;

  const hInf = overrides.heightAsymptoteM ?? species.height_asymptote_m;
  const k = overrides.shapeKCm ?? species.height_shape_k_cm;

  let dbh: number;
  try {
    dbh = calc.dbhFromPerimeter(tree.perimeter_cm);
  } catch (exc) {
    warnings.push(`DBH not computed: ${(exc as Error).message}.`);
    result.confidence = "low";
    result.warnings = warnings;
    return result;
  }

  result.dbh_cm = calc.roundDecimal(dbh, 1);
  result.trunk_diameter_m = calc.roundDecimal(calc.dbhCmToTrunkDiameterM(dbh), 4);

  let height: number;
  try {
    height = calc.heightFromDbh(dbh, hInf, k);
  } catch (exc) {
    warnings.push(`Height not computed: ${(exc as Error).message}.`);
    result.confidence = "low";
    result.warnings = warnings;
    return result;
  }

  result.height_m = height;
  const [hmin, hmax] = calc.heightBand(height);
  result.height_min_m = hmin;
  result.height_max_m = hmax;

  if (dbh > DBH_EXTRAPOLATION_CM) {
    warnings.push(
      `DBH ${dbh.toFixed(0)} cm is a large extrapolation for the adopted height ` +
        "curve; treat the height with caution.",
    );
    confidence = minConfidence(confidence, "low");
  }

  const group = getCrownGroup(species.crown_group);
  if (group === null) {
    warnings.push(`Crown group '${species.crown_group}' not found; crown geometry skipped.`);
    result.confidence = minConfidence(confidence, "low");
    result.warnings = warnings;
    return result;
  }

  let crownD: number;
  if (species.crown_method === "palm_height_scaled" || group.crown_method === "palm_height_scaled") {
    crownD = crownmod.crownDiameterPalm(height, PALM_RULE);
    warnings.push(
      "Palm crown estimated from height, not DBH; confidence is low. " +
        "Field measurement is recommended.",
    );
    confidence = minConfidence(confidence, "low");
  } else {
    crownD = crownmod.crownDiameterDbhScaled(result.trunk_diameter_m as number, height, group);
  }

  result.crown_diameter_x_m = calc.roundDecimal(crownD, 2);
  result.crown_diameter_y_m = calc.roundDecimal(crownD, 2);
  const [base, depth] = crownmod.crownBaseAndDepth(height, group);
  result.crown_base_height_m = calc.roundDecimal(base, 2);
  result.crown_depth_m = calc.roundDecimal(depth, 2);
  result.crown_projected_area_m2 = calc.roundDecimal(crownmod.crownProjectedArea(crownD), 2);
  const [cmin, cmax] = crownmod.crownBand(crownD);
  result.crown_min_m = calc.roundDecimal(cmin, 2);
  result.crown_max_m = calc.roundDecimal(cmax, 2);

  result.confidence = confidence;
  result.warnings = warnings;
  return result;
}

export function processMany(trees: TreeInput[]): TreeGeometryResult[] {
  return trees.map((t) => processTree(t));
}
