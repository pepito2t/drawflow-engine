import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// jsdom has no modal dialogs; the browser behaviour the UI relies on is the open state only.
HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
  this.open = true;
};
HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
  this.open = false;
};

// Vitest globals are off, so Testing Library cannot register its own cleanup.
afterEach(() => {
  cleanup();
});
