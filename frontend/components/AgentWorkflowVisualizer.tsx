'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  WorkflowState,
  AgentExecutionLog,
  ClinicalFinding,
  LabFinding,
  FinalReport,
  AuditEntry,
  AgentStatus,
  WorkflowStatus,
} from '@/lib/types';
import { useAuth } from '@/lib/authContext';
import api from '@/lib/api';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock,
  Copy,
  ExternalLink,
  FileCheck,
  FileSearch,
  FileText,
  Flame,
  Info,
  Layers,
  Lock,
  MessageSquare,
  Play,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Terminal,
  TrendingUp,
  UserCheck,
  Zap,
} from 'lucide-react';

interface AgentWorkflowVisualizerProps {
  workflowId: string;
  onWorkflowComplete?: (state: WorkflowState) => void;
}

interface AgentMetadata {
  id: string;
  name: string;
  role: string;
  icon: React.ElementType;
  badge?: string;
}

const AGENT_CATALOG: AgentMetadata[] = [
  { id: 'patient_intake', name: 'Patient Intake', role: 'Context & Demographics', icon: UserCheck },
  { id: 'document_intelligence', name: 'Document Intelligence', role: 'Multimodal Classifier', icon: FileSearch },
  { id: 'ocr', name: 'OCR & Layout Engine', role: 'Text & Table Extraction', icon: FileText },
  { id: 'data_validation', name: 'Data Validation', role: 'Physiological Bounds', icon: ShieldCheck },
  { id: 'lab_analysis', name: 'Lab Analysis ⭐', role: 'Biomarkers & Panic Checks', icon: Flame, badge: 'Core Feature' },
  { id: 'patient_history', name: 'Patient History', role: 'Longitudinal Trends', icon: TrendingUp },
  { id: 'symptom_clinical', name: 'Symptom & Clinical', role: 'Clinical Correlation', icon: Stethoscope },
  { id: 'medical_rag', name: 'Medical RAG', role: 'Verified Guidelines', icon: Search },
  { id: 'risk_prediction', name: 'Risk Prediction', role: 'Health & Integrity Risk', icon: Activity },
  { id: 'verification_report', name: 'Verification & Report', role: 'Synthesis & Cryptography', icon: FileCheck },
];

