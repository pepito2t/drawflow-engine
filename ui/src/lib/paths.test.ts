import { describe, expect, it } from "vitest";
import { fileName } from "./paths";

describe("fileName", () => {
  it("extracts file names from Windows and Unix paths", () => {
    expect(fileName("C:\\Modèles\\liste é.xlsx")).toBe("liste é.xlsx");
    expect(fileName("\\\\serveur\\partage\\plan.dwg")).toBe("plan.dwg");
    expect(fileName("/tmp/rapport.docx")).toBe("rapport.docx");
    expect(fileName("sans-dossier.pdf")).toBe("sans-dossier.pdf");
  });
});
