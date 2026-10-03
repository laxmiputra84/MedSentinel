'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/authContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AgentWorkflowVisualizer } from '@/components/AgentWorkflowVisualizer';
import { WorkflowHistoryItem, WorkflowType } from '@/lib/types';
import api from '@/lib/api';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileCheck,
  FileSearch,
  FileText,
  Flame,
  History,
  Layers,
  Play,
  PlusCircle,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UploadCloud,
  Zap,
} from 'lucide-react';

export default function AgentWorkflowPage() {
  return (
    <ProtectedRoute>
      <AgentWorkflowContent />
    </ProtectedRoute>
  );
}

function AgentWorkflowContent() {
  const { user } = useAuth();

  // Workflow Launcher State
  const [patientIdInput, setPatientIdInput] = useState<string>('');
  const [workflowType, setWorkflowType] = useState<WorkflowType>('AUTOMATIC' as WorkflowType);
  const [clinicalText, setClinicalText] = useState<string>('');
  const [sampleType, setSampleType] = useState<'custom' | 'cbc_panic' | 'normal_lipid' | 'prescription' | 'claim'>('custom');
  const [launching, setLaunching] = useState<boolean>(false);
  const [launchError, setLaunchError] = useState<string | null>(null);

  // Active Workflow Tracking
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);

  // Patient History State
  const [history, setHistory] = useState<WorkflowHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Sample medical test cases for quick evaluator testing
  const samplePresets = {
    cbc_panic: `PATIENT NAME: John Doe
AGE: 45 | GENDER: MALE | REPORT DATE: 2026-09-10
TEST PERFORMED: COMPLETE BLOOD COUNT (CBC)

HEMOGLOBIN: 6.2 g/dL (Reference: 13.5 - 17.5 g/dL) [CRITICAL LOW]
PLATELETS: 24,000 /uL (Reference: 150,000 - 450,000 /uL) [CRITICAL LOW]
WBC COUNT: 14,800 /uL (Reference: 4,500 - 11,000 /uL) [HIGH]
NEUTROPHILS: 82 % (Reference: 40 - 70 %) [HIGH]
RBC COUNT: 2.8 mil/uL (Reference: 4.5 - 5.9 mil/uL) [LOW]

CLINICAL IMPRESSION: Severe microcytic anemia with profound thrombocytopenia requiring immediate doctor evaluation.`,

    normal_lipid: `PATIENT NAME: Jane Smith
AGE: 38 | GENDER: FEMALE | REPORT DATE: 2026-09-10
TEST PERFORMED: COMPREHENSIVE METABOLIC & LIPID PANEL

TOTAL CHOLESTEROL: 185 mg/dL (Reference: < 200 mg/dL) [NORMAL]
TRIGLYCERIDES: 130 mg/dL (Reference: < 150 mg/dL) [NORMAL]
HDL CHOLESTEROL: 58 mg/dL (Reference: > 50 mg/dL) [NORMAL]
LDL CHOLESTEROL: 98 mg/dL (Reference: < 100 mg/dL) [NORMAL]
FASTING GLUCOSE: 92 mg/dL (Reference: 70 - 99 mg/dL) [NORMAL]

CLINICAL IMPRESSION: Normal cardiovascular lipid profile within expected healthy parameters.`,

    prescription: `Rx PRESCRIPTION
DOCTOR: Dr. Rajesh Kumar, MD | DATE: 2026-09-10
PATIENT: Rahul Sharma | AGE: 52

DIAGNOSIS: Essential Hypertension & Type 2 Diabetes Mellitus
MEDICATIONS:
1. Telmisartan 40mg - 1 tablet daily morning after breakfast
2. Metformin 500mg - 1 tablet twice daily with meals
3. Atorvastatin 10mg - 1 tablet at bedtime

ADVICE: Monitor BP daily, restrict sodium intake (<2g/day), HbA1c repeat after 3 months.`,

    claim: `INSURANCE REIMBURSEMENT CLAIM FORM
POLICY NUMBER: POL-2026-88421 | CLAIM ID: CLM-99214
HOSPITAL: Fortis Healthcare Bengaluru
ADMISSION DATE: 2026-09-02 | DISCHARGE DATE: 2026-09-05
PROCEDURE: Laparoscopic Cholecystectomy
TOTAL CLAIM AMOUNT: ₹ 1,45,000
SUBMITTED INVOICES: Hospital Bill #INV-9921 (₹ 1,15,000), Pharmacy #PH-4421 (₹ 30,000)`
  };

  const handlePresetChange = (type: 'custom' | 'cbc_panic' | 'normal_lipid' | 'prescription' | 'claim') => {
    setSampleType(type);
    if (type === 'cbc_panic') {
      setClinicalText(samplePresets.cbc_panic);
      setWorkflowType('LAB_REPORT' as WorkflowType);
    } else if (type === 'normal_lipid') {
      setClinicalText(samplePresets.normal_lipid);
      setWorkflowType('LAB_REPORT' as WorkflowType);
    } else if (type === 'prescription') {
      setClinicalText(samplePresets.prescription);
      setWorkflowType('PRESCRIPTION' as WorkflowType);
    } else if (type === 'claim') {
      setClinicalText(samplePresets.claim);
      setWorkflowType('INSURANCE_CLAIM' as WorkflowType);
    } else {
      setClinicalText('');
      setWorkflowType('AUTOMATIC' as WorkflowType);
    }
  };

  // Fetch workflow history for patient
  const fetchHistory = async () => {
    const resolvedPid = patientIdInput ? parseInt(patientIdInput, 10) : user?.id;
    if (!resolvedPid) return;
    setLoadingHistory(true);
    try {
      const res = await api.get<WorkflowHistoryItem[]>(`/agent-workflow/patient/${resolvedPid}/history`);
      setHistory(res.data);
    } catch (err) {
      console.log('History fetch note:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [user]);

  // Trigger POST /api/agent-workflow/run
  const handleLaunchWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    setLaunching(true);
    setLaunchError(null);

    const payload: any = {
      workflow_type: workflowType,
      extracted_text: clinicalText.trim() || undefined,
      filename: `clinical_note_${Date.now()}.txt`,
    };

    if (patientIdInput.trim()) {
      payload.patient_id = parseInt(patientIdInput.trim(), 10);
    }

    try {
      const res = await api.post<{ workflow_id: string; status: string; message: string }>(
        '/agent-workflow/run',
        payload
      );
      setActiveWorkflowId(res.data.workflow_id);
      fetchHistory();
    } catch (err: any) {
      setLaunchError(err.response?.data?.detail || 'Failed to start agent workflow');
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title & Hero */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white font-['Manrope'] tracking-tight">
                Agentic Healthcare Intelligence Dashboard
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Real-Time Orchestrated AI Pipeline with 11 Specialized Healthcare Agents & Human-in-the-Loop Review
              </p>
            </div>
          </div>
        </div>

        {activeWorkflowId && (
          <button
            onClick={() => setActiveWorkflowId(null)}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all self-start"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Launch New Workflow</span>
          </button>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 1. WORKFLOW LAUNCHER & CONFIGURATION PANEL */}
      {/* ========================================================================= */}
      {!activeWorkflowId ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Launch Form */}
          <div className="lg:col-span-2 bg-gray-900/80 border border-white/10 rounded-2xl p-6 backdrop-blur-xl shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center space-x-2">
                <Play className="w-5 h-5 text-blue-400" />
                <h2 className="text-base font-bold text-white">Launch Agentic Workflow</h2>
              </div>
              <span className="text-xs text-blue-400 font-semibold bg-blue-500/10 px-2.5 py-1 rounded-full border border-blue-500/20">
                Dynamic DAG Planner
              </span>
            </div>

            {launchError && (
              <div className="p-4 bg-red-950/50 border border-red-500/40 rounded-xl text-xs text-red-200">
                {launchError}
              </div>
            )}

            <form onSubmit={handleLaunchWorkflow} className="space-y-5">
              {/* Preset Sample Selector for Evaluator Convenience */}
              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                  Test Scenarios & Presets:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    type="button"
                    onClick={() => handlePresetChange('cbc_panic')}
                    className={`p-2.5 rounded-xl border text-left text-xs transition-all ${
                      sampleType === 'cbc_panic'
                        ? 'border-red-500 bg-red-950/40 text-red-200 font-bold'
                        : 'border-white/10 bg-black/30 text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="block text-[11px] font-extrabold text-red-400">⚠️ CBC Panic Alert</span>
                    <span className="text-[10px] text-gray-400">Severe Anemia + Low Plt</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handlePresetChange('normal_lipid')}
                    className={`p-2.5 rounded-xl border text-left text-xs transition-all ${
                      sampleType === 'normal_lipid'
                        ? 'border-emerald-500 bg-emerald-950/40 text-emerald-200 font-bold'
                        : 'border-white/10 bg-black/30 text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="block text-[11px] font-extrabold text-emerald-400">✓ Lipid Profile</span>
                    <span className="text-[10px] text-gray-400">Normal range lab test</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handlePresetChange('prescription')}
                    className={`p-2.5 rounded-xl border text-left text-xs transition-all ${
                      sampleType === 'prescription'
                        ? 'border-blue-500 bg-blue-950/40 text-blue-200 font-bold'
                        : 'border-white/10 bg-black/30 text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="block text-[11px] font-extrabold text-blue-400">💊 Prescription</span>
                    <span className="text-[10px] text-gray-400">Hypertension & Diabetes</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handlePresetChange('claim')}
                    className={`p-2.5 rounded-xl border text-left text-xs transition-all ${
                      sampleType === 'claim'
                        ? 'border-purple-500 bg-purple-950/40 text-purple-200 font-bold'
                        : 'border-white/10 bg-black/30 text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="block text-[11px] font-extrabold text-purple-400">📋 Claim Audit</span>
                    <span className="text-[10px] text-gray-400">Reimbursement audit</span>
                  </button>
                </div>
              </div>

              {/* Patient ID & Workflow Type Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">
                    Patient ID (Optional / Auto-resolved)
                  </label>
                  <input
                    type="number"
                    value={patientIdInput}
                    onChange={(e) => setPatientIdInput(e.target.value)}
                    placeholder="e.g. 1"
                    className="w-full bg-black/40 border border-white/15 rounded-xl px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">
                    Workflow Routing Mode
                  </label>
                  <select
                    value={workflowType}
                    onChange={(e) => setWorkflowType(e.target.value as WorkflowType)}
                    className="w-full bg-black/40 border border-white/15 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="AUTOMATIC">Automatic Orchestrator Discovery (Recommended)</option>
                    <option value="LAB_REPORT">Laboratory Analysis Workflow ⭐</option>
                    <option value="PRESCRIPTION">Prescription & Medication Workflow</option>
                    <option value="INSURANCE_CLAIM">Insurance Claim & Fraud Audit</option>
                    <option value="CLINICAL_SUMMARY">Full Longitudinal Clinical Summary</option>
                  </select>
                </div>
              </div>

              {/* Clinical Document / Text Content */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">
                  Clinical Record / Laboratory Report Text Content:
                </label>
                <textarea
                  rows={8}
                  value={clinicalText}
                  onChange={(e) => {
                    setClinicalText(e.target.value);
                    setSampleType('custom');
                  }}
                  placeholder="Paste OCR text, laboratory findings, clinical discharge summary, or doctor prescription here..."
                  className="w-full bg-black/40 border border-white/15 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono placeholder-gray-500 focus:outline-none focus:border-blue-500 leading-relaxed"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={launching}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl text-sm font-bold flex items-center justify-center space-x-2 transition-all shadow-xl shadow-blue-500/25 disabled:opacity-50"
              >
                {launching ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Engaging Orchestrator...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>Run Agentic Healthcare Workflow</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Architecture Overview Card */}
          <div className="space-y-6">
            <div className="bg-gray-900/80 border border-white/10 rounded-2xl p-6 backdrop-blur-xl shadow-2xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Layers className="w-4 h-4 text-purple-400" />
                <span>Agentic Execution Pipeline</span>
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                MedSentinel dynamically constructs an asynchronous Directed Acyclic Graph (DAG) across 11 specialized healthcare agents:
              </p>

              <div className="space-y-2.5 text-xs">
                <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center space-x-3">
                  <div className="w-7 h-7 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-[11px]">
                    1
                  </div>
                  <div>
                    <h5 className="font-bold text-white text-[11px]">Multimodal Intake & OCR</h5>
                    <p className="text-[10px] text-gray-400">Context verification, document classification, layout parsing</p>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center space-x-3">
                  <div className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-[11px]">
                    2
                  </div>
                  <div>
                    <h5 className="font-bold text-white text-[11px]">Laboratory Analysis ⭐</h5>
                    <p className="text-[10px] text-gray-400">Biomarkers, panic range checks, physiological bounds</p>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center space-x-3">
                  <div className="w-7 h-7 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-[11px]">
                    3
                  </div>
                  <div>
                    <h5 className="font-bold text-white text-[11px]">Longitudinal Trends & Risk</h5>
                    <p className="text-[10px] text-gray-400">Delta tracking, disease risk score, claim integrity</p>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center space-x-3">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-[11px]">
                    4
                  </div>
                  <div>
                    <h5 className="font-bold text-white text-[11px]">Medical RAG & Verification</h5>
                    <p className="text-[10px] text-gray-400">Verified citations, SHA-256 integrity, doctor escalation</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Vault Link */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-950/40 to-black border border-blue-500/20 text-xs text-gray-300 flex items-center justify-between">
              <div>
                <strong className="block text-white mb-0.5">Need vaulted documents?</strong>
                <span className="text-gray-400 text-[11px]">Run workflows directly from your Medical Vault</span>
              </div>
              <a
                href="/medical-vault"
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold whitespace-nowrap"
              >
                Open Vault
              </a>
            </div>
          </div>
        </div>
      ) : (
        /* ========================================================================= */
        /* 2. ACTIVE LIVE WORKFLOW VISUALIZER */
        /* ========================================================================= */
        <div>
          <AgentWorkflowVisualizer
            workflowId={activeWorkflowId}
            onWorkflowComplete={() => fetchHistory()}
          />
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. PATIENT WORKFLOW HISTORY */}
      {/* ========================================================================= */}
      <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-6 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">Agent Workflow History</h3>
          </div>
          <button
            onClick={fetchHistory}
            className="text-xs text-gray-400 hover:text-white flex items-center space-x-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {history.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-500 bg-black/20 rounded-xl border border-white/5">
            No previous workflows found for this patient session. Launch a workflow above to see real-time execution.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-white/10">
            <table className="w-full text-left text-xs">
              <thead className="bg-black/50 text-gray-400 font-semibold border-b border-white/10 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-4 py-3">Workflow ID</th>
                  <th className="px-4 py-3">Workflow Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Escalation</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 bg-black/20">
                {history.map((item) => (
                  <tr key={item.workflow_id} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-blue-300">
                      {item.workflow_id}
                    </td>
                    <td className="px-4 py-3 text-gray-300 font-semibold">
                      {item.workflow_type}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                          item.status === 'COMPLETED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : item.status === 'DOCTOR_REVIEW_REQUIRED'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : item.status === 'FAILED'
                            ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                            : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {item.escalation_required ? (
                        <span className="text-amber-400 font-semibold flex items-center space-x-1">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Escalated</span>
                        </span>
                      ) : (
                        <span className="text-gray-500 font-mono">Standard</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setActiveWorkflowId(item.workflow_id)}
                        className="px-3 py-1 bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 rounded-lg text-xs font-semibold transition-all"
                      >
                        Inspect State
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
