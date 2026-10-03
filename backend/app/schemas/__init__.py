from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    MessageResponse,
)
from app.schemas.user import UserBase, UserUpdate, UserResponse
from app.schemas.hospital import HospitalBase, HospitalResponse, HospitalPaginatedResponse, SavedHospitalCreate
from app.schemas.scheme import SchemeBase, SchemeResponse
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    SchemeEligibilityItem,
    EligibilityRecommendationRequest,
    EligibilityRecommendationResponse,
    SchemeRecommendationItem,
    IneligibleSchemeItem,
    InsuranceEligibilityRequest,
    InsuranceEligibilityResponse,
    InsuranceEligibilityItem,
)
from app.schemas.insurance import (
    InsuranceBase,
    InsuranceResponse,
    UserInsuranceEnrollRequest,
    UserInsuranceResponse,
)
from app.schemas.claim import (
    InsuranceClaimCreate,
    InsuranceClaimResponse,
    ClaimStatusUpdateRequest,
    ClaimStatusHistoryResponse,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
    AppointmentStatusUpdateRequest,
    AvailableSlotResponse,
)
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentVerificationRequest,
)
from app.schemas.notification import NotificationResponse
from app.schemas.analytics import (
    PlatformAnalyticsResponse,
    HospitalAnalyticsResponse,
    InsuranceAnalyticsResponse,
)
from app.schemas.otp import SendOtpRequest, SendOtpResponse, VerifyOtpRequest, VerifyOtpResponse

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenRefreshRequest",
    "TokenResponse",
    "MessageResponse",
    "UserBase",
    "UserUpdate",
    "UserResponse",
    "HospitalBase",
    "HospitalResponse",
    "HospitalPaginatedResponse",
    "SavedHospitalCreate",
    "SchemeBase",
    "SchemeResponse",
    "EligibilityCheckRequest",
    "EligibilityCheckResponse",
    "SchemeEligibilityItem",
    "EligibilityRecommendationRequest",
    "EligibilityRecommendationResponse",
    "SchemeRecommendationItem",
    "IneligibleSchemeItem",
    "InsuranceEligibilityRequest",
    "InsuranceEligibilityResponse",
    "InsuranceEligibilityItem",
    "InsuranceBase",
    "InsuranceResponse",
    "UserInsuranceEnrollRequest",
    "UserInsuranceResponse",
    "InsuranceClaimCreate",
    "InsuranceClaimResponse",
    "ClaimStatusUpdateRequest",
    "ClaimStatusHistoryResponse",
    "AppointmentCreate",
    "AppointmentResponse",
    "AppointmentRescheduleRequest",
    "AppointmentCancelRequest",
    "AppointmentStatusUpdateRequest",
    "AvailableSlotResponse",
    "DocumentResponse",
    "DocumentUploadResponse",
    "DocumentVerificationRequest",
    "NotificationResponse",
    "PlatformAnalyticsResponse",
    "HospitalAnalyticsResponse",
    "InsuranceAnalyticsResponse",
    "SendOtpRequest",
    "SendOtpResponse",
    "VerifyOtpRequest",
    "VerifyOtpResponse",
]
