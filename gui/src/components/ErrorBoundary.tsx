import React from "react";

interface State { hasError: boolean; error: Error | null }

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-[var(--color-bg)]" role="alert" aria-live="assertive">
          <div className="text-center p-8">
            <div className="text-4xl mb-4">💥</div>
            <h1 className="text-lg text-white font-semibold mb-2">Something went wrong</h1>
            <p className="text-sm text-white/40 mb-4 max-w-md">{this.state.error?.message}</p>
            <button onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
              className="px-4 py-2 rounded-lg bg-[var(--color-accent)] text-white text-sm">
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
