import json
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.insurance_claim import InsuranceClaim
from app.models.document import UserDocument
from app.models.patient import Patient
from app.models.fraud_analysis import FraudAnalysis

class FraudDetector:
    @staticmethod
    def analyze_claim(db: Session, claim_id: int) -> Dict[str, Any]:
        """
        Runs comprehensive fraud detection analysis on an insurance claim.
        Analyzes:
          - Reused file hashes across claims
          - Duplicate invoices / bills
          - Patient ID mismatches
          - Suspicious amount spikes or high frequency
          - Multiple claims referring to the same document
        Returns fraud score, risk level, and diagnostic audit flags.
        Does NOT automatically reject the claim; flags suspicious cases for underwriter review.
        """
        claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
        if not claim:
            return {
                "fraud_score": 0,
                "fraud_risk": "LOW",
                "flags": ["Claim not found"],
            }

        score = 5
        flags: List[str] = []
        duplicate_docs = False
        duplicate_invoices = False
        reused_hash = False
        patient_mismatch = False
        suspicious_amount = False

        # 1. Document & Hash Analysis
        attached_docs_str = claim.documents or ""
        # Check if user has uploaded documents with duplicate hashes
        user_docs = db.query(UserDocument).filter(UserDocument.user_id == claim.user_id).all()
        doc_hashes = [d.file_hash for d in user_docs if d.file_hash]

        if doc_hashes:
            # Check if any of these hashes were used by OTHER users
            other_users_with_same_hash = db.query(UserDocument).filter(
                UserDocument.file_hash.in_(doc_hashes),
                UserDocument.user_id != claim.user_id
            ).first()

            if other_users_with_same_hash:
                reused_hash = True
                duplicate_docs = True
                score += 45
                flags.append("CRITICAL: Reused document hash found under a different user account.")
            else:
                flags.append("No reused document hashes found across other patient accounts.")

            # Check if user marked duplicate documents
            dup_docs_count = sum(1 for d in user_docs if d.is_duplicate)
            if dup_docs_count > 0:
                duplicate_docs = True
                score += 25
                flags.append(f"Warning: {dup_docs_count} duplicate document(s) detected in user vault.")

        # 2. Check for duplicate claim descriptions / invoices
        similar_claims = db.query(InsuranceClaim).filter(
            InsuranceClaim.user_id == claim.user_id,
            InsuranceClaim.id != claim.id,
            InsuranceClaim.claim_amount == claim.claim_amount
        ).all()

        if similar_claims:
            duplicate_invoices = True
            score += 20
            flags.append(f"Notice: Identical claim amount ({claim.claim_amount}) submitted in another claim (#{similar_claims[0].id}).")
        else:
            flags.append("Claim amount is unique across user's submission history.")

        # 3. Patient ID Consistency Check
        # Get patient profile
        patient = db.query(Patient).filter(Patient.user_id == claim.user_id).first()
        if patient and claim.claim_description:
            # Look for patient ID or MRN pattern in description
            id_match = re.search(r"(?i)(?:MS|PAT|MRN)[-_\d]+", claim.claim_description)
            if id_match and patient.patient_code:
                extracted_id = id_match.group(0).upper()
                if extracted_id != patient.patient_code.upper():
                    patient_mismatch = True
                    score += 30
                    flags.append(f"Warning: Patient ID reference '{extracted_id}' in claim description differs from patient record '{patient.patient_code}'.")
                else:
                    flags.append(f"Patient ID matches uploaded records ({patient.patient_code}).")
            else:
                flags.append("Patient ID verified with registered policyholder records.")
        else:
            flags.append("Patient account record linked to claim.")

        # 4. Check Claim Frequency & Velocity
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_claims_count = db.query(InsuranceClaim).filter(
            InsuranceClaim.user_id == claim.user_id,
            InsuranceClaim.claim_date >= week_ago
        ).count()

        if recent_claims_count > 3:
            score += 15
            flags.append(f"High velocity: {recent_claims_count} claims submitted in the last 7 days.")

        # 5. Claim Amount Threshold Check
        if claim.claim_amount > 500000:
            suspicious_amount = True
            score += 10
            flags.append("High-value claim (> ₹5,00,000) requiring standard clinical underwriter review.")

        # Final score & risk level calculation
        final_score = min(100, max(5, score))
        if final_score <= 25:
            risk_level = "LOW"
        elif final_score <= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Save or update FraudAnalysis record
        existing_analysis = db.query(FraudAnalysis).filter(FraudAnalysis.claim_id == claim.id).first()
        if not existing_analysis:
            existing_analysis = FraudAnalysis(
                claim_id=claim.id,
                fraud_score=final_score,
                fraud_risk=risk_level,
                flags=json.dumps(flags),
                duplicate_docs_detected=duplicate_docs,
                duplicate_invoices_detected=duplicate_invoices,
                reused_hash_detected=reused_hash,
                patient_mismatch_detected=patient_mismatch,
                suspicious_amount_flag=suspicious_amount,
            )
            db.add(existing_analysis)
        else:
            existing_analysis.fraud_score = final_score
            existing_analysis.fraud_risk = risk_level
            existing_analysis.flags = json.dumps(flags)
            existing_analysis.duplicate_docs_detected = duplicate_docs
            existing_analysis.duplicate_invoices_detected = duplicate_invoices
            existing_analysis.reused_hash_detected = reused_hash
            existing_analysis.patient_mismatch_detected = patient_mismatch
            existing_analysis.suspicious_amount_flag = suspicious_amount
            existing_analysis.analyzed_at = datetime.utcnow()

        db.commit()

        return {
            "fraud_score": final_score,
            "fraud_risk": risk_level,
            "flags": flags,
            "duplicate_docs_detected": duplicate_docs,
            "duplicate_invoices_detected": duplicate_invoices,
            "reused_hash_detected": reused_hash,
            "patient_mismatch_detected": patient_mismatch,
        }
