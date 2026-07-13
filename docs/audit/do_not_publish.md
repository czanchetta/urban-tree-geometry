# Files and content that must NOT be published

The original workbook is client project data. This page states the
**anonymisation policy**; the specific identifying values found in the source
are recorded only in the git-ignored private audit file
(`data/private/AUDIT_SENSITIVE.md`) and are deliberately **not** reproduced here.

## Must never be committed to the public repository
1. **The original client workbook** and any copy of it.
2. **Any real inventory** containing actual tree IDs + perimeters tied to the
   project.
3. Any file or text naming the client authority, the site/square, or the source
   project document (PDF).

## Categories of sensitive content to scrub before publishing
- Client / contracting authority name.
- Project / site (square) name.
- Source project-document filename.
- Any professional names, CREA/ART numbers, signatures, addresses or GPS
  coordinates.

## Guardrails in place
- `.gitignore` excludes `*.xlsx` (except generated outputs), `data/private/`,
  and `PROJETO_*` patterns.
- The public demo dataset is synthetic (`scripts/generate_sample_data.py`).
- The methodology docs cite the *reference literature* (Embrapa, Lorenzi, FAO,
  Huang et al.) but not the project document.

## Review-before-publish checklist
- [ ] No `.xlsx` other than `outputs/*.xlsx` is staged.
- [ ] The sensitive-token scan (see `PUBLISHING.md` §0) returns nothing outside
      `data/private/`.
- [ ] `data/raw/` contains only the synthetic file.
- [ ] Author contact placeholders reviewed (see `PUBLISHING.md`).
