import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RotateCcw,
  ArrowRight,
  GitBranch,
  ExternalLink,
  ShieldAlert,
  Copy,
  Cpu,
} from 'lucide-react';
import { API_BASE_URL } from '../config';

const PIPELINE_STEPS = [
  {
    id: 'clone',
    number: '01',
    label: 'Clone repository',
    description: 'Fetch source tree and filter reviewable files',
  },
  {
    id: 'score',
    number: '02',
    label: 'Score with Gemini 3.5',
    description: 'Structured JSON evaluation against 4 hackathon rubrics',
  },
  {
    id: 'duplicate_check',
    number: '03',
    label: 'Check for duplicates',
    description: 'Vector similarity against previous submissions',
  },
  {
    id: 'firestore_write',
    number: '04',
    label: 'Write verdict',
    description: 'Persist verdict document to Firestore collection',
  },
  {
    id: 'alert',
    number: '05',
    label: 'Alert if flagged',
    description: 'Check score thresholds and trigger organizer alert',
  },
];

export default function AgentActivityPanel({
  isOpen,
  onClose,
  onVerdictCreated,
  onViewVerdict,
}) {
  const [repoUrl, setRepoUrl] = useState('');
  const [phase, setPhase] = useState('input'); // 'input' | 'running' | 'complete' | 'failed'
  const [stepsState, setStepsState] = useState({});
  const [finalVerdict, setFinalVerdict] = useState(null);
  const [failureInfo, setFailureInfo] = useState(null);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  if (!isOpen) return null;

  const startPipeline = (targetUrl) => {
    const url = targetUrl.trim();
    if (!url.startsWith('https://github.com/')) {
      alert('Please enter a valid GitHub HTTPS URL (https://github.com/owner/repo)');
      return;
    }

    setPhase('running');
    setFinalVerdict(null);
    setFailureInfo(null);

    // Initialize all steps as pending
    const initial = {};
    PIPELINE_STEPS.forEach((s) => {
      initial[s.id] = { status: 'pending', detail: null };
    });
    setStepsState(initial);

    // Close any previous stream
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const streamUrl = `${API_BASE_URL}/judge/stream?repo_url=${encodeURIComponent(url)}`;
    const es = new EventSource(streamUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);

        if (payload.type === 'step') {
          setStepsState((prev) => ({
            ...prev,
            [payload.step]: {
              status: payload.status === 'started' ? 'active' : payload.status,
              detail: payload.detail,
            },
          }));
        } else if (payload.type === 'pipeline_complete') {
          es.close();
          setPhase('complete');
          setFinalVerdict(payload.verdict);
          if (onVerdictCreated) {
            onVerdictCreated(payload.verdict);
          }
        } else if (payload.type === 'pipeline_failed') {
          es.close();
          setPhase('failed');
          setFailureInfo({
            step: payload.step,
            error: payload.error || 'An unexpected error occurred during pipeline execution.',
          });
          if (payload.step) {
            setStepsState((prev) => ({
              ...prev,
              [payload.step]: {
                status: 'failed',
                detail: payload.error,
              },
            }));
          }
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    es.onerror = (err) => {
      console.error('EventSource connection error:', err);
      es.close();
      if (phase !== 'complete') {
        setPhase('failed');
        setFailureInfo({
          step: 'network',
          error: 'Connection to backend event stream failed. Make sure `python app.py` is running.',
        });
      }
    };
  };

  const handleReset = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setPhase('input');
    setStepsState({});
    setFinalVerdict(null);
    setFailureInfo(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="tactile-card w-full max-w-xl bg-paper p-6 relative flex flex-col gap-5 shadow-tactile-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-ink/15 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-mono uppercase tracking-wider font-bold text-ink-secondary bg-canvas-subtle border border-ink/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Cpu className="w-3 h-3 text-accent-coral" />
                Live Agent Activity
              </span>
            </div>
            <h2 className="font-serif text-2xl font-bold text-ink">
              {phase === 'input' && 'Submit Repository for Evaluation'}
              {phase === 'running' && 'Evaluating Submission in Real Time'}
              {phase === 'complete' && 'Evaluation Verdict Complete'}
              {phase === 'failed' && 'Pipeline Execution Stopped'}
            </h2>
          </div>

          <button
            onClick={onClose}
            disabled={phase === 'running'}
            className="tactile-pill p-1.5 bg-white text-ink hover:bg-canvas-subtle disabled:opacity-40"
            title="Close"
          >
            <X className="w-4 h-4 stroke-[2.5]" />
          </button>
        </div>

        {/* Input Phase */}
        {phase === 'input' && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              startPipeline(repoUrl);
            }}
            className="flex flex-col gap-4"
          >
            <p className="text-xs text-ink-secondary leading-relaxed">
              Enter a public GitHub repository. The autonomous judging agent will execute the full 5-stage evaluation pipeline in real time.
            </p>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-mono font-semibold text-ink">
                GitHub Repository HTTPS URL
              </label>
              <div className="relative">
                <GitBranch className="w-4 h-4 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  required
                  className="w-full bg-white border border-ink rounded-lg pl-9 pr-3 py-2.5 text-xs font-mono text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-accent-coral"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-ink/10">
              <button
                type="button"
                onClick={onClose}
                className="tactile-pill px-4 py-2 bg-white text-ink text-xs font-medium hover:bg-canvas-subtle"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="tactile-pill flex items-center gap-2 px-5 py-2 bg-accent-coral text-ink text-xs font-bold hover:bg-accent-coral-hover shadow-tactile"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Launch Evaluation Pipeline</span>
              </button>
            </div>
          </form>
        )}

        {/* Workflow Storytelling Steps (Running, Complete, Failed) */}
        {phase !== 'input' && (
          <div className="flex flex-col gap-4">
            {/* Target Repo Badge */}
            <div className="flex items-center gap-2 text-xs font-mono bg-canvas-subtle border border-ink/20 px-3 py-2 rounded-lg text-ink">
              <GitBranch className="w-3.5 h-3.5 text-ink-secondary shrink-0" />
              <span className="truncate">{repoUrl}</span>
            </div>

            {/* Steps Workflow List */}
            <div className="flex flex-col gap-2.5">
              {PIPELINE_STEPS.map((step) => {
                const state = stepsState[step.id] || { status: 'pending', detail: null };
                const isPending = state.status === 'pending';
                const isActive = state.status === 'active';
                const isDone = state.status === 'completed';
                const isFailed = state.status === 'failed';

                let cardStyle = 'bg-white/60 border-ink/20 text-ink-muted';
                let numStyle = 'border-ink/20 text-ink-muted bg-canvas-subtle';

                if (isActive) {
                  cardStyle = 'bg-ink text-paper border-ink shadow-tactile ring-2 ring-accent-coral animate-pulse';
                  numStyle = 'border-paper text-ink bg-accent-coral font-bold';
                } else if (isDone) {
                  cardStyle = 'bg-pastel-mint text-ink border-ink shadow-tactile-sm';
                  numStyle = 'border-ink text-ink bg-white font-bold';
                } else if (isFailed) {
                  cardStyle = 'bg-accent-coral text-ink border-ink shadow-tactile font-bold';
                  numStyle = 'border-ink text-paper bg-ink font-bold';
                }

                return (
                  <div
                    key={step.id}
                    className={`border rounded-lg p-3 transition-all duration-200 flex items-start gap-3 ${cardStyle}`}
                  >
                    {/* Step Number / Icon */}
                    <div
                      className={`w-7 h-7 rounded-full border flex items-center justify-center font-mono text-xs shrink-0 mt-0.5 ${numStyle}`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 stroke-[2.5]" />
                      ) : isFailed ? (
                        <AlertTriangle className="w-4 h-4 stroke-[2.5]" />
                      ) : isActive ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        step.number
                      )}
                    </div>

                    {/* Step Info & Detail */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold tracking-tight">
                          {step.number} {step.label}
                        </span>
                        {isActive && (
                          <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 bg-paper text-ink rounded-full font-bold">
                            In Progress
                          </span>
                        )}
                      </div>

                      <p
                        className={`text-[11px] leading-tight mt-0.5 ${
                          isActive ? 'text-paper/80' : isDone || isFailed ? 'text-ink/80' : 'text-ink-muted'
                        }`}
                      >
                        {state.detail || step.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pipeline Complete Summary Card */}
            {phase === 'complete' && finalVerdict && (
              <div className="tactile-card p-4 bg-white border border-ink flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-ink" />
                    <div>
                      <span className="text-[10px] font-mono uppercase text-ink-secondary font-bold">
                        Final Result
                      </span>
                      <h4 className="font-serif text-lg font-bold text-ink">
                        Scored {Math.round(finalVerdict.score)}/100
                      </h4>
                    </div>
                  </div>

                  {/* Status Badge */}
                  {finalVerdict.duplicate_flag ? (
                    <span className="px-3 py-1 bg-pastel-yellow text-ink border border-ink rounded-full text-xs font-bold shadow-tactile-sm flex items-center gap-1">
                      <Copy className="w-3.5 h-3.5" />
                      <span>Duplicate Warning</span>
                    </span>
                  ) : finalVerdict.score < 50 ? (
                    <span className="px-3 py-1 bg-accent-coral text-ink border border-ink rounded-full text-xs font-bold shadow-tactile-sm flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      <span>Flagged</span>
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-pastel-mint text-ink border border-ink rounded-full text-xs font-bold shadow-tactile-sm flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Passed</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-ink/10">
                  <button
                    onClick={onClose}
                    className="tactile-pill px-4 py-2 bg-white text-ink text-xs font-medium hover:bg-canvas-subtle"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      if (onViewVerdict) onViewVerdict(finalVerdict);
                      onClose();
                    }}
                    className="tactile-pill flex items-center gap-1.5 px-4 py-2 bg-ink text-paper text-xs font-bold hover:bg-ink-secondary shadow-tactile"
                  >
                    <span>View Rubric Inspection</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* Pipeline Failed Summary Card */}
            {phase === 'failed' && failureInfo && (
              <div className="tactile-card p-4 bg-[#FDECE7] border border-accent-coral flex flex-col gap-3">
                <div className="flex items-start gap-2 text-ink">
                  <AlertTriangle className="w-5 h-5 text-accent-coral shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <span className="text-[10px] font-mono uppercase text-ink-secondary font-bold">
                      Failure at step: {failureInfo.step}
                    </span>
                    <p className="text-xs text-ink font-mono mt-1 whitespace-pre-wrap break-words">
                      {failureInfo.error}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-accent-coral/20">
                  <button
                    onClick={onClose}
                    className="tactile-pill px-4 py-2 bg-white text-ink text-xs font-medium hover:bg-canvas-subtle"
                  >
                    Dismiss
                  </button>
                  <button
                    onClick={handleReset}
                    className="tactile-pill flex items-center gap-1.5 px-4 py-2 bg-accent-coral text-ink text-xs font-bold hover:bg-accent-coral-hover shadow-tactile"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Try Again</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
