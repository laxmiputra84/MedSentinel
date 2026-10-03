from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.models.hospital import Hospital
from app.core.constants import ILLNESS_SPECIALTY_MAP, DIAGNOSTIC_SPECIALTY_MAP

class HospitalService:
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
        sort_by: Optional[str] = None, # rating, distance, name
        sort_order: Optional[str] = "desc",
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Tuple[List[Hospital], int]:
        query = db.query(Hospital)

        if search:
            search_clean = search.strip().lower()
            filters = [
                Hospital.name.ilike(f"%{search}%"),
                Hospital.location.ilike(f"%{search}%"),
                Hospital.specialization.ilike(f"%{search}%"),
                Hospital.schemes.ilike(f"%{search}%"),
                Hospital.facilities.ilike(f"%{search}%"),
            ]

            # Semantic keyword mapping for illnesses
            for keyword, specialties in ILLNESS_SPECIALTY_MAP.items():
                if keyword in search_clean:
                    for specialty in specialties:
                        filters.append(Hospital.specialization.ilike(f"%{specialty}%"))

            # Semantic keyword mapping for diagnostics
            for keyword, specialties in DIAGNOSTIC_SPECIALTY_MAP.items():
                if keyword in search_clean:
                    for specialty in specialties:
                        filters.append(Hospital.specialization.ilike(f"%{specialty}%"))

            query = query.filter(or_(*filters))

        if location:
            query = query.filter(Hospital.location.ilike(f"%{location}%"))

        if specialization:
            query = query.filter(Hospital.specialization.ilike(f"%{specialization}%"))

        if insurance_accepted:
            query = query.filter(Hospital.insurance_accepted.ilike(f"%{insurance_accepted}%"))

        if max_distance is not None:
            query = query.filter(Hospital.distance <= max_distance)

        if min_rating is not None:
            query = query.filter(Hospital.rating >= min_rating)

        if scheme:
            query = query.filter(Hospital.schemes.ilike(f"%{scheme}%"))

        if is_available is not None:
            query = query.filter(Hospital.is_available == is_available)

        # Sorting
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

        return query.all(), total

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
    ) -> dict:
        search_term = query or search
        items, total = HospitalService.get_hospitals(
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
        )
        return {"items": items, "total": total}


