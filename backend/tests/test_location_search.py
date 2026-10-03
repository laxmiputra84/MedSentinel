import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.hospital import Hospital
from app.services.hospital_service import HospitalService, haversine_distance
try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

client = TestClient(app)

@pytest.fixture(autouse=True)
def seed_hospitals():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    db.query(Hospital).delete()
    db.commit()

    sample_hospitals = [
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
        Hospital(
            name="Manipal Hospital North Yelahanka",
            location="Doddaballapur Main Road, Yelahanka, Bengaluru, Karnataka",
            specialization="Cardiology, Orthopedics, Neurology, Multi-speciality",
            rating=4.8,
            distance=3.2,
            cost_range="₹48,000 - ₹98,000",
            schemes="Ayushman Bharat, CGHS, MJPJAY",
            insurance_accepted="Star Health, ICICI Lombard, Care Supreme",
            is_available=True,
            facilities="200 Beds, 24/7 Cardiac Emergency, Cath Lab, Dialysis Center",
            description="State-of-the-art super-speciality facility providing multi-disciplinary tertiary care in Yelahanka",
            phone="+91-80-2856-7777",
            email="info.yelahanka@manipalhospitals.demo",
            latitude=13.1007,
            longitude=77.5963,
        ),
        Hospital(
            name="Aster CMI Hospital",
            location="Hebbal, Bengaluru, Karnataka",
            specialization="Neurology, Gastroenterology, Urology",
            rating=4.6,
            distance=8.0,
            cost_range="₹55,000 - ₹1,05,000",
            schemes="Ayushman Bharat, MJPJAY",
            insurance_accepted="Optima Secure, Max Bupa, Star Health",
            is_available=True,
            facilities="500 Beds, Comprehensive Liver Care, Neuro Navigation, 24/7 Stroke Unit",
            description="Leading healthcare landmark in North Bengaluru with multispeciality Centers of Excellence",
            phone="+91-80-4342-0100",
            email="care@astercmi.demo",
            latitude=13.0560,
            longitude=77.5925,
        ),
        Hospital(
            name="Apollo Hospital Bannerghatta",
            location="Bannerghatta Road, Bengaluru, Karnataka",
            specialization="Oncology, Cardiology, Pediatrics",
            rating=4.9,
            distance=6.2,
            cost_range="₹60,000 - ₹1,30,000",
            schemes="Ayushman Bharat, CGHS",
            insurance_accepted="Optima Secure, HDFC ERGO, Care Supreme",
            is_available=True,
            facilities="250 Beds, JCI Accredited, 3T MRI, Level 3 NICU, Bone Marrow Transplant",
            description="Flagship quaternary care hospital with international patient services and advanced oncology",
            phone="+91-80-2630-4050",
            email="contact@apollo-bannerghatta.demo",
            latitude=12.8942,
            longitude=77.5978,
        ),
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
            facilities="323 Beds, 12 Operation Theatres, Dialysis Unit, Linear Accelerator",
            description="Premier multi-specialty healthcare institution in Mumbai offering cutting-edge surgical precision",
            phone="+91-22-2675-1000",
            email="info@lilavati.demo",
            latitude=19.0519,
            longitude=72.8291,
        ),
    ]
    db.bulk_save_objects(sample_hospitals)
    db.commit()
    db.close()

def test_haversine_distance_calculation():
    # Known distance between REVA University (13.1147, 77.6346) and Cytecare (13.1118, 77.6186)
    dist = haversine_distance(13.1147, 77.6346, 13.1118, 77.6186)
    assert 1.5 <= dist <= 2.0, f"Expected approx 1.76 km, got {dist}"

    # Same point distance should be 0.0
    zero_dist = haversine_distance(12.9716, 77.5946, 12.9716, 77.5946)
    assert zero_dist == 0.0

def test_intent_detection():
    # 1. Nearby Search
    res_nearby = HospitalService.detect_search_intent("hospitals near reva university")
    assert res_nearby["search_type"] == "nearby"
    assert res_nearby["is_nearby_search"] is True
    assert res_nearby["detected_location"].lower() == "reva university"

    # 2. Location Search
    res_loc = HospitalService.detect_search_intent("hospitals in yelahanka")
    assert res_loc["search_type"] == "location"
    assert res_loc["detected_location"].lower() == "yelahanka"

    # 3. Specialty Search
    res_spec = HospitalService.detect_search_intent("cancer hospitals")
    assert res_spec["search_type"] == "specialty"
    assert res_spec["detected_specialty"] == "Oncology"

    # 4. Specialty + Location Search
    res_spec_loc = HospitalService.detect_search_intent("cancer hospitals in yelahanka")
    assert res_spec_loc["search_type"] == "specialty_location"
    assert res_spec_loc["detected_specialty"] == "Oncology"
    assert res_spec_loc["detected_location"].lower() == "yelahanka"

    # 5. Normal Keyword Search
    res_kw = HospitalService.detect_search_intent("apollo hospital")
    assert res_kw["search_type"] == "keyword"
    assert "Apollo" in (res_kw["detected_keyword"] or "")

