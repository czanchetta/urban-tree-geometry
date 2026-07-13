// Schematic (NOT to-scale-precise) tree diagram driven by computed geometry.
// Draws trunk, crown ellipse and dimension annotations for total height,
// crown diameter, crown base height, crown depth and trunk diameter.
// Returns an SVG string; the caller injects it into the DOM.
import { TreeGeometryResult } from "./pipeline";
import { fmt } from "./format";

export function treeSchematicSVG(r: TreeGeometryResult): string {
  const H = r.height_m;
  if (H === null || H <= 0) {
    return `<svg viewBox="0 0 420 360" role="img" aria-label="no diagram">
      <text x="210" y="180" text-anchor="middle" fill="#8a8f98" font-size="13">
        No geometry to display</text></svg>`;
  }
  const crownD = r.crown_diameter_x_m ?? 0;
  const crownBase = r.crown_base_height_m ?? 0;
  const crownDepth = r.crown_depth_m ?? 0;
  const trunkD = r.trunk_diameter_m ?? 0;

  // Layout: fixed canvas; vertical scale maps 0..H to plot area.
  const W = 460;
  const Hpx = 380;
  const padTop = 24;
  const padBottom = 34;
  const groundY = Hpx - padBottom;
  const plotH = groundY - padTop;
  const axisX = 92; // vertical dimension axis on the left
  const centerX = 250; // trunk centre
  const vscale = plotH / Math.max(H, 1e-6);

  const yOf = (m: number) => groundY - m * vscale;

  // Widths (schematic): scale crown/trunk to a sensible fraction of canvas.
  const maxCrownPx = 150;
  const crownScale = crownD > 0 ? maxCrownPx / Math.max(crownD, 1e-6) : 0;
  const crownRx = Math.max(8, (crownD * crownScale) / 2);
  const crownCyTop = yOf(H);
  const crownCyBottom = yOf(crownBase);
  const crownCy = (crownCyTop + crownCyBottom) / 2;
  const crownRy = Math.max(8, (crownCyBottom - crownCyTop) / 2);
  const trunkW = Math.max(6, Math.min(26, trunkD * 60));

  const rightAxisX = W - 70; // right-side dimension column (for crown depth)
  const dim = (y1: number, y2: number, label: string, side: "left" | "right" = "left") => {
    const yy1 = Math.min(y1, y2);
    const yy2 = Math.max(y1, y2);
    const mid = (yy1 + yy2) / 2;
    const x = side === "left" ? axisX : rightAxisX;
    const tx = side === "left" ? x - 9 : x + 9;
    const anchor = side === "left" ? "end" : "start";
    return `
      <line x1="${x}" y1="${yy1}" x2="${x}" y2="${yy2}" class="dim-line"/>
      <line x1="${x - 5}" y1="${yy1}" x2="${x + 5}" y2="${yy1}" class="dim-tick"/>
      <line x1="${x - 5}" y1="${yy2}" x2="${x + 5}" y2="${yy2}" class="dim-tick"/>
      <text x="${tx}" y="${mid + 4}" text-anchor="${anchor}" class="dim-label">${label}</text>`;
  };

  return `<svg viewBox="0 0 ${W} ${Hpx}" role="img"
      aria-label="Schematic tree: total height ${fmt(H, 1)} m, crown diameter ${fmt(crownD, 1)} m">
    <style>
      .ground{stroke:#9aa0a6;stroke-width:1.4}
      .trunk{fill:#8a5a2b}
      .crown{fill:#4f8a5b;fill-opacity:0.55;stroke:#3c6b46;stroke-width:1.4}
      .dim-line{stroke:#5b6169;stroke-width:1}
      .dim-tick{stroke:#5b6169;stroke-width:1}
      .dim-label{fill:#3a3f45;font-size:11px;font-family:inherit}
      .cd-line{stroke:#5b6169;stroke-width:1}
      .cd-label{fill:#3a3f45;font-size:11px;font-family:inherit}
      .note{fill:#8a8f98;font-size:10px;font-family:inherit}
    </style>
    <line x1="40" y1="${groundY}" x2="${W - 20}" y2="${groundY}" class="ground"/>
    <rect x="${centerX - trunkW / 2}" y="${yOf(crownBase)}" width="${trunkW}"
          height="${groundY - yOf(crownBase)}" class="trunk" rx="2"/>
    <ellipse cx="${centerX}" cy="${crownCy}" rx="${crownRx}" ry="${crownRy}" class="crown"/>
    ${dim(yOf(H), groundY, `Z=${fmt(H, 1)} m`)}
    ${dim(yOf(crownBase), groundY, `base ${fmt(crownBase, 1)}`)}
    ${dim(crownCyTop, crownCyBottom, `copa ${fmt(crownDepth, 1)}`, "right")}
    <line x1="${centerX - crownRx}" y1="${crownCy}" x2="${centerX + crownRx}" y2="${crownCy}" class="cd-line"/>
    <text x="${centerX}" y="${crownCy - 6}" text-anchor="middle" class="cd-label">X=Y=${fmt(crownD, 1)} m</text>
    <text x="${centerX}" y="${groundY + 16}" text-anchor="middle" class="cd-label">trunk ${fmt(trunkD, 2)} m</text>
    <text x="${W - 20}" y="${Hpx - 6}" text-anchor="end" class="note">schematic — not to scale</text>
  </svg>`;
}
