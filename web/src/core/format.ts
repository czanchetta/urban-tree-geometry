// Small display helpers shared by the UI (locale-aware number formatting).
export function fmt(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function confidenceLabel(c: string): { text: string; cls: string } {
  switch (c) {
    case "high":
      return { text: "high", cls: "conf-high" };
    case "medium":
      return { text: "medium", cls: "conf-medium" };
    default:
      return { text: "low", cls: "conf-low" };
  }
}
