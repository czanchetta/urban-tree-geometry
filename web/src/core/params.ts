// Typed access to the shared single-source-of-truth parameter document.
// The JSON is copied verbatim from ../../data/species_parameters.json by
// scripts/sync-params.mjs (run automatically before dev/build/test) so this
// file never hand-duplicates parameters.
import shared from "../data/species_parameters.json";

export type Confidence = "low" | "medium" | "high";
export type CrownMethod = "dbh_scaled" | "palm_height_scaled";

export interface SpeciesParameters {
  common_name: string;
  scientific_name: string | null;
  height_asymptote_m: number;
  height_shape_k_cm: number;
  size_class?: string | null;
  crown_group: string;
  crown_method: CrownMethod;
  confidence: Confidence;
  reference_basis?: string | null;
  limitation?: string | null;
  source_url?: string | null;
}

export interface CrownGroup {
  crown_group: string;
  crown_dbh_factor: number;
  crown_height_limit_fraction: number;
  crown_depth_fraction: number;
  crown_method: CrownMethod;
  description?: string | null;
}

export interface PalmRule {
  palm_crown_height_factor: number;
  palm_crown_min_m: number;
  palm_crown_max_m: number;
}

export interface Constants {
  breast_height_m: number;
  round_step_m: number;
  band_lower_factor: number;
  band_upper_factor: number;
  band_lower_floor_m: number;
  dbh_extrapolation_cm: number;
  crown_band_rel: number;
  crown_band_min_m: number;
  suspicious_perimeter_cm: number;
}

interface SharedDoc {
  schema_version: string;
  description: string;
  constants: Constants;
  crown_groups: Record<string, Omit<CrownGroup, "crown_group">>;
  palm_rule: PalmRule;
  species: SpeciesParameters[];
}

const doc = shared as unknown as SharedDoc;

export const CONSTANTS: Constants = doc.constants;
export const PALM_RULE: PalmRule = doc.palm_rule;

const speciesByName = new Map<string, SpeciesParameters>();
for (const sp of doc.species) {
  speciesByName.set(sp.common_name.trim().toUpperCase(), sp);
}

const crownGroups = new Map<string, CrownGroup>();
for (const [name, g] of Object.entries(doc.crown_groups)) {
  crownGroups.set(name, { crown_group: name, ...g });
}

export function getSpecies(commonName: string | null | undefined): SpeciesParameters | null {
  if (!commonName) return null;
  return speciesByName.get(commonName.trim().toUpperCase()) ?? null;
}

export function getCrownGroup(group: string): CrownGroup | null {
  return crownGroups.get(group) ?? null;
}

export function allSpecies(): SpeciesParameters[] {
  return doc.species.slice();
}
