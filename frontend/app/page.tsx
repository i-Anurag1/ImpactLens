"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "./lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDemoLogin() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.demoLogin();
      setToken(res.token);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-8 py-6 border-b border-ink-700">
        <div className="font-display font-semibold text-lg tracking-tight">ImpactLens AI</div>
        <div className="text-mist-500 text-sm">Code Change Risk & Test Intelligence</div>
      </header>

      <section className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-12 px-8 lg:px-16 py-16 items-center max-w-6xl mx-auto w-full">
        <div className="rise-in">
          <h1 className="font-display text-4xl lg:text-5xl font-semibold leading-tight text-mist-100">
            Know what a change will break before you merge it.
          </h1>
          <p className="mt-5 text-mist-300 text-lg leading-relaxed max-w-md">
            ImpactLens traces every change through your real dependency graph, scores the risk,
            and hands you the four tests that actually matter — with file:line evidence for each one.
          </p>

          <div className="mt-8 flex flex-col gap-3 max-w-xs">
            <button
              onClick={handleDemoLogin}
              disabled={loading}
              className="bg-signal-indigo hover:bg-signal-indigo/90 disabled:opacity-60 text-white font-medium px-5 py-3 rounded-sm transition-colors flex items-center justify-center gap-2"
            >
              {loading ? "Signing in…" : "Sign in with GitHub (demo)"}
            </button>
            <p className="text-mist-500 text-xs leading-relaxed">
              This build uses a fixed demo GitHub identity and a bundled demo repository so
              the full flow works with zero setup. Real GitHub OAuth wires in via
              GITHUB_CLIENT_ID/SECRET — see the README.
            </p>
          </div>

          {error && (
            <p className="mt-4 text-signal.critical text-sm risk-CRITICAL">{error}</p>
          )}
        </div>

        <div className="rise-in bg-ink-800 border border-ink-600 rounded-sm p-6">
          <p className="text-mist-500 text-xs mb-4">Evidence chain — example</p>
          <ol className="space-y-0">
            {[
              { label: "PaymentService.processPayment", file: "payment_service.py:42", changed: true },
              { label: "CheckoutService.checkout", file: "checkout_service.py:31" },
              { label: "OrderController.placeOrder", file: "order_controller.py:19", tag: "public API" },
            ].map((step, i) => (
              <li key={step.label} className="relative pl-6 pb-6 last:pb-0">
                {i > 0 && (
                  <span className="absolute left-[7px] top-[-14px] h-4 w-px bg-ink-600" />
                )}
                <span
                  className={`absolute left-0 top-1 h-3.5 w-3.5 rounded-full border-2 ${
                    step.changed ? "border-signal-high bg-signal-high/30" : "border-signal-indigo bg-signal-indigo/20"
                  }`}
                />
                <div className="font-mono text-sm text-mist-100">{step.label}</div>
                <div className="evidence-line text-mist-500">{step.file}</div>
                {step.tag && (
                  <span className="inline-block mt-1 text-[11px] px-2 py-0.5 rounded-sm bg-signal-critical/20 risk-CRITICAL border">
                    {step.tag}
                  </span>
                )}
              </li>
            ))}
          </ol>
          <div className="mt-2 pt-4 border-t border-ink-600 flex items-center justify-between">
            <span className="text-mist-500 text-xs">Risk classification</span>
            <span className="risk-HIGH bg-risk-HIGH border px-2 py-1 rounded-sm text-xs font-medium">HIGH</span>
          </div>
        </div>
      </section>

      <footer className="px-8 py-6 border-t border-ink-700 text-mist-500 text-xs">
        Entire Graph evidence · Entire Checkpoints · Databricks historical intelligence · AI explanation only
      </footer>
    </main>
  );
}
