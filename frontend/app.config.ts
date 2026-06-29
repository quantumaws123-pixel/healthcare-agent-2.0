import { defineConfig } from "@tanstack/start/config";
import viteTsConfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  routers: {
    client: {
      entry: "./src/client.tsx",
    },
    ssr: {
      entry: "./src/ssr.tsx",
    },
  },
  tsr: {
    routesDirectory: "./src/routes",
    generatedRouteTree: "./src/routeTree.gen.ts",
    quoteStyle: "double",
    semicolons: true,
  },
  vite: {
    plugins: [
      viteTsConfigPaths({
        projects: ["./tsconfig.json"],
      }),
    ],
    css: {
      postcss: "./postcss.config.cjs",
    },
  },
});
