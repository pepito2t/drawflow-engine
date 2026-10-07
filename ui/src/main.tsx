import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./components/App";
import { ConsoleWindow } from "./components/ConsoleWindow";
import { detectLanguage, setLanguage } from "./i18n";
import { captureGlobalErrors } from "./lib/console-capture";
import { isConsoleWindow, recordConsoleEntry } from "./lib/tauri/console";
import "./styles.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Élément #root introuvable dans index.html.");
}

setLanguage(detectLanguage());
captureGlobalErrors(window, recordConsoleEntry);

createRoot(rootElement).render(
  <StrictMode>{isConsoleWindow() ? <ConsoleWindow /> : <App />}</StrictMode>,
);
