// Verifies the in-browser .3ds writer produces bytes identical to the Python
// reference for the same computed tree, and that basic chunk structure holds.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { describe, expect, it } from "vitest";

import { processTree, type TreeInput } from "../src/core/pipeline";
import { buildTreeMesh, meshTo3dsBytes, resultTo3dsBytes, ExportError } from "../src/core/dialux3ds";

const here = dirname(fileURLToPath(import.meta.url));
const fixturesDir = join(here, "fixtures");
const meta = JSON.parse(readFileSync(join(fixturesDir, "fixture_tree_3ds.json"), "utf-8"));
const refBytes = new Uint8Array(readFileSync(join(fixturesDir, "fixture_tree.3ds")));

function fixtureResult() {
  const input: TreeInput = {
    tree_id: meta.input.tree_id,
    common_name: meta.input.common_name,
    scientific_name: meta.input.scientific_name,
    perimeter_cm: meta.input.perimeter_cm,
  };
  return processTree(input);
}

describe("dialux .3ds writer", () => {
  it("matches the Python reference byte-for-byte", () => {
    const r = fixtureResult();
    // sanity: the TS pipeline reproduces the reference geometry
    expect(r.height_m).toBeCloseTo(meta.result.height_m, 9);
    expect(r.trunk_diameter_m).toBeCloseTo(meta.result.trunk_diameter_m, 9);
    const bytes = resultTo3dsBytes(r);
    expect(bytes.length).toBe(meta.n_bytes);
    expect(Array.from(bytes)).toEqual(Array.from(refBytes));
  });

  it("writes a MAIN3DS magic and self-consistent top-chunk length", () => {
    const bytes = resultTo3dsBytes(fixtureResult());
    const dv = new DataView(bytes.buffer);
    expect(dv.getUint16(0, true)).toBe(0x4d4d);
    expect(dv.getUint32(2, true)).toBe(bytes.length);
  });

  it("mesh Z-extent equals total height and base sits at 0", () => {
    const r = fixtureResult();
    const mesh = buildTreeMesh(r);
    const zs = mesh.vertices.map((v) => v[2]);
    const zmin = Math.min(...zs);
    const zmax = Math.max(...zs);
    expect(zmin).toBeCloseTo(0, 4);
    expect(zmax - zmin).toBeCloseTo(r.height_m as number, 3);
    const xs = mesh.vertices.map((v) => v[0]);
    expect(Math.max(...xs) - Math.min(...xs)).toBeCloseTo(r.crown_diameter_x_m as number, 3);
  });

  it("throws on a tree without geometry", () => {
    const r = processTree({
      tree_id: "X",
      common_name: "ESPÉCIE NÃO IDENTIFICADA",
      scientific_name: "",
      perimeter_cm: 100,
    });
    expect(r.height_m).toBeNull();
    expect(() => resultTo3dsBytes(r)).toThrow(ExportError);
  });

  it("meshTo3dsBytes is deterministic", () => {
    const r = fixtureResult();
    const a = meshTo3dsBytes(buildTreeMesh(r), "ANGICO BRANCO");
    const b = meshTo3dsBytes(buildTreeMesh(r), "ANGICO BRANCO");
    expect(Array.from(a)).toEqual(Array.from(b));
  });
});
