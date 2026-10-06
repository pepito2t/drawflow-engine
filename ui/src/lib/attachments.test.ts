import { describe, expect, it } from "vitest";
import { addAttachments, fileName, withAttachments } from "./attachments";

describe("attachments", () => {
  it("appends the dropped paths to the question as a visible list", () => {
    expect(withAttachments("Fais la liste", ["C:\\Plans\\a.dwg"])).toBe(
      "Fais la liste\n\nFichiers joints :\n- C:\\Plans\\a.dwg",
    );
    expect(withAttachments("Bonjour", [])).toBe("Bonjour");
  });

  it("asks a default question when only files are given", () => {
    expect(withAttachments("  ", ["C:\\a.pdf"]).startsWith("Que peux-tu faire")).toBe(true);
  });

  it("keeps each path once and shows file names", () => {
    expect(addAttachments(["C:\\a.dwg"], ["C:\\a.dwg", "C:\\b.dwg"])).toEqual([
      "C:\\a.dwg",
      "C:\\b.dwg",
    ]);
    expect(fileName("C:\\Plans\\a.dwg")).toBe("a.dwg");
  });
});
