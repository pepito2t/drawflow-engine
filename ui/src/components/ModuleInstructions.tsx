export function ModuleInstructions({ steps }: { steps: string[] }) {
  return (
    <details className="instructions" open>
      <summary>Comment ça marche</summary>
      <ol>
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
    </details>
  );
}
