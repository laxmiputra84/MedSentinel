"""
MedSentinel Automated Test Suite — Patient Condition-Driven Hospital Matching & Geo-Ranking
Tests:
 1. Condition evidence extraction strictly derived from patient data (no random selection).
 2. Insufficient evidence handling (returns explicit false state without guessing).
 3. Medical condition to clinical specialization mapping.
 4. Real Haversine geographic distance calculation.
 5. Radius filtering (e.g., 5km, 10km, 25km).
 6. Nearest hospital ranking (distance_km ascending).
 7. Missing coordinates handling (distance_km is None, no fake distance).
 8. Search query handling for "Find cardiology hospitals in Bengaluru with ICU availability".
 9. API endpoints for patient-condition hospital recommendation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.hospital import Hospital
from app.services.patient_condition_service import PatientConditionService
from app.services.hospital_service import HospitalService, haversine_distance

try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_test_hospitals():
    """Seed a consistent set of test hospitals with verified coordinates & facilities."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    db.query(Hospital).delete()
    db.commit()

    sample_hospitals = [
        # Hospital 1: Yelahanka, Bengaluru (Near REVA ~0.8 km) - Emergency / General
        Hospital(
            name="REVA Health & Clinical Research Centre",
            location="Kattigenahalli, Near REVA University, Yelahanka, Bengaluru, Karnataka",
            specialization="General Medicine, Emergency Care, Pediatrics",
            rating=4.8,
            distance=0.8,
            cost_range="₹15,000 - ₹40,000",
            schemes="Ayushman Bharat, State Health Card",
            insurance_accepted="Care Supreme, Star Health, Optima Secure",
            is_available=True,
            facilities="120 Beds, 24/7 Casualty, Ambulance Bay, Pharmacy, Diagnostic Lab",
            description="Comprehensive community health and trauma center located right adjacent to the REVA University campus",
            phone="+91-80-4696-6966",
            email="healthcenter@reva.edu.demo",
            latitude=13.1145,
            longitude=77.6340,
        ),
        # Hospital 2: Yelahanka, Bengaluru (Near REVA ~1.8 km) - Oncology
        Hospital(
            name="Cytecare Cancer Hospital",
            location="Venkatala, Near REVA University, Yelahanka, Bengaluru, Karnataka",
            specialization="Oncology, Surgical Oncology, Hematology",
            rating=4.9,
            distance=2.4,
            cost_range="₹45,000 - ₹95,000",
            schemes="Ayushman Bharat, CGHS",
            insurance_accepted="Star Health, Care Supreme, Optima Secure, HDFC ERGO",
            is_available=True,
            facilities="150 Beds, Organ Site Specialized Onco Team, CyberKnife, Digital Mammography",
            description="Premier comprehensive organ-site cancer hospital serving North Bengaluru and Yelahanka",
            phone="+91-80-2217-6767",
            email="info@cytecare.demo",
            latitude=13.1118,
            longitude=77.6186,
        ),
        # Hospital 3: Yelahanka, Bengaluru (Near REVA ~4.2 km) - Cardiology + Multi-speciality + ICU
        Hospital(
            name="Manipal Hospital North Yelahanka",
            location="Doddaballapur Main Road, Yelahanka, Bengaluru, Karnataka",
            specialization="Cardiology, Orthopedics, Neurology, Multi-speciality, Endocrinology",
            rating=4.8,
            distance=3.2,
            cost_range="₹48,000 - ₹98,000",
            schemes="Ayushman Bharat, CGHS, MJPJAY",
            insurance_accepted="Star Health, ICICI Lombard, Care Supreme",
            is_available=True,
            facilities="200 Beds, 24/7 Cardiac Emergency, Cath Lab, 24-Bed ICU, Dialysis Center",
            description="State-of-the-art super-speciality facility providing multi-disciplinary tertiary care with cardiac ICU in Yelahanka",
            phone="+91-80-2856-7777",
            email="info.yelahanka@manipalhospitals.demo",
            latitude=13.1007,
            longitude=77.5963,
        ),
        # Hospital 4: Bannerghatta Road, Bengaluru (~26 km from REVA) - Cardiology / Oncology + ICU
        Hospital(
            name="Apollo Hospital Bannerghatta",
            location="Bannerghatta Road, Bengaluru, Karnataka",
            specialization="Oncology, Cardiology, Pediatrics, Endocrinology",
            rating=4.9,
            distance=6.2,
            cost_range="₹60,000 - ₹1,30,000",
            schemes="Ayushman Bharat, CGHS",
            insurance_accepted="Optima Secure, HDFC ERGO, Care Supreme",
            is_available=True,
            facilities="250 Beds, JCI Accredited, 3T MRI, 30-Bed Level 3 NICU & Cardiac ICU, Bone Marrow Transplant",
            description="Flagship quaternary care hospital in South Bengaluru with 24/7 ICU availability and interventional cardiology",
            phone="+91-80-2630-4050",
            email="contact@apollo-bannerghatta.demo",
            latitude=12.8942,
            longitude=77.5978,
        ),
        # Hospital 5: Mumbai (Different City) - Cardiology
        Hospital(
            name="Lilavati Hospital and Research Centre",
            location="Bandra West, Mumbai, Maharashtra",
            specialization="Multi-speciality, Cardiology, Nephrology",
            rating=4.8,
            distance=4.2,
            cost_range="₹65,000 - ₹1,45,000",
            schemes="MJPJAY, CGHS",
            insurance_accepted="Star Health, ICICI Lombard, Care Supreme",
            is_available=True,
            facilities="323 Beds, 12 Operation Theatres, Dialysis Unit, Linear Accelerator, Multi-Bed ICU",
            description="Premier multi-specialty healthcare institution in Mumbai offering cutting-edge surgical precision",
            phone="+91-22-2675-1000",
            email="info@lilavati.demo",
            latitude=19.0519,
            longitude=72.8291,
        ),
        # Hospital 6: Hospital without GPS coordinates
        Hospital(
            name="City Community Clinic",
            location="Central Bengaluru, Karnataka",
            specialization="General Medicine, Pediatrics",
            rating=4.2,
            distance=5.0,
            cost_range="₹5,000 - ₹15,000",
            schemes="Ayushman Bharat",
            insurance_accepted="Care Supreme",
            is_available=True,
            facilities="10 Beds, Outpatient Clinic",
            description="Neighborhood community clinic for primary outpatient care",
            phone="+91-80-2222-1111",
            email="community@clinic.demo",
            latitude=None,
            longitude=None,
        ),
    ]

    db.bulk_save_objects(sample_hospitals)
    db.commit()
    db.close()


