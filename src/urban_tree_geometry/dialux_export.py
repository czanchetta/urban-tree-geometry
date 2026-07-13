"""DIALux 3D export — parametric ``.3ds`` mesh writer and ``.dxobj`` rewriter.

This module turns a computed :class:`~urban_tree_geometry.models.TreeGeometryResult`
into a 3D object that DIALux can import for outdoor-lighting pre-modelling.

Two paths are provided:

* :func:`write_3ds` / :func:`result_to_3ds_bytes` — build a **schematic** tree
  (a trunk cylinder plus a crown ellipsoid) sized to the computed geometry and
  serialise it as a valid ``.3ds`` binary (Autodesk 3D Studio chunk format, a
  documented open format that DIALux imports natively). This is a stand-in
  *volume* for lighting studies, not a botanically realistic mesh.

* :func:`rewrite_dxobj` — take a **user-supplied** DIALux ``.dxobj`` template and
  rewrite only the editable STEP dimensions / scale factors so the template's
  own mesh is resized to the computed tree (see :mod:`.dxobj_rewrite`... kept in
  this module). The template is a proprietary DIALux asset and must never be
  committed to a public repository.

Provenance note
---------------
The mesh geometry is **heuristic** — it is derived from the heuristic crown
layer, not measured. The trunk/crown are simplified primitives. Do not present
the exported object as a survey-accurate tree model.

Coordinate convention: metres, Z up (matches DIALux ``DimensionsPropertySet``
``(X, Y, Z)`` where Z is height). Origin at the trunk base, centred in X/Y.
"""

from __future__ import annotations

import math
import re as _re
import struct
import uuid as _uuid
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TreeGeometryResult

# --- 3DS chunk identifiers (Autodesk 3D Studio) ------------------------------
_M3DMAGIC = 0x4D4D  # MAIN3DS
_M3D_VERSION = 0x0002
_MDATA = 0x3D3D  # 3D editor
_MESH_VERSION = 0x3D3E
_NAMED_OBJECT = 0x4000
_N_TRI_OBJECT = 0x4100
_POINT_ARRAY = 0x4110
_FACE_ARRAY = 0x4120

# Vertex count is stored as uint16 in the 3DS POINT_ARRAY chunk.
_MAX_VERTICES = 0xFFFF


class ExportError(ValueError):
    """Raised when a result cannot be exported (missing/invalid geometry)."""


