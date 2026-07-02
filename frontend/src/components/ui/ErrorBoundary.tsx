/**
 * ErrorBoundary — catches runtime errors and shows a clean recovery UI.
 * Replaces raw JS stack traces with user-friendly messages.
 */
import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface State { hasError: boolean; message: string }

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: string },
  State
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[300px] gap-4 p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
            <AlertTriangle size={24} className="text-red-500" />
          </div>
          <div>
            <p className="text-base font-semibold text-gray-900 dark:text-white">
              {this.props.fallback ?? "Something went wrong"}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Unable to load this section. Please try refreshing the page.
            </p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium transition-colors"
          >
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