def test_condition_extraction_diabetes_evidence():
    """Verify that elevated HbA1c and glucose strictly derive diabetes without random guessing."""
    labs = [
        {"name": "HbA1c", "value": 8.6, "unit": "%", "status": "HIGH"},
        {"name": "Fasting Blood Glucose", "value": 182.0, "unit": "mg/dL", "status": "HIGH"},
    ]
    res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text="Patient reports increased thirst and fatigue. Rx: Metformin 500mg daily.",
        lab_results=labs,
    )

    assert res.has_sufficient_evidence is True
    assert res.primary_condition is not None
    assert "Diabetes" in res.primary_condition.condition_name
    assert res.primary_condition.category == "ENDOCRINOLOGY"
    assert "Endocrinology" in res.recommended_specialties
    assert any("HbA1c" in ev for ev in res.primary_condition.supporting_evidence)
    assert any("Glucose" in ev for ev in res.primary_condition.supporting_evidence)
    assert any("Metformin" in ev for ev in res.primary_condition.supporting_evidence)


def test_condition_extraction_cardiac_evidence():
    """Verify cardiac biomarker and clinical documentation trigger cardiology matching."""
    labs = [
        {"name": "Troponin-I", "value": 1.45, "unit": "ng/mL", "status": "CRITICAL"},
        {"name": "Total Cholesterol", "value": 245.0, "unit": "mg/dL", "status": "HIGH"},
    ]
    res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text="Patient presents with acute chest pain and shortness of breath.",
        lab_results=labs,
    )

    assert res.has_sufficient_evidence is True
    assert res.primary_condition is not None
    assert res.primary_condition.category == "CARDIOLOGY"
    assert "Cardiology" in res.recommended_specialties
    assert res.requires_icu_or_critical_care is True  # Troponin is critical


def test_insufficient_evidence_returns_no_guess():
    """Verify that normal parameters and generic non-diagnostic text return insufficient evidence."""
    labs = [
        {"name": "Hemoglobin", "value": 14.2, "unit": "g/dL", "status": "NORMAL"},
        {"name": "Platelets", "value": 250000, "unit": "/uL", "status": "NORMAL"},
        {"name": "Glucose", "value": 88.0, "unit": "mg/dL", "status": "NORMAL"},
    ]
    res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text="Routine annual executive health checkup. Patient feels fine.",
        lab_results=labs,
    )

    assert res.has_sufficient_evidence is False
    assert res.primary_condition is None
    assert len(res.all_conditions) == 0
    assert len(res.recommended_specialties) == 0
    assert "Insufficient" in res.clinical_summary


