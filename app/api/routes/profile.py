"""User profile validation endpoint."""

from fastapi import APIRouter

from app.schemas.profile import ProfileRequest, ProfileValidationResponse

router = APIRouter()


@router.post("/profile/validate", response_model=ProfileValidationResponse)
def validate_profile(profile: ProfileRequest) -> ProfileValidationResponse:
    """Validate profile fields without saving them or making health claims."""
    return ProfileValidationResponse(
        valid=True,
        message="Profile details are valid.",
    )
