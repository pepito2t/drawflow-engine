import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["ch.drawflow.sdPlugin/bin", "ch.drawflow.sdPlugin/ui/pi.js", "dist"] },
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      globals: globals.node,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
  },
  { files: ["eslint.config.js", "rollup.config.js"], ...tseslint.configs.disableTypeChecked },
);