export const AgentWorkflowVisualizer: React.FC<AgentWorkflowVisualizerProps> = ({
  workflowId,
  onWorkflowComplete,
}) => {
  const { user } = useAuth();
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [streamConnected, setStreamConnected] = useState<boolean>(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('lab_analysis');
  const [activeTab, setActiveTab] = useState<'flow' | 'labs' | 'findings' | 'rag' | 'report' | 'audit'>('flow');

  // Human-in-the-loop review form state
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<boolean>(false);

  // Live elapsed time timer
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const isDoctorOrAdmin =
    user?.role === 'SUPER_ADMIN' ||
    user?.role === 'HOSPITAL_ADMIN' ||
    user?.role === 'INSURANCE_ADMIN';

  // 1. Initial State Fetch
  const fetchState = async () => {
    try {
      const res = await api.get<WorkflowState>(`/agent-workflow/${workflowId}`);
      setWorkflowState(res.data);
      if (res.data.current_agent) {
        setSelectedAgentId(res.data.current_agent);
      }
      setLoading(false);
    } catch (err: any) {
      console.error('Error fetching workflow state:', err);
      setStreamError(err.response?.data?.detail || 'Failed to fetch workflow state');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!workflowId) return;
    setLoading(true);
    setStreamError(null);
    fetchState();
  }, [workflowId]);

  // 2. Stopwatch Timer for in-progress execution
  useEffect(() => {
    if (workflowState?.status === 'IN_PROGRESS' || workflowState?.status === 'PENDING') {
      const startTime = new Date(workflowState.created_at || Date.now()).getTime();
      timerRef.current = setInterval(() => {
        const now = Date.now();
        const diff = Math.max(0, Math.floor((now - startTime) / 1000));
        setElapsedSeconds(diff);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      if (workflowState?.created_at && workflowState?.updated_at) {
        const start = new Date(workflowState.created_at).getTime();
        const end = new Date(workflowState.updated_at).getTime();
        setElapsedSeconds(Math.max(0, Math.floor((end - start) / 1000)));
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [workflowState?.status, workflowState?.created_at, workflowState?.updated_at]);

  // 3. Real-Time SSE Stream Connection
  useEffect(() => {
    if (!workflowId) return;

    let evtSource: EventSource | null = null;
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const streamUrl = `${apiBase}/api/agent-workflow/${workflowId}/stream${token ? `?token=${token}` : ''}`;

    try {
      evtSource = new EventSource(streamUrl);

      evtSource.onopen = () => {
        setStreamConnected(true);
        setStreamError(null);
      };

      evtSource.addEventListener('workflow_started', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setWorkflowState((prev) => {
          if (!prev) return prev;
          return { ...prev, status: 'IN_PROGRESS' };
        });
      });

      evtSource.addEventListener('agent_started', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setSelectedAgentId(data.agent);
        setWorkflowState((prev) => {
          if (!prev) return prev;
          const currentLogs = [...prev.execution_logs];
          const existingIdx = currentLogs.findIndex((l) => l.agent_name === data.agent);
          const newLog: AgentExecutionLog = {
            agent_name: data.agent,
            status: 'RUNNING',
            started_at: new Date().toISOString(),
          };
          if (existingIdx >= 0) {
            currentLogs[existingIdx] = { ...currentLogs[existingIdx], status: 'RUNNING' };
          } else {
            currentLogs.push(newLog);
          }
          return {
            ...prev,
            current_agent: data.agent,
            status: 'IN_PROGRESS',
            execution_logs: currentLogs,
          };
        });
      });

      evtSource.addEventListener('agent_completed', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setWorkflowState((prev) => {
          if (!prev) return prev;
          const completed = Array.from(new Set([...prev.completed_agents, data.agent]));
          const currentLogs = [...prev.execution_logs];
          const idx = currentLogs.findIndex((l) => l.agent_name === data.agent);
          if (idx >= 0) {
            currentLogs[idx] = {
              ...currentLogs[idx],
              status: 'COMPLETED',
              duration_ms: data.duration_ms,
              confidence: data.confidence,
              completed_at: new Date().toISOString(),
            };
          }
          return {
            ...prev,
            completed_agents: completed,
            execution_logs: currentLogs,
          };
        });
        // Refresh full state incrementally to pull extracted lab/clinical findings
        fetchState();
      });

      evtSource.addEventListener('agent_failed', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setWorkflowState((prev) => {
          if (!prev) return prev;
          const failed = Array.from(new Set([...prev.failed_agents, data.agent]));
          return { ...prev, failed_agents: failed };
        });
        fetchState();
      });

      evtSource.addEventListener('agent_skipped', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setWorkflowState((prev) => {
          if (!prev) return prev;
          const skipped = Array.from(new Set([...prev.skipped_agents, data.agent]));
          return { ...prev, skipped_agents: skipped };
        });
      });

      evtSource.addEventListener('decision', (e: MessageEvent) => {
        fetchState();
      });

      evtSource.addEventListener('escalation_required', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setWorkflowState((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            escalation_required: true,
            escalation_reason: data.reason,
            status: 'DOCTOR_REVIEW_REQUIRED',
          };
        });
        fetchState();
      });

      evtSource.addEventListener('workflow_completed', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setStreamConnected(false);
        fetchState().then(() => {
          if (workflowState && onWorkflowComplete) {
            onWorkflowComplete(workflowState);
          }
        });
        if (evtSource) evtSource.close();
      });

      evtSource.addEventListener('workflow_failed', (e: MessageEvent) => {
        setStreamConnected(false);
        fetchState();
        if (evtSource) evtSource.close();
      });

      evtSource.onerror = () => {
        // SSE disconnected or complete
        setStreamConnected(false);
      };
    } catch (err) {
      console.error('SSE initialization error:', err);
      setStreamConnected(false);
    }

    return () => {
      if (evtSource) {
        evtSource.close();
      }
    };
  }, [workflowId]);

  // Handle Human-in-the-Loop Doctor Review Action
  const handleReviewDecision = async (decision: 'APPROVE' | 'REJECT' | 'REQUEST_MORE_INFORMATION') => {
    if (!workflowId) return;
    setSubmittingReview(true);
    setReviewSuccessMsg(null);
    try {
      await api.post(`/agent-workflow/${workflowId}/review`, {
        decision,
        notes: reviewNotes,
      });
      setReviewSuccessMsg(`Review decision '${decision}' submitted successfully.`);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit review.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const copyWorkflowId = () => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(workflowId);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  // Helper to determine agent visual status
  const getAgentStatus = (agentId: string): AgentStatus => {
    if (!workflowState) return 'IDLE';
    if (workflowState.completed_agents.includes(agentId)) return 'COMPLETED';
    if (workflowState.failed_agents.includes(agentId)) return 'FAILED';
    if (workflowState.skipped_agents.includes(agentId)) return 'SKIPPED';
    if (workflowState.current_agent === agentId && workflowState.status === 'IN_PROGRESS') return 'RUNNING';
    return 'IDLE';
  };

  const getAgentLog = (agentId: string): AgentExecutionLog | undefined => {
    return workflowState?.execution_logs.find((l) => l.agent_name === agentId);
  };

  if (loading && !workflowState) {
    return (
      <div className="bg-gray-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center shadow-2xl">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white">Initializing MedSentinel Agent Architecture...</h3>
        <p className="text-gray-400 text-sm mt-1">Connecting to Orchestrator and specialized agent telemetry</p>
      </div>
    );
  }

  if (streamError && !workflowState) {
    return (
      <div className="bg-red-950/40 border border-red-500/30 rounded-2xl p-8 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white">Workflow Unavailable</h3>
        <p className="text-red-300 text-sm mt-1">{streamError}</p>
        <button
          onClick={fetchState}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const selectedAgentMeta = AGENT_CATALOG.find((a) => a.id === selectedAgentId) || AGENT_CATALOG[4];
  const selectedAgentLog = getAgentLog(selectedAgentId);
  const criticalFindings = workflowState?.clinical_findings.filter((f) => f.is_critical) || [];
  const labResults = workflowState?.lab_results || [];

  return (
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* 1. TOP HEADER & TELEMETRY DASHBOARD */}
      {/* ========================================================================= */}
      <div className="bg-gradient-to-r from-gray-900 via-gray-900/90 to-blue-950/50 border border-white/10 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-xl font-bold text-white font-['Manrope']">
                    Agentic Healthcare Workflow
                  </h2>
                  {streamConnected ? (
                    <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                      <span>Live SSE Stream</span>
                    </span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-gray-700/50 text-gray-300 border border-white/10">
                      {workflowState?.status === 'COMPLETED' ? 'Stream Finished' : 'Polling Sync'}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2 mt-0.5 text-xs text-gray-400">
                  <span>Workflow ID:</span>
                  <code className="px-2 py-0.5 bg-black/40 rounded text-blue-300 font-mono">
                    {workflowId}
                  </code>
                  <button
                    onClick={copyWorkflowId}
                    className="hover:text-white transition-colors"
                    title="Copy Workflow ID"
                  >
                    {copiedId ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                  {workflowState?.patient_name && (
                    <>
                      <span>•</span>
                      <span className="text-gray-300">
                        Patient: <strong>{workflowState.patient_name}</strong> (ID: {workflowState.patient_id})
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Status & Metrics Bar */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Status Badge */}
            <div className="px-3.5 py-1.5 rounded-xl border flex items-center space-x-2 text-xs font-bold uppercase tracking-wider bg-black/40 shadow-inner">
              {workflowState?.status === 'COMPLETED' && (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">Completed</span>
                </>
              )}
              {workflowState?.status === 'IN_PROGRESS' && (
                <>
                  <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                  <span className="text-blue-400">Executing DAG</span>
                </>
              )}
              {workflowState?.status === 'DOCTOR_REVIEW_REQUIRED' && (
                <>
                  <ShieldAlert className="w-4 h-4 text-amber-400 animate-pulse" />
                  <span className="text-amber-400">Doctor Review Required</span>
                </>
              )}
              {workflowState?.status === 'FAILED' && (
                <>
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <span className="text-red-400">Failed</span>
                </>
              )}
              {workflowState?.status === 'PENDING' && (
                <>
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-400">Pending</span>
                </>
              )}
            </div>

            {/* Elapsed Time */}
            <div className="px-3.5 py-1.5 rounded-xl bg-black/40 border border-white/10 flex items-center space-x-2 text-xs">
              <Clock className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-400">Elapsed:</span>
              <span className="font-mono font-bold text-white">{elapsedSeconds}s</span>
            </div>

            {/* Agents Progress */}
            <div className="px-3.5 py-1.5 rounded-xl bg-black/40 border border-white/10 flex items-center space-x-2 text-xs">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-gray-400">Completed:</span>
              <span className="font-bold text-blue-400">
                {workflowState?.completed_agents.length || 0} / {AGENT_CATALOG.length}
              </span>
            </div>

            {/* Manual Refresh */}
            <button
              onClick={fetchState}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white transition-all"
              title="Refresh State"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Dynamic Orchestrator Routing Banner */}
        {workflowState?.workflow_type && (
          <div className="mt-4 pt-4 border-t border-white/10 flex flex-col md:flex-row md:items-center justify-between text-xs gap-2">
            <div className="flex items-center space-x-2 text-gray-300">
              <Zap className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>
                <strong>Dynamic Orchestration:</strong> Classified as{' '}
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded font-semibold border border-blue-500/30">
                  {workflowState.workflow_type}
                </span>
                {workflowState.document_type && (
                  <span className="ml-2 text-gray-400">
                    (Document: <em>{workflowState.document_type}</em>)
                  </span>
                )}
              </span>
            </div>
            {workflowState.escalation_required && (
              <div className="flex items-center space-x-1.5 text-amber-300 bg-amber-500/10 px-3 py-1 rounded-lg border border-amber-500/20">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                <span>
                  <strong>Escalation Triggered:</strong>{' '}
                  {workflowState.escalation_reason || 'Critical clinical findings require verification'}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 2. DYNAMIC AGENT DAG WORKFLOW VISUALIZER */}
      {/* ========================================================================= */}
      <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-6 backdrop-blur-xl shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <span>Dynamic Agent DAG Execution Flow</span>
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Click any agent node to inspect real execution telemetry, tools, and confidence metrics
            </p>
          </div>
          <div className="hidden sm:flex items-center space-x-3 text-[11px] text-gray-400">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Completed</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <span>Running</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-gray-600" />
              <span>Pending</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span>Skipped</span>
            </span>
          </div>
        </div>

        {/* Horizontal DAG Nodes Flow */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-5 gap-3">
          {AGENT_CATALOG.map((agent, idx) => {
            const status = getAgentStatus(agent.id);
            const log = getAgentLog(agent.id);
            const isSelected = selectedAgentId === agent.id;
            const IconComponent = agent.icon;

            return (
              <div
                key={agent.id}
                onClick={() => setSelectedAgentId(agent.id)}
                className={`cursor-pointer relative p-3.5 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                  isSelected
                    ? 'ring-2 ring-blue-500 bg-blue-950/40 border-blue-500/50 shadow-lg shadow-blue-500/10'
                    : 'bg-black/30 hover:bg-white/5 border-white/5 hover:border-white/15'
                } ${
                  status === 'RUNNING'
                    ? 'border-blue-500 bg-blue-950/50 ring-1 ring-blue-400 shadow-lg shadow-blue-500/20'
                    : status === 'COMPLETED'
                    ? 'border-emerald-500/30'
                    : status === 'FAILED'
                    ? 'border-red-500/40 bg-red-950/20'
                    : status === 'SKIPPED'
                    ? 'opacity-40 border-dashed'
                    : 'opacity-70'
                }`}
              >
                {/* Badge if special */}
                {agent.badge && (
                  <span className="absolute -top-2 right-2 px-2 py-0.5 rounded-full text-[9px] font-extrabold bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-sm">
                    {agent.badge}
                  </span>
                )}

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                        status === 'COMPLETED'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : status === 'RUNNING'
                          ? 'bg-blue-500/20 text-blue-400 animate-pulse'
                          : status === 'FAILED'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-white/5 text-gray-400'
                      }`}
                    >
                      <IconComponent className="w-4 h-4" />
                    </div>

                    {/* Status Pill */}
                    <div>
                      {status === 'COMPLETED' && (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      )}
                      {status === 'RUNNING' && (
                        <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                      )}
                      {status === 'FAILED' && (
                        <AlertCircle className="w-4 h-4 text-red-400" />
                      )}
                      {status === 'SKIPPED' && (
                        <span className="text-[10px] text-gray-500 font-mono">—</span>
                      )}
                      {status === 'IDLE' && (
                        <Clock className="w-3.5 h-3.5 text-gray-600" />
                      )}
                    </div>
                  </div>

                  <h4 className="text-xs font-bold text-white truncate">{agent.name}</h4>
                  <p className="text-[10px] text-gray-400 truncate mt-0.5">{agent.role}</p>
                </div>

                {/* Duration / Confidence Footer */}
                <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-gray-400">
                  <span>
                    {log?.duration_ms ? `${Math.round(log.duration_ms)} ms` : status === 'RUNNING' ? '...' : '—'}
                  </span>
                  {log?.confidence && (
                    <span className="text-emerald-400 font-semibold">
                      {Math.round(log.confidence * 100)}% conf
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. HUMAN-IN-THE-LOOP DOCTOR REVIEW PANEL (IF ESCALATED) */}
      {/* ========================================================================= */}
      {(workflowState?.status === 'DOCTOR_REVIEW_REQUIRED' || workflowState?.escalation_required) && (
        <div className="bg-gradient-to-r from-amber-950/60 via-gray-900 to-red-950/40 border-2 border-amber-500/50 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start space-x-3">
              <div className="p-3 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30">
                <ShieldAlert className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                  <span>DOCTOR REVIEW REQUIRED</span>
                  <span className="px-2 py-0.5 rounded text-[11px] bg-red-500/20 text-red-300 font-bold border border-red-500/30">
                    Critical Clinical Escalation
                  </span>
                </h3>
                <p className="text-xs text-amber-200/90 mt-1 max-w-2xl">
                  {workflowState?.escalation_reason ||
                    'One or more critical physiological parameters or contradiction flags were detected. Review and authorize before finalizing decision-support report.'}
                </p>

                {criticalFindings.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <span className="text-[11px] font-bold text-gray-300 uppercase tracking-wider">
                      Flagged Critical Findings:
                    </span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {criticalFindings.map((cf, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 bg-red-950/60 border border-red-500/40 rounded-lg text-xs text-red-200 font-semibold"
                        >
                          ⚠️ {cf.title} ({cf.observed_value} {cf.unit || ''}) — {cf.status}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Doctor Actions */}
          <div className="mt-6 pt-5 border-t border-amber-500/20">
            {isDoctorOrAdmin ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">
                    Doctor Review Notes & Clinical Assessment:
                  </label>
                  <textarea
                    rows={2}
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Enter clinical observations, protocol adjustments, or verification commentary..."
                    className="w-full bg-black/40 border border-white/15 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-amber-400"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => handleReviewDecision('APPROVE')}
                    disabled={submittingReview}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold flex items-center space-x-2 transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve Decision Support</span>
                  </button>

                  <button
                    onClick={() => handleReviewDecision('REQUEST_MORE_INFORMATION')}
                    disabled={submittingReview}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-bold flex items-center space-x-2 transition-all disabled:opacity-50"
                  >
                    <MessageSquare className="w-4 h-4" />
                    <span>Request More Information</span>
                  </button>

                  <button
                    onClick={() => handleReviewDecision('REJECT')}
                    disabled={submittingReview}
                    className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold flex items-center space-x-2 transition-all disabled:opacity-50"
                  >
                    <AlertCircle className="w-4 h-4" />
                    <span>Reject / Flag Contradiction</span>
                  </button>

                  {reviewSuccessMsg && (
                    <span className="text-xs text-emerald-400 font-semibold">{reviewSuccessMsg}</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-3 bg-black/30 rounded-xl border border-white/5 text-xs text-gray-400 flex items-center space-x-2">
                <Lock className="w-4 h-4 text-amber-400" />
                <span>
                  Waiting for a licensed physician or hospital administrator to review and authorize this critical workflow.
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. MAIN DETAILS TAB VIEW */}
      {/* ========================================================================= */}
      <div className="bg-gray-900/70 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-xl shadow-xl">
        {/* Navigation Tabs */}
        <div className="flex border-b border-white/10 overflow-x-auto bg-black/30 px-4">
          <button
            onClick={() => setActiveTab('flow')}
            className={`px-4 py-3.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'flow'
                ? 'border-blue-500 text-blue-400 bg-white/5'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Agent Telemetry ({selectedAgentMeta.name})</span>
          </button>

          <button
            onClick={() => setActiveTab('labs')}
            className={`px-4 py-3.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'labs'
                ? 'border-blue-500 text-blue-400 bg-white/5'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <Flame className="w-4 h-4 text-amber-400" />
            <span>Laboratory Analysis ⭐ ({labResults.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('findings')}
            className={`px-4 py-3.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'findings'
                ? 'border-blue-500 text-blue-400 bg-white/5'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            <span>Clinical Findings ({workflowState?.clinical_findings.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('rag')}
            className={`px-4 py-3.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'rag'
                ? 'border-blue-500 text-blue-400 bg-white/5'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Medical RAG & Citations</span>
          </button>

          <button
            onClick={() => setActiveTab('report')}
            className={`px-4 py-3.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'report'
                ? 'border-blue-500 text-blue-400 bg-white/5'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            <span>Final Report</span>
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`px-4 py-3.5 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'audit'
                ? 'border-blue-500 text-blue-400 bg-white/5'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Audit Trail ({workflowState?.audit_trail.length || 0})</span>
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="p-6">
          {/* TAB 1: AGENT TELEMETRY / DETAIL */}
          {activeTab === 'flow' && (
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-black/40 border border-white/5">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center border border-blue-500/30">
                    <selectedAgentMeta.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-white">{selectedAgentMeta.name}</h4>
                    <p className="text-xs text-gray-400">{selectedAgentMeta.role}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4 text-xs">
                  <div>
                    <span className="text-gray-400">Execution Status:</span>
                    <span className="ml-1.5 font-bold text-white">
                      {getAgentStatus(selectedAgentMeta.id)}
                    </span>
                  </div>
                  {selectedAgentLog?.duration_ms && (
                    <div>
                      <span className="text-gray-400">Duration:</span>
                      <span className="ml-1.5 font-mono text-emerald-400 font-bold">
                        {Math.round(selectedAgentLog.duration_ms)} ms
                      </span>
                    </div>
                  )}
                  {selectedAgentLog?.confidence && (
                    <div>
                      <span className="text-gray-400">Confidence:</span>
                      <span className="ml-1.5 font-bold text-blue-400">
                        {Math.round(selectedAgentLog.confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Execution Summary Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-black/30 border border-white/5">
                  <h5 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                    Inputs / Context Summary
                  </h5>
                  {selectedAgentLog?.inputs_summary && Object.keys(selectedAgentLog.inputs_summary).length > 0 ? (
                    <pre className="text-[11px] font-mono text-gray-300 bg-black/50 p-3 rounded-lg overflow-x-auto border border-white/5">
                      {JSON.stringify(selectedAgentLog.inputs_summary, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-xs text-gray-500 italic">No direct input payload logged.</p>
                  )}
                </div>

                <div className="p-4 rounded-xl bg-black/30 border border-white/5">
                  <h5 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                    Outputs / Findings Summary
                  </h5>
                  {selectedAgentLog?.outputs_summary && Object.keys(selectedAgentLog.outputs_summary).length > 0 ? (
                    <pre className="text-[11px] font-mono text-emerald-300 bg-black/50 p-3 rounded-lg overflow-x-auto border border-white/5">
                      {JSON.stringify(selectedAgentLog.outputs_summary, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-xs text-gray-500 italic">No output summary recorded yet.</p>
                  )}
                </div>
              </div>

              {selectedAgentLog?.error_message && (
                <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-xs text-red-200">
                  <strong className="block mb-1 text-red-400">Execution Error:</strong>
                  {selectedAgentLog.error_message}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: LAB ANALYSIS VISUALIZATION (CORE FEATURE) */}
          {activeTab === 'labs' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                    <Flame className="w-4 h-4 text-amber-400" />
                    <span>Laboratory Biomarker Analysis</span>
                  </h4>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Extracted from medical document and evaluated against clinical physiological reference ranges
                  </p>
                </div>

                {criticalFindings.length > 0 && (
                  <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-xs font-bold border border-red-500/30 animate-pulse">
                    {criticalFindings.length} Panic Value(s) Detected
                  </span>
                )}
              </div>

              {labResults.length === 0 ? (
                <div className="p-8 text-center text-gray-500 text-xs bg-black/30 rounded-xl border border-white/5">
                  No laboratory test results recorded for this document type yet.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-white/10">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-black/50 text-gray-400 font-semibold border-b border-white/10 uppercase tracking-wider text-[11px]">
                      <tr>
                        <th className="px-4 py-3">Biomarker / Test Name</th>
                        <th className="px-4 py-3">Observed Value</th>
                        <th className="px-4 py-3">Unit</th>
                        <th className="px-4 py-3">Reference Range</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Classification</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-black/20">
                      {labResults.map((item: any, idx: number) => {
                        const status = (item.status || 'NORMAL').toUpperCase();
                        const isCritical = item.is_critical || status === 'CRITICAL';

                        return (
                          <tr
                            key={idx}
                            className={`hover:bg-white/5 transition-colors ${
                              isCritical ? 'bg-red-950/20' : ''
                            }`}
                          >
                            <td className="px-4 py-3 font-semibold text-white">
                              {item.name || item.test_name}
                            </td>
                            <td className="px-4 py-3 font-mono font-bold text-blue-300">
                              {item.value || item.observed_value}
                            </td>
                            <td className="px-4 py-3 text-gray-400">{item.unit || '—'}</td>
                            <td className="px-4 py-3 text-gray-400">
                              {item.reference_min !== undefined && item.reference_max !== undefined
                                ? `${item.reference_min} - ${item.reference_max}`
                                : item.reference_range || 'Standard'}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                                  isCritical
                                    ? 'bg-red-500 text-white animate-pulse'
                                    : status === 'LOW'
                                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                    : status === 'HIGH'
                                    ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                }`}
                              >
                                {status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-[11px] text-gray-300">
                              {isCritical ? (
                                <span className="text-red-400 font-bold">⚠️ Critical Panic Alert</span>
                              ) : status === 'NORMAL' ? (
                                <span className="text-emerald-400">Within Normal Limits</span>
                              ) : (
                                <span className="text-amber-400">Physiological Variance</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: CLINICAL FINDINGS */}
          {activeTab === 'findings' && (
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-white">Extracted Clinical Findings</h4>
              {workflowState?.clinical_findings.length === 0 ? (
                <p className="text-xs text-gray-500 italic">No clinical findings recorded.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {workflowState?.clinical_findings.map((f, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border ${
                        f.is_critical
                          ? 'bg-red-950/30 border-red-500/40 shadow-lg shadow-red-500/10'
                          : 'bg-black/30 border-white/5'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="px-2 py-0.5 rounded bg-white/5 text-[10px] font-semibold text-blue-300 uppercase">
                          {f.category}
                        </span>
                        <span
                          className={`text-[10px] font-bold uppercase ${
                            f.is_critical ? 'text-red-400 font-extrabold' : 'text-gray-400'
                          }`}
                        >
                          {f.status}
                        </span>
                      </div>
                      <h5 className="text-xs font-bold text-white">{f.title}</h5>
                      <p className="text-[11px] text-gray-300 mt-1">{f.description}</p>
                      {f.evidence && (
                        <p className="text-[10px] text-gray-500 mt-2 italic">
                          Evidence: &quot;{f.evidence}&quot;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MEDICAL RAG & CITATIONS */}
          {activeTab === 'rag' && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Search className="w-4 h-4 text-blue-400" />
                  <span>Medical Knowledge & Verified RAG Evidence</span>
                </h4>
                <p className="text-xs text-gray-400 mt-0.5">
                  Cross-referenced with verified clinical guidelines and internal healthcare datasets
                </p>
              </div>

              {workflowState?.retrieved_evidence.length === 0 ? (
                <div className="p-8 text-center text-xs text-gray-500 bg-black/30 rounded-xl border border-white/5">
                  No explicit medical citations retrieved for this workflow type.
                </div>
              ) : (
                <div className="space-y-3">
                  {workflowState?.retrieved_evidence.map((ev, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-black/30 border border-white/5">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-blue-400">
                          {ev.source || `Clinical Reference #${idx + 1}`}
                        </span>
                        {ev.confidence && (
                          <span className="text-[10px] text-emerald-400 font-semibold">
                            {Math.round(ev.confidence * 100)}% Match
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-300 mt-1">
                        {ev.text || ev.snippet || JSON.stringify(ev)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 5: FINAL REPORT */}
          {activeTab === 'report' && (
            <div className="space-y-6">
              {workflowState?.final_report ? (
                <div className="space-y-6">
                  {/* Executive Summary */}
                  <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-950/40 via-gray-900 to-black border border-blue-500/20 shadow-xl">
                    <h4 className="text-sm font-bold text-blue-300 uppercase tracking-wider mb-2">
                      Executive Summary
                    </h4>
                    <p className="text-xs text-gray-200 leading-relaxed">
                      {workflowState.final_report.executive_summary}
                    </p>
                  </div>

                  {/* Recommendations */}
                  {workflowState.final_report.recommendations.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-3">
                        Clinical Recommendations & Action Items
                      </h4>
                      <div className="space-y-2">
                        {workflowState.final_report.recommendations.map((rec, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-black/30 rounded-xl border border-white/5 text-xs text-gray-300 flex items-start space-x-2"
                          >
                            <ChevronRight className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Disclaimer Banner */}
                  <div className="p-4 rounded-xl bg-black/50 border border-white/10 text-[11px] text-gray-400 flex items-start space-x-3">
                    <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-white block mb-0.5">Clinical Disclaimer:</strong>
                      {workflowState.final_report.disclaimer}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-gray-500 bg-black/30 rounded-xl border border-white/5">
                  Final decision-support report is still synthesizing or pending workflow completion.
                </div>
              )}
            </div>
          )}

          {/* TAB 6: AUDIT TRAIL TIMELINE */}
          {activeTab === 'audit' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-3">
                Chronological Audit & Execution Trail
              </h4>
              {workflowState?.audit_trail.length === 0 ? (
                <p className="text-xs text-gray-500 italic">No audit events recorded.</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {workflowState?.audit_trail.map((entry, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-black/30 rounded-xl border border-white/5 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-blue-400 uppercase text-[10px]">
                            {entry.agent_name}
                          </span>
                          <span className="text-gray-300">{entry.action}</span>
                        </div>
                        {entry.tool_used && (
                          <span className="text-[10px] text-gray-500 font-mono">
                            Tool: {entry.tool_used}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-gray-500 font-mono whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
