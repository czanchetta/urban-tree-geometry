import { defineConfig } from "vite";

// `base` defaults to "./" so the built site works under any GitHub Pages
// sub-path (https://USER.github.io/urban-tree-geometry/app/). Override with
// the BASE_PATH env var in CI if a different mount point is needed.
export default defineConfig({
  base: process.env.BASE_PATH ?? "./",
  build: {
    outDir: "dist",
    sourcemap: false,
    target: "es2020",
  },
  test: {
    globals: true,
    environment: "node",
    include: ["test/**/*.test.ts"],
  },
});