def test_search_reva():
    res = client.get("/api/hospitals", params={"search": "reva"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert any("REVA" in h["name"] for h in data)

def test_search_near_by_reva_hospital():
    res = client.get("/api/hospitals", params={"search": "near by reva hospital"})
    assert res.status_code == 200
    assert res.headers.get("X-Search-Type") == "nearby"
    data = res.json()
    assert len(data) >= 1
    assert any("REVA" in h["name"] or "Cytecare" in h["name"] for h in data)

def test_search_hospitals_near_reva_university():
    res = client.get("/api/hospitals", params={"search": "hospitals near reva university"})
    assert res.status_code == 200
    assert res.headers.get("X-Search-Type") == "nearby"
    data = res.json()
    assert len(data) >= 1
    assert any("REVA" in h["name"] or "Cytecare" in h["name"] for h in data)

def test_search_hospitals_in_yelahanka():
    res = client.get("/api/hospitals", params={"search": "hospitals in yelahanka"})
    assert res.status_code == 200
    assert res.headers.get("X-Search-Type") == "location"
    data = res.json()
    assert len(data) >= 2
    for h in data:
        assert "yelahanka" in h["location"].lower()

def test_search_cancer_hospitals():
    res = client.get("/api/hospitals", params={"search": "cancer hospitals"})
    assert res.status_code == 200
    assert res.headers.get("X-Search-Type") == "specialty"
    data = res.json()
    assert len(data) >= 1
    for h in data:
        assert "oncology" in (h["specialization"] or "").lower() or "cancer" in (h["name"] or "").lower()

def test_search_cancer_hospitals_in_yelahanka():
    res = client.get("/api/hospitals", params={"search": "cancer hospitals in yelahanka"})
    assert res.status_code == 200
    assert res.headers.get("X-Search-Type") == "specialty_location"
    data = res.json()
    assert len(data) >= 1
    assert any("Cytecare" in h["name"] for h in data)

def test_empty_and_invalid_search():
    # Empty search should return seeded hospitals
    res_empty = client.get("/api/hospitals", params={"search": ""})
    assert res_empty.status_code == 200
    assert len(res_empty.json()) >= 6

    # Non-matching search should return empty list without crashing
    res_none = client.get("/api/hospitals", params={"search": "xyznonexistentquery999"})
    assert res_none.status_code == 200
    assert len(res_none.json()) == 0

def test_nearby_search_without_coordinates():
    # Without GPS coordinates, distance_km MUST be None (no fake distance)
    res = client.get("/api/hospitals", params={"search": "hospitals near reva university"})
    assert res.status_code == 200
    assert res.headers.get("X-Has-Coordinates") == "false"
    data = res.json()
    for h in data:
        assert h.get("distance_km") is None

def test_nearby_search_with_coordinates():
    # With GPS coordinates at REVA University (13.1147, 77.6346)
    res = client.get("/api/hospitals", params={"latitude": 13.1147, "longitude": 77.6346})
    assert res.status_code == 200
    assert res.headers.get("X-Has-Coordinates") == "true"
    data = res.json()
    assert len(data) > 0
    # Closest hospital should have distance_km calculated
    first = data[0]
    assert first["distance_km"] is not None
    assert first["distance_km"] < 1.0 # REVA Health is adjacent to REVA campus (< 0.1km)
    # Distances must be sorted in ascending order
    distances = [h["distance_km"] for h in data if h.get("distance_km") is not None]
    assert distances == sorted(distances)

def test_dedicated_intent_endpoint():
    res = client.get("/api/hospitals/intent", params={"query": "cardiac hospitals near bengaluru"})
    assert res.status_code == 200
    intent = res.json()
    assert intent["is_nearby_search"] is True
    assert intent["detected_specialty"] == "Cardiology"
    assert intent["detected_location"].lower() == "bengaluru"
