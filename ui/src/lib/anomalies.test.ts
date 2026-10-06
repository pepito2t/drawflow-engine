import { describe, expect, it } from "vitest";
import { anomaliesAsText, groupAnomalies } from "./anomalies";
import type { LogEntry } from "./run-state";

function entry(partial: Partial<LogEntry> & { message: string }): LogEntry {
  return { id: 0, level: "warning", file: null, location: null, hint: null, ...partial };
}

const LOG: LogEntry[] = [
  entry({ id: 1, level: "info", message: "3 fichier(s) à traiter." }),
  entry({
    id: 2,
    message: "Attribut « LONGUEUR » absent sur 2 blocs.",
    file: "C:\\Plans\\A.dwg",
    hint: "Ajoutez l'attribut.",
  }),
  entry({ id: 3, message: "Aucun bloc retenu.", hint: "Vérifiez les blocs retenus." }),
  entry({ id: 4, message: "Blocs trop imbriqués.", file: "C:\\Plans\\A.dwg", location: "blocs X" }),
  entry({ id: 5, message: "PDF scanné.", file: "C:\\Plans\\B.pdf" }),
];

describe("anomalies", () => {
  it("groups warnings by file, general ones first, keeping first-seen order", () => {
    const groups = groupAnomalies(LOG);

    expect(groups.map((group) => group.fileName)).toEqual(["Général", "A.dwg", "B.pdf"]);
    expect(groups[1]?.items.map((item) => item.id)).toEqual([2, 4]);
  });

  it("renders a plain-text report with locations and hints", () => {
    const text = anomaliesAsText(groupAnomalies(LOG));

    expect(text).toContain(
      "C:\\Plans\\A.dwg\n- Attribut « LONGUEUR » absent sur 2 blocs. → Ajoutez l'attribut.",
    );
    expect(text).toContain("- Blocs trop imbriqués. (blocs X)");
    expect(text.startsWith("Général\n- Aucun bloc retenu.")).toBe(true);
  });
});
