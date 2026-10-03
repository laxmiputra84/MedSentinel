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
def setup_test_hospitals():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    db.query(Hospital).delete()
    db.commit()

    # Create realistic test hospitals with coordinates & missing coordinates
    hospitals = [
        Hospital(
            name="Manipal Hospital Hebbal",
            location="Hebbal, Bengaluru, Karnataka",
            specialization="Cardiology, Oncology, Emergency Care",
            rating=4.8,
            distance=6.5,
            facilities="32-Bed ICU, Cardiac Cath Lab, 24/7 Emergency",
            description="Leading cardiac emergency center in Bengaluru with comprehensive ICU.",
            schemes="Ayushman Bharat, CGHS",
            insurance_accepted="Star Health, Care Supreme",
            is_available=True,
            latitude=13.0560,
            longitude=77.5925,
        ),
        Hospital(
            name="Apollo Multispeciality Bengaluru",
            location="Bannerghatta Road, Bengaluru, Karnataka",
            specialization="Cardiology, Organ Transplants, Oncology",
            rating=4.9,
            distance=24.5,
            facilities="Advanced Neonatal ICU, Digital Cath Lab, Robotic Surgery",
            description="Premier cardiac and cancer hospital in Bengaluru.",
            schemes="Ayushman Bharat, MJPJAY",
            insurance_accepted="Star Health, Optima Secure",
            is_available=True,
            latitude=12.8944,
            longitude=77.5986,
        ),
        Hospital(
            name="Yelahanka General Clinic",
            location="Yelahanka, Bengaluru, Karnataka",
            specialization="General Medicine, Pediatrics",
            rating=4.2,
            distance=2.0,
            facilities="Outpatient Consultation, Minor OT",
            description="Community outpatient healthcare clinic without ICU.",
            schemes="State Health Card",
            insurance_accepted="Care Supreme",
            is_available=True,
            latitude=13.1007,
            longitude=77.5963,
        ),
        Hospital(
            name="Mumbai Heart & Lung Institute",
            location="Bandra, Mumbai, Maharashtra",
            specialization="Cardiology, Pulmonology",
            rating=4.7,
            distance=980.0,
            facilities="20-Bed ICU, ECMO, Cath Lab",
            description="Dedicated cardiac facility in Mumbai.",
            schemes="MJPJAY",
            insurance_accepted="Star Health",
            is_available=True,
            latitude=19.0596,
            longitude=72.8295,
        ),
        Hospital(
            name="Heritage City Hospital",
            location="Mysuru, Karnataka",
            specialization="Orthopedics, General Surgery",
            rating=4.5,
            distance=140.0,
            facilities="24/7 Emergency, Standard ICU",
            description="Regional surgical hospital in Mysuru.",
            schemes="Ayushman Bharat",
            insurance_accepted="Star Health",
            is_available=True,
            latitude=None, # Missing coordinates intentionally
            longitude=None,
        ),
    ]

    for h in hospitals:
        db.add(h)
    db.commit()
    db.close()


def test_case_1_no_gps_with_max_distance_slider():
    """
    Case 1: All Locations, All Schemes, Rating All, No GPS, Max Distance 15 km
    -> Hospitals MUST still appear and not be rejected by non-GPS distance filter!
    """
    res = client.get("/api/hospitals?maxDistance=15")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4, f"Expected all hospitals without GPS distance filter, got {len(data)}"
    # Every hospital distance_km must be None when no GPS
    for item in data:
        assert item["distance_km"] is None


def test_case_2_gps_enabled_radius_15km():
    """
    Case 2: GPS enabled (REVA Univ: 13.1147, 77.6346), Radius 15 km
    -> Only hospitals within 15 km should be returned (e.g. Manipal Hebbal at ~7.8km, Yelahanka at ~4.4km).
    """
    reva_lat, reva_lon = 13.1147, 77.6346
    res = client.get(f"/api/hospitals?latitude={reva_lat}&longitude={reva_lon}&radius=15")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2 # Manipal Hebbal and Yelahanka General Clinic
    for item in data:
        assert item["distance_km"] is not None
        assert item["distance_km"] <= 15.0
    # Must be sorted nearest first
    assert data[0]["distance_km"] <= data[1]["distance_km"]


def test_case_3_gps_enabled_radius_25km_wider_results():
    """
    Case 3: GPS enabled (REVA Univ), Radius 30 km
    -> Wider results including Apollo Bannerghatta (~24.7 km).
    """
    reva_lat, reva_lon = 13.1147, 77.6346
    res = client.get(f"/api/hospitals?latitude={reva_lat}&longitude={reva_lon}&radius=30")
    assert res.status_code == 200
    data = res.json()
    names = [h["name"] for h in data]
    assert "Apollo Multispeciality Bengaluru" in names
    assert "Manipal Hospital Hebbal" in names
    assert "Yelahanka General Clinic" in names
    # Mumbai hospital at ~980km must NOT be in 30km radius
    assert "Mumbai Heart & Lung Institute" not in names


def test_case_4_search_cardiology():
    """
    Case 4: Search = Cardiology
    -> Cardiology hospitals should be returned.
    """
    res = client.get("/api/hospitals?search=Cardiology")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    for h in data:
        assert "Cardiology" in h["specialization"]


def test_case_5_location_bengaluru():
    """
    Case 5: Location = Bengaluru
    -> Only Bengaluru hospitals.
    """
    res = client.get("/api/hospitals?location=Bengaluru")
    assert res.status_code == 200
    data = res.json()
    for h in data:
        assert "Bengaluru" in h["location"] or "Bengaluru" in h["name"]
    names = [h["name"] for h in data]
    assert "Mumbai Heart & Lung Institute" not in names


def test_case_6_cardiology_bengaluru_icu():
    """
    Case 6: Search = 'Find cardiology hospitals in Bengaluru with ICU availability'
    -> Only hospitals matching Cardiology + Bengaluru whose actual data supports ICU.
    """
    res = client.get("/api/hospitals/search?query=Find+cardiology+hospitals+in+Bengaluru+with+ICU+availability")
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    assert len(items) >= 1
    for h in items:
        assert "Cardiology" in h["specialization"]
        assert "Bengaluru" in h["location"]
        fac_and_desc = (h["facilities"] or "") + " " + (h["description"] or "")
        assert "ICU" in fac_and_desc or "Intensive Care" in fac_and_desc


def test_case_7_missing_hospital_coordinates():
    """
    Case 7: Missing hospital coordinates
    -> Hospital should not disappear when searching without GPS or broad search.
    """
    # Without GPS coordinates, hospital with missing coords is returned with distance_km = None
    res = client.get("/api/hospitals?search=Heritage")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "Heritage City Hospital"
    assert data[0]["distance_km"] is None
