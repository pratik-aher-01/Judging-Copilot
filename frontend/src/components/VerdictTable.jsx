import React from 'react';
import {
  ShieldAlert,
  Copy,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ArrowUpDown,
  Clock,
  GitBranch,
} from 'lucide-react';

export default function VerdictTable({
  verdicts = [],
  selectedVerdict,
  onSelectVerdict,
  sortField,
  sortDirection,
  onSort,
}) {
  const getStatusBadge = (verdict) => {
    const isDuplicate = verdict.duplicate_flag;
    const isLowScore = verdict.score !== undefined && verdict.score < 50;

    if (isDuplicate) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-yellow text-ink border border-ink shadow-[1px_1px_0px_#191817]">
          <Copy className="w-3.5 h-3.5 stroke-[2.2]" />
          <span>Duplicate</span>
        </span>
      );
    }

    if (isLowScore) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-accent-coral text-ink border border-ink shadow-[1px_1px_0px_#191817]">
          <ShieldAlert className="w-3.5 h-3.5 stroke-[2.2]" />
          <span>Flagged</span>
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-mint text-ink border border-ink shadow-[1px_1px_0px_#191817]">
        <CheckCircle2 className="w-3.5 h-3.5 stroke-[2.2]" />
        <span>Passed</span>
      </span>
    );
  };

  const formatRepoName = (url = '') => {
    if (!url) return 'Unknown Repo';
    return url.replace('https://github.com/', '').replace(/\/$/, '');
  };

  const formatTimestamp = (ts) => {
    if (!ts) return '—';
    try {
      const date = new Date(ts);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  const getSortIcon = (field) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-ink-muted opacity-50" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-3.5 h-3.5 text-ink font-bold" />
    ) : (
      <ChevronDown className="w-3.5 h-3.5 text-ink font-bold" />
    );
  };

  return (
    <div className="tactile-card overflow-hidden w-full">
      <div className="overflow-x-auto w-full">
        <table className="w-full min-w-[560px] text-left border-collapse text-xs">
          {/* Table Header */}
          <thead>
            <tr className="bg-canvas-subtle border-b border-ink text-ink font-mono text-[11px] uppercase tracking-wider">
              <th
                onClick={() => onSort('repo_url')}
                className="py-3 px-4 font-semibold cursor-pointer hover:bg-[#EAE4D7] transition-colors min-w-[180px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Repository</span>
                  {getSortIcon('repo_url')}
                </div>
              </th>

              <th
                onClick={() => onSort('score')}
                className="py-3 px-4 font-semibold cursor-pointer hover:bg-[#EAE4D7] transition-colors text-right w-24"
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span>Score</span>
                  {getSortIcon('score')}
                </div>
              </th>

              <th className="py-3 px-4 font-semibold text-center w-32">
                <span>Verdict Status</span>
              </th>

              <th
                onClick={() => onSort('similarity_score')}
                className="py-3 px-4 font-semibold cursor-pointer hover:bg-[#EAE4D7] transition-colors text-right w-24 hidden sm:table-cell"
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span>Similarity</span>
                  {getSortIcon('similarity_score')}
                </div>
              </th>

              <th
                onClick={() => onSort('timestamp')}
                className="py-3 px-4 font-semibold cursor-pointer hover:bg-[#EAE4D7] transition-colors text-right w-36 whitespace-nowrap"
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span>Evaluated At</span>
                  {getSortIcon('timestamp')}
                </div>
              </th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-ink/15">
            {verdicts.map((v, idx) => {
              const isSelected =
                selectedVerdict &&
                (selectedVerdict._doc_id === v._doc_id ||
                  selectedVerdict.doc_id === v.doc_id ||
                  selectedVerdict.repo_url === v.repo_url);

              const repoLabel = formatRepoName(v.repo_url);
              const score = Math.round(v.score || 0);

              return (
                <tr
                  key={v._doc_id || v.doc_id || idx}
                  onClick={() => onSelectVerdict(v)}
                  className={`cursor-pointer transition-colors group ${
                    isSelected
                      ? 'bg-[#F2ECE1] border-l-4 border-l-ink font-medium'
                      : 'hover:bg-canvas-subtle/60 bg-white'
                  }`}
                >
                  {/* Repo URL */}
                  <td className="py-3 px-4 min-w-[180px]">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-ink-secondary shrink-0" />
                      <span className="font-mono font-medium text-ink group-hover:underline truncate max-w-[180px] sm:max-w-xs md:max-w-sm">
                        {repoLabel}
                      </span>
                    </div>
                  </td>

                  {/* Score */}
                  <td className="py-3 px-4 text-right w-24 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center justify-center font-mono font-bold text-xs px-2.5 py-0.5 rounded border border-ink ${
                        score >= 75
                          ? 'bg-[#E3F8EC] text-ink'
                          : score >= 50
                          ? 'bg-[#FFF9DE] text-ink'
                          : 'bg-[#FDECE7] text-ink'
                      }`}
                    >
                      {score}
                      <span className="text-[10px] text-ink-secondary">/100</span>
                    </span>
                  </td>

                  {/* Status Badge (Color + Shape) */}
                  <td className="py-3 px-4 text-center w-32 whitespace-nowrap">
                    {getStatusBadge(v)}
                  </td>

                  {/* Similarity Score */}
                  <td className="py-3 px-4 text-right font-mono w-24 hidden sm:table-cell whitespace-nowrap">
                    <span
                      className={`${
                        (v.similarity_score || 0) > 0.8
                          ? 'text-accent-coral font-bold'
                          : 'text-ink-secondary'
                      }`}
                    >
                      {((v.similarity_score || 0) * 100).toFixed(1)}%
                    </span>
                  </td>

                  {/* Timestamp */}
                  <td className="py-3 px-4 text-right font-mono text-ink-secondary text-[11px] w-36 whitespace-nowrap">
                    <div className="flex items-center justify-end gap-1">
                      <Clock className="w-3 h-3 opacity-60" />
                      <span>{formatTimestamp(v.timestamp)}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
