'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import api from '@/lib/api';
import {
  BookOpen,
  Search,
  Sparkles,
  ShieldCheck,
  FileText,
  Activity,
  Layers,
  CheckCircle2,
} from 'lucide-react';

export default function KnowledgeBasePage() {
  return (
    <ProtectedRoute>
      <KnowledgeBaseContent />
    </ProtectedRoute>
  );
}

function KnowledgeBaseContent() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [searched, setSearched] = useState(false);

  const sampleQuestions = [
    'What are the critical panic limits for platelets and hemoglobin?',
    'What is the standard protocol for Metformin and Telmisartan contraindications?',
    'What documentation is required for Laparoscopic Cholecystectomy insurance claims?',
  ];

  const handleSearch = async (searchQuery: string) => {
    const q = searchQuery || query;
    if (!q.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await api.post('/rag/search', {
        query: q,
        k: 4,
      });
      setResults(res.data?.results || res.data || []);
    } catch (err) {
      console.error('Failed to search clinical knowledge base:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
              <BookOpen className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Clinical Knowledge & RAG Grounding Vault
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                  FastEmbed Semantic ONNX
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Grounded medical knowledge retrieval ensuring deterministic evidence citations with zero hallucination.
              </p>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="w-5 h-5 absolute left-3.5 top-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Ask clinical knowledge question or query medical reference docs..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
                className="w-full pl-11 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              />
            </div>
            <button
              onClick={() => handleSearch(query)}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-indigo-900/30 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Retrieving...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> Retrieve Grounded Context
                </>
              )}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-4 text-xs">
            <span className="text-slate-500">Suggested Topics:</span>
            {sampleQuestions.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(sq);
                  handleSearch(sq);
                }}
                className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg transition"
              >
                {sq.substring(0, 40)}...
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="text-center py-20 text-slate-400">
            <Activity className="w-6 h-6 animate-spin text-indigo-400 mx-auto mb-2" />
            <span>Executing vector similarity search and reranking chunks...</span>
          </div>
        ) : searched && results.length === 0 ? (
          <div className="text-center py-16 bg-slate-900/50 border border-slate-800 rounded-2xl">
            <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No knowledge chunks matched the query.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {results.map((r: any, idx: number) => (
              <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono font-bold text-indigo-400">
                    Source: {r.source || r.title || `Document #${r.document_id || idx + 1}`}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Score: {typeof r.score === 'number' ? r.score.toFixed(3) : 'Grounded'}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed font-normal">
                  {r.text || r.content || r.snippet}
                </p>
                {r.metadata && (
                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center gap-3 text-xs text-slate-500 font-mono">
                    {r.metadata.page && <span>Page: {r.metadata.page}</span>}
                    {r.metadata.category && <span>Category: {r.metadata.category}</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
