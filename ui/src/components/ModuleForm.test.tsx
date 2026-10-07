import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { setNextSelection } from "../lib/tauri/__mocks__/dialog";
import type { FieldDescriptor, FormValues, UiKind } from "../lib/form-schema";
import { ModuleForm } from "./ModuleForm";

vi.mock("../lib/tauri/dialog");

function field(name: string, label: string, kind: UiKind): FieldDescriptor {
  return {
    name,
    label,
    description: null,
    kind,
    required: false,
    options: [],
    defaultValue: kind === "files" || kind === "mapping" ? [] : "",
    mappingLabels: null,
  };
}

const FIELDS = [
  field("drawings", "Plans", "files"),
  field("output", "Dossier de sortie", "output_folder"),
  field("columns", "Colonnes", "mapping"),
];

function StatefulForm() {
  const [values, setValues] = useState<FormValues>({});
  return (
    <ModuleForm
      moduleId="parts"
      fields={FIELDS}
      values={values}
      disabled={false}
      onChange={(name, value) => {
        setValues((current) => ({ ...current, [name]: value }));
      }}
    />
  );
}

describe("ModuleForm accessibility", () => {
  it("names each path list and mapping as a group after its label", () => {
    render(<StatefulForm />);

    expect(screen.getByRole("group", { name: "Plans" })).toBeTruthy();
    expect(screen.getByRole("group", { name: "Dossier de sortie" })).toBeTruthy();
    expect(screen.getByRole("group", { name: "Colonnes" })).toBeTruthy();
  });

  it("gives every Browse button the name of its field", async () => {
    render(<StatefulForm />);
    setNextSelection(["C:\\plans\\façade.dwg"]);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Parcourir : Plans" }));
      await Promise.resolve();
    });

    expect(screen.getByRole("button", { name: "Parcourir : Dossier de sortie" })).toBeTruthy();
    const drawings = within(screen.getByRole("group", { name: "Plans" }));
    expect(drawings.getByText("C:\\plans\\façade.dwg")).toBeTruthy();
  });
});
