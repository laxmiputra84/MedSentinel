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
  cancellation_reason?: string;
  created_at?: string;
}

export interface UserDocument {
  id: number;
  user_id: number;
  doc_type: string;
  filename: string;
  original_name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  upload_date?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | string;
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
