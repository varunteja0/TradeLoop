import { Component, ErrorInfo, ReactNode } from "react";

interface Props { children: ReactNode }
interface State { hasError: boolean; error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
    try {
      const w = window as unknown as Record<string, unknown>;
      const Sentry = w.__SENTRY__ as { captureException?: (err: Error, ctx?: unknown) => void } | undefined;
      if (Sentry?.captureException) {
        Sentry.captureException(error, { extra: { componentStack: info.componentStack } });
      }
    } catch {
      // Sentry not loaded — that's fine in dev
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
          <div className="card max-w-md text-center">
            <div className="text-4xl mb-4">
              <svg className="w-12 h-12 mx-auto text-loss" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Something went wrong</h2>
            <p className="text-gray-400 text-sm mb-6">
              An unexpected error occurred. Our team has been notified.
            </p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => window.location.reload()} className="btn-primary">
                Reload Page
              </button>
              <a href="/" className="btn-secondary">
                Go Home
              </a>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
