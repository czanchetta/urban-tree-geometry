# urban-tree-geometry

[![tests](https://github.com/czanchetta/urban-tree-geometry/actions/workflows/tests.yml/badge.svg)](https://github.com/czanchetta/urban-tree-geometry/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

**Estimativa preliminar de altura, diâmetro do dossel e parâmetros geométricos
de árvores para modelos luminotécnicos externos (DIALux), a partir de dados de
inventário arbóreo.**

*Leia em [English](README.md).*

> **Ressalva de escopo.** Ferramenta **preliminar** para estimativa de
> parâmetros geométricos de árvores destinados à **pré-modelagem luminotécnica**,
> quando não há levantamento dendrométrico completo em campo. **Não** é modelo
> alométrico regional calibrado, inventário florestal, laudo arborístico, nem
> substituto de medição com hipsômetro, clinômetro ou levantamento topográfico.
> Não deve ser usada para supressão, compensação, estabilidade ou decisões legais.

---

## Problema

Projetos luminotécnicos externos (por exemplo no DIALux) precisam de geometria
aproximada das árvores (altura, dossel, tronco) para avaliar obstrução e
aparência. Na fase de projeto raramente há dados dendrométricos de campo —
com frequência existem apenas espécie e **perímetro do tronco**.

## Solução

A partir de um inventário mínimo (id, espécie, perímetro), o pacote produz
parâmetros geométricos preliminares, separando claramente quatro níveis de
confiança:

- **medido** — informado pelo projeto (perímetro);
- **derivado** — calculado matematicamente (DAP, altura);
- **adotado** — parâmetros de literatura por espécie (H∞, k);
- **heurístico** — hipóteses de engenharia para a geometria de dossel/DIALux.

O **núcleo de altura** reproduz fielmente uma planilha de origem e é testado por
regressão contra as suas 62 linhas. A **camada de dossel/DIALux** é uma
heurística claramente identificada e **não** é apresentada como derivada da
planilha nem validada.

![Fluxo de cálculo](images/workflow.svg)

## Duas implementações, uma fonte de verdade

O GitHub Pages serve apenas arquivos estáticos — não executa Python no
servidor. Por isso o projeto tem **duas implementações**:

1. **Pacote Python** (`src/urban_tree_geometry/`) — a referência científica:
   leitura de XLSX/CSV, validação, testes e geração de relatórios.
2. **Frontend TypeScript** (`web/`) — uma calculadora estática, que roda
   inteiramente no navegador (Vite + TypeScript, sem framework, sem servidor),
   publicada no GitHub Pages.

As duas carregam o **mesmo** arquivo de parâmetros,
[`data/species_parameters.json`](data/species_parameters.json) — os parâmetros
nunca são duplicados manualmente. Um **teste de equivalência** entre linguagens
processa um conjunto de referência compartilhado
(`tests/fixtures/equivalence_cases.json`) nas duas implementações e verifica a
igualdade campo a campo. A publicação no Pages é condicionada à aprovação dos
testes Python, dos testes TypeScript/equivalência e das duas builds. Veja
[`docs/dual_implementation.md`](docs/dual_implementation.md).

## Instalação

```bash
git clone https://github.com/czanchetta/urban-tree-geometry.git
cd urban-tree-geometry
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,viz]"
```

## Uso (CLI)

```bash
urban-tree-geometry calculate \
    --input data/raw/sample_tree_inventory.csv \
    --output outputs/tree_geometry.csv \
    --excel outputs/tree_geometry.xlsx

urban-tree-geometry validate --input data/raw/sample_tree_inventory.csv
urban-tree-geometry inspect-workbook --input planilha.xlsx
urban-tree-geometry export-excel --input outputs/tree_geometry.csv --output resultado.xlsx

# Exportação 3D DIALux — .3ds esquemático paramétrico (formato aberto, um por árvore)
urban-tree-geometry export-3ds --input data/raw/sample_tree_inventory.csv --outdir outputs/3ds/

# Exportação 3D DIALux — redimensiona um template .dxobj seu (malha proprietária, fora do git)
urban-tree-geometry export-dxobj --input data/raw/sample_tree_inventory.csv \
    --template MinhaArvore.dxobj --outdir outputs/dxobj/
```

## Formato dos dados

CSV de entrada (mínimo): `tree_id, common_name, scientific_name, perimeter_cm`
(também aceita `ua`, `especie`, `nome_cientifico`, `perimetro_cm`).

## Equações

- **DAP:** `DAP = P / π` (cm); diâmetro do tronco `= DAP / 100` (m)
- **Altura:** `H = 1,30 + (H∞ − 1,30)·[1 − exp(−DAP / k)]`, arredondada a 0,5 m
- **Faixa de altura:** `H_mín = máx(2; 0,8·H)`, `H_máx = 1,2·H` (operacional, não é IC)
- **Dossel (heurístico):** `D = mín(fator·tronco_m; limite·H)`; palmeiras `D = clip(0,35·H; 3,5; 6,0)`
- **Área do dossel:** `A = π·D²/4` (circular)

## Fluxo de processamento

`inventário → DAP → altura (+faixa) → geometria de dossel/DIALux → tabela de resultados + tabela DIALux`

## Exemplo de resultado

| tree_id | common_name | total_height_z_m | crown_diameter_x_m | trunk_diameter_m | crown_base_height_m | confidence |
|---|---|---|---|---|---|---|
| TREE-001 | ANGICO BRANCO | 22.5 | 22.5 | 1.0504 | 4.5 | medium |
| TREE-002 | COPAÍBA | 7.0 | 3.71 | 0.1687 | 2.1 | medium |
| TREE-003 | JACARANDÁ MIMOSO | 14.5 | 14.5 | 0.5984 | 2.9 | medium |
| TREE-004 | AMENDOIM DO CAMPO | 14.0 | 14.0 | 0.5761 | 2.8 | medium |
| TREE-005 | IPÊ BRANCO | 10.5 | 8.4 | 0.4011 | 3.15 | medium |

Saídas completas: [`outputs/`](outputs/) e a tabela DIALux sem fórmulas em
[`data/processed/dialux_tree_parameters.csv`](data/processed/dialux_tree_parameters.csv).

## Integração conceitual com o DIALux

`altura total → Z`, `dossel_x/y → X, Y`, além de diâmetro do tronco, base e
profundidade da copa para objetos que modelam tronco e copa separadamente. Ver
[`docs/dialux_workflow.md`](docs/dialux_workflow.md). O projeto **não** afirma
existir formato de importação automática do DIALux.

![Parâmetros geométricos da árvore](images/geometry.svg)

## Documentação

- [Metodologia](docs/methodology.md) · [Hipóteses](docs/assumptions.md) ·
  [Limitações](docs/limitations.md)
- [Dicionário de dados](docs/data_dictionary.md) · [Referências](docs/references.md) ·
  [Fluxo DIALux](docs/dialux_workflow.md)
- [Relatório de auditoria e validação](docs/validation_report.md)

## Limitações

Parâmetros não calibrados localmente; alturas e copas não medidas em campo;
copas assumidas circulares; palmeiras e identificações incompletas têm baixa
confiabilidade; DAP elevado é extrapolação. Ver
[`docs/limitations.md`](docs/limitations.md). **Não serve para decisões legais
ou arborísticas.**

## Referências

FAO (medição de DAP), Huang et al. 1992 (modelos altura–diâmetro),
Carvalho/Embrapa e Lorenzi (referências de árvores brasileiras). Ver
[`docs/references.md`](docs/references.md). Os coeficientes adotados são
operacionais, não coeficientes publicados por espécie.

## Licença

Código: **MIT**. Documentação e dados sintéticos de demonstração: **CC BY 4.0**.
Não há licença sobre dados de inventário de terceiros ou proprietários —
verifique os direitos de uso de qualquer inventário real. Ver [LICENSE](LICENSE).

## Aviso

Os resultados são **estimativas preliminares** para pré-modelagem luminotécnica.
Não substituem levantamento dendrométrico, inventário florestal, laudo
arborístico, avaliação de estabilidade ou levantamento topográfico.
