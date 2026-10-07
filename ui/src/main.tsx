import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./components/App";
import { detectLanguage, setLanguage } from "./i18n";
import "./styles.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Élément #root introuvable dans index.html.");
}

setLanguage(detectLanguage());

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
