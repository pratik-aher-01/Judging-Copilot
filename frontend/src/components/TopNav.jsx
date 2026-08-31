import React from 'react';
import { ShieldAlert, RefreshCw, Plus, CheckCircle2, Copy } from 'lucide-react';

export default function TopNav({
  verdicts = [],
  loading = false,
  onRefresh,
  onOpenSubmit,
}) {
  const flaggedCount = verdicts.filter(
    (v) => v.duplicate_flag || (v.score !== undefined && v.score < 50)
  ).length;

  const duplicateCount = verdicts.filter((v) => v.duplicate_flag).length;
  const cleanCount = verdicts.filter(
    (v) => !v.duplicate_flag && v.score >= 50
  ).length;

  return (
    <header className="sticky top-0 z-30 border-b border-ink bg-paper/95 backdrop-blur px-6 py-3.5 flex items-center justify-between">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-3">
        <img src="/favicon.svg" alt="Judging Copilot Logo" className="w-8 h-8 rounded-lg shadow-tactile-sm shrink-0" />
        <span className="font-serif text-2xl font-bold tracking-tight text-ink">
          Judging Copilot
        </span>
        <span className="text-xs uppercase font-mono tracking-wider font-semibold text-ink-secondary bg-canvas-subtle border border-ink/20 px-2 py-0.5 rounded-full">
          Organizer Hub
        </span>
      </div>

      {/* Center / Right State Badges & Actions */}
      <div className="flex items-center gap-3">
        {/* Flagged Status Pill */}
        {flaggedCount > 0 ? (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-accent-coral text-ink border border-ink rounded-full text-xs font-semibold shadow-tactile-sm animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 stroke-[2.2]" />
            <span>{flaggedCount} Flagged</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-pastel-mint text-ink border border-ink rounded-full text-xs font-semibold shadow-tactile-sm">
            <CheckCircle2 className="w-3.5 h-3.5 stroke-[2.2]" />
            <span>All Clear</span>
          </div>
        )}

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="tactile-pill flex items-center gap-1.5 px-3 py-1.5 bg-white text-ink text-xs font-medium hover:bg-canvas-subtle disabled:opacity-50"
          title="Refresh verdicts from Firestore"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
          />
          <span className="hidden sm:inline">Refresh</span>
        </button>

        {/* Submit Repo Button */}
        <button
          onClick={onOpenSubmit}
          className="tactile-pill flex items-center gap-1.5 px-4 py-1.5 bg-ink text-paper text-xs font-semibold hover:bg-ink-secondary"
        >
          <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>Submit Repo</span>
        </button>
      </div>
    </header>
  );
}
