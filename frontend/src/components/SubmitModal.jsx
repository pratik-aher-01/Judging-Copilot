import React, { useState } from 'react';
import { X, Sparkles, AlertCircle, Loader2, GitBranch } from 'lucide-react';

export default function SubmitModal({ isOpen, onClose, onSuccess }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const cleanUrl = repoUrl.trim();
    if (!cleanUrl.startsWith('https://github.com/')) {
      setError('Please enter a valid GitHub HTTPS URL (e.g. https://github.com/owner/repo)');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/judge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: cleanUrl }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Pipeline execution failed.');
      }

      setRepoUrl('');
      onSuccess(data);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server at http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-sm">
      <div className="tactile-card w-full max-w-lg bg-paper p-6 relative flex flex-col gap-4 shadow-tactile-lg animate-in fade-in zoom-in-95 duration-150">
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={loading}
          className="absolute top-4 right-4 tactile-pill p-1.5 bg-white text-ink hover:bg-canvas-subtle"
        >
          <X className="w-4 h-4 stroke-[2.5]" />
        </button>

        {/* Title */}
        <div>
          <div className="flex items-center gap-2 text-accent-coral mb-1">
            <Sparkles className="w-4 h-4" />
            <span className="text-[11px] font-mono uppercase tracking-wider font-bold text-ink-secondary">
              Automated Evaluation
            </span>
          </div>
          <h3 className="font-serif text-2xl font-bold text-ink">
            Score New Submission
          </h3>
          <p className="text-xs text-ink-secondary mt-1">
            Clones repo, runs Gemini 3.5 structured rubric evaluation, performs duplicate vector checks, and writes to Firestore.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-[#FDECE7] border border-accent-coral rounded-lg flex items-start gap-2 text-xs text-ink">
            <AlertCircle className="w-4 h-4 text-accent-coral shrink-0 mt-0.5" />
            <span className="leading-tight">{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-mono font-semibold text-ink">
              GitHub Repository URL
            </label>
            <div className="relative">
              <GitBranch className="w-4 h-4 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                required
                disabled={loading}
                className="w-full bg-white border border-ink rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-accent-coral"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-ink/10">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="tactile-pill px-4 py-2 bg-white text-ink text-xs font-medium hover:bg-canvas-subtle"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="tactile-pill flex items-center gap-2 px-5 py-2 bg-accent-coral text-ink text-xs font-bold hover:bg-accent-coral-hover disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating Pipeline...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Run Evaluation</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
