from fastapi import APIRouter
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, os
from datetime import datetime, UTC

from starlette import status

from apps.egypt_national_id.schemas import ValidationResponse, NationalIDRequest, EgyptianNationalIDValidator
from core.logger import logger
from core.middlewares import rate_limit_dependency
from core.security import verify_service_key

router = APIRouter(
    prefix="/nid-egypt",
    tags=["Egypt National Id"]
)



@router.post(
    "/",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_nid(
    request: NationalIDRequest,
    payload: dict = Depends(verify_service_key),
    _: None = Depends(rate_limit_dependency)
):
    """
    Validate an Egyptian National ID and extract all available data.

    - **national_id**: 14-digit Egyptian National ID number

    Returns detailed information including:
    - Date of birth
    - Gender
    - Birth governorate
    - Validity status
    """
    try:
        logger.info(f"Validating ID: {request.national_id}")

        data = EgyptianNationalIDValidator.validate_and_extract(request.national_id)

        return ValidationResponse(
            success=True,
            data=data,
            message="Validation completed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
