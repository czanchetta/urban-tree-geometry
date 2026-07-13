"""Tests for the DIALux 3D exporters (.3ds writer + .dxobj rewriter).

The .dxobj test builds a SYNTHETIC minimal template in-memory — a ZIP with a
STEP data member and placeholder mesh bytes — so we never ship or depend on
DIALux's proprietary asset.
"""

from __future__ import annotations

import zipfile
from io import BytesIO

import pytest

from urban_tree_geometry import dialux_export as dx
from urban_tree_geometry.models import TreeGeometryResult, TreeInput
from urban_tree_geometry.pipeline import process_tree


@pytest.fixture
def angico(params) -> TreeGeometryResult:
    return process_tree(
        TreeInput(
            tree_id="UA01",
            common_name="ANGICO BRANCO",
            scientific_name="Anadenanthera colubrina",
            perimeter_cm=330.0,
        ),
        params,
    )


# --- .3ds writer -------------------------------------------------------------
def test_3ds_magic_and_parse(angico):
    data = dx.result_to_3ds_bytes(angico)
    assert data[:2] == b"\x4d\x4d"  # MAIN3DS little-endian
    mesh = dx.parse_3ds(data)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0


def test_3ds_chunk_length_consistent(angico):
    import struct

    data = dx.result_to_3ds_bytes(angico)
    cid, clen = struct.unpack_from("<HI", data, 0)
    assert cid == 0x4D4D
    assert clen == len(data)  # top chunk length spans the whole file


def test_3ds_extents_match_geometry(angico):
    mesh = dx.build_tree_mesh(angico)
    (mn, mx) = mesh.bounds()
    # Z spans 0 .. total height
    assert mn[2] == pytest.approx(0.0, abs=1e-4)
    assert (mx[2] - mn[2]) == pytest.approx(angico.height_m, abs=1e-3)
    # X extent equals the crown X diameter (widest ring is sampled exactly on X)
    assert (mx[0] - mn[0]) == pytest.approx(angico.crown_diameter_x_m, rel=1e-3)
    # Y extent is within the crown Y diameter (UV-sphere sampling <= true radius)
    assert (mx[1] - mn[1]) <= angico.crown_diameter_y_m + 1e-6
    assert (mx[1] - mn[1]) >= 0.95 * angico.crown_diameter_y_m


def test_3ds_roundtrip_vertices(angico):
    data = dx.result_to_3ds_bytes(angico)
    reparsed = dx.parse_3ds(data)
    built = dx.build_tree_mesh(angico)
    assert len(reparsed.vertices) == len(built.vertices)
    for (a, b, c), (x, y, z) in zip(reparsed.vertices, built.vertices, strict=False):
        assert a == pytest.approx(x, abs=1e-4)
        assert b == pytest.approx(y, abs=1e-4)
        assert c == pytest.approx(z, abs=1e-4)


def test_3ds_write_file(angico, tmp_path):
    p = dx.write_3ds(angico, tmp_path / "UA01.3ds")
    assert p.exists() and p.stat().st_size > 100


def test_3ds_unrecognised_raises(params):
    r = process_tree(
        TreeInput(tree_id="X", common_name="ESPÉCIE NÃO IDENTIFICADA", perimeter_cm=100.0), params
    )
    assert r.height_m is None
    with pytest.raises(dx.ExportError):
        dx.result_to_3ds_bytes(r)


# --- synthetic .dxobj template -----------------------------------------------
_STEP_TEMPLATE = (
    "ISO-10303-21;\r\nHEADER;\r\nFILE_SCHEMA (('DIALux'));\r\nENDSEC;\r\nDATA;\r\n"
    "#1 = FurniturePrototype (1486, 'guid', (#2), #6, #7);\r\n"
    "#2 = DimensionsPropertySet (1487, 'g2', #1, (4., 3., 4.25), (-2., -1.5, 0.));\r\n"
    "#14 = BinaryVolumeRepresentationDataPart "
    "(#10, 0, #16, .M3D., 'x%2Em3d', '1486_0', (1., 1., 1.), ());\r\n"
    "#15 = BinaryVolumeRepresentationDataPart "
    "(#10, 600000, #17, .GDMS., 'x%2Egdms', '1486_600000', (1., 1., 1.), ());\r\n"
    "ENDSEC;\r\nEND-ISO-10303-21;\r\n"
)
_ARCHIVE_XML = (
    '<?xml version="1.0" encoding="utf-8"?>\r\n<ArchiveInfo>\r\n'
    "  <UniqueName>old-guid</UniqueName>\r\n  <Title>Tree05</Title>\r\n</ArchiveInfo>\r\n"
)


