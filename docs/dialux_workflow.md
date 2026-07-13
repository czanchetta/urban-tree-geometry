# DIALux workflow and 3D export

This page explains how the estimated parameters map to a 3D tree object in
outdoor-lighting software such as DIALux, and documents the two export formats
the tools can generate. DIALux functionality should always be confirmed against
the official DIALux documentation, and any generated object should be
**test-imported once** into your DIALux version before batch use.

## Parameter → geometry mapping

| Estimated parameter | Role in a 3D tree object |
|---|---|
| `total_height_z_m` | **Z** — total height of the object |
| `crown_diameter_x_m` | **X** — horizontal crown diameter |
| `crown_diameter_y_m` | **Y** — orthogonal horizontal crown diameter (= X here) |
| `trunk_diameter_m` | trunk cylinder diameter, when modelled separately |
| `crown_base_height_m` | height from ground to the base of the crown |
| `crown_depth_m` | vertical extent of the crown body |

![Tree geometry parameters](assets/geometry.svg)

## Suggested steps (conceptual)

1. Place a tree/vegetation object at the luminaire-relevant location.
2. Set total height to **Z** (`total_height_z_m`).
3. Set the crown horizontal size using **X** and **Y**
   (`crown_diameter_x_m`, `crown_diameter_y_m`).
4. If the object supports a separate trunk and crown, set the trunk diameter
   (`trunk_diameter_m`), the crown base height (`crown_base_height_m`) and the
   crown depth (`crown_depth_m`).
5. Treat the sensitivity bands (`height_min/max_m`, `crown_min/max_m`) as
   alternative scenarios for a light-obstruction sensitivity check.

## Automatic 3D export

DIALux imports several native 3D formats (`.3ds`, `M3D`, `.SAT`, `.IFC`). The
tools generate objects sized to each computed tree in two ways:

### 1. Parametric `.3ds` (open format, recommended)

Builds a **schematic** tree — a trunk cylinder plus a crown ellipsoid — sized to
the computed `trunk_diameter_m`, `crown_diameter_x/y_m`, `crown_base_height_m`,
`crown_depth_m` and total height `Z`, and writes it as a valid Autodesk 3D
Studio `.3ds` binary (a documented, open chunk format).

```bash
urban-tree-geometry export-3ds -i inventory.csv -o outputs/3ds/
```

In the browser app, the single-tree view has an **Export .3ds** button (for the
displayed min/central/max scenario) and the batch view offers **Baixar .3ds
(ZIP)** — one `.3ds` per tree, generated entirely in the browser.

The mesh is a **heuristic stand-in volume** for lighting pre-modelling, not a
botanically accurate model. The Python and TypeScript writers are verified to
emit byte-identical output for the same tree (`web/test/dialux3ds.test.ts`).

### 2. Template-driven `.dxobj` (native DIALux mesh)

If you own a DIALux tree `.dxobj`, the rewriter reuses that object's own mesh and
only resizes it: it rewrites the STEP `DimensionsPropertySet` bounding box and
the `ScaleFactors` so the template is stretched to `(crown_X, crown_Y, height)`,
regenerates the object GUID and title, and re-packs the archive. The proprietary
mesh bytes are copied verbatim.

```bash
urban-tree-geometry export-dxobj -i inventory.csv -t MyTree.dxobj -o outputs/dxobj/
```

!!! warning "Template is your own DIALux asset"
    A `.dxobj` template is a proprietary DIALux file. It is **never** committed
    to this repository — supply it at runtime via `--template`. Generated
    `.dxobj`/`.3ds` files and any `data/templates/` directory are git-ignored.

    Because one template mesh is anisotropically scaled, every tree takes the
    same silhouette resized; the `.3ds` path gives a distinct trunk/crown volume
    per tree.

### Validation caveat

Neither exporter can be validated from outside DIALux. **Import one generated
file into your DIALux version once** to confirm scale, orientation (Z up) and
placement before relying on a batch. Round-trip structure (chunk validity, STEP
dimensions/scale factors, preserved mesh) is covered by the automated tests.

## Important

- When a field survey is available, replace **X** and **Y** with the two real
  orthogonal crown diameters measured on site — real crowns are rarely circular.
- For trees that directly obstruct or are illuminated by a fixture, measure the
  tree in the field; a preliminary estimate is not sufficient for photometric
  decisions.
- The `dialux` sheet in `outputs/sample_results.xlsx` and
  `data/processed/dialux_tree_parameters.csv` contain fixed values only (no
  formulas), suitable as a hand-off table.
