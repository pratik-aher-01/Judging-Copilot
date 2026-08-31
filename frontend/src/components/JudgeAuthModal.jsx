import React, { useState } from 'react';
import { Lock, KeyRound, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';

const EXPECTED_USER = import.meta.env.VITE_JUDGE_USERNAME || 'pratik@devpost';
const EXPECTED_PASS = import.meta.env.VITE_JUDGE_PASSWORD || 'pratik2026';

export default function JudgeAuthModal({ isOpen, onAuthenticate }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    const cleanUser = username.trim();
    const cleanPass = password.trim();

    if (cleanUser === EXPECTED_USER && cleanPass === EXPECTED_PASS) {
      localStorage.setItem('judge_authenticated', 'true');
      onAuthenticate();
    } else {
      setError('Invalid judge credentials. Access restricted to hackathon evaluators.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/60 backdrop-blur-md animate-in fade-in duration-200">
      <div className="tactile-card w-full max-w-md bg-paper p-6 relative flex flex-col gap-5 shadow-tactile-lg border-2 border-ink">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-ink/15 pb-4">
          <div className="w-10 h-10 rounded-xl bg-accent-coral text-ink border border-ink flex items-center justify-center shadow-tactile-sm shrink-0">
            <Lock className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-ink-secondary bg-canvas-subtle border border-ink/20 px-2 py-0.5 rounded-full">
              Judge Access Gate
            </span>
            <h2 className="font-serif text-xl font-bold text-ink">
              Organizer & Judge Verification
            </h2>
          </div>
        </div>

        <p className="text-xs text-ink-secondary leading-relaxed">
          This application is locked for hackathon evaluation. Please enter your authorized judge credentials to access the Judging Copilot dashboard.
        </p>

        {/* Error Alert */}
        {error && (
          <div className="bg-[#FDECE7] border border-accent-coral p-3 rounded-lg flex items-start gap-2 text-xs text-ink animate-in fade-in">
            <ShieldAlert className="w-4 h-4 text-accent-coral shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-mono font-semibold text-ink">
              Judge Username / Email
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="pratik@devpost"
                required
                className="w-full bg-white border border-ink rounded-lg pl-9 pr-3 py-2.5 text-xs font-mono text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-accent-coral"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-mono font-semibold text-ink">
              Judge Passcode
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-white border border-ink rounded-lg pl-9 pr-3 py-2.5 text-xs font-mono text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-accent-coral"
              />
            </div>
          </div>

          <button
            type="submit"
            className="tactile-pill flex items-center justify-center gap-2 px-5 py-2.5 bg-ink text-paper text-xs font-bold hover:bg-ink-secondary shadow-tactile mt-2"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Authenticate & Enter Hub</span>
          </button>
        </form>
      </div>
    </div>
  );
}
