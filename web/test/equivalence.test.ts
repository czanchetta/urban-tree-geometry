// Cross-language equivalence: every case in tests/fixtures/equivalence_cases.json
// was produced by the PYTHON pipeline. Here we run the identical inputs through
// the TypeScript pipeline and assert field-by-field equality. If the two
// implementations ever diverge, this test (and CI) fails.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { describe, it, expect } from "vitest";
import { processTree, TreeInput } from "../src/core/pipeline";

const here = dirname(fileURLToPath(import.meta.url));
const fixturePath = resolve(here, "..", "..", "tests", "fixtures", "equivalence_cases.json");

interface Case {
  input: { tree_id: string; common_name: string; scientific_name: string | null; perimeter_cm: number | null };
  expected: Record<string, unknown>;
}

const cases: Case[] = JSON.parse(readFileSync(fixturePath, "utf-8"));

// Numeric fields compared with a tiny tolerance (rounding already applied in
// both implementations; tolerance only guards binary FP representation).
const NUMERIC_FIELDS = [
  "dbh_cm", "trunk_diameter_m", "height_m", "height_min_m", "height_max_m",
  "crown_diameter_x_m", "crown_diameter_y_m", "crown_base_height_m", "crown_depth_m",
  "crown_projected_area_m2", "crown_min_m", "crown_max_m",
] as const;
const STRING_FIELDS = ["tree_id", "common_name", "scientific_name", "crown_group", "confidence"] as const;
const TOL = 1e-9;

describe("Python <-> TypeScript equivalence", () => {
  it("has a non-trivial number of cases", () => {
    expect(cases.length).toBeGreaterThan(100);
  });

  for (const c of cases) {
    it(`matches Python for ${c.input.tree_id} (${c.input.common_name})`, () => {
      const input: TreeInput = {
        tree_id: c.input.tree_id,
        common_name: c.input.common_name,
        scientific_name: c.input.scientific_name,
        perimeter_cm: c.input.perimeter_cm,
      };
      const got = processTree(input) as unknown as Record<string, unknown>;
      const exp = c.expected;

      for (const f of NUMERIC_FIELDS) {
        const g = got[f] as number | null;
        const e = exp[f] as number | null;
        if (e === null || e === undefined) {
          expect(g, `${f} should be null`).toBeNull();
        } else {
          expect(g, `${f} should be a number`).not.toBeNull();
          expect(Math.abs((g as number) - e), `${f}: got ${g}, expected ${e}`).toBeLessThan(TOL);
        }
      }
      for (const f of STRING_FIELDS) {
        expect(got[f] ?? null, `${f}`).toEqual(exp[f] ?? null);
      }
      // warnings: same count and same text, in order
      expect(got.warnings, "warnings").toEqual(exp.warnings);
    });
  }
});
