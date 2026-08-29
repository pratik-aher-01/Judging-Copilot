import React from 'react';
import { Plus } from 'lucide-react';

export default function EmptyState({ onOpenSubmit, filterName = 'all' }) {
  return (
    <div className="tactile-card p-10 flex flex-col items-center justify-center text-center my-6">
      {/* Handcrafted Doodle SVG Illustration */}
      <svg
        className="w-28 h-28 text-ink mb-4"
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Playful cartoon folder with eyes & glasses judging submissions */}
        <path
          d="M20 38C20 34.6863 22.6863 32 26 32H44L52 42H94C97.3137 42 100 44.6863 100 48V88C100 91.3137 97.3137 94 94 94H26C22.6863 94 20 91.3137 20 88V38Z"
          stroke="#191817"
          strokeWidth="2.5"
          fill="#FAF7F2"
          strokeLinejoin="round"
        />
        {/* Doodle sparkle lines */}
        <path
          d="M102 30L108 24M104 24L110 30"
          stroke="#F47B56"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <path
          d="M12 28L18 24M14 22L16 30"
          stroke="#7DD6AC"
          strokeWidth="2"
          strokeLinecap="round"
        />
        {/* Monocle / magnifying glass */}
        <circle cx="56" cy="66" r="14" stroke="#191817" strokeWidth="2.5" fill="#FFE678" />
        <circle cx="56" cy="66" r="5" fill="#191817" />
        <path d="M66 76L76 86" stroke="#191817" strokeWidth="3" strokeLinecap="round" />
        {/* Smirk line */}
        <path
          d="M42 74C44 77 47 78 50 77"
          stroke="#191817"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>

      <h3 className="font-serif text-2xl font-bold text-ink mb-2">
        {filterName === 'all'
          ? 'No verdicts recorded yet'
          : `No ${filterName} submissions found`}
      </h3>
      <p className="text-sm text-ink-secondary max-w-md mb-6 leading-relaxed">
        {filterName === 'all'
          ? 'Submit a public GitHub repository URL above to clone, score against hackathon rubrics, and run duplicate checks.'
          : `There are currently no submissions matching the "${filterName}" filter criteria.`}
      </p>

      {filterName === 'all' && (
        <button
          onClick={onOpenSubmit}
          className="tactile-pill flex items-center gap-2 px-5 py-2.5 bg-accent-coral text-ink font-semibold text-xs hover:bg-accent-coral-hover shadow-tactile"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Submit First Repo</span>
        </button>
      )}
    </div>
  );
}
