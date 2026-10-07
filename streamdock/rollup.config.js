import commonjs from "@rollup/plugin-commonjs";
import nodeResolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

const PLUGIN_FOLDER = "ch.drawflow.sdPlugin";

const compileTypeScript = (outDir) =>
  typescript({
    noEmit: false,
    outDir,
    include: ["src/**/*.ts"],
    exclude: ["src/**/*.test.ts", "src/**/*.test-helper.ts"],
  });

const plugin = {
  input: "src/plugin.ts",
  output: {
    file: `${PLUGIN_FOLDER}/bin/plugin.js`,
    // Stream Dock runs the plugin with its built-in Node 20 as a plain CommonJS script.
    format: "cjs",
    sourcemap: true,
  },
  plugins: [
    compileTypeScript(`${PLUGIN_FOLDER}/bin`),
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

// The settings panel runs in the browser of Stream Dock as a classic script.
const inspector = {
  input: "src/pi.ts",
  output: { file: `${PLUGIN_FOLDER}/ui/pi.js`, format: "iife", sourcemap: false },
  plugins: [compileTypeScript(`${PLUGIN_FOLDER}/ui`)],
};

export default [plugin, inspector];
