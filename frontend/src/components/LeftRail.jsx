import React from 'react';
import { ShieldAlert, Copy, CheckCircle2, LayoutGrid, Award, BarChart3 } from 'lucide-react';

export default function LeftRail({
  activeFilter,
  onSelectFilter,
  verdicts = [],
}) {
  const total = verdicts.length;
  const flagged = verdicts.filter(
    (v) => (v.score !== undefined && v.score < 50) || v.duplicate_flag
  ).length;
  const duplicate = verdicts.filter((v) => v.duplicate_flag).length;
  const clean = verdicts.filter(
    (v) => !v.duplicate_flag && v.score >= 50
  ).length;

  const avgScore = total
    ? Math.round(verdicts.reduce((acc, v) => acc + (v.score || 0), 0) / total)
    : 0;

  const filters = [
    {
      id: 'all',
      label: 'All Submissions',
      count: total,
      icon: LayoutGrid,
      activeClass: 'bg-ink text-paper border-ink shadow-tactile',
      inactiveClass: 'bg-white text-ink hover:bg-canvas-subtle',
      badgeClass: 'bg-canvas-subtle text-ink',
    },
    {
      id: 'flagged',
      label: 'Flagged',
      count: flagged,
      icon: ShieldAlert,
      activeClass: 'bg-accent-coral text-ink border-ink font-bold shadow-tactile',
      inactiveClass: 'bg-white text-ink hover:bg-[#FDE8E1]',
      badgeClass: 'bg-[#FBE0D7] text-ink font-bold',
    },
    {
      id: 'duplicate',
      label: 'Duplicates',
      count: duplicate,
      icon: Copy,
      activeClass: 'bg-pastel-yellow text-ink border-ink font-bold shadow-tactile',
      inactiveClass: 'bg-white text-ink hover:bg-[#FFF9DE]',
      badgeClass: 'bg-[#FFF3C2] text-ink font-bold',
    },
    {
      id: 'clean',
      label: 'Clean / Passed',
      count: clean,
      icon: CheckCircle2,
      activeClass: 'bg-pastel-mint text-ink border-ink font-bold shadow-tactile',
      inactiveClass: 'bg-white text-ink hover:bg-[#EAFBF3]',
      badgeClass: 'bg-[#D2F4E3] text-ink font-bold',
    },
  ];

  return (
    <aside className="w-full flex flex-col gap-4">
      {/* Filter Category Block */}
      <div className="tactile-card p-4 flex flex-col gap-2">
        <h2 className="text-xs font-mono uppercase tracking-wider font-semibold text-ink-secondary mb-1">
          Filter by Status
        </h2>

        <div className="flex flex-col gap-2">
          {filters.map((f) => {
            const Icon = f.icon;
            const isActive = activeFilter === f.id;
            return (
              <button
                key={f.id}
                onClick={() => onSelectFilter(f.id)}
                className={`tactile-pill w-full flex items-center justify-between px-3.5 py-2 text-xs font-medium text-left transition-all ${
                  isActive ? f.activeClass : f.inactiveClass
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5 stroke-[2]" />
                  <span>{f.label}</span>
                </div>
                <span
                  className={`text-[11px] font-mono px-2 py-0.5 rounded-full border border-ink/20 ${
                    isActive && f.id === 'all'
                      ? 'bg-paper text-ink'
                      : f.badgeClass
                  }`}
                >
                  {f.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Organizer Summary Card */}
      <div className="tactile-card p-4 flex flex-col gap-3 bg-canvas-subtle/50">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono uppercase tracking-wider font-semibold text-ink-secondary">
            Evaluation Stats
          </span>
          <BarChart3 className="w-3.5 h-3.5 text-ink-secondary" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="bg-white border border-ink/30 rounded-lg p-2.5 flex flex-col">
            <span className="text-[10px] uppercase font-mono text-ink-muted">Avg Score</span>
            <span className="text-xl font-bold font-serif text-ink mt-0.5">
              {avgScore}<span className="text-xs font-sans text-ink-secondary">/100</span>
            </span>
          </div>

          <div className="bg-white border border-ink/30 rounded-lg p-2.5 flex flex-col">
            <span className="text-[10px] uppercase font-mono text-ink-muted">Dupl. Rate</span>
            <span className="text-xl font-bold font-serif text-ink mt-0.5">
              {total ? Math.round((duplicate / total) * 100) : 0}%
            </span>
          </div>
        </div>

        <div className="text-[11px] text-ink-secondary leading-relaxed pt-1 border-t border-ink/10">
          Scoring via <strong className="font-mono text-ink">Gemini 3.5 Flash</strong> & Gemini text embeddings.
        </div>
      </div>
    </aside>
  );
}
