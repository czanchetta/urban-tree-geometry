// In-browser DIALux `.3ds` exporter — mirrors the Python
// `urban_tree_geometry.dialux_export` writer byte-for-byte for the same inputs.
//
// Builds a schematic tree (trunk cylinder + crown ellipsoid) sized to a
// computed TreeGeometryResult and serialises it as an Autodesk 3D Studio
// (.3ds) binary — a documented open format DIALux imports natively.
//
// The mesh is a HEURISTIC stand-in volume for lighting pre-modelling, not a
// survey-accurate tree. All processing is in the browser; nothing is uploaded.

import type { TreeGeometryResult } from "./pipeline";

// 3DS chunk identifiers
const M3DMAGIC = 0x4d4d;
const M3D_VERSION = 0x0002;
const MDATA = 0x3d3d;
const MESH_VERSION = 0x3d3e;
const NAMED_OBJECT = 0x4000;
const N_TRI_OBJECT = 0x4100;
const POINT_ARRAY = 0x4110;
const FACE_ARRAY = 0x4120;
const MAX_VERTICES = 0xffff;

export type Vec3 = [number, number, number];
export type Tri = [number, number, number];

export interface Mesh {
  vertices: Vec3[];
  faces: Tri[];
}

export class ExportError extends Error {}

// --- geometry builders (identical construction to the Python module) --------
function cylinder(radius: number, z0: number, z1: number, segments: number): Mesh {
  const vertices: Vec3[] = [];
  const faces: Tri[] = [];
  for (const z of [z0, z1]) {
    for (let i = 0; i < segments; i++) {
      const a = (2 * Math.PI * i) / segments;
      vertices.push([radius * Math.cos(a), radius * Math.sin(a), z]);
    }
  }
  for (let i = 0; i < segments; i++) {
    const j = (i + 1) % segments;
    const b0 = i,
      t0 = i + segments,
      b1 = j,
      t1 = j + segments;
    faces.push([b0, b1, t1]);
    faces.push([b0, t1, t0]);
  }
  const cb = vertices.length;
  vertices.push([0, 0, z0]);
  const ct = vertices.length;
  vertices.push([0, 0, z1]);
  for (let i = 0; i < segments; i++) {
    const j = (i + 1) % segments;
    faces.push([cb, j, i]);
    faces.push([ct, i + segments, j + segments]);
  }
  return { vertices, faces };
}

function ellipsoid(
  rx: number,
  ry: number,
  rz: number,
  cz: number,
  lat: number,
  lon: number,
): Mesh {
  const vertices: Vec3[] = [];
  const faces: Tri[] = [];
  const top = vertices.length;
  vertices.push([0, 0, cz + rz]);
  const ringStart: number[] = [];
  for (let r = 1; r < lat; r++) {
    const theta = (Math.PI * r) / lat;
    ringStart.push(vertices.length);
    for (let c = 0; c < lon; c++) {
      const phi = (2 * Math.PI * c) / lon;
      vertices.push([
        rx * Math.sin(theta) * Math.cos(phi),
        ry * Math.sin(theta) * Math.sin(phi),
        cz + rz * Math.cos(theta),
      ]);
    }
  }
  const bot = vertices.length;
  vertices.push([0, 0, cz - rz]);
  const first = ringStart[0];
  for (let c = 0; c < lon; c++) {
    faces.push([top, first + c, first + ((c + 1) % lon)]);
  }
  for (let r = 0; r < lat - 2; r++) {
    const a = ringStart[r];
    const b = ringStart[r + 1];
    for (let c = 0; c < lon; c++) {
      const c1 = (c + 1) % lon;
      faces.push([a + c, b + c, b + c1]);
      faces.push([a + c, b + c1, a + c1]);
    }
  }
  const last = ringStart[ringStart.length - 1];
  for (let c = 0; c < lon; c++) {
    faces.push([bot, last + ((c + 1) % lon), last + c]);
  }
  return { vertices, faces };
}

