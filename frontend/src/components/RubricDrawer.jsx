import React from 'react';
import {
  X,
  ExternalLink,
  ShieldAlert,
  CheckCircle2,
  Copy,
  Code2,
  Sparkles,
  BookOpen,
  Layers,
  Clock,
  Fingerprint,
} from 'lucide-react';

export default function RubricDrawer({ verdict, onClose }) {
  if (!verdict) return null;

  const breakdown = verdict.rubric_breakdown || {};
  const isDuplicate = verdict.duplicate_flag;
  const isLowScore = verdict.score !== undefined && verdict.score < 50;
  const score = Math.round(verdict.score || 0);

  const criteriaList = [
    {
      key: 'code_quality',
      label: 'Code Quality & Structure',
      icon: Code2,
      max: 25,
      score: Number(breakdown.code_quality) || 0,
      description: 'Readability, modularity, error handling & hygiene',
    },
    {
      key: 'functionality_completeness',
      label: 'Functionality & Completeness',
      icon: Layers,
      max: 25,
      score: Number(breakdown.functionality_completeness) || 0,
      description: 'Works end-to-end, completeness against hackathon intent',
    },
    {
      key: 'use_of_required_technology',
      label: 'Gemini / ADK Integration',
      icon: Sparkles,
      max: 25,
      score: Number(breakdown.use_of_required_technology) || 0,
      description: 'Core, meaningful integration with Gemini 3.5+ & ADK',
    },
    {
      key: 'documentation',
      label: 'Documentation & Setup',
      icon: BookOpen,
      max: 25,
      score: Number(breakdown.documentation) || 0,
      description: 'Clear README, setup instructions, architecture notes',
    },
  ];

  return (
    <aside className="w-full lg:w-[420px] shrink-0 flex flex-col h-full bg-white border-l border-ink shadow-tactile-lg z-20 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-canvas-subtle border-b border-ink px-5 py-4 flex items-center justify-between z-10">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-secondary font-bold">
            Verdict Inspection
          </span>
          <h3 className="font-serif text-lg font-bold text-ink truncate max-w-[280px]">
            {verdict.repo_url?.replace('https://github.com/', '') || 'Submission'}
          </h3>
        </div>

        <button
          onClick={onClose}
          className="tactile-pill p-1.5 bg-white text-ink hover:bg-paper"
          title="Close drawer"
        >
          <X className="w-4 h-4 stroke-[2.5]" />
        </button>
      </div>

      <div className="p-5 flex flex-col gap-5">
        {/* Overall Score Block */}
        <div className="tactile-card p-4 flex items-center justify-between bg-paper">
          <div>
            <span className="text-xs font-mono uppercase text-ink-secondary font-semibold">
              Final Rubric Score
            </span>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="font-serif text-4xl font-bold text-ink">{score}</span>
              <span className="text-sm font-sans font-medium text-ink-secondary">/100</span>
            </div>
          </div>

          {/* Status Badge */}
          <div className="flex flex-col items-end gap-1">
            {isDuplicate ? (
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-pastel-yellow text-ink border border-ink rounded-full text-xs font-bold shadow-tactile-sm">
                <Copy className="w-3.5 h-3.5 stroke-[2.2]" />
                <span>Duplicate Flagged</span>
              </span>
            ) : isLowScore ? (
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-accent-coral text-ink border border-ink rounded-full text-xs font-bold shadow-tactile-sm">
                <ShieldAlert className="w-3.5 h-3.5 stroke-[2.2]" />
                <span>Low Score Flag</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-pastel-mint text-ink border border-ink rounded-full text-xs font-bold shadow-tactile-sm">
                <CheckCircle2 className="w-3.5 h-3.5 stroke-[2.2]" />
                <span>Verified Clean</span>
              </span>
            )}
            <span className="text-[11px] font-mono text-ink-secondary">
              Sim: {((verdict.similarity_score || 0) * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Rubric Breakdown by Criteria */}
        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-mono uppercase tracking-wider font-semibold text-ink-secondary">
            Rubric Criteria Breakdown
          </h4>

          <div className="flex flex-col gap-3">
            {criteriaList.map((crit) => {
              const Icon = crit.icon;
              const percent = Math.min(100, Math.max(0, (crit.score / crit.max) * 100));

              return (
                <div
                  key={crit.key}
                  className="bg-white border border-ink/30 rounded-lg p-3 flex flex-col gap-2 shadow-sm"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5 font-medium text-ink">
                      <Icon className="w-3.5 h-3.5 text-ink-secondary" />
                      <span>{crit.label}</span>
                    </div>
                    <span className="font-mono font-bold text-ink">
                      {crit.score}
                      <span className="text-ink-secondary font-normal">/{crit.max}</span>
                    </span>
                  </div>

                  {/* Tactile Progress Bar (Proportional Fill) */}
                  <div className="w-full h-2.5 bg-canvas-subtle border border-ink/30 rounded-full overflow-hidden p-0.5">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ease-out ${
                        percent >= 75
                          ? 'bg-pastel-mint'
                          : percent >= 50
                          ? 'bg-pastel-yellow'
                          : 'bg-accent-coral'
                      }`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>

                  <span className="text-[11px] text-ink-muted leading-tight">
                    {crit.description}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Gemini Reasoning Assessment */}
        <div className="tactile-card p-4 bg-canvas-subtle/70 flex flex-col gap-2">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-accent-coral" />
            <span className="text-xs font-mono uppercase font-bold text-ink">
              Gemini 3.5 Assessment
            </span>
          </div>

          <p className="text-xs text-ink leading-relaxed font-sans whitespace-pre-wrap">
            {breakdown.reasoning ||
              verdict.reasoning ||
              'Evaluation completed according to hackathon rubric standards.'}
          </p>
        </div>

        {/* Duplicate & Metadata Details */}
        <div className="bg-white border border-ink/20 rounded-lg p-3.5 flex flex-col gap-2 text-xs font-mono">
          <div className="flex items-center justify-between text-ink-secondary">
            <span>Duplicate Check:</span>
            <span className={`font-bold ${isDuplicate ? 'text-accent-coral' : 'text-ink'}`}>
              {isDuplicate ? '⚠️ Match Detected' : '✓ Unique Submission'}
            </span>
          </div>

          <div className="flex items-center justify-between text-ink-secondary">
            <span>Vector Similarity:</span>
            <span className="text-ink font-bold">
              {((verdict.similarity_score || 0) * 100).toFixed(2)}%
            </span>
          </div>

          <div className="flex items-center justify-between text-ink-secondary">
            <span>Evaluated At:</span>
            <span className="text-ink">
              {verdict.timestamp ? new Date(verdict.timestamp).toLocaleString() : '—'}
            </span>
          </div>

          {(verdict._doc_id || verdict.doc_id) && (
            <div className="flex items-center justify-between text-ink-secondary pt-1 border-t border-ink/10">
              <span>Firestore Doc ID:</span>
              <span className="text-ink text-[10px] truncate max-w-[180px]">
                {verdict._doc_id || verdict.doc_id}
              </span>
            </div>
          )}
        </div>

        {/* External Link Button */}
        {verdict.repo_url && (
          <a
            href={verdict.repo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="tactile-pill flex items-center justify-center gap-2 py-2 px-4 bg-ink text-paper text-xs font-semibold hover:bg-ink-secondary text-center"
          >
            <span>Open Repository on GitHub</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </aside>
  );
}