@dataclass(frozen=True)
class Mesh:
    """A triangle mesh: vertices (metres, Z up) and 0-based triangle indices."""

    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]

    def bounds(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Return (min_xyz, max_xyz) over all vertices."""
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        zs = [v[2] for v in self.vertices]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


# --- geometry builders -------------------------------------------------------
def _cylinder(
    radius: float, z0: float, z1: float, segments: int
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Closed cylinder along Z from z0 to z1, centred on the Z axis."""
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for z in (z0, z1):
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((radius * math.cos(a), radius * math.sin(a), z))
    # side quads -> two triangles each
    for i in range(segments):
        j = (i + 1) % segments
        b0, t0, b1, t1 = i, i + segments, j, j + segments
        faces.append((b0, b1, t1))
        faces.append((b0, t1, t0))
    # caps
    cb = len(verts)
    verts.append((0.0, 0.0, z0))
    ct = len(verts)
    verts.append((0.0, 0.0, z1))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((cb, j, i))  # bottom (downward)
        faces.append((ct, i + segments, j + segments))  # top (upward)
    return verts, faces


def _ellipsoid(
    rx: float, ry: float, rz: float, cz: float, lat: int, lon: int
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """UV-sphere ellipsoid with radii (rx, ry, rz), centred at (0, 0, cz)."""
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    # poles + interior rings
    top = len(verts)
    verts.append((0.0, 0.0, cz + rz))
    ring_start: list[int] = []
    for r in range(1, lat):
        theta = math.pi * r / lat  # 0..pi from top
        ring_start.append(len(verts))
        for c in range(lon):
            phi = 2.0 * math.pi * c / lon
            verts.append(
                (
                    rx * math.sin(theta) * math.cos(phi),
                    ry * math.sin(theta) * math.sin(phi),
                    cz + rz * math.cos(theta),
                )
            )
    bot = len(verts)
    verts.append((0.0, 0.0, cz - rz))
    # top cap
    first = ring_start[0]
    for c in range(lon):
        faces.append((top, first + c, first + (c + 1) % lon))
    # middle bands
    for r in range(lat - 2):
        a = ring_start[r]
        b = ring_start[r + 1]
        for c in range(lon):
            c1 = (c + 1) % lon
            faces.append((a + c, b + c, b + c1))
            faces.append((a + c, b + c1, a + c1))
    # bottom cap
    last = ring_start[-1]
    for c in range(lon):
        faces.append((bot, last + (c + 1) % lon, last + c))
    return verts, faces


def build_tree_mesh(
    result: TreeGeometryResult,
    trunk_segments: int = 12,
    crown_lat: int = 10,
    crown_lon: int = 18,
) -> Mesh:
    """Build a schematic trunk+crown mesh sized to a computed result.

    Trunk: cylinder from z=0 to ``crown_base_height_m``, diameter
    ``trunk_diameter_m``. Crown: ellipsoid with horizontal radii from
    ``crown_diameter_x_m`` / ``crown_diameter_y_m``, vertical radius
    ``crown_depth_m / 2``, its top reaching total height ``height_m``.

    Raises :class:`ExportError` if the required geometry is missing (e.g. an
    unrecognised species with no estimate).
    """
    req = {
        "height_m": result.height_m,
        "trunk_diameter_m": result.trunk_diameter_m,
        "crown_diameter_x_m": result.crown_diameter_x_m,
        "crown_diameter_y_m": result.crown_diameter_y_m,
        "crown_base_height_m": result.crown_base_height_m,
        "crown_depth_m": result.crown_depth_m,
    }
    missing = [k for k, v in req.items() if v is None or (isinstance(v, float) and v <= 0)]
    if missing:
        raise ExportError(
            f"cannot export tree {result.tree_id!r}: missing/invalid geometry {missing}"
        )

    base_h = float(result.crown_base_height_m)  # type: ignore[arg-type]
    depth = float(result.crown_depth_m)  # type: ignore[arg-type]
    rx = float(result.crown_diameter_x_m) / 2.0  # type: ignore[arg-type]
    ry = float(result.crown_diameter_y_m) / 2.0  # type: ignore[arg-type]
    rz = depth / 2.0
    trunk_r = float(result.trunk_diameter_m) / 2.0  # type: ignore[arg-type]
    crown_cz = base_h + rz  # centre; top = base_h + depth = height_m

    tv, tf = _cylinder(trunk_r, 0.0, base_h, trunk_segments)
    cv, cf = _ellipsoid(rx, ry, rz, crown_cz, crown_lat, crown_lon)
    offset = len(tv)
    vertices = tv + cv
    faces = tf + [(a + offset, b + offset, c + offset) for (a, b, c) in cf]
    if len(vertices) > _MAX_VERTICES:
        raise ExportError(
            f"mesh has {len(vertices)} vertices, exceeds 3DS limit {_MAX_VERTICES}; "
            "reduce segment counts"
        )
    return Mesh(vertices, faces)


# --- 3DS serialisation -------------------------------------------------------
def _chunk(chunk_id: int, payload: bytes) -> bytes:
    """Wrap a payload in a 3DS chunk header (id: u16, length: u32 incl. header)."""
    return struct.pack("<HI", chunk_id, 6 + len(payload)) + payload


def _object_name(name: str) -> bytes:
    """3DS names are ASCII, NUL-terminated, <= 10 chars historically (we cap 32)."""
    safe = "".join(ch for ch in name if 32 <= ord(ch) < 127)[:32] or "Tree"
    return safe.encode("ascii") + b"\x00"


def mesh_to_3ds_bytes(mesh: Mesh, name: str = "Tree") -> bytes:
    """Serialise a :class:`Mesh` to a valid ``.3ds`` byte string."""
    pts = struct.pack("<H", len(mesh.vertices))
    for x, y, z in mesh.vertices:
        pts += struct.pack("<fff", x, y, z)
    point_array = _chunk(_POINT_ARRAY, pts)

    fcs = struct.pack("<H", len(mesh.faces))
    for a, b, c in mesh.faces:
        fcs += struct.pack("<HHHH", a, b, c, 0)
    face_array = _chunk(_FACE_ARRAY, fcs)

    tri = _chunk(_N_TRI_OBJECT, point_array + face_array)
    named = _chunk(_NAMED_OBJECT, _object_name(name) + tri)
    mesh_ver = _chunk(_MESH_VERSION, struct.pack("<i", 3))
    mdata = _chunk(_MDATA, mesh_ver + named)
    m3d_ver = _chunk(_M3D_VERSION, struct.pack("<i", 3))
    return _chunk(_M3DMAGIC, m3d_ver + mdata)


def result_to_3ds_bytes(result: TreeGeometryResult, **mesh_kwargs) -> bytes:
    """Build and serialise a schematic ``.3ds`` for one computed result."""
    mesh = build_tree_mesh(result, **mesh_kwargs)
    name = (result.common_name or result.tree_id or "Tree").strip()
    return mesh_to_3ds_bytes(mesh, name=name)


def write_3ds(result: TreeGeometryResult, path: str | Path, **mesh_kwargs) -> Path:
    """Write a schematic ``.3ds`` file for one computed result; returns the path."""
    path = Path(path)
    path.write_bytes(result_to_3ds_bytes(result, **mesh_kwargs))
    return path


# --- minimal 3DS reader (for round-trip tests) -------------------------------
def parse_3ds(data: bytes) -> Mesh:
    """Parse a ``.3ds`` produced by :func:`mesh_to_3ds_bytes` back into a Mesh.

    A pragmatic reader that walks the chunk tree and extracts the first
    triangle object. Sufficient for verifying our own output round-trips.
    """
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []

    def walk(buf: bytes, start: int, end: int) -> None:
        pos = start
        while pos + 6 <= end:
            cid, clen = struct.unpack_from("<HI", buf, pos)
            body = pos + 6
            cend = pos + clen
            if clen < 6 or cend > end:
                break
            if cid in (_M3DMAGIC, _MDATA, _NAMED_OBJECT, _N_TRI_OBJECT):
                if cid == _NAMED_OBJECT:  # skip NUL-terminated name first
                    n = body
                    while n < cend and buf[n] != 0:
                        n += 1
                    walk(buf, n + 1, cend)
                else:
                    walk(buf, body, cend)
            elif cid == _POINT_ARRAY:
                (count,) = struct.unpack_from("<H", buf, body)
                off = body + 2
                for _ in range(count):
                    verts.append(struct.unpack_from("<fff", buf, off))
                    off += 12
            elif cid == _FACE_ARRAY:
                (count,) = struct.unpack_from("<H", buf, body)
                off = body + 2
                for _ in range(count):
                    a, b, c, _flags = struct.unpack_from("<HHHH", buf, off)
                    faces.append((a, b, c))
                    off += 8
            pos = cend

    walk(data, 0, len(data))
    return Mesh(verts, faces)


# --- .dxobj template rewriter ------------------------------------------------
# A DIALux .dxobj is a ZIP holding a STEP text file (PrototypeData.dat) with the
# editable dimensions + scale factors, plus proprietary binary mesh streams
# (.m3d / .gdms) that we DO NOT touch. We resize the template's own mesh by
# rewriting the STEP DimensionsPropertySet and the ScaleFactors, leaving the
# mesh bytes intact — DIALux applies the scale factors on import.
#
# The template is a proprietary DIALux asset. Keep it user-supplied and
# git-ignored; never commit it to a public repository.

_STEP_MEMBER = "Project/PrototypeData_0/PrototypeData.dat"
_ARCHIVE_INFO = "ArchiveInfo/ArchiveInfo.xml"

# float tuple like "(4., 3., 4.25)" — STEP uses a trailing dot for integers
_FLOAT = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?\.?"


@dataclass(frozen=True)
class DxobjTemplateInfo:
    """What we read out of a template ``.dxobj`` before rewriting."""

    dimensions: tuple[float, float, float]
    min_position: tuple[float, float, float]
    title: str


def _parse_step_float(tok: str) -> float:
    """Parse a STEP real literal, tolerating the trailing-dot integer form."""
    tok = tok.strip()
    if tok.endswith(".") and tok.count(".") == 1:
        tok = tok[:-1]
    return float(tok)


def _read_dimensions(step: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Extract (dimensions, min_position) from the DimensionsPropertySet line."""
    m = _re.search(
        r"DimensionsPropertySet\s*\([^;]*?"
        r"\((" + _FLOAT + r")\s*,\s*(" + _FLOAT + r")\s*,\s*(" + _FLOAT + r")\)"
        r"\s*,\s*"
        r"\((" + _FLOAT + r")\s*,\s*(" + _FLOAT + r")\s*,\s*(" + _FLOAT + r")\)",
        step,
    )
    if not m:
        raise ExportError("template .dxobj: DimensionsPropertySet not found in STEP data")
    g = [_parse_step_float(x) for x in m.groups()]
    return (g[0], g[1], g[2]), (g[3], g[4], g[5])


def read_dxobj_template(template_path: str | Path) -> DxobjTemplateInfo:
    """Inspect a template ``.dxobj`` without modifying it."""
    with zipfile.ZipFile(template_path) as z:
        names = set(z.namelist())
        if _STEP_MEMBER not in names:
            raise ExportError(
                f"not a recognised DIALux .dxobj (missing {_STEP_MEMBER}); "
                f"got members: {sorted(names)[:6]}..."
            )
        step = z.read(_STEP_MEMBER).decode("utf-8-sig", "replace")
        title = "Tree"
        if _ARCHIVE_INFO in names:
            ai = z.read(_ARCHIVE_INFO).decode("utf-8-sig", "replace")
            tm = _re.search(r"<Title>(.*?)</Title>", ai)
            if tm:
                title = tm.group(1) or "Tree"
    dims, minpos = _read_dimensions(step)
    return DxobjTemplateInfo(dimensions=dims, min_position=minpos, title=title)


def _fmt_step_real(v: float) -> str:
    """Format a real in STEP style (e.g. 4.0 -> '4.', 4.25 -> '4.25')."""
    if v == int(v):
        return f"{int(v)}."
    return repr(round(v, 6))


def _fmt_triplet(t: tuple[float, float, float]) -> str:
    return "(" + ", ".join(_fmt_step_real(x) for x in t) + ")"


def _rewrite_step(step: str, target_dims: tuple[float, float, float], title: str) -> str:
    """Rewrite dimensions, min-position and all ScaleFactors in the STEP text."""
    tmpl_dims, _ = _read_dimensions(step)
    scale: tuple[float, float, float] = (
        (target_dims[0] / tmpl_dims[0]) if tmpl_dims[0] else 1.0,
        (target_dims[1] / tmpl_dims[1]) if tmpl_dims[1] else 1.0,
        (target_dims[2] / tmpl_dims[2]) if tmpl_dims[2] else 1.0,
    )
    # tree centred in X/Y, base at ground
    new_min = (-target_dims[0] / 2.0, -target_dims[1] / 2.0, 0.0)

    # 1) DimensionsPropertySet: replace the two triplets that follow it
    def _dim_sub(m: _re.Match) -> str:
        head = m.group(1)
        return head + _fmt_triplet(target_dims) + ", " + _fmt_triplet(new_min)

    step = _re.sub(
        r"(DimensionsPropertySet\s*\([^;]*?)"
        r"\(" + _FLOAT + r"\s*,\s*" + _FLOAT + r"\s*,\s*" + _FLOAT + r"\)"
        r"\s*,\s*"
        r"\(" + _FLOAT + r"\s*,\s*" + _FLOAT + r"\s*,\s*" + _FLOAT + r"\)",
        _dim_sub,
        step,
        count=1,
    )

    # 2) ScaleFactors: the (1., 1., 1.) triplets in the representation entities.
    #    Replace every unit-scale triplet with the computed scale.
    unit = _re.compile(r"\(\s*1\.?\s*,\s*1\.?\s*,\s*1\.?\s*\)")
    step = unit.sub(_fmt_triplet(scale), step)
    return step


def rewrite_dxobj(
    result: TreeGeometryResult,
    template_path: str | Path,
    out_path: str | Path,
) -> Path:
    """Rewrite a template ``.dxobj`` to match one computed tree's geometry.

    Only the STEP dimensions / scale factors and the ArchiveInfo title+GUID are
    changed; the template's proprietary mesh streams are copied verbatim and
    resized by DIALux via the scale factors on import.

    Raises :class:`ExportError` if the result lacks the geometry to size the
    bounding box, or the template is not a recognised ``.dxobj``.
    """
    for field in ("height_m", "crown_diameter_x_m", "crown_diameter_y_m"):
        if getattr(result, field) is None:
            raise ExportError(f"cannot rewrite .dxobj for {result.tree_id!r}: missing {field}")
    target_dims = (
        float(result.crown_diameter_x_m),  # type: ignore[arg-type]
        float(result.crown_diameter_y_m),  # type: ignore[arg-type]
        float(result.height_m),  # type: ignore[arg-type]
    )
    title = (result.common_name or result.tree_id or "Tree").strip()

    src = Path(template_path)
    out = Path(out_path)
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        if _STEP_MEMBER not in names:
            raise ExportError(f"not a recognised DIALux .dxobj (missing {_STEP_MEMBER})")
        contents = {n: zin.read(n) for n in names}

    step = contents[_STEP_MEMBER].decode("utf-8-sig", "replace")
    new_step = _rewrite_step(step, target_dims, title)
    # preserve the UTF-8 BOM the DIALux writer uses
    contents[_STEP_MEMBER] = b"\xef\xbb\xbf" + new_step.encode("utf-8")

    if _ARCHIVE_INFO in contents:
        ai = contents[_ARCHIVE_INFO].decode("utf-8-sig", "replace")
        ai = _re.sub(r"<Title>.*?</Title>", f"<Title>{title}</Title>", ai, count=1)
        ai = _re.sub(
            r"<UniqueName>.*?</UniqueName>",
            f"<UniqueName>{_uuid.uuid4()}</UniqueName>",
            ai,
            count=1,
        )
        contents[_ARCHIVE_INFO] = b"\xef\xbb\xbf" + ai.encode("utf-8")

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:  # preserve original member order
            zout.writestr(n, contents[n])
    out.write_bytes(buf.getvalue())
    return out