def _make_template() -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("ArchiveInfo/ArchiveInfo.xml", ("\ufeff" + _ARCHIVE_XML).encode("utf-8"))
        z.writestr(
            "Project/PrototypeData_0/PrototypeData.dat",
            ("\ufeff" + _STEP_TEMPLATE).encode("utf-8"),
        )
        z.writestr("Project/Furniture/1486_0/x.m3d", b"\xde\xad\xbe\xef" * 64)  # opaque mesh
        z.writestr("Project/Furniture/1486_600000/x.gdms", b"\x00\x01\x02\x03" * 32)
    return buf.getvalue()


@pytest.fixture
def template_path(tmp_path):
    p = tmp_path / "TreeTemplate.dxobj"
    p.write_bytes(_make_template())
    return p


def test_dxobj_read_template(template_path):
    info = dx.read_dxobj_template(template_path)
    assert info.dimensions == (4.0, 3.0, 4.25)
    assert info.min_position == (-2.0, -1.5, 0.0)
    assert info.title == "Tree05"


def test_dxobj_rewrite_dimensions_and_scale(angico, template_path, tmp_path):
    out = dx.rewrite_dxobj(angico, template_path, tmp_path / "UA01.dxobj")
    info = dx.read_dxobj_template(out)
    # bounding box now (crownX, crownY, height); centred in X/Y, base at 0
    assert info.dimensions == pytest.approx(
        (angico.crown_diameter_x_m, angico.crown_diameter_y_m, angico.height_m)
    )
    assert info.min_position == pytest.approx(
        (-angico.crown_diameter_x_m / 2, -angico.crown_diameter_y_m / 2, 0.0)
    )
    assert info.title == "ANGICO BRANCO"


def test_dxobj_scale_factors_computed(angico, template_path, tmp_path):
    import re

    out = dx.rewrite_dxobj(angico, template_path, tmp_path / "UA01.dxobj")
    with zipfile.ZipFile(out) as z:
        step = z.read(dx._STEP_MEMBER).decode("utf-8-sig")
    # expected scale = target / template dims
    ex = (angico.crown_diameter_x_m / 4.0, angico.crown_diameter_y_m / 3.0, angico.height_m / 4.25)
    scales = re.findall(
        r"BinaryVolumeRepresentationDataPart[^;]*?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)\)\s*,\s*\(\)",
        step,
    )
    assert scales, "no ScaleFactors triplet found"
    for sx, sy, sz in scales:
        assert (float(sx), float(sy), float(sz)) == pytest.approx(ex, rel=1e-4)


def test_dxobj_mesh_preserved(angico, template_path, tmp_path):
    out = dx.rewrite_dxobj(angico, template_path, tmp_path / "UA01.dxobj")
    with zipfile.ZipFile(template_path) as zt, zipfile.ZipFile(out) as zo:
        assert zo.read("Project/Furniture/1486_0/x.m3d") == zt.read(
            "Project/Furniture/1486_0/x.m3d"
        )
        assert zo.read("Project/Furniture/1486_600000/x.gdms") == zt.read(
            "Project/Furniture/1486_600000/x.gdms"
        )


def test_dxobj_new_guid(angico, template_path, tmp_path):
    out = dx.rewrite_dxobj(angico, template_path, tmp_path / "UA01.dxobj")
    with zipfile.ZipFile(out) as z:
        ai = z.read("ArchiveInfo/ArchiveInfo.xml").decode("utf-8-sig")
    assert "old-guid" not in ai  # GUID regenerated


def test_dxobj_bad_template_raises(angico, tmp_path):
    bad = tmp_path / "bad.dxobj"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("random.txt", "not a dialux object")
    with pytest.raises(dx.ExportError):
        dx.rewrite_dxobj(angico, bad, tmp_path / "out.dxobj")
