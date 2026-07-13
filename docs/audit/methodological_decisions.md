# Methodological decisions (interpretations)

Decisions taken where the task required interpretation. Each is conservative and
documented; none silently alters the workbook methodology.

1. **`Parâmetros` sheet is the authoritative parameter source.** Where the
   calculation sheet left `k` blank (UA02–UA06), the species `k` from
   `Parâmetros` reproduces the cached heights exactly, so parameters are loaded
   from the species table, with optional per-tree overrides.

2. **Height core vs crown layer are separated by trust level.** The workbook
   estimates **height only**. Height (DAP, H, bands) is reproduced faithfully
   and regression-tested. Crown/DIALux geometry is implemented as a clearly
   labelled **heuristic** layer, per the project brief's own guidance
   ("parâmetros operacionais derivados de literatura geral"), and is *not*
   presented as workbook-derived or validated.

3. **Crown architectural groups.** The brief's suggested crown factors
   (broad 25, intermediate 22, compact 18, narrow 14) and height-limit fractions
   (1.00 / 0.80 / 0.90 / 0.50) were adopted as the heuristic defaults and
   externalised to `crown_parameters.csv`. Species were assigned to groups from
   general crown-form knowledge; these assignments are heuristic and overridable.

4. **Palm rule.** `D_crown = 0.35·H`, bounded to [3.5, 6.0] m, per the brief;
   palms are always `confidence = low` with a field-measurement recommendation.

5. **Circular crown projection.** `A = π·D²/4`, with X = Y (single diameter),
   documented as ignoring real crown asymmetry — pre-modelling only.

6. **Crown sensitivity band.** `uncertainty = max(0.20·D, 1.5 m)`, per the brief;
   labelled a sensitivity scenario, not a confidence interval.

7. **Confidence policy.** Base confidence = medium; lowered to low for palms,
   genus/family-only identifications, unknown species, and large extrapolations
   (DBH > 120 cm).

8. **Unknown species are not fabricated.** A species absent from the parameter
   set yields no estimate and a low-confidence warning, rather than a guessed
   value.

9. **Original workbook excluded; synthetic demo substituted.** For anonymisation
   (see do-not-publish list), the public dataset is synthetic and preserves
   distribution characteristics only.
