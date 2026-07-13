"""Input validation for inventory tables.

Validation is intentionally permissive: rather than reject an entire file for a
single bad row, it reports issues per row so the pipeline can still process the
good records and attach warnings to the rest.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import TreeInput

# A perimeter above this (cm) is suspicious for an urban tree and likely a unit
# error (e.g. a value entered in mm). Flag, do not reject.
SUSPICIOUS_PERIMETER_CM = 700.0


@dataclass
class ValidationIssue:
    tree_id: str
    level: str  # "error" | "warning"
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def n_errors(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def n_warnings(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    @property
    def ok(self) -> bool:
        return self.n_errors == 0

    def add(self, tree_id: str, level: str, message: str) -> None:
        self.issues.append(ValidationIssue(tree_id, level, message))


REQUIRED_COLUMNS = {"tree_id", "perimeter_cm"}


def validate_columns(columns: list[str]) -> list[str]:
    """Return the list of missing required columns (empty if all present)."""
    present = {c.strip().lower() for c in columns}
    return sorted(REQUIRED_COLUMNS - present)


def validate_tree(tree: TreeInput) -> ValidationReport:
    """Validate a single record."""
    report = ValidationReport()
    tid = tree.tree_id or "<no id>"

    if tree.perimeter_cm is None:
        report.add(tid, "warning", "perimeter is missing; row cannot be estimated")
    elif tree.perimeter_cm < 0:
        report.add(tid, "error", f"perimeter is negative ({tree.perimeter_cm} cm)")
    elif tree.perimeter_cm == 0:
        report.add(tid, "warning", "perimeter is zero; row cannot be estimated")
    elif tree.perimeter_cm > SUSPICIOUS_PERIMETER_CM:
        report.add(
            tid,
            "warning",
            f"perimeter {tree.perimeter_cm} cm is unusually large; check units (cm, not mm).",
        )

    if not tree.common_name:
        report.add(tid, "warning", "common name is missing; species parameters cannot be matched")

    return report


def validate_trees(trees: list[TreeInput]) -> ValidationReport:
    """Validate a list of records into a single report."""
    combined = ValidationReport()
    seen: set[str] = set()
    for tree in trees:
        if tree.tree_id in seen:
            combined.add(tree.tree_id, "warning", "duplicate tree_id")
        seen.add(tree.tree_id)
        combined.issues.extend(validate_tree(tree).issues)
    return combined
