import { Component, type ErrorInfo, type ReactNode } from "react";
import { uiErrorDraft } from "../lib/console-capture";
import { recordConsoleEntry } from "../lib/tauri/console";

interface ErrorBoundaryProps {
  fallback: (error: unknown) => ReactNode;
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: unknown;
}

const NO_ERROR = Symbol("no-error");

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { error: NO_ERROR };

  static getDerivedStateFromError(error: unknown): ErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: unknown, info: ErrorInfo): void {
    recordConsoleEntry(uiErrorDraft(error, info.componentStack));
  }

  override render() {
    return this.state.error === NO_ERROR
      ? this.props.children
      : this.props.fallback(this.state.error);
  }
}
