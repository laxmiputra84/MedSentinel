import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User,
    Hospital,
    Scheme,
    Insurance,
    UserInsurance,
    InsuranceClaim,
    ClaimStatusHistory,
    Appointment,
    Notification,
    Patient,
    UserDocument,
    LabResult,
    HealthScore,
    FraudAnalysis,
    Recommendation,
)

def seed_database():
    print("Connecting to MySQL Database...")
    try:
        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connected to MySQL successfully.")
    except Exception as e:
        print(f"Could not connect to MySQL: {e}")
        print("Please check your DATABASE_URL in .env (e.g. mysql+pymysql://root:password@localhost:3306/medsentinel)")
        return

    print("Ensuring MySQL InnoDB schema is up to date...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # 1. Seed RBAC Users
        users_data = [
            {
                "name": "Alex Demo Patient",
                "email": "demo@medsentinel.com",
                "password": "password123",
                "role": "USER",
                "phone": "+91 98765 43210",
                "blood_group": "O+",
                "allergies": "Penicillin, Peanuts",
                "emergency_contact": "+91 91234 56789",
                "schemes": "Ayushman Bharat, MJPJAY"
            },
            {
                "name": "Dr. Sarah Hospital Director",
                "email": "hospitaladmin@medsentinel.com",
                "password": "hospital123",
                "role": "HOSPITAL_ADMIN",
                "phone": "+91 98765 11111",
                "hospital_id": 1
            },
            {
                "name": "Marcus Claim Underwriter",
                "email": "insuranceadmin@medsentinel.com",
                "password": "insurance123",
                "role": "INSURANCE_ADMIN",
                "phone": "+91 98765 22222",
                "insurance_id": 1
            },
            {
                "name": "Chief Platform Admin",
                "email": "superadmin@medsentinel.com",
                "password": "admin123",
                "role": "SUPER_ADMIN",
                "phone": "+91 98765 99999"
            }
        ]

        for u_data in users_data:
            existing_user = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing_user:
                new_u = User(
                    name=u_data["name"],
                    email=u_data["email"],
                    hashed_password=get_password_hash(u_data["password"]),
                    role=u_data["role"],
                    phone=u_data.get("phone"),
                    blood_group=u_data.get("blood_group"),
                    allergies=u_data.get("allergies"),
                    emergency_contact=u_data.get("emergency_contact"),
                    schemes=u_data.get("schemes"),
                    hospital_id=u_data.get("hospital_id"),
                    insurance_id=u_data.get("insurance_id")
                )
                db.add(new_u)
                print(f"Created user: {u_data['email']} ({u_data['role']})")
            else:
                existing_user.hashed_password = get_password_hash(u_data["password"])
                existing_user.role = u_data["role"]
                if u_data.get("hospital_id"):
                    existing_user.hospital_id = u_data["hospital_id"]
                if u_data.get("insurance_id"):
                    existing_user.insurance_id = u_data["insurance_id"]
                print(f"Updated password & credentials for: {u_data['email']}")
        db.commit()

        # 2. Seed Hospitals
        hospitals_data = [
            {
                "name": "City General Hospital",
                "location": "Bengaluru Central, Karnataka",
                "specialization": "Multispeciality, Emergency Care, Cardiology",
                "rating": 4.8,
                "distance": 2.4,
                "cost_range": "₹45,000 - ₹85,000",
                "schemes": "Ayushman Bharat, MJPJAY, State Health Card",
                "insurance_accepted": "Care Supreme, Star Health, Optima Secure",
                "is_available": True,
                "facilities": "24/7 Trauma Care, 32-Bed ICU, Cath Lab, MRI & CT Diagnostics, Blood Bank",
                "description": "Premier multispeciality center offering tertiary healthcare and high-volume emergency trauma response.",
                "phone": "+91-80-2222-1111",
                "email": "contact@citygeneral.org"
            },
            {
                "name": "Apollo Multispeciality Hospital",
                "location": "Bannerghatta Road, Bengaluru",
                "specialization": "Cardiology, Oncology, Organ Transplants",
                "rating": 4.9,
                "distance": 4.1,
                "cost_range": "₹90,000 - ₹1,80,000",
                "schemes": "Ayushman Bharat, CGHS, ESIC",
                "insurance_accepted": "Care Supreme, Optima Secure, Star Health",
                "is_available": True,
                "facilities": "Robotic Surgery Suites, Comprehensive Cancer Center, 64-Slice Cardiac CT, Advanced Neonatal ICU",
                "description": "Internationally accredited hospital with world-renowned cardiology and organ transplant surgeons.",
                "phone": "+91-80-2630-4050",
                "email": "info@apollomulti.in"
            },
            {
                "name": "St. Jude Medical Research Institute",
                "location": "Indiranagar, Bengaluru",
                "specialization": "Neurology, Neurosurgery, Orthopedics",
                "rating": 4.7,
                "distance": 5.8,
                "cost_range": "₹60,000 - ₹1,10,000",
                "schemes": "Ayushman Bharat, MJPJAY",
                "insurance_accepted": "Optima Secure, Star Health",
                "is_available": True,
                "facilities": "Neuro Navigation System, High-Field 3T MRI, Joint Replacement Center, Dedicated Stroke Unit",
                "description": "Leading center of excellence in complex neurosurgical procedures and joint replacement surgeries.",
                "phone": "+91-80-4100-7890",
                "email": "care@stjudemedical.org"
            },
            {
                "name": "Fortis HealthCare Super Speciality",
                "location": "Cunningham Road, Bengaluru",
                "specialization": "Cardiology, Nephrology, Urology",
                "rating": 4.6,
                "distance": 3.2,
                "cost_range": "₹80,000 - ₹1,50,000",
                "schemes": "Ayushman Bharat, CGHS",
                "insurance_accepted": "Care Supreme, Optima Secure",
                "is_available": True,
                "facilities": "Hemodialysis Wing, Renal Transplant Unit, Digital Cath Lab, 24/7 Pharmacy",
                "description": "Advanced renal care and cardiovascular treatment facility with rapid diagnosis support.",
                "phone": "+91-80-4011-1222",
                "email": "support@fortisblr.com"
            },
            {
                "name": "Manipal Comprehensive Hospital",
                "location": "Old Airport Road, Bengaluru",
                "specialization": "Pediatrics, Oncology, Gastrointestinal Surgery",
                "rating": 4.8,
                "distance": 6.5,
                "cost_range": "₹70,000 - ₹1,35,000",
                "schemes": "Ayushman Bharat, MJPJAY, ESIC",
                "insurance_accepted": "Care Supreme, Star Health, Optima Secure",
                "is_available": True,
                "facilities": "Pediatric ICU, Bone Marrow Transplant Unit, Endoscopy Suites, Genetic Testing Lab",
                "description": "Distinguished hospital group delivering patient-centric cancer care and pediatric super-specialties.",
                "phone": "+91-80-2502-4444",
                "email": "info@manipalhospitals.com"
            }
        ]

        for h in hospitals_data:
            existing = db.query(Hospital).filter(Hospital.name == h["name"]).first()
            if not existing:
                db.add(Hospital(**h))
                print(f"Created hospital: {h['name']}")
        db.commit()

        # 3. Seed Government Schemes
        schemes_data = [
            {
                "name": "Ayushman Bharat (PM-JAY)",
                "coverage": "₹5,00,000 / family / year",
                "description": "World's largest government-funded health assurance scheme providing secondary and tertiary care hospitalization across empanelled public and private hospitals.",
                "eligibility": "Low-income households, BPL card holders, SECC identified families with no earning adult member.",
                "benefits": "100% cashless hospitalization, covers 3 days pre-hospitalization and 15 days post-hospitalization medications.",
                "category": "National Government",
                "max_income": "₹2,50,000 / year"
            },
            {
                "name": "Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)",
                "coverage": "₹1,50,000 - ₹5,00,000 / family",
                "description": "Flagship health scheme of the Government of Maharashtra offering comprehensive financial cover for serious illnesses requiring surgery and hospitalization.",
                "eligibility": "Families holding Yellow or Orange Ration Cards, Antyodaya Anna Yojana (AAY) beneficiaries.",
                "benefits": "996 recognized surgical procedures, renal transplants, cardiology surgeries, oncology cycles.",
                "category": "State Government",
                "max_income": "₹1,00,000 / year"
            },
            {
                "name": "Employees' State Insurance (ESIC)",
                "coverage": "Full Comprehensive Medical Benefit",
                "description": "Self-financing social security and health insurance scheme for Indian workers earning monthly wages up to ₹21,000.",
                "eligibility": "Organized workforce employees with ESIC registration and monthly statutory contributions.",
                "benefits": "Unlimited medical coverage for worker and dependents from day one of insurable employment, plus sickness cash benefits.",
                "category": "Social Security",
                "max_income": "₹2,52,000 / year"
            },
            {
                "name": "Central Government Health Scheme (CGHS)",
                "coverage": "Comprehensive Medical Care & Hospitalization",
                "description": "Healthcare facility for Central Government employees, pensioners, and their dependents across allopathic and AYUSH systems.",
                "eligibility": "Central government employees, retired defense personnel, members of parliament.",
                "benefits": "Dispensary services, cashless indoor treatment at CGHS empanelled hospitals, cancer & cardiac care.",
                "category": "Central Government",
                "max_income": "N/A"
            }
        ]

        for s in schemes_data:
            existing = db.query(Scheme).filter(Scheme.name == s["name"]).first()
            if not existing:
                db.add(Scheme(**s))
                print(f"Created scheme: {s['name']}")
        db.commit()

        # 4. Seed Insurances
        insurances_data = [
            {
                "name": "Care Supreme Comprehensive Plan",
                "provider": "Care Health Insurance",
                "coverage_amount": 1000000.0,
                "premium_monthly": 850.0,
                "premium_annual": 9800.0,
                "cashless_network": 21000,
                "claim_settlement_days": 2,
                "rating": 4.9,
                "features": "Unlimited Automatic Recharge, 500% No Claim Bonus, OPD Consultations, AYUSH Cover, No Room Rent Capping",
                "inclusions": "In-patient hospitalization, Day care treatments, Pre & Post hospitalization (60/180 days), Ambulance charges",
                "exclusions": "Cosmetic surgeries, Self-inflicted injuries, Drug abuse treatments",
                "coverage_type": "Comprehensive",
                "waiting_period_days": 30,
                "eligibility_age_min": 18,
                "eligibility_age_max": 75
            },
            {
                "name": "Optima Secure Smart Health",
                "provider": "HDFC ERGO",
                "coverage_amount": 1500000.0,
                "premium_monthly": 1250.0,
                "premium_annual": 14200.0,
                "cashless_network": 14000,
                "claim_settlement_days": 1,
                "rating": 4.8,
                "features": "2X Coverage from Day 1, Plus Benefit (100% bonus in 2 yrs), Global Emergency Cover, Zero Deductibles",
                "inclusions": "All day-care surgeries, Robotic surgery, Organ donor expenses, Home healthcare",
                "exclusions": "Unproven treatments, Rest cure and rehabilitation admissions",
                "coverage_type": "Family Floater",
                "waiting_period_days": 30,
                "eligibility_age_min": 18,
                "eligibility_age_max": 65
            },
            {
                "name": "Star Comprehensive Health Plan",
                "provider": "Star Health Insurance",
                "coverage_amount": 750000.0,
                "premium_monthly": 680.0,
                "premium_annual": 7800.0,
                "cashless_network": 13000,
                "claim_settlement_days": 3,
                "rating": 4.6,
                "features": "Maternity cover for up to 2 deliveries, New-born baby cover, Free annual health check-ups, Air ambulance cover",
                "inclusions": "Hospital room rent up to single private room, ICU charges, Surgeon & anesthetist fees",
                "exclusions": "Dental cosmetic procedures, Weight control treatments",
                "coverage_type": "Individual",
                "waiting_period_days": 30,
                "eligibility_age_min": 18,
                "eligibility_age_max": 65
            }
        ]

        for ins in insurances_data:
            existing = db.query(Insurance).filter(Insurance.name == ins["name"]).first()
            if not existing:
                db.add(Insurance(**ins))
                print(f"Created insurance: {ins['name']}")
        db.commit()

        # 5. Seed sample claim and status history for demo user
        demo_user = db.query(User).filter(User.email == "demo@medsentinel.com").first()
        ins_plan = db.query(Insurance).first()
        hosp = db.query(Hospital).first()

        if demo_user and ins_plan and hosp:
            # Seed active policy
            existing_pol = db.query(UserInsurance).filter(UserInsurance.user_id == demo_user.id).first()
            if not existing_pol:
                db.add(UserInsurance(
                    user_id=demo_user.id,
                    insurance_id=ins_plan.id,
                    policy_number="MS-POL-2026-0091",
                    sum_insured=ins_plan.coverage_amount,
                    status="active",
                    dependents="Self + Spouse"
                ))
                db.commit()

            # Seed sample claim with history timeline
            existing_claim = db.query(InsuranceClaim).filter(InsuranceClaim.user_id == demo_user.id).first()
            if not existing_claim:
                sample_claim = InsuranceClaim(
                    user_id=demo_user.id,
                    insurance_id=ins_plan.id,
                    hospital_id=hosp.id,
                    claim_amount=65000.0,
                    claim_status="UNDER_REVIEW",
                    claim_description="Inpatient hospitalization for laparoscopic appendectomy surgery.",
                )
                db.add(sample_claim)
                db.commit()
                db.refresh(sample_claim)

                # Add timeline history
                db.add(ClaimStatusHistory(
                    claim_id=sample_claim.id,
                    previous_status=None,
                    new_status="SUBMITTED",
                    comment="Claim submitted by patient with hospital discharge slip.",
                ))
                db.add(ClaimStatusHistory(
                    claim_id=sample_claim.id,
                    previous_status="SUBMITTED",
                    new_status="UNDER_REVIEW",
                    comment="Medical bills and surgical records verified by insurance underwriter.",
                ))
                db.commit()

            # Seed sample notification
            existing_notif = db.query(Notification).filter(Notification.user_id == demo_user.id).first()
            if not existing_notif:
                db.add(Notification(
                    user_id=demo_user.id,
                    title="Welcome to MedSentinel 2.3",
                    message="Your MySQL-powered health intelligence dashboard is ready.",
                    type="info",
                    is_read=False
                ))
                db.commit()

            # Seed Patient record
            patient = db.query(Patient).filter(Patient.user_id == demo_user.id).first()
            if not patient:
                patient = Patient(
                    user_id=demo_user.id,
                    patient_code="MS-PAT-2026-0001",
                    name=demo_user.name,
                    gender="Male",
                    blood_group=demo_user.blood_group or "O+",
                    emergency_contact="+91 98765 00000",
                    allergies=demo_user.allergies or "None reported",
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)

            # Seed sample UserDocument
            sample_doc = db.query(UserDocument).filter(UserDocument.user_id == demo_user.id).first()
            if not sample_doc:
                sample_doc = UserDocument(
                    user_id=demo_user.id,
                    patient_id=patient.id,
                    document_code="DOC-2026-0001",
                    file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    doc_type="Lab Report",
                    filename="sample_cbc_panel.pdf",
                    original_name="Comprehensive Blood Count & Metabolic Panel.pdf",
                    file_path="uploads/sample_cbc_panel.pdf",
                    file_type="application/pdf",
                    file_size=245760,
                    status="APPROVED",
                    verification_status="VERIFIED",
                    ai_classification="Lab Report",
                    ai_confidence=0.98,
                    ocr_extracted_text="HEMOGLOBIN: 14.5 g/dL (Normal 13.5-17.5)\nWBC: 6800 /mcL (Normal 4500-11000)\nPLATELETS: 245000 /mcL (Normal 150000-450000)\nFASTING GLUCOSE: 95 mg/dL (Normal 70-99)\nHBA1C: 5.4% (Normal < 5.7%)\nCHOLESTEROL TOTAL: 185 mg/dL (Normal < 200)",
                )
                db.add(sample_doc)
                db.commit()
                db.refresh(sample_doc)

            # Seed sample LabResults
            existing_labs = db.query(LabResult).filter(LabResult.patient_id == patient.id).count()
            if existing_labs == 0:
                labs = [
                    LabResult(patient_id=patient.id, document_id=sample_doc.id, test_name="Hemoglobin", observed_value=14.5, unit="g/dL", reference_min=13.5, reference_max=17.5, status="NORMAL", is_critical=False),
                    LabResult(patient_id=patient.id, document_id=sample_doc.id, test_name="White Blood Cells", observed_value=6800.0, unit="/mcL", reference_min=4500.0, reference_max=11000.0, status="NORMAL", is_critical=False),
                    LabResult(patient_id=patient.id, document_id=sample_doc.id, test_name="Platelet Count", observed_value=245000.0, unit="/mcL", reference_min=150000.0, reference_max=450000.0, status="NORMAL", is_critical=False),
                    LabResult(patient_id=patient.id, document_id=sample_doc.id, test_name="Fasting Glucose", observed_value=95.0, unit="mg/dL", reference_min=70.0, reference_max=99.0, status="NORMAL", is_critical=False),
                    LabResult(patient_id=patient.id, document_id=sample_doc.id, test_name="HbA1c", observed_value=5.4, unit="%", reference_min=4.0, reference_max=5.7, status="NORMAL", is_critical=False),
                ]
                db.add_all(labs)
                db.commit()

            # Seed sample HealthScore
            existing_score = db.query(HealthScore).filter(HealthScore.patient_id == patient.id).first()
            if not existing_score:
                h_score = HealthScore(
                    patient_id=patient.id,
                    document_id=sample_doc.id,
                    health_score=87,
                    risk_score=13,
                    risk_level="LOW",
                    abnormal_tests=0,
                    ai_summary="All biometric markers, metabolic parameters, and hematologic indices are within standard reference ranges.",
                )
                db.add(h_score)
                db.commit()

            # Seed FraudAnalysis for sample claim
            claim_for_fraud = db.query(InsuranceClaim).filter(InsuranceClaim.user_id == demo_user.id).first()
            if claim_for_fraud:
                existing_fa = db.query(FraudAnalysis).filter(FraudAnalysis.claim_id == claim_for_fraud.id).first()
                if not existing_fa:
                    db.add(FraudAnalysis(
                        claim_id=claim_for_fraud.id,
                        fraud_score=15,
                        fraud_risk="LOW",
                        flags='["Patient ID verified with registered policyholder records.", "Hospital is accredited in cashless network.", "Claim amount within approved surgical procedure limits."]',
                        duplicate_docs_detected=False,
                        duplicate_invoices_detected=False,
                        reused_hash_detected=False,
                        patient_mismatch_detected=False,
                        suspicious_amount_flag=False,
                    ))
                    db.commit()

            # Seed sample Recommendations
            existing_rec = db.query(Recommendation).filter(Recommendation.user_id == demo_user.id).first()
            if not existing_rec:
                recs = [
                    Recommendation(
                        user_id=demo_user.id,
                        patient_id=patient.id,
                        recommendation_type="LIFESTYLE",
                        priority="LOW",
                        title="Annual Preventive Health Checkup Scheduled",
                        description="Your metabolic and lipid profiles are in optimal ranges. Continue balanced nutrition and maintain 150 minutes of moderate cardiovascular activity weekly.",
                        reason="Standard routine preventive health guideline for healthy adults.",
                        confidence=0.94,
                        sources='["PREVENTIVE_GUIDELINE", "METABOLIC_NORMAL"]',
                        status="ACTIVE",
                    ),
                    Recommendation(
                        user_id=demo_user.id,
                        patient_id=patient.id,
                        recommendation_type="DOCUMENT_FOLLOW_UP",
                        priority="MEDIUM",
                        title="Upload Insurance Card Copy to Vault",
                        description="Keep a digital scan of your active health insurance card in your encrypted Medical Vault for instantaneous hospital admission pre-authorization.",
                        reason="Medical vault optimization for rapid emergency pre-authorization.",
                        confidence=0.88,
                        sources='["VAULT_COMPLETION"]',
                        status="ACTIVE",
                    ),
                ]
                db.add_all(recs)
                db.commit()

        print("MySQL Database successfully seeded with all initial data!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
