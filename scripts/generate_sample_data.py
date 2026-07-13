"""Generate a synthetic, anonymised demonstration inventory.

The output preserves the *statistical variety* of a real urban inventory
(species mix, perimeter distribution, small/medium/large trees, a palm, a
low-confidence genus-only record, and an intentionally unrecognised species)
WITHOUT reproducing any client identifiers, project name, location, or the
original tree IDs. All identifiers here are synthetic.

Run:
    python scripts/generate_sample_data.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "sample_tree_inventory.csv"

SEED = 20260713

# (common_name, scientific_name, perimeter_range_cm) drawn from the parameter
# set so species resolve; ranges span small/medium/large.
SPECIES_POOL = [
    ("AMENDOIM DO CAMPO", "Platypodium elegans", (150, 240)),
    ("ANGICO BRANCO", "Anadenanthera colubrina", (35, 290)),
    ("COPAÍBA", "Copaifera langsdorffii", (50, 55)),
    ("IPÊ BRANCO", "Tabebuia roseoalba", (40, 200)),
    ("IPÊ AMARELO", "Handroanthus albus", (30, 45)),
    ("FICUS", "Ficus benjamina", (33, 60)),
    ("ACÁCIA MIMOSA", "Acacia podalyriifolia", (40, 120)),
    ("LEUCENA", "Leucaena leucocephala", (35, 110)),
    ("PITANGA", "Eugenia uniflora", (60, 90)),
    ("OITI", "Licania tomentosa", (70, 100)),
    ("PAINEIRA VERMELHA", "Bombax ceiba", (90, 110)),
    ("EUCALIPTO", "Eucalyptus sp.", (250, 340)),
    ("JACARANDÁ MIMOSO", "Jacaranda mimosifolia", (180, 210)),
    ("ACEROLA", "Malpighia glabra", (8, 20)),  # very small
]

# Explicit edge cases to guarantee variety.
FORCED = [
    # a palm (low confidence)
    ("PALMEIRA JERIVÁ", "Syagrus romanzoffiana", 55),
    # a genus/family-only, low-confidence record
    ("PATA DE VACA", "Bauhinia sp.", 40),
    # a taxonomic divergence (common vs scientific mismatch)
    ("ANGICO BRANCO", "Platypodium elegans", 330),
    # an intentionally unrecognised species (not in the parameter set)
    ("ESPÉCIE NÃO IDENTIFICADA", "", 65),
    # a very large tree (extrapolation)
    ("ANGICO BRANCO", "Anadenanthera colubrina", 520),
]


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    idx = 1

    def add(common, sci, perim):
        nonlocal idx
        rows.append(
            {
                "tree_id": f"TREE-{idx:03d}",
                "common_name": common,
                "scientific_name": sci,
                "perimeter_cm": int(round(perim)),
            }
        )
        idx += 1

    # ~25 sampled trees
    for _ in range(25):
        common, sci, (lo, hi) = rng.choice(SPECIES_POOL)
        add(common, sci, rng.uniform(lo, hi))

    # forced edge cases
    for common, sci, perim in FORCED:
        add(common, sci, perim)

    rng.shuffle(rows)
    for n, r in enumerate(rows, 1):
        r["tree_id"] = f"TREE-{n:03d}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["tree_id", "common_name", "scientific_name", "perimeter_cm"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
