// In-browser batch processing: CSV/XLSX import -> column mapping -> validation
// -> compute -> CSV/XLSX export. All local; nothing is uploaded. XLSX support
// is lazy-loaded (dynamic import) so it does not weigh down the initial bundle.
import Papa from "papaparse";
import { processTree, TreeGeometryResult, TreeInput } from "./core/pipeline";
import { fmt, confidenceLabel } from "./core/format";

// Canonical fields the app needs, and Portuguese/English header aliases used to
// auto-guess the mapping (mirrors the Python io._INPUT_ALIASES intent).
const TARGETS = [
  { key: "tree_id", label: "ID da árvore", required: false,
    aliases: ["tree_id", "id", "ua", "codigo", "código", "arvore", "árvore"] },
  { key: "common_name", label: "Nome popular", required: true,
    aliases: ["common_name", "nome_popular", "nome popular", "especie", "espécie", "nome", "popular"] },
  { key: "scientific_name", label: "Nome científico", required: false,
    aliases: ["scientific_name", "nome_cientifico", "nome científico", "cientifico", "científico"] },
  { key: "perimeter_cm", label: "Perímetro (cm)", required: true,
    aliases: ["perimeter_cm", "perimetro_cm", "perímetro_cm", "perimetro", "perímetro", "cap", "circunferencia", "circunferência", "perimeter"] },
] as const;

type RawRow = Record<string, string>;

interface State {
  headers: string[];
  rows: RawRow[];
  mapping: Record<string, string>; // targetKey -> header
  results: TreeGeometryResult[] | null;
}

const state: State = { headers: [], rows: [], mapping: {}, results: null };
let root: HTMLElement;

export function mountBatch(el: HTMLElement): void {
  root = el;
  root.innerHTML = `
    <div class="filedrop" id="filedrop">
      <p><strong>Arraste um CSV/XLSX</strong> ou
        <label style="display:inline"><a href="#" id="pick">selecione um arquivo</a>
          <input id="file" type="file" accept=".csv,.xlsx,.xls,text/csv" hidden />
        </label>
      </p>
      <p class="small">Os dados são processados no seu navegador e não saem do dispositivo.</p>
    </div>
    <div id="batch-body"></div>
  `;
  const fileInput = root.querySelector<HTMLInputElement>("#file")!;
  root.querySelector<HTMLAnchorElement>("#pick")!.addEventListener("click", (e) => {
    e.preventDefault();
    fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) void loadFile(fileInput.files[0]);
  });
  const drop = root.querySelector<HTMLDivElement>("#filedrop")!;
  ["dragover", "dragenter"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.style.borderColor = "var(--accent)"; }));
  ["dragleave", "drop"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.style.borderColor = "var(--line)"; }));
  drop.addEventListener("drop", (e) => {
    const f = e.dataTransfer?.files?.[0];
    if (f) void loadFile(f);
  });
}

async function loadFile(file: File): Promise<void> {
  const name = file.name.toLowerCase();
  try {
    if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
      const XLSX = await import("xlsx"); // lazy
      const buf = await file.arrayBuffer();
      const wb = XLSX.read(buf, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json<RawRow>(ws, { defval: "", raw: false });
      ingest(json);
    } else {
      const text = await file.text();
      const parsed = Papa.parse<RawRow>(text, { header: true, skipEmptyLines: true });
      ingest(parsed.data);
    }
  } catch (err) {
    renderError(`Falha ao ler o arquivo: ${(err as Error).message}`);
  }
}

function ingest(rows: RawRow[]): void {
  if (!rows.length) { renderError("Arquivo vazio ou sem linhas de dados."); return; }
  state.rows = rows;
  state.headers = Object.keys(rows[0]);
  state.mapping = guessMapping(state.headers);
  state.results = null;
  renderMappingAndPreview();
}

function guessMapping(headers: string[]): Record<string, string> {
  const norm = (s: string) => s.trim().toLowerCase();
  const m: Record<string, string> = {};
  for (const t of TARGETS) {
    const hit = headers.find((h) => (t.aliases as readonly string[]).includes(norm(h)));
    if (hit) m[t.key] = hit;
  }
  return m;
}

