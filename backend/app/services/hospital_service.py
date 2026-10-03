import re
import math
from typing import List, Optional, Tuple, Set, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from app.models.hospital import Hospital
from app.core.constants import ILLNESS_SPECIALTY_MAP, DIAGNOSTIC_SPECIALTY_MAP
from app.services.patient_condition_service import PatientConditionService, PatientConditionAnalysisResult


def haversine_distance(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> Optional[float]:
    """
    Calculate the great-circle distance between two points on the Earth
    in kilometers using the Haversine formula.
    Safely handles None, numerical drift, and antipodal domain limits.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    try:
        R = 6371.0  # Earth's mean radius in km
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))

        a = (math.sin(delta_phi / 2.0) ** 2) + \
            math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
        # Clamped to [0.0, 1.0] to prevent math.sqrt domain errors from floating-point inaccuracies
        a = min(1.0, max(0.0, a))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 2)
    except Exception:
        return None


class HospitalService:
    @staticmethod
    def detect_search_intent(query_str: Optional[str]) -> Dict[str, Any]:
        """
        Analyze a natural language query to classify search intent into:
        - keyword: General name or brand search (e.g. "apollo hospital")
        - location: Geographical query without specific specialty (e.g. "hospitals in yelahanka")
        - specialty: Medical focus query (e.g. "cancer hospitals")
        - specialty_location: Both specialty and locality (e.g. "cancer hospitals in yelahanka")
        - nearby: Proximity/nearness intent (e.g. "hospitals near reva university")
        Also extracts requested facilities (e.g. ICU) and availability requirements.
        """
        if not query_str or not query_str.strip():
            return {
                "search_query": None,
                "search_type": "keyword",
                "is_nearby_search": False,
                "detected_location": None,
                "detected_specialty": None,
                "detected_keyword": None,
                "detected_facilities": [],
                "requires_availability": False,
                "has_coordinates": False,
            }

        raw = query_str.strip()
        clean = raw.lower()

        # 1. Detect Nearby Intent
        nearby_patterns = [
            r"\bnear\s+by\b", r"\bnearby\b", r"\bnear\s+to\b", r"\bnear\b",
            r"\baround\b", r"\bclose\s+to\b", r"\bproximity\s+to\b",
            r"\bclosest\s+to\b", r"\bclosest\b", r"\bnearest\b",
            r"\bin\s+the\s+vicinity\s+of\b", r"\bnear\s+me\b", r"\bclose\s+by\b"
        ]
        is_nearby = any(re.search(pat, clean) for pat in nearby_patterns)

        # 2. Extract Medical Specialties
        specialty_dict: Dict[str, str] = {
            "cancer": "Oncology",
            "oncology": "Oncology",
            "tumor": "Oncology",
            "chemo": "Oncology",
            "cardiac": "Cardiology",
            "cardiology": "Cardiology",
            "heart": "Cardiology",
            "vascular": "Cardiology",
            "orthopedic": "Orthopedics",
            "orthopedics": "Orthopedics",
            "ortho": "Orthopedics",
            "bone": "Orthopedics",
            "joint": "Orthopedics",
            "spine": "Orthopedics",
            "neurology": "Neurology",
            "neuro": "Neurology",
            "brain": "Neurology",
            "stroke": "Neurology",
            "pediatric": "Pediatrics",
            "pediatrics": "Pediatrics",
            "child": "Pediatrics",
            "kidney": "Nephrology",
            "renal": "Nephrology",
            "dialysis": "Nephrology",
            "nephrology": "Nephrology",
            "gastro": "Gastroenterology",
            "gastroenterology": "Gastroenterology",
            "liver": "Gastroenterology",
            "pulmonary": "Pulmonology",
            "pulmonology": "Pulmonology",
            "respiratory": "Pulmonology",
            "chest": "Pulmonology",
            "trauma": "Emergency Care",
            "emergency": "Emergency Care",
            "transplant": "Organ Transplant",
        }
        for kw, specs in ILLNESS_SPECIALTY_MAP.items():
            if kw not in specialty_dict and specs:
                specialty_dict[kw] = specs[0]
        for kw, specs in DIAGNOSTIC_SPECIALTY_MAP.items():
            if kw not in specialty_dict and specs:
                specialty_dict[kw] = specs[0]

        detected_specialty: Optional[str] = None
        for kw, spec_name in sorted(specialty_dict.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(kw)}\b", clean):
                detected_specialty = spec_name
                break

        # 3. Extract Locations (Known landmarks, regions & cities)
        known_locations = [
            "reva university", "reva", "kattigenahalli", "yelahanka", "hebbal",
            "bengaluru", "bangalore", "cunningham road", "cunningham",
            "bannerghatta road", "bannerghatta", "indiranagar", "old airport road",
            "bommasandra", "mumbai", "bandra west", "bandra", "andheri west", "andheri",
            "parel", "mahim", "new delhi", "delhi", "saket", "sarita vihar", "okhla",
            "rajinder nagar", "gurugram", "gurgaon", "chennai", "greams road", "adyar",
            "manapakkam", "perumbakkam", "hyderabad", "secunderabad", "somajiguda",
            "banjara hills", "pune", "sassoon road", "station road", "kharadi",
            "kolkata", "kankurgachi", "anandapur", "ahmedabad", "thaltej",
            "jaipur", "jawahar circle", "kochi", "cheranalloor"
        ]
        detected_location: Optional[str] = None
        for loc in known_locations:
            if re.search(rf"\b{re.escape(loc)}\b", clean):
                if loc == "reva":
                    detected_location = "REVA University"
                else:
                    detected_location = loc.title()
                break

        # If no explicit known location, inspect preposition patterns: "in <loc>", "near <loc>", "around <loc>"
        if not detected_location:
            prep_match = re.search(r"\b(?:in|near|around|at|close to|nearby)\s+([a-zA-Z\s]{2,25})\b", clean)
            if prep_match:
                cand = prep_match.group(1).strip()
                cand_clean = re.sub(r"\b(me|hospital|hospitals|clinic|clinics|center|centers|doctors|doctor|icu|availability|available)\b", "", cand).strip()
                if len(cand_clean) >= 3:
                    detected_location = cand_clean.title()

        # 4. Extract Hospital Brand Keyword
        known_brands = [
            "apollo", "fortis", "manipal", "narayana", "aster", "lilavati", "kokilaben",
            "tata memorial", "hinduja", "global", "max", "medanta", "miot", "gleneagles",
            "kims", "yashoda", "care", "ruby hall", "jehangir", "zydus", "eternal",
            "cytecare", "reva health", "st. jude", "st jude", "city general"
        ]
        detected_brand: Optional[str] = None
        for brand in known_brands:
            if re.search(rf"\b{re.escape(brand)}\b", clean):
                detected_brand = brand.title()
                break

        # 5. Extract Facility Requirements (e.g. ICU, Emergency, Cath Lab, Dialysis)
        detected_facilities: List[str] = []
        if re.search(r"\b(icu|intensive care|critical care|nicu|picu|micu)\b", clean):
            detected_facilities.append("ICU")
        if re.search(r"\b(cath lab|cardiac cath lab)\b", clean):
            detected_facilities.append("Cath Lab")
        if re.search(r"\b(dialysis|hemodialysis)\b", clean):
            detected_facilities.append("Dialysis")
        if re.search(r"\b(emergency|trauma|casualty|24/7)\b", clean):
            detected_facilities.append("Emergency Care")

        # 6. Extract Availability Requirement
        requires_availability = bool(re.search(r"\b(available|availability|open|vacant)\b", clean))

        # 7. Determine Search Strategy / Search Type
        if is_nearby:
            search_type = "nearby"
        elif detected_specialty and detected_location:
            search_type = "specialty_location"
        elif detected_location and not detected_brand:
            search_type = "location"
        elif detected_specialty and not detected_brand:
            search_type = "specialty"
        else:
            search_type = "keyword"

        return {
            "search_query": raw,
            "search_type": search_type,
            "is_nearby_search": is_nearby,
            "detected_location": detected_location,
            "detected_specialty": detected_specialty,
            "detected_keyword": detected_brand or raw,
            "detected_facilities": detected_facilities,
            "requires_availability": requires_availability,
            "has_coordinates": False,
        }

    @staticmethod
    def get_hospitals(
        db: Session,
        search: Optional[str] = None,
        location: Optional[str] = None,
        specialization: Optional[str] = None,
        insurance_accepted: Optional[str] = None,
        max_distance: Optional[float] = None,
        min_rating: Optional[float] = None,
        scheme: Optional[str] = None,
        is_available: Optional[bool] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
        page: Optional[int] = None,
        limit: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[float] = None,
    ) -> Tuple[List[Hospital], int, Dict[str, Any]]:
        """
        Retrieve hospitals using intelligent intent detection, location awareness,
        and optional Haversine geographic distance calculation.
        """
        intent = HospitalService.detect_search_intent(search)
        has_coords = (latitude is not None and longitude is not None)
        intent["has_coordinates"] = has_coords

        query = db.query(Hospital)

        # 1. Apply Search Strategy
        if search:
            stype = intent["search_type"]
            det_loc = intent.get("detected_location")
            det_spec = intent.get("detected_specialty")
            det_facs = intent.get("detected_facilities", [])
            req_avail = intent.get("requires_availability", False)

            if stype == "specialty_location" and det_loc and det_spec:
                # Combined Specialty + Location Filter
                loc_filter = or_(
                    Hospital.location.ilike(f"%{det_loc}%"),
                    Hospital.name.ilike(f"%{det_loc}%")
                )
                query = query.filter(
                    Hospital.specialization.ilike(f"%{det_spec}%"),
                    loc_filter
                )

            elif stype == "location" and det_loc:
                # Pure Location Search
                query = query.filter(
                    or_(
                        Hospital.location.ilike(f"%{det_loc}%"),
                        Hospital.name.ilike(f"%{det_loc}%")
                    )
                )

            elif stype == "specialty" and det_spec:
                # Pure Specialty Search
                query = query.filter(Hospital.specialization.ilike(f"%{det_spec}%"))

            elif stype == "nearby" and det_loc:
                # Nearby Location Search
                loc_tokens = [det_loc]
                if det_loc.lower() in ("reva university", "reva"):
                    loc_tokens.extend(["reva", "kattigenahalli", "yelahanka"])
                elif det_loc.lower() == "kattigenahalli":
                    loc_tokens.extend(["kattigenahalli", "yelahanka", "reva"])

                filters = []
                for tok in loc_tokens:
                    filters.extend([
                        Hospital.location.ilike(f"%{tok}%"),
                        Hospital.name.ilike(f"%{tok}%"),
                        Hospital.description.ilike(f"%{tok}%")
                    ])
                if det_spec:
                    query = query.filter(Hospital.specialization.ilike(f"%{det_spec}%"), or_(*filters))
                else:
                    query = query.filter(or_(*filters))

            else:
                # Normal Keyword Search with conversational noise stripping
                search_raw = search.strip()
                search_clean = search_raw.lower()
                fillers = [
                    r"\bnear\s+by\b", r"\bnearby\b", r"\bnear\s+to\b", r"\bnear\b",
                    r"\baround\b", r"\bclose\s+to\b", r"\bhospitals\s+in\b", r"\bhospital\s+in\b",
                    r"\bhospitals\s+near\b", r"\bhospital\s+near\b", r"\bhospitals\b", r"\bhospital\b",
                    r"\bclinics\b", r"\bclinic\b", r"\bcenters\b", r"\bcenter\b", r"\bbest\b",
                    r"\btop\b", r"\bfind\b", r"\bgood\b"
                ]
                core_query = search_clean
                for pat in fillers:
                    core_query = re.sub(pat, " ", core_query)
                core_query = " ".join(core_query.split()).strip()

                search_terms: Set[str] = {search_raw}
                if core_query and len(core_query) >= 2:
                    search_terms.add(core_query)
                    for word in core_query.split():
                        if len(word) >= 3:
                            search_terms.add(word)

                filters = []
                for term in search_terms:
                    t_pat = f"%{term}%"
                    filters.extend([
                        Hospital.name.ilike(t_pat),
                        Hospital.location.ilike(t_pat),
                        Hospital.specialization.ilike(t_pat),
                        Hospital.schemes.ilike(t_pat),
                        Hospital.facilities.ilike(t_pat),
                        Hospital.description.ilike(t_pat),
                    ])

                for keyword, specialties in ILLNESS_SPECIALTY_MAP.items():
                    if keyword in search_clean or (core_query and keyword in core_query):
                        for spec in specialties:
                            filters.append(Hospital.specialization.ilike(f"%{spec}%"))

                for keyword, specialties in DIAGNOSTIC_SPECIALTY_MAP.items():
                    if keyword in search_clean or (core_query and keyword in core_query):
                        for spec in specialties:
                            filters.append(Hospital.specialization.ilike(f"%{spec}%"))

                query = query.filter(or_(*filters))

            # Apply detected facility requirements (e.g. ICU)
            if "ICU" in det_facs:
                query = query.filter(
                    or_(
                        Hospital.facilities.ilike("%ICU%"),
                        Hospital.facilities.ilike("%Intensive Care%"),
                        Hospital.facilities.ilike("%Critical Care%"),
                        Hospital.facilities.ilike("%NICU%"),
                        Hospital.facilities.ilike("%PICU%"),
                        Hospital.facilities.ilike("%MICU%"),
                        Hospital.description.ilike("%ICU%"),
                        Hospital.description.ilike("%Intensive Care%"),
                        Hospital.description.ilike("%Critical Care%"),
                    )
                )

            # Apply availability if requested in query
            if req_avail:
                query = query.filter(Hospital.is_available == True)

        # 2. Additional Explicit Filters (safely ignoring 'All' / empty values)
        if location and location.strip() and location.strip().lower() not in ("all", "all locations", ""):
            clean_loc = location.strip()
            query = query.filter(
                or_(
                    Hospital.location.ilike(f"%{clean_loc}%"),
                    Hospital.name.ilike(f"%{clean_loc}%")
                )
            )

        if specialization and specialization.strip() and specialization.strip().lower() not in ("all", "all specializations", ""):
            clean_spec = specialization.strip()
            query = query.filter(Hospital.specialization.ilike(f"%{clean_spec}%"))

        if insurance_accepted and insurance_accepted.strip() and insurance_accepted.strip().lower() not in ("all", "all insurances", ""):
            clean_ins = insurance_accepted.strip()
            query = query.filter(Hospital.insurance_accepted.ilike(f"%{clean_ins}%"))

        if min_rating is not None and min_rating > 0:
            query = query.filter(Hospital.rating >= min_rating)

        if scheme and scheme.strip() and scheme.strip().lower() not in ("all", "all schemes", ""):
            clean_scheme = scheme.strip()
            query = query.filter(Hospital.schemes.ilike(f"%{clean_scheme}%"))

        if is_available is not None:
            query = query.filter(Hospital.is_available == is_available)

        # 3. Handle GPS Distance Calculation (Haversine)
        if has_coords:
            effective_radius = radius if radius is not None else max_distance
            all_candidates = query.all()
            with_distance: List[Tuple[Hospital, float]] = []
            without_distance: List[Hospital] = []

            for h in all_candidates:
                calc_dist = haversine_distance(latitude, longitude, h.latitude, h.longitude) if (h.latitude is not None and h.longitude is not None) else None
                if calc_dist is not None:
                    setattr(h, "distance_km", calc_dist)
                    if effective_radius is None or effective_radius <= 0 or calc_dist <= effective_radius:
                        with_distance.append((h, calc_dist))
                else:
                    setattr(h, "distance_km", None)
                    # If no explicit radius filter is enforced, keep hospitals with unlisted coordinates
                    if effective_radius is None or effective_radius <= 0:
                        without_distance.append(h)

            # Sort by actual calculated distance ascending
            with_distance.sort(key=lambda x: x[1])
            sorted_items = [item[0] for item in with_distance] + without_distance
            total = len(sorted_items)

            if page is not None and limit is not None and page > 0 and limit > 0:
                start_idx = (page - 1) * limit
                paged_items = sorted_items[start_idx:start_idx + limit]
            else:
                paged_items = sorted_items

            return paged_items, total, intent

        # 4. Standard Database Sorting when coordinates are unavailable (DO NOT filter by distance)
        if sort_by == "rating":
            query = query.order_by(desc(Hospital.rating) if sort_order == "desc" else asc(Hospital.rating))
        elif sort_by == "distance":
            query = query.order_by(asc(Hospital.distance) if sort_order == "asc" else desc(Hospital.distance))
        elif sort_by == "name":
            query = query.order_by(asc(Hospital.name) if sort_order == "asc" else desc(Hospital.name))
        else:
            query = query.order_by(desc(Hospital.rating))

        total = query.count()

        if page is not None and limit is not None and page > 0 and limit > 0:
            query = query.offset((page - 1) * limit).limit(limit)

        items = query.all()
        for h in items:
            setattr(h, "distance_km", None)

        return items, total, intent

    @staticmethod
    def search_hospitals(
        db: Session,
        query: Optional[str] = None,
        search: Optional[str] = None,
        location: Optional[str] = None,
        specialization: Optional[str] = None,
        insurance: Optional[str] = None,
        scheme: Optional[str] = None,
        min_rating: Optional[float] = None,
        is_available: Optional[bool] = None,
        page: int = 1,
        limit: int = 10,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[float] = None,
    ) -> Dict[str, Any]:
        search_term = query or search
        items, total, intent = HospitalService.get_hospitals(
            db=db,
            search=search_term,
            location=location,
            specialization=specialization,
            insurance_accepted=insurance,
            min_rating=min_rating,
            scheme=scheme,
            is_available=is_available,
            page=page,
            limit=limit,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
        )
        return {"items": items, "total": total, "intent": intent}

    @staticmethod
    def recommend_hospitals_for_patient_condition(
        db: Session,
        condition_analysis: Any,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location: Optional[str] = None,
        radius_km: Optional[float] = None,
        is_available: Optional[bool] = None,
        min_rating: Optional[float] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Ranks and recommends verified hospitals from the database driven strictly by
        the patient's detected medical condition, clinical specializations, location,
        and real Haversine geographic distance calculation.
        """
        # Handle dict or Pydantic object
        if isinstance(condition_analysis, dict):
            has_evidence = condition_analysis.get("has_sufficient_evidence", False)
            specialties = condition_analysis.get("recommended_specialties", [])
            primary_cond = condition_analysis.get("primary_condition")
            all_conds = condition_analysis.get("all_conditions", [])
            summary = condition_analysis.get("clinical_summary", "")
            requires_icu = condition_analysis.get("requires_icu_or_critical_care", False)
        else:
            has_evidence = getattr(condition_analysis, "has_sufficient_evidence", False)
            specialties = getattr(condition_analysis, "recommended_specialties", [])
            primary_cond = getattr(condition_analysis, "primary_condition", None)
            all_conds = getattr(condition_analysis, "all_conditions", [])
            summary = getattr(condition_analysis, "clinical_summary", "")
            requires_icu = getattr(condition_analysis, "requires_icu_or_critical_care", False)

        has_coords = (latitude is not None and longitude is not None)

        if not has_evidence or not specialties:
            return {
                "has_sufficient_evidence": False,
                "patient_condition": None,
                "all_conditions": [],
                "recommended_specialties": [],
                "requires_icu_or_critical_care": False,
                "clinical_summary": summary or "Insufficient clinical evidence in patient record to determine specific medical specialty requirements.",
                "hospitals": [],
                "total_found": 0,
                "applied_filters": {
                    "patient_location": location,
                    "coordinates": {"latitude": latitude, "longitude": longitude} if has_coords else None,
                    "radius_km": radius_km,
                    "specialties": [],
                }
            }

        # 1. Build Query for Specialization match
        spec_filters = [Hospital.specialization.ilike(f"%{spec}%") for spec in specialties]
        # Also include Multispeciality / Comprehensive healthcare centers for general conditions
        spec_filters.append(Hospital.specialization.ilike("%Multispeciality%"))
        spec_filters.append(Hospital.specialization.ilike("%Multi-speciality%"))
        spec_filters.append(Hospital.specialization.ilike("%Multispecialty%"))
        query = db.query(Hospital).filter(or_(*spec_filters))

        # 2. Location Filter (if specified)
        if location:
            query = query.filter(
                or_(
                    Hospital.location.ilike(f"%{location}%"),
                    Hospital.name.ilike(f"%{location}%")
                )
            )

        # 3. Real Availability Filter
        if is_available is not None:
            query = query.filter(Hospital.is_available == is_available)

        # 4. Rating Filter
        if min_rating is not None:
            query = query.filter(Hospital.rating >= min_rating)

        candidates = query.all()

        # 5. Process Candidates & Compute Real Haversine Distance
        matched_results: List[Dict[str, Any]] = []

        for h in candidates:
            dist_km: Optional[float] = None
            if has_coords and h.latitude is not None and h.longitude is not None:
                dist_km = haversine_distance(latitude, longitude, h.latitude, h.longitude)
                if radius_km is not None and dist_km is not None and dist_km > radius_km:
                    continue

            # Evaluate real ICU status from facilities & description
            fac_text = f"{h.facilities or ''} {h.description or ''}".lower()
            has_icu_facility = any(k in fac_text for k in ["icu", "intensive care", "critical care", "nicu", "picu", "micu"])

            if has_icu_facility:
                icu_status = "Available" if h.is_available else "Occupied / Unavailable"
            else:
                icu_status = "Unknown / Not Listed"

            # Match reasons
            reasons = [f"Specialized in {h.specialization}"]
            if dist_km is not None:
                reasons.append(f"{dist_km} km away from patient location")
            if has_icu_facility:
                reasons.append(f"ICU & Critical Care: {icu_status}")
            if h.rating >= 4.7:
                reasons.append(f"Top-rated medical institution ({h.rating} ★)")
            if h.schemes:
                reasons.append(f"Supports schemes: {h.schemes}")

            h_dict = {
                "id": h.id,
                "name": h.name,
                "location": h.location,
                "specialization": h.specialization,
                "rating": h.rating,
                "distance": h.distance,
                "distance_km": dist_km,
                "cost_range": h.cost_range,
                "schemes": h.schemes,
                "insurance_accepted": h.insurance_accepted,
                "is_available": h.is_available,
                "image_url": h.image_url,
                "facilities": h.facilities,
                "description": h.description,
                "phone": h.phone,
                "email": h.email,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "icu_status": icu_status,
                "is_verified": True,
                "match_reasons": reasons,
            }
            matched_results.append(h_dict)

        # 6. Rank Results: Nearest First if coordinates available, otherwise highest rating
        if has_coords:
            with_dist = [x for x in matched_results if x["distance_km"] is not None]
            no_dist = [x for x in matched_results if x["distance_km"] is None]
            with_dist.sort(key=lambda x: x["distance_km"])
            no_dist.sort(key=lambda x: x["rating"], reverse=True)
            ranked_hospitals = (with_dist + no_dist)[:limit]
        else:
            matched_results.sort(key=lambda x: (x["rating"], -(x["distance"] or 999)), reverse=True)
            ranked_hospitals = matched_results[:limit]

        # Convert primary_condition and all_conditions to dict if model
        primary_dict = primary_cond.model_dump() if hasattr(primary_cond, "model_dump") else primary_cond
        all_conds_dict = [c.model_dump() if hasattr(c, "model_dump") else c for c in all_conds]

        return {
            "has_sufficient_evidence": True,
            "patient_condition": primary_dict,
            "all_conditions": all_conds_dict,
            "recommended_specialties": specialties,
            "requires_icu_or_critical_care": requires_icu,
            "clinical_summary": summary,
            "hospitals": ranked_hospitals,
            "total_found": len(matched_results),
            "applied_filters": {
                "patient_location": location,
                "coordinates": {"latitude": latitude, "longitude": longitude} if has_coords else None,
                "radius_km": radius_km,
                "specialties": specialties,
                "is_available": is_available,
            }
        }
