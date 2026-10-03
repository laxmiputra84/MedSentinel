from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def main():
    print("=== Case A: GPS OFF + All Filters ===")
    r = client.get("/api/hospitals")
    data = r.json()
    print(f"Status: {r.status_code}, Found: {len(data)} hospitals")
    for h in data:
        print(f"  - {h['name']} | {h['location']} | distance_km: {h['distance_km']}")

    print("\n=== Case B: GPS ON + 15 km (REVA coords: 13.1147, 77.6346) ===")
    r = client.get("/api/hospitals?latitude=13.1147&longitude=77.6346&radius=15")
    data = r.json()
    print(f"Status: {r.status_code}, Found: {len(data)} hospitals within 15km")
    for h in data:
        print(f"  - {h['name']} | dist: {h['distance_km']} km")

    print("\n=== Case C: GPS ON + 25 km ===")
    r = client.get("/api/hospitals?latitude=13.1147&longitude=77.6346&radius=25")
    data = r.json()
    print(f"Status: {r.status_code}, Found: {len(data)} hospitals within 25km")
    for h in data:
        print(f"  - {h['name']} | dist: {h['distance_km']} km")

    print("\n=== Case D: Search Cardiology ===")
    r = client.get("/api/hospitals?search=Cardiology")
    data = r.json()
    print(f"Status: {r.status_code}, Found: {len(data)} cardiology hospitals")
    for h in data:
        print(f"  - {h['name']} | {h['specialization']}")

    print("\n=== Case E1: Patient with NO diabetes evidence ===")
    payload_empty = {"extracted_text": "Patient routine annual wellness checkup. Normal observations.", "lab_results": []}
    r = client.post("/api/hospitals/recommendations/patient-condition", json=payload_empty)
    res_json = r.json()
    print(f"Status: {r.status_code}, has_sufficient_evidence: {res_json['has_sufficient_evidence']}, condition: {res_json['patient_condition']}")

    print("\n=== Case E2: Patient with REAL diabetes evidence (HbA1c=8.2, Glucose=175) ===")
    payload_diabetes = {
        "extracted_data": {"hba1c": 8.2, "fasting_blood_glucose": 175},
        "extracted_text": "Elevated HbA1c and fasting blood sugar.",
        "latitude": 13.1147,
        "longitude": 77.6346,
        "radius_km": 25.0
    }
    r = client.post("/api/hospitals/recommendations/patient-condition", json=payload_diabetes)
    res_json = r.json()
    print(f"Status: {r.status_code}, has_sufficient_evidence: {res_json['has_sufficient_evidence']}")
    if res_json['patient_condition']:
        print(f"Condition: {res_json['patient_condition']['condition_name']}")
        print(f"Evidence: {res_json['patient_condition']['supporting_evidence']}")
        print(f"Specialties: {res_json['patient_condition']['recommended_specialties']}")
    print(f"Recommended Hospitals ({len(res_json['hospitals'])}):")
    for h in res_json["hospitals"]:
        name = h['name']
        dist = h['distance_km']
        print(f"  - {name} | dist: {dist} km")

if __name__ == "__main__":
    main()
