import "./style.css";
import { CONFIG } from "./config";
import { allSpecies, getSpecies } from "./core/params";
import { processTree, TreeGeometryResult, TreeInput } from "./core/pipeline";
import { treeSchematicSVG } from "./core/schematic";
import { fmt, confidenceLabel } from "./core/format";
import { mountBatch } from "./batch";

type Scenario = "min" | "central" | "max";

const app = document.querySelector<HTMLDivElement>("#app")!;

const DISCLAIMER = `Ferramenta de <strong>pré-modelagem</strong>. A altura reproduz o modelo
da planilha de origem; o dossel e os parâmetros X/Y/Z são uma camada <strong>heurística</strong>
(não medida, não calibrada). Não substitui levantamento em campo. Processamento
100% no seu navegador — nenhum dado é enviado a servidores.`;

app.innerHTML = `
  <div class="wrap">
    <header class="site">
      <img src="${CONFIG.logoPath}" alt="logo" onerror="this.style.display='none'"/>
      <div>
        <h1>Tree Geometry Estimator — DIALux</h1>
        <p>Altura, dossel e parâmetros X/Y/Z a partir de espécie e perímetro do tronco</p>
      </div>
    </header>
    <div class="disclaimer">${DISCLAIMER}</div>
    <div class="grid">
      <section class="card" aria-label="Entrada e resultado">
        <h2>Cálculo individual</h2>
        <form id="single-form" autocomplete="off">
          <label for="species">Espécie (nome popular)</label>
          <input id="species" list="species-list" placeholder="ex.: ANGICO BRANCO" />
          <datalist id="species-list"></datalist>
          <label for="sciname">Nome científico (opcional)</label>
          <input id="sciname" placeholder="ex.: Anadenanthera colubrina" />
          <div class="row">
            <div>
              <label for="perimeter">Perímetro do tronco (cm)</label>
              <input id="perimeter" type="number" min="0" step="0.1" inputmode="decimal" placeholder="ex.: 330" />
            </div>
          </div>
          <div class="btns">
            <button type="submit" class="primary">Calcular</button>
            <button type="button" class="ghost" id="clear-btn">Limpar</button>
          </div>
        </form>
        <div id="result" aria-live="polite"></div>
      </section>
      <section class="card" aria-label="Diagrama esquemático">
        <h2>Diagrama esquemático</h2>
        <div class="scenario-tabs" id="scenario-tabs" role="group" aria-label="Cenário">
          <button type="button" data-s="min">Mínimo</button>
          <button type="button" data-s="central" aria-pressed="true">Central</button>
          <button type="button" data-s="max">Máximo</button>
        </div>
        <div class="schematic" id="schematic"></div>
        <p class="small">O diagrama é esquemático (proporções aproximadas), para leitura rápida das dimensões.</p>
      </section>
    </div>
    <section class="card" style="margin-top:1.25rem" aria-label="Importação em lote">
      <h2>Processamento em lote (CSV / XLSX)</h2>
      <div id="batch"></div>
    </section>
    <footer class="site">
      <div>${CONFIG.authorName}${CONFIG.authorTitle ? " — " + CONFIG.authorTitle : ""}</div>
      <div class="small">Sem analytics nem rastreadores. Código: <a href="${CONFIG.repoUrl}">${CONFIG.repoUrl}</a></div>
    </footer>
  </div>
`;

// Populate species datalist
const dl = document.querySelector<HTMLDataListElement>("#species-list")!;
for (const sp of allSpecies().sort((a, b) => a.common_name.localeCompare(b.common_name))) {
  const opt = document.createElement("option");
  opt.value = sp.common_name;
  opt.label = sp.scientific_name ?? "";
  dl.appendChild(opt);
}

const form = document.querySelector<HTMLFormElement>("#single-form")!;
const speciesInput = document.querySelector<HTMLInputElement>("#species")!;
const sciInput = document.querySelector<HTMLInputElement>("#sciname")!;
const perimInput = document.querySelector<HTMLInputElement>("#perimeter")!;
const resultDiv = document.querySelector<HTMLDivElement>("#result")!;
const schematicDiv = document.querySelector<HTMLDivElement>("#schematic")!;
const scenarioTabs = document.querySelector<HTMLDivElement>("#scenario-tabs")!;

let current: TreeGeometryResult | null = null;
let scenario: Scenario = "central";

