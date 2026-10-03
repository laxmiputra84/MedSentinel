export type UserRole = 'USER' | 'HOSPITAL_ADMIN' | 'INSURANCE_ADMIN' | 'SUPER_ADMIN';

export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  role?: UserRole;
  hospital_id?: number;
  insurance_id?: number;
  blood_group?: string;
  allergies?: string;
  emergency_contact?: string;
  schemes?: string;
  created_at?: string;
}

export interface SearchIntentMeta {
  search_query?: string | null;
  search_type: 'keyword' | 'location' | 'specialty' | 'specialty_location' | 'nearby';
  is_nearby_search: boolean;
  detected_location?: string | null;
  detected_specialty?: string | null;
  detected_keyword?: string | null;
  has_coordinates?: boolean;
}

export interface Hospital {
  id: number;
  name: string;
  location?: string;
  specialization?: string;
  rating: number;
  distance: number;
  cost_range?: string;
  schemes?: string;
  insurance_accepted?: string;
  is_available?: boolean;
  image_url?: string;
  facilities?: string;
  description?: string;
  phone?: string;
  email?: string;
  latitude?: number;
  longitude?: number;
  distance_km?: number | null;
}

export interface Scheme {
  id: number;
  name: string;
  description?: string;
  coverage?: string;
  eligibility?: string;
  benefits?: string;
  category?: string;
  max_income?: string;
  type?: string;
}

export interface Insurance {
  id: number;
  name: string;
  provider: string;
  coverage_amount: number;
  premium_monthly: number;
  premium_annual: number;
  cashless_network: number;
  claim_settlement_days: number;
  rating: number;
  features?: string;
  inclusions?: string;
  exclusions?: string;
  coverage_type?: string;
  waiting_period_days: number;
  eligibility_age_min: number;
  eligibility_age_max: number;
}

export interface UserInsurance {
  id: number;
  user_id: number;
  insurance_id: number;
  policy_number: string;
  start_date?: string;
  end_date?: string;
  status: string;
  sum_insured: number;
  dependents?: string;
  insurance?: Insurance;
}

export interface ClaimStatusHistory {
  id: number;
  claim_id: number;
  previous_status?: string;
  new_status: string;
  updated_by_id?: number;
  comment?: string;
  created_at?: string;
}

export interface FraudAnalysisData {
  fraud_score: number;
  fraud_risk: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  flags: string[];
  duplicate_docs_detected?: boolean;
  duplicate_invoices_detected?: boolean;
  reused_hash_detected?: boolean;
  patient_mismatch_detected?: boolean;
}

export interface InsuranceClaim {
  id: number;
  user_id: number;
  insurance_id?: number;
  hospital_id?: number;
  claim_amount: number;
  claim_date?: string;
  claim_status: 'SUBMITTED' | 'UNDER_REVIEW' | 'DOCUMENTS_REQUIRED' | 'APPROVED' | 'REJECTED' | 'COMPLETED' | string;
  claim_description?: string;
  documents?: string;
  insurance?: Insurance;
  hospital?: Hospital;
  status_history?: ClaimStatusHistory[];
  fraud_analysis?: FraudAnalysisData;
}

export interface Appointment {
  id: number;
  user_id?: number;
  hospital_id?: number;
  name: string;
  phone: string;
  email: string;
  preferred_date: string;
  preferred_time: string;
  department: string;
  reason?: string;
  status: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | string;
  notes?: string;
  cancelled_at?: string;
  created_at?: string;
}

export interface Recommendation {
  id: number;
  user_id: number;
  patient_id?: number;
  recommendation_type: 'MISSING_RECORD' | 'RELATED_RECORD' | 'TREND_REVIEW' | 'CLAIM_SUPPORT' | 'DATA_QUALITY' | 'DOCUMENT_FOLLOW_UP' | string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  title: string;
  description?: string;
  reason?: string;
  confidence: number;
  sources: string[];
  status: 'ACTIVE' | 'VIEWED' | 'DISMISSED' | 'COMPLETED' | string;
  related_document_id?: number;
  related_claim_id?: number;
  created_at: string;
  updated_at: string;
}

export interface LabTestItem {
  name: string;
  value: number;
  unit: string;
  reference_min?: number;
  reference_max?: number;
  status: 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL' | 'UNKNOWN' | string;
  is_critical?: boolean;
}

export interface LabExtractionResponse {
  patient_name: string;
  patient_id: string;
  report_date: string;
  report_type: string;
  tests: LabTestItem[];
}

export interface HealthDashboardData {
  total_documents: number;
  latest_lab_reports_count: number;
  normal_results_count: number;
  abnormal_results_count: number;
  critical_results_count: number;
  health_score: number;
  risk_score: number;
  risk_level: string;
  critical_alerts: LabTestItem[];
  ai_summary?: string;
  trends: Record<string, Array<{ date: string; value: number; status?: string; unit?: string; reference_min?: number; reference_max?: number }>>;
}

export interface UserDocument {
  id: number;
  user_id: number;
  patient_id?: number;
  document_code?: string;
  file_hash?: string;
  doc_type: string;
  filename: string;
  original_name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  upload_date?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | string;
  verification_status?: 'PENDING' | 'VERIFIED' | 'FLAGGED' | 'REJECTED' | string;
  is_duplicate?: boolean;
  duplicate_of_id?: number;
  ai_classification?: string;
  ai_confidence?: number;
  ocr_extracted_text?: string;
  verified_by_id?: number;
  verified_at?: string;
  rejection_reason?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at?: string;
}