def test_hospital_recommendations_near_reva_coordinates():
    """
    Test hospital matching using patient's real GPS coordinates at REVA University (13.1147, 77.6346)
    for a cardiac condition. Hospitals should be ranked nearest-first.
    """
    db = TestingSessionLocal()
    labs = [
        {"name": "Troponin-I", "value": 0.8, "unit": "ng/mL", "status": "CRITICAL"},
    ]
    condition_res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text="Acute coronary syndrome evaluation.",
        lab_results=labs,
    )

    # Search from REVA campus coordinates
    match_res = HospitalService.recommend_hospitals_for_patient_condition(
        db=db,
        condition_analysis=condition_res,
        latitude=13.1147,
        longitude=77.6346,
        location="Bengaluru",
        limit=5,
    )
    db.close()

    assert match_res["has_sufficient_evidence"] is True
    hospitals = match_res["hospitals"]
    assert len(hospitals) >= 2

    # Verify nearest hospital is ranked first:
    # Manipal North Yelahanka (~4.2 km) should come BEFORE Apollo Bannerghatta (~26 km)
    assert hospitals[0]["name"] == "Manipal Hospital North Yelahanka"
    assert hospitals[0]["distance_km"] is not None
    assert hospitals[0]["distance_km"] < 6.0

    # Second hospital should be farther away
    assert hospitals[1]["distance_km"] > hospitals[0]["distance_km"]

    # Verify ICU status detection
    assert hospitals[0]["icu_status"] == "Available"


def test_radius_filtering():
    """Verify that a 10 km radius filter includes Yelahanka hospitals but excludes Bannerghatta (>20 km)."""
    db = TestingSessionLocal()
    labs = [{"name": "Troponin-I", "value": 0.8, "unit": "ng/mL", "status": "HIGH"}]
    condition_res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text="Cardiac checkup",
        lab_results=labs,
    )

    # 10 km radius from REVA (13.1147, 77.6346)
    match_10km = HospitalService.recommend_hospitals_for_patient_condition(
        db=db,
        condition_analysis=condition_res,
        latitude=13.1147,
        longitude=77.6346,
        radius_km=10.0,
    )

    # 50 km radius from REVA
    match_50km = HospitalService.recommend_hospitals_for_patient_condition(
        db=db,
        condition_analysis=condition_res,
        latitude=13.1147,
        longitude=77.6346,
        radius_km=50.0,
    )
    db.close()

    names_10km = [h["name"] for h in match_10km["hospitals"]]
    names_50km = [h["name"] for h in match_50km["hospitals"]]

    assert "Manipal Hospital North Yelahanka" in names_10km
    assert "Apollo Hospital Bannerghatta" not in names_10km
    assert "Apollo Hospital Bannerghatta" in names_50km


def test_missing_coordinates_handling():
    """Verify that when coordinates are omitted, distance_km is None and no fake distances are generated."""
    db = TestingSessionLocal()
    labs = [{"name": "HbA1c", "value": 8.0, "unit": "%", "status": "HIGH"}]
    condition_res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text="Diabetes review",
        lab_results=labs,
    )

    match_res = HospitalService.recommend_hospitals_for_patient_condition(
        db=db,
        condition_analysis=condition_res,
        latitude=None,
        longitude=None,
        location="Bengaluru",
    )
    db.close()

    assert match_res["has_sufficient_evidence"] is True
    for h in match_res["hospitals"]:
        assert h["distance_km"] is None


def test_hospital_search_cardiology_bengaluru_icu():
    """Verify query: 'Find cardiology hospitals in Bengaluru with ICU availability'."""
    res = client.get("/api/hospitals", params={"search": "Find cardiology hospitals in Bengaluru with ICU availability"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1

    # Every returned hospital MUST be in Bengaluru, have Cardiology, have ICU, and be available
    for h in data:
        assert "bengaluru" in h["location"].lower() or "bengaluru" in h["name"].lower()
        assert "cardiology" in (h["specialization"] or "").lower()
        fac_desc = f"{h.get('facilities', '')} {h.get('description', '')}".lower()
        assert any(k in fac_desc for k in ["icu", "intensive care", "critical care"])
        assert h["is_available"] is True

    # Lilavati (Mumbai) must NOT be returned in Bengaluru search
    assert not any("Lilavati" in h["name"] for h in data)


def test_recommend_hospitals_api_endpoint():
    """Test POST /api/hospitals/recommendations/patient-condition API."""
    payload = {
        "extracted_text": "Patient has uncontrolled Type 2 Diabetes Mellitus with elevated fasting blood sugar.",
        "lab_results": [
            {"name": "HbA1c", "value": 9.2, "unit": "%", "status": "HIGH"},
            {"name": "Fasting Blood Sugar", "value": 195.0, "unit": "mg/dL", "status": "HIGH"},
        ],
        "latitude": 13.1147,
        "longitude": 77.6346,
        "location": "Bengaluru",
        "radius_km": 30.0,
        "limit": 5,
    }
    res = client.post("/api/hospitals/recommendations/patient-condition", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["has_sufficient_evidence"] is True
    assert data["patient_condition"] is not None
    assert "Diabetes" in data["patient_condition"]["condition_name"]
    assert len(data["hospitals"]) > 0

    first_hosp = data["hospitals"][0]
    assert first_hosp["distance_km"] is not None
    assert first_hosp["is_verified"] is True
    assert len(first_hosp["match_reasons"]) > 0
