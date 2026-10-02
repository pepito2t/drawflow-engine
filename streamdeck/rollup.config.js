import commonjs from "@rollup/plugin-commonjs";
import nodeResolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

const PLUGIN_FOLDER = "ch.drawflow.sdPlugin";

export default {
  input: "src/plugin.ts",
  output: {
    file: `${PLUGIN_FOLDER}/bin/plugin.js`,
    format: "esm",
    sourcemap: true,
  },
  plugins: [
    typescript({
      noEmit: false,
      outDir: `${PLUGIN_FOLDER}/bin`,
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.test.ts"],
    }),
    nodeResolve({ browser: false, exportConditions: ["node"], preferBuiltins: true }),
    commonjs(),
    {
      name: "emit-module-package-file",
      generateBundle() {
        this.emitFile({ fileName: "package.json", source: '{ "type": "module" }', type: "asset" });
      },
    },
  ],
};
