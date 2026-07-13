// Guard: the bundled parameter JSON must be byte-identical to the root
// single-source-of-truth file. Fails if scripts/sync-params.mjs was not run or
// if someone hand-edited the copy.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { describe, it, expect } from "vitest";
import { allSpecies, getSpecies, CONSTANTS } from "../src/core/params";

const here = dirname(fileURLToPath(import.meta.url));
const rootJson = resolve(here, "..", "..", "data", "species_parameters.json");
const bundled = resolve(here, "..", "src", "data", "species_parameters.json");

describe("shared parameters", () => {
  it("bundled copy is identical to the root source of truth", () => {
    expect(readFileSync(bundled, "utf-8")).toEqual(readFileSync(rootJson, "utf-8"));
  });
  it("loads all 26 species", () => {
    expect(allSpecies().length).toBe(26);
  });
  it("looks up case-insensitively", () => {
    const a = getSpecies("angico branco");
    expect(a).not.toBeNull();
    expect(a?.crown_group).toBeTruthy();
  });
  it("exposes constants", () => {
    expect(CONSTANTS.breast_height_m).toBe(1.3);
    expect(CONSTANTS.round_step_m).toBe(0.5);
  });
});
