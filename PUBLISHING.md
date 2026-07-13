# Publishing guide / Guia de publicação

This repository was prepared for public release but ships with **placeholders**
that you must review and replace first. Nothing here contains real client data.

---

## 0. Review-before-publish checklist (do this first)

- [ ] Confirm **no original workbook** is present:
      `git ls-files | grep -i "\.xlsx$"` should list only `outputs/*.xlsx` (none are tracked by default).
- [ ] Scan for sensitive tokens (must return **nothing** in tracked files). The
      exact terms are listed in the git-ignored private audit file
      `data/private/AUDIT_SENSITIVE.md`; run its scrub command, which searches
      every tracked file except `data/private/` itself:
      ```bash
      # pattern is defined in data/private/AUDIT_SENSITIVE.md
      git grep -Iis "$SENSITIVE_PATTERN" -- ':!data/private/*' && echo "LEAK" || echo "clean"
      ```
- [ ] Confirm `data/raw/` holds only the **synthetic** `sample_tree_inventory.csv`.
- [ ] Replace every `czanchetta` placeholder:
      ```bash
      git grep -n "czanchetta"
      ```
      (in `pyproject.toml`, `mkdocs.yml`, `CITATION.cff`, both READMEs, docs).
- [ ] Fill the author/contact fields (`AUTHOR_EMAIL`, `AUTHOR_LINKEDIN`,
      `AUTHOR_GITHUB`, `COMPANY_NAME`, `COMPANY_URL`) in `mkdocs.yml` (`extra:`)
      and in `docs/about*.md`, `docs/contact*.md`.
- [ ] Re-run `pytest -q`, `ruff check .`, `mkdocs build --strict` — all green.

---

## 1. Initialise Git and first commit

```bash
cd urban-tree-geometry
git init
git add .
git status                      # verify no .xlsx / private data is staged
git commit -m "Initial public release: urban-tree-geometry v0.1.0"
git branch -M main
```

## 2. Create the GitHub repository and push

Using the GitHub CLI:

```bash
gh repo create urban-tree-geometry --public \
  --description "Preliminary tree height, crown & 3D geometry parameters for outdoor lighting (DIALux) models, from inventory data." \
  --source . --remote origin --push
```

Or manually: create an empty public repo named `urban-tree-geometry` on GitHub,
then:

```bash
git remote add origin https://github.com/czanchetta/urban-tree-geometry.git
git push -u origin main
```

## 3. Suggested repository description

> Preliminary estimation of tree height, crown diameter and 3D geometry
> parameters (X/Y/Z) for outdoor lighting models (DIALux), from minimal tree
> inventory data (species + trunk perimeter). Faithful, regression-tested height
> core plus a clearly labelled heuristic crown layer. Bilingual (PT-BR/EN).

## 4. Suggested topics (GitHub → About → Topics)

```
python, dialux, lighting-design, urban-forestry, dendrometry, tree-inventory,
allometry, crown-geometry, engineering, cli, mkdocs-material, bilingual
```

## 5. Enable GitHub Pages (site + interactive calculator)

1. Push to `main` — the `deploy` workflow runs three gates and only then
   publishes: **python-tests** (pytest incl. 62-row workbook regression +
   equivalence fixture), **ts-tests** (Vitest unit + cross-language
   equivalence), and **build-deploy** (MkDocs strict build + Vite calculator
   build). A failure in either test job blocks the deploy.
2. GitHub → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Published at `https://czanchetta.github.io/urban-tree-geometry/`
   (Portuguese default, English under `/en/`), with the interactive calculator
   at `https://czanchetta.github.io/urban-tree-geometry/app/`.
4. If you rename the repository, update `BASE_PATH` in
   `.github/workflows/deploy.yml` (currently `/urban-tree-geometry/app/`) so
   the calculator's asset paths resolve.
5. Before publishing, fill the author/contact fields: `AUTHOR_EMAIL`,
   `AUTHOR_LINKEDIN`, `AUTHOR_GITHUB` (already filled) in `mkdocs.yml`,
   `web/src/config.ts`, `README*.md`, `CITATION.cff` and `pyproject.toml`.

## 6. Optional: create the v0.1.0 release

```bash
gh release create v0.1.0 --title "v0.1.0" \
  --notes "First public release. Faithful height core (62/62 workbook rows reproduced) + heuristic crown/DIALux layer. Bilingual docs and site."
```

---

## 7. Suggested LinkedIn post (edit before posting)

> 🌳 Publiquei um projeto open-source: **urban-tree-geometry**.
>
> É uma ferramenta em Python que estima, de forma **preliminar e transparente**,
> a altura, o diâmetro de copa e os parâmetros geométricos (X/Y/Z) de árvores
> para modelos luminotécnicos externos (DIALux), a partir de dados mínimos de
> inventário — espécie e perímetro do tronco.
>
> Diferenciais:
> • Núcleo de altura fiel a uma planilha de referência (reproduz 62/62 linhas em
>   teste de regressão);
> • Camada de copa/DIALux claramente identificada como heurística — nada é
>   apresentado como medição de campo;
> • Proveniência explícita de cada valor (medido / derivado / adotado /
>   heurístico), com limitações e advertências;
> • Documentação bilíngue (PT-BR/EN) e site MkDocs Material com deploy automático;
> • Dados de demonstração 100% sintéticos e anonimizados.
>
> Código MIT · Documentação CC BY 4.0.
> 🔗 github.com/czanchetta/urban-tree-geometry
>
> #engenharia #iluminacao #dialux #python #arborizacaourbana #opensource
>
> ---
> *English:* Open-source Python tool for preliminary, transparent estimation of
> tree height, crown diameter and 3D geometry parameters for outdoor lighting
> (DIALux) models from minimal inventory data. Faithful, regression-tested height
> core + a clearly labelled heuristic crown layer. Bilingual docs. MIT / CC BY 4.0.

---

## 8. What must never be published (reminder)

See [`docs/audit/do_not_publish.md`](docs/audit/do_not_publish.md). In short: the
original client workbook, any real inventory tied to the project, and any mention
of the client, site or project document. The `.gitignore` already excludes
`*.xlsx` (except generated outputs), `data/private/`, and `PROJETO_*`.