function renderMappingAndPreview(): void {
  const body = root.querySelector<HTMLDivElement>("#batch-body")!;
  const previewRows = state.rows.slice(0, 8);
  body.innerHTML = `
    <div class="mapping">
      ${TARGETS.map((t) => `
        <label style="margin:0">${t.label}${t.required ? " *" : ""}</label>
        <select data-target="${t.key}">
          <option value="">— não mapeado —</option>
          ${state.headers.map((h) => `<option value="${escapeAttr(h)}" ${state.mapping[t.key] === h ? "selected" : ""}>${escapeHtml(h)}</option>`).join("")}
        </select>
      `).join("")}
    </div>
    <div class="btns">
      <button type="button" class="primary" id="compute-btn">Calcular ${state.rows.length} linha(s)</button>
    </div>
    <div id="validation"></div>
    <div class="preview-wrap">
      <table>
        <thead><tr>${state.headers.map((h) => `<th>${escapeHtml(h)}</th>`).join("")}</tr></thead>
        <tbody>
          ${previewRows.map((r) => `<tr>${state.headers.map((h) => `<td>${escapeHtml(String(r[h] ?? ""))}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
      ${state.rows.length > previewRows.length ? `<p class="small">Prévia de ${previewRows.length} de ${state.rows.length} linhas.</p>` : ""}
    </div>
    <div id="batch-results"></div>
  `;
  body.querySelectorAll<HTMLSelectElement>("select[data-target]").forEach((sel) => {
    sel.addEventListener("change", () => {
      const k = sel.dataset.target!;
      if (sel.value) state.mapping[k] = sel.value; else delete state.mapping[k];
    });
  });
  body.querySelector<HTMLButtonElement>("#compute-btn")!.addEventListener("click", compute);
}

function validate(): string[] {
  const problems: string[] = [];
  for (const t of TARGETS) {
    if (t.required && !state.mapping[t.key]) {
      problems.push(`Coluna obrigatória não mapeada: ${t.label}.`);
    }
  }
  return problems;
}

function compute(): void {
  const problems = validate();
  const vdiv = root.querySelector<HTMLDivElement>("#validation")!;
  if (problems.length) {
    vdiv.innerHTML = `<ul class="warnings">${problems.map((p) => `<li>${escapeHtml(p)}</li>`).join("")}</ul>`;
    return;
  }
  vdiv.innerHTML = "";
  const results: TreeGeometryResult[] = [];
  state.rows.forEach((row, i) => {
    const get = (k: string) => (state.mapping[k] ? row[state.mapping[k]] : undefined);
    const perimRaw = get("perimeter_cm");
    const perim = perimRaw === undefined || String(perimRaw).trim() === ""
      ? null : Number(String(perimRaw).replace(",", "."));
    const input: TreeInput = {
      tree_id: (get("tree_id") ?? `row-${i + 1}`).toString(),
      common_name: (get("common_name") ?? "").toString(),
      scientific_name: (get("scientific_name") ?? "").toString() || null,
      perimeter_cm: perim === null || Number.isNaN(perim) ? null : perim,
    };
    results.push(processTree(input));
  });
  state.results = results;
  renderResults(results);
}

function renderResults(results: TreeGeometryResult[]): void {
  const div = root.querySelector<HTMLDivElement>("#batch-results")!;
  const nWarn = results.filter((r) => r.warnings.length).length;
  const conf = { low: 0, medium: 0, high: 0 } as Record<string, number>;
  results.forEach((r) => (conf[r.confidence] += 1));
  const head = ["ID", "Popular", "Z (m)", "Dossel X=Y (m)", "Base (m)", "Prof. (m)", "Área (m²)", "Conf.", "Alertas"];
  const rowsHtml = results.map((r) => {
    const c = confidenceLabel(r.confidence);
    return `<tr>
      <td>${escapeHtml(r.tree_id)}</td>
      <td>${escapeHtml(r.common_name)}</td>
      <td class="num">${fmt(r.height_m, 1)}</td>
      <td class="num">${fmt(r.crown_diameter_x_m, 2)}</td>
      <td class="num">${fmt(r.crown_base_height_m, 2)}</td>
      <td class="num">${fmt(r.crown_depth_m, 2)}</td>
      <td class="num">${fmt(r.crown_projected_area_m2, 2)}</td>
      <td><span class="pill ${c.cls}">${c.text}</span></td>
      <td class="num">${r.warnings.length || ""}</td>
    </tr>`;
  }).join("");
  div.innerHTML = `
    <div style="margin:0.75rem 0 0.4rem">
      <strong>${results.length}</strong> processadas ·
      confiabilidade low=${conf.low}, medium=${conf.medium}, high=${conf.high} ·
      ${nWarn} com alertas
    </div>
    <div class="btns">
      <button type="button" class="primary" id="dl-csv">Baixar CSV</button>
      <button type="button" class="ghost" id="dl-xlsx">Baixar XLSX</button>
    </div>
    <div class="preview-wrap">
      <table>
        <thead><tr>${head.map((h) => `<th class="${h.includes("(") || h === "Alertas" ? "num" : ""}">${h}</th>`).join("")}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
  `;
  div.querySelector<HTMLButtonElement>("#dl-csv")!.addEventListener("click", () => downloadCSV(results));
  div.querySelector<HTMLButtonElement>("#dl-xlsx")!.addEventListener("click", () => void downloadXLSX(results));
}

// DIALux-oriented export columns (mirror Python io.DIALUX_COLUMNS).
const EXPORT_COLUMNS: [string, (r: TreeGeometryResult) => unknown][] = [
  ["tree_id", (r) => r.tree_id],
  ["common_name", (r) => r.common_name],
  ["scientific_name", (r) => r.scientific_name ?? ""],
  ["total_height_z_m", (r) => r.height_m],
  ["crown_diameter_x_m", (r) => r.crown_diameter_x_m],
  ["crown_diameter_y_m", (r) => r.crown_diameter_y_m],
  ["trunk_diameter_m", (r) => r.trunk_diameter_m],
  ["crown_base_height_m", (r) => r.crown_base_height_m],
  ["crown_depth_m", (r) => r.crown_depth_m],
  ["crown_projected_area_m2", (r) => r.crown_projected_area_m2],
  ["crown_min_m", (r) => r.crown_min_m],
  ["crown_max_m", (r) => r.crown_max_m],
  ["height_min_m", (r) => r.height_min_m],
  ["height_max_m", (r) => r.height_max_m],
  ["confidence", (r) => r.confidence],
  ["warnings", (r) => r.warnings.join("; ")],
];

function toRecords(results: TreeGeometryResult[]): Record<string, unknown>[] {
  return results.map((r) => {
    const o: Record<string, unknown> = {};
    for (const [k, f] of EXPORT_COLUMNS) o[k] = f(r);
    return o;
  });
}

function downloadCSV(results: TreeGeometryResult[]): void {
  const csv = Papa.unparse(toRecords(results), { columns: EXPORT_COLUMNS.map(([k]) => k) });
  triggerDownload(new Blob([csv], { type: "text/csv;charset=utf-8" }), "dialux_tree_parameters.csv");
}

async function downloadXLSX(results: TreeGeometryResult[]): Promise<void> {
  const XLSX = await import("xlsx");
  const ws = XLSX.utils.json_to_sheet(toRecords(results), { header: EXPORT_COLUMNS.map(([k]) => k) });
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "dialux");
  const out = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  triggerDownload(new Blob([out], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }), "dialux_tree_parameters.xlsx");
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderError(msg: string): void {
  root.querySelector<HTMLDivElement>("#batch-body")!.innerHTML =
    `<ul class="warnings"><li>${escapeHtml(msg)}</li></ul>`;
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
}
function escapeAttr(s: string): string { return escapeHtml(s).replace(/`/g, "&#96;"); }