// Autofill scientific name when a known species is chosen and the field is empty.
speciesInput.addEventListener("change", () => {
  const sp = getSpecies(speciesInput.value);
  if (sp && sp.scientific_name && !sciInput.value.trim()) {
    sciInput.value = sp.scientific_name;
  }
});

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const perim = perimInput.value.trim() === "" ? null : Number(perimInput.value);
  const input: TreeInput = {
    tree_id: "single",
    common_name: speciesInput.value.trim(),
    scientific_name: sciInput.value.trim() || null,
    perimeter_cm: perim,
  };
  current = processTree(input);
  scenario = "central";
  setScenarioPressed();
  render();
});

document.querySelector<HTMLButtonElement>("#clear-btn")!.addEventListener("click", () => {
  speciesInput.value = "";
  sciInput.value = "";
  perimInput.value = "";
  current = null;
  resultDiv.innerHTML = "";
  schematicDiv.innerHTML = "";
});

scenarioTabs.addEventListener("click", (e) => {
  const t = e.target as HTMLElement;
  if (t.tagName === "BUTTON" && t.dataset.s) {
    scenario = t.dataset.s as Scenario;
    setScenarioPressed();
    render();
  }
});

function setScenarioPressed() {
  scenarioTabs.querySelectorAll("button").forEach((b) => {
    b.setAttribute("aria-pressed", String((b as HTMLElement).dataset.s === scenario));
  });
}

function scaledForScenario(r: TreeGeometryResult): TreeGeometryResult {
  if (scenario === "central" || r.height_m === null) return r;
  const clone: TreeGeometryResult = { ...r };
  if (scenario === "min") {
    clone.height_m = r.height_min_m;
    clone.crown_diameter_x_m = r.crown_min_m;
    clone.crown_diameter_y_m = r.crown_min_m;
  } else {
    clone.height_m = r.height_max_m;
    clone.crown_diameter_x_m = r.crown_max_m;
    clone.crown_diameter_y_m = r.crown_max_m;
  }
  return clone;
}

function render() {
  if (!current) return;
  const r = current;
  const conf = confidenceLabel(r.confidence);
  const warnings = r.warnings.length
    ? `<ul class="warnings">${r.warnings.map((w) => `<li>${escapeHtml(w)}</li>`).join("")}</ul>`
    : `<p class="small">Sem alertas.</p>`;

  const rows: [string, string, string][] = [
    ["DAP", fmt(r.dbh_cm, 1) + (r.dbh_cm !== null ? " cm" : ""), "derivado"],
    ["Diâmetro do tronco", fmt(r.trunk_diameter_m, 4) + (r.trunk_diameter_m !== null ? " m" : ""), "derivado"],
    ["Altura total (Z)", fmt(r.height_m, 1) + (r.height_m !== null ? " m" : ""), "derivado (adotado H∞,k)"],
    ["Altura mín / máx", `${fmt(r.height_min_m, 1)} / ${fmt(r.height_max_m, 1)} m`, "faixa operacional"],
    ["Diâmetro do dossel (X=Y)", fmt(r.crown_diameter_x_m, 2) + (r.crown_diameter_x_m !== null ? " m" : ""), "heurístico"],
    ["Altura da base da copa", fmt(r.crown_base_height_m, 2) + (r.crown_base_height_m !== null ? " m" : ""), "heurístico"],
    ["Profundidade da copa", fmt(r.crown_depth_m, 2) + (r.crown_depth_m !== null ? " m" : ""), "heurístico"],
    ["Área projetada", fmt(r.crown_projected_area_m2, 2) + (r.crown_projected_area_m2 !== null ? " m²" : ""), "heurístico"],
    ["Dossel mín / máx", `${fmt(r.crown_min_m, 2)} / ${fmt(r.crown_max_m, 2)} m`, "faixa operacional"],
  ];

  resultDiv.innerHTML = `
    <div style="margin:0.6rem 0 0.3rem">
      Confiabilidade: <span class="pill ${conf.cls}">${conf.text}</span>
      ${r.crown_group ? `<span class="small"> · grupo de copa: ${r.crown_group}</span>` : ""}
    </div>
    <table>
      <thead><tr><th>Parâmetro</th><th class="num">Valor</th><th>Proveniência</th></tr></thead>
      <tbody>
        ${rows.map(([k, v, p]) => `<tr><td>${k}</td><td class="num">${v}</td><td class="provenance">${p}</td></tr>`).join("")}
      </tbody>
    </table>
    ${warnings}
  `;
  schematicDiv.innerHTML = treeSchematicSVG(scaledForScenario(r));
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string,
  );
}

// Mount the batch import/export panel.
mountBatch(document.querySelector<HTMLDivElement>("#batch")!);
