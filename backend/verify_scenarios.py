import requests

BASE = "http://localhost:8000/api"

def run_verification():
    print("=== Case A: GPS OFF + All Filters ===")
    r = requests.get(f"{BASE}/hospitals")
    print(f"Status: {r.status_code}, Found: {len(r.json())} hospitals")
    for h in r.json():
        print(f"  - {h['name']} | {h['location']} | distance_km: {h['distance_km']}")

    print("\n=== Case B: GPS ON + 15 km (REVA coords: 13.1147, 77.6346) ===")
    r = requests.get(f"{BASE}/hospitals?latitude=13.1147&longitude=77.6346&radius=15")
    print(f"Status: {r.status_code}, Found: {len(r.json())} hospitals within 15km")
    for h in r.json():
        print(f"  - {h['name']} | dist: {h['distance_km']} km")

    print("\n=== Case C: GPS ON + 25 km ===")
    r = requests.get(f"{BASE}/hospitals?latitude=13.1147&longitude=77.6346&radius=25")
    print(f"Status: {r.status_code}, Found: {len(r.json())} hospitals within 25km")
    for h in r.json():
        print(f"  - {h['name']} | dist: {h['distance_km']} km")

    print("\n=== Case D: Search Cardiology ===")
    r = requests.get(f"{BASE}/hospitals?search=Cardiology")
    print(f"Status: {r.status_code}, Found: {len(r.json())} cardiology hospitals")
    for h in r.json():
        print(f"  - {h['name']} | {h['specialization']}")

    print("\n=== Case E1: Patient with NO diabetes evidence ===")
    payload_empty = {"extracted_text": "Patient routine annual wellness checkup. Normal observations.", "lab_results": []}
    r = requests.post(f"{BASE}/hospitals/recommendations/patient-condition", json=payload_empty)
    print(f"Status: {r.status_code}, has_sufficient_evidence: {r.json()['has_sufficient_evidence']}, condition: {r.json()['patient_condition']}")

    print("\n=== Case E2: Patient with REAL diabetes evidence (HbA1c=8.2, Glucose=175) ===")
    payload_diabetes = {
        "extracted_data": {"hba1c": 8.2, "fasting_blood_glucose": 175},
        "extracted_text": "Elevated HbA1c and fasting blood sugar.",
        "latitude": 13.1147,
        "longitude": 77.6346,
        "radius_km": 25.0
    }
    r = requests.post(f"{BASE}/hospitals/recommendations/patient-condition", json=payload_diabetes)
    res_json = r.json()
    print(f"Status: {r.status_code}, has_sufficient_evidence: {res_json['has_sufficient_evidence']}")
    if res_json['patient_condition']:
        print(f"Condition: {res_json['patient_condition']['condition_name']}")
        print(f"Evidence: {res_json['patient_condition']['supporting_evidence']}")
        print(f"Specialties: {res_json['patient_condition']['recommended_specialties']}")
    print(f"Recommended Hospitals ({len(res_json['hospitals'])}):")
    for h in res_json["hospitals"]:
        print(f"  - {h['name']} | dist: {h['distance_km']} km | matched: {h.get('matched_specialties')}")

if __name__ == "__main__":
    run_verification()