export function buildTreeMesh(
  r: TreeGeometryResult,
  trunkSegments = 12,
  crownLat = 10,
  crownLon = 18,
): Mesh {
  const req: Record<string, number | null> = {
    height_m: r.height_m,
    trunk_diameter_m: r.trunk_diameter_m,
    crown_diameter_x_m: r.crown_diameter_x_m,
    crown_diameter_y_m: r.crown_diameter_y_m,
    crown_base_height_m: r.crown_base_height_m,
    crown_depth_m: r.crown_depth_m,
  };
  const missing = Object.entries(req)
    .filter(([, v]) => v === null || (v as number) <= 0)
    .map(([k]) => k);
  if (missing.length) {
    throw new ExportError(
      `cannot export tree ${r.tree_id}: missing/invalid geometry ${missing.join(", ")}`,
    );
  }
  const baseH = r.crown_base_height_m as number;
  const depth = r.crown_depth_m as number;
  const rx = (r.crown_diameter_x_m as number) / 2;
  const ry = (r.crown_diameter_y_m as number) / 2;
  const rz = depth / 2;
  const trunkR = (r.trunk_diameter_m as number) / 2;
  const crownCz = baseH + rz;

  const trunk = cylinder(trunkR, 0, baseH, trunkSegments);
  const crown = ellipsoid(rx, ry, rz, crownCz, crownLat, crownLon);
  const offset = trunk.vertices.length;
  const vertices = trunk.vertices.concat(crown.vertices);
  const faces = trunk.faces.concat(
    crown.faces.map(([a, b, c]) => [a + offset, b + offset, c + offset] as Tri),
  );
  if (vertices.length > MAX_VERTICES) {
    throw new ExportError(
      `mesh has ${vertices.length} vertices, exceeds 3DS limit ${MAX_VERTICES}`,
    );
  }
  return { vertices, faces };
}

// --- 3DS serialisation -------------------------------------------------------
function objectName(name: string): Uint8Array {
  let safe = "";
  for (const ch of name) {
    const code = ch.charCodeAt(0);
    if (code >= 32 && code < 127) safe += ch;
  }
  safe = safe.slice(0, 32) || "Tree";
  const bytes = new Uint8Array(safe.length + 1);
  for (let i = 0; i < safe.length; i++) bytes[i] = safe.charCodeAt(i);
  bytes[safe.length] = 0;
  return bytes;
}

function chunk(id: number, payload: Uint8Array): Uint8Array {
  const out = new Uint8Array(6 + payload.length);
  const dv = new DataView(out.buffer);
  dv.setUint16(0, id, true);
  dv.setUint32(2, 6 + payload.length, true);
  out.set(payload, 6);
  return out;
}

function concat(parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let off = 0;
  for (const p of parts) {
    out.set(p, off);
    off += p.length;
  }
  return out;
}

function int32le(v: number): Uint8Array {
  const b = new Uint8Array(4);
  new DataView(b.buffer).setInt32(0, v, true);
  return b;
}

export function meshTo3dsBytes(mesh: Mesh, name = "Tree"): Uint8Array {
  // POINT_ARRAY
  const pts = new Uint8Array(2 + mesh.vertices.length * 12);
  let dv = new DataView(pts.buffer);
  dv.setUint16(0, mesh.vertices.length, true);
  let off = 2;
  for (const [x, y, z] of mesh.vertices) {
    dv.setFloat32(off, x, true);
    dv.setFloat32(off + 4, y, true);
    dv.setFloat32(off + 8, z, true);
    off += 12;
  }
  const pointArray = chunk(POINT_ARRAY, pts);

  // FACE_ARRAY
  const fcs = new Uint8Array(2 + mesh.faces.length * 8);
  dv = new DataView(fcs.buffer);
  dv.setUint16(0, mesh.faces.length, true);
  off = 2;
  for (const [a, b, c] of mesh.faces) {
    dv.setUint16(off, a, true);
    dv.setUint16(off + 2, b, true);
    dv.setUint16(off + 4, c, true);
    dv.setUint16(off + 6, 0, true);
    off += 8;
  }
  const faceArray = chunk(FACE_ARRAY, fcs);

  const tri = chunk(N_TRI_OBJECT, concat([pointArray, faceArray]));
  const named = chunk(NAMED_OBJECT, concat([objectName(name), tri]));
  const meshVer = chunk(MESH_VERSION, int32le(3));
  const mdata = chunk(MDATA, concat([meshVer, named]));
  const m3dVer = chunk(M3D_VERSION, int32le(3));
  return chunk(M3DMAGIC, concat([m3dVer, mdata]));
}

export function resultTo3dsBytes(r: TreeGeometryResult): Uint8Array {
  const mesh = buildTreeMesh(r);
  const name = (r.common_name || r.tree_id || "Tree").trim();
  return meshTo3dsBytes(mesh, name);
}

// Trigger a browser download of the .3ds for one result.
export function download3ds(r: TreeGeometryResult): void {
  const bytes = resultTo3dsBytes(r);
  const blob = new Blob([bytes.buffer as ArrayBuffer], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${r.tree_id || "tree"}.3ds`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
