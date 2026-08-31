import React, { useState, useEffect, useMemo } from 'react';
import TopNav from './components/TopNav';
import LeftRail from './components/LeftRail';
import VerdictTable from './components/VerdictTable';
import RubricDrawer from './components/RubricDrawer';
import EmptyState from './components/EmptyState';
import AgentActivityPanel from './components/AgentActivityPanel';
import JudgeAuthModal from './components/JudgeAuthModal';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { API_BASE_URL } from './config';

const API_BASE = API_BASE_URL;

export default function App() {
  const [verdicts, setVerdicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedVerdict, setSelectedVerdict] = useState(null);
  const [isActivityOpen, setIsActivityOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('judge_authenticated') === 'true';
  });

  // Sorting state
  const [sortField, setSortField] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');

  const fetchVerdicts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/verdicts`);
      if (!res.ok) {
        throw new Error(`Failed to fetch verdicts (HTTP ${res.status})`);
      }
      const data = await res.json();
      setVerdicts(Array.isArray(data) ? data : []);
      // If a verdict was previously selected, update its reference
      if (selectedVerdict) {
        const updated = data.find(
          (v) =>
            (v._doc_id && v._doc_id === selectedVerdict._doc_id) ||
            v.repo_url === selectedVerdict.repo_url
        );
        if (updated) setSelectedVerdict(updated);
      }
    } catch (err) {
      console.error('Error fetching verdicts:', err);
      setError(
        `Backend unreachable at ${API_BASE}/verdicts. Ensure FastAPI server is running with \`python app.py\`.`
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVerdicts();
  }, []);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Filtered and Sorted Verdicts
  const filteredVerdicts = useMemo(() => {
    return verdicts.filter((v) => {
      if (activeFilter === 'flagged') {
        return v.duplicate_flag || (v.score !== undefined && v.score < 50);
      }
      if (activeFilter === 'duplicate') {
        return v.duplicate_flag;
      }
      if (activeFilter === 'clean') {
        return !v.duplicate_flag && v.score >= 50;
      }
      return true;
    });
  }, [verdicts, activeFilter]);

  const sortedVerdicts = useMemo(() => {
    return [...filteredVerdicts].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (sortField === 'score' || sortField === 'similarity_score') {
        valA = Number(valA || 0);
        valB = Number(valB || 0);
      } else if (sortField === 'timestamp') {
        valA = new Date(valA || 0).getTime();
        valB = new Date(valB || 0).getTime();
      } else if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = (valB || '').toLowerCase();
      }

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredVerdicts, sortField, sortDirection]);

  const handleVerdictCreated = (newVerdict) => {
    fetchVerdicts();
  };

  const handleViewVerdict = (verdict) => {
    fetchVerdicts();
    setSelectedVerdict(verdict);
  };

  return (
    <div className="min-h-screen bg-paper flex flex-col selection:bg-accent-coral selection:text-ink">
      {/* Slim Top Bar */}
      <TopNav
        verdicts={verdicts}
        loading={loading}
        onRefresh={fetchVerdicts}
        onOpenSubmit={() => setIsActivityOpen(true)}
        isAuthenticated={isAuthenticated}
        onSignOut={() => {
          localStorage.removeItem('judge_authenticated');
          setIsAuthenticated(false);
        }}
      />

      {/* Backend Disconnected Notice (if any) */}
      {error && (
        <div className="bg-[#FDECE7] border-b border-accent-coral px-6 py-2.5 flex items-center justify-between text-xs text-ink">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-accent-coral shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchVerdicts}
            className="font-mono underline font-bold hover:text-accent-coral flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Retry Connection
          </button>
        </div>
      )}

      {/* Main 3-Part Layout Architecture */}
      <main className="flex-1 flex flex-col md:flex-row overflow-hidden min-h-[calc(100vh-65px)]">
        {/* Left Filter Rail */}
        <div className="w-full md:w-72 shrink-0 p-6 border-r border-ink/10 bg-paper">
          <LeftRail
            activeFilter={activeFilter}
            onSelectFilter={(id) => {
              setActiveFilter(id);
            }}
            verdicts={verdicts}
          />
        </div>

        {/* Center Main Canvas: Dense Verdict Table */}
        <div className="flex-1 min-w-0 p-6 overflow-y-auto flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-serif text-xl font-bold text-ink">
                Submission Verdicts
              </h1>
              <p className="text-xs text-ink-secondary">
                Showing {sortedVerdicts.length} of {verdicts.length} total evaluations
              </p>
            </div>
          </div>

          {loading && verdicts.length === 0 ? (
            <div className="tactile-card p-12 text-center flex flex-col items-center justify-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-ink-secondary" />
              <span className="font-mono text-xs text-ink-secondary">
                Fetching verdicts from Firestore...
              </span>
            </div>
          ) : sortedVerdicts.length === 0 ? (
            <EmptyState
              onOpenSubmit={() => setIsActivityOpen(true)}
              filterName={activeFilter}
            />
          ) : (
            <VerdictTable
              verdicts={sortedVerdicts}
              selectedVerdict={selectedVerdict}
              onSelectVerdict={(v) => setSelectedVerdict(v)}
              sortField={sortField}
              sortDirection={sortDirection}
              onSort={handleSort}
            />
          )}
        </div>

        {/* Right Drawer: Rubric Breakdown */}
        {selectedVerdict && (
          <RubricDrawer
            verdict={selectedVerdict}
            onClose={() => setSelectedVerdict(null)}
          />
        )}
      </main>

      {/* Live Agent Activity & Submission Panel */}
      <AgentActivityPanel
        isOpen={isActivityOpen}
        onClose={() => setIsActivityOpen(false)}
        onVerdictCreated={handleVerdictCreated}
        onViewVerdict={handleViewVerdict}
      />

      {/* Judge Authentication Gate Modal */}
      <JudgeAuthModal
        isOpen={!isAuthenticated}
        onAuthenticate={() => setIsAuthenticated(true)}
      />
    </div>
  );
}
