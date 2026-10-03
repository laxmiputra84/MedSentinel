from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.hospital_service import HospitalService
from app.models.hospital_image import HospitalImage

class HospitalAgent:
    """
    Handles hospital inquiries combining verified database records, facility media, and hospital-scoped RAG.
    """
    @staticmethod
    async def get_hospital_data(
        query: str,
        db: Session,
        location: Optional[str] = None,
        specialization: Optional[str] = None
    ) -> Dict[str, Any]:
        res = HospitalService.search_hospitals(
            db=db,
            search=query if not location and not specialization else None,
            location=location,
            specialization=specialization,
            limit=5
        )
        hospital_items = res.get("items", []) if isinstance(res, dict) else res

        hosp_list = []
        for h in hospital_items:
            # Fetch approved gallery and facility media
            images = db.query(HospitalImage).filter(
                HospitalImage.hospital_id == h.id,
                HospitalImage.is_active == True,
                HospitalImage.is_approved_by_admin == True
            ).all()

            hosp_list.append({
                "id": h.id,
                "name": h.name,
                "location": h.location,
                "specialization": h.specialization,
                "rating": h.rating,
                "facilities": h.facilities,
                "cost_range": h.cost_range,
                "phone": h.phone,
                "image_count": len(images)
            })

        return {
            "hospitals": hosp_list,
            "count": len(hosp_list)
        }