export interface SchemeRecommendationItem {
  scheme_id: number;
  scheme_name: string;
  coverage?: string;
  reason: string;
  match_score: number;
}

export interface IneligibleSchemeItem {
  scheme_id: number;
  scheme_name: string;
  reason: string;
}

export interface EligibilityRecommendationResponse {
  eligible: SchemeRecommendationItem[];
  not_eligible: IneligibleSchemeItem[];
  evaluation_engine: string;
}

export interface SchemeEligibilityResult {
  scheme: string;
  probability: number;
}

export interface PlatformAnalytics {
  total_users: number;
  total_hospitals: number;
  total_appointments: number;
  total_insurance_policies: number;
  total_claims: number;
  approved_claims: number;
  rejected_claims: number;
  under_review_claims: number;
  total_claims_amount: number;
  recent_users_count: number;
}

// ==========================================
// Agentic Healthcare Architecture Types
// ==========================================

export type AgentStatus = 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
export type WorkflowStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'ESCALATED' | 'DOCTOR_REVIEW_REQUIRED';
export type WorkflowType = 'LAB_REPORT' | 'PRESCRIPTION' | 'INSURANCE_CLAIM' | 'CLINICAL_SUMMARY' | 'GENERAL_INQUIRY' | 'AUTOMATIC';
export type EscalationLevel = 'NONE' | 'MILD' | 'MODERATE' | 'HIGH' | 'DOCTOR_REVIEW_REQUIRED';

export interface AgentExecutionLog {
  agent_name: string;
  status: AgentStatus;
  started_at: string;
  completed_at?: string | null;
  duration_ms?: number | null;
  tool_called?: string | null;
  inputs_summary?: Record<string, any>;
  outputs_summary?: Record<string, any>;
  error_message?: string | null;
  confidence?: number | null;
}

export interface ClinicalFinding {
  category: string;
  title: string;
  description: string;
  parameter_name?: string | null;
  observed_value?: number | null;
  reference_range?: string | null;
  unit?: string | null;
  status: 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL' | 'UNKNOWN' | string;
  is_critical: boolean;
  evidence?: string | null;
  confidence: number;
}

export interface LabFinding {
  test_name: string;
  observed_value: number;
  unit: string;
  reference_min?: number | null;
  reference_max?: number | null;
  status: 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL' | string;
  is_critical: boolean;
  historical_trend?: 'STABLE' | 'INCREASING' | 'DECREASING' | 'UNKNOWN' | string | null;
  delta_percent?: number | null;
  evidence?: string | null;
}

export interface VerificationResult {
  is_valid: boolean;
  file_hash?: string | null;
  stored_hash?: string | null;
  document_code?: string | null;
  tamper_free: boolean;
  is_duplicate: boolean;
  duplicate_of_id?: number | null;
  contradiction_flags: string[];
  confidence: number;
  verification_notes?: string | null;
}

export interface FinalReport {
  workflow_id: string;
  patient_id?: number | null;
  patient_name?: string | null;
  document_id?: number | null;
  document_type: string;
  generated_at: string;
  executive_summary: string;
  findings: ClinicalFinding[];
  lab_summary?: Record<string, any> | null;
  risk_assessment?: Record<string, any> | null;
  recommendations: string[];
  citations: Array<Record<string, any>>;
  disclaimer: string;
  requires_human_review: boolean;
  escalation_reason?: string | null;
  escalation_level?: EscalationLevel;
  doctor_review_notes?: string | null;
  reviewer_id?: number | null;
  review_status?: string | null;
}

export interface AuditEntry {
  timestamp: string;
  agent_name: string;
  action: string;
  tool_used?: string | null;
  status: string;
  confidence?: number | null;
  error?: string | null;
  details?: Record<string, any>;
}

export interface WorkflowState {
  workflow_id: string;
  patient_id?: number | null;
  patient_name?: string | null;
  user_id?: number | null;
  user_role: string;
  document_id?: number | null;
  document_code?: string | null;
  hospital_id?: number | null;
  file_path?: string | null;
  filename?: string | null;
  workflow_type: WorkflowType;
  status: WorkflowStatus;
  current_agent?: string | null;
  completed_agents: string[];
  skipped_agents: string[];
  failed_agents: string[];
  document_type?: string | null;
  document_confidence?: number | null;
  extracted_text?: string | null;
  extracted_entities: Record<string, any>;
  document_metadata: Record<string, any>;
  validation_status: Record<string, any>;
  validation_errors: string[];
  validation_warnings: string[];
  lab_results: Array<Record<string, any>>;
  historical_results: Array<Record<string, any>>;
  longitudinal_trends: Record<string, any>;
  clinical_findings: ClinicalFinding[];
  retrieved_evidence: Array<Record<string, any>>;
  rag_context?: string | null;
  risk_result?: Record<string, any> | null;
  fraud_result?: Record<string, any> | null;
  verification_result?: VerificationResult | null;
  escalation_required: boolean;
  escalation_reason?: string | null;
  escalation_level: EscalationLevel;
  final_report?: FinalReport | null;
  execution_logs: AgentExecutionLog[];
  audit_trail: AuditEntry[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowHistoryItem {
  workflow_id: string;
  patient_id?: number | null;
  patient_name?: string | null;
  document_id?: number | null;
  document_type?: string | null;
  workflow_type: string;
  status: string;
  escalation_required: boolean;
  risk_level?: string | null;
  created_at: string;
  updated_at: string;
  has_final_report: boolean;
}

