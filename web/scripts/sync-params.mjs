// Copies the single source-of-truth parameter file into the web bundle.
// Run automatically before dev/build/test (see package.json scripts) so the
// frontend never carries a hand-edited duplicate. The equivalence test and
// the params.test.ts guard fail if the copy drifts from the root file.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "..", "..", "data", "species_parameters.json");
const dst = resolve(here, "..", "src", "data", "species_parameters.json");
mkdirSync(dirname(dst), { recursive: true });
copyFileSync(src, dst);
console.log(`synced params: ${src} -> ${dst}`);
