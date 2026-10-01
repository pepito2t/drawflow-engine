import { Component, type ReactNode } from "react";

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

  override render() {
    return this.state.error === NO_ERROR
      ? this.props.children
      : this.props.fallback(this.state.error);
  }
}
