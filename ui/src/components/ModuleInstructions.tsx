import { t } from "../i18n/shell";
export function ModuleInstructions({ steps }: { steps: string[] }) {
  return (
    <details className="instructions" open>
      <summary>{t("moduleInstructions.title")}</summary>
      <ol>
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
    </details>
  );
}
