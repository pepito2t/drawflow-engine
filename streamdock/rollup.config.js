import commonjs from "@rollup/plugin-commonjs";
import nodeResolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

const PLUGIN_FOLDER = "ch.drawflow.sdPlugin";

export default {
  input: "src/plugin.ts",
  output: {
    file: `${PLUGIN_FOLDER}/bin/plugin.js`,
    // Stream Dock runs the plugin with its built-in Node 20 as a plain CommonJS script.
    format: "cjs",
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
      name: "emit-commonjs-package-file",
      generateBundle() {
        // Keeps the bundle CommonJS even under a parent package.json declaring ES modules.
        this.emitFile({
          fileName: "package.json",
          source: '{ "type": "commonjs" }',
          type: "asset",
        });
      },
    },
  ],
};
