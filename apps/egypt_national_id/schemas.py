# Create your schemas here.

from fastapi import HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date
from enum import Enum
import re
from core.logger import logger


# Enums
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class GovernorateCode(str, Enum):
    CAIRO = "01"
    ALEXANDRIA = "02"
    PORT_SAID = "03"
    SUEZ = "04"
    DAMIETTA = "11"
    DAKAHLIA = "12"
    SHARQIA = "13"
    QALYUBIA = "14"
    KAFR_EL_SHEIKH = "15"
    GHARBIA = "16"
    MENOUFIA = "17"
    BEHEIRA = "18"
    ISMAILIA = "19"
    GIZA = "21"
    BENI_SUEF = "22"
    FAYOUM = "23"
    MINYA = "24"
    ASYUT = "25"
    SOHAG = "26"
    QENA = "27"
    ASWAN = "28"
    LUXOR = "29"
    RED_SEA = "31"
    NEW_VALLEY = "32"
    MATROUH = "33"
    NORTH_SINAI = "34"
    SOUTH_SINAI = "35"
    OUTSIDE_EGYPT = "88"


# Governorate mapping
GOVERNORATE_NAMES = {
    "01": "Cairo",
    "02": "Alexandria",
    "03": "Port Said",
    "04": "Suez",
    "11": "Damietta",
    "12": "Dakahlia",
    "13": "Sharqia",
    "14": "Qalyubia",
    "15": "Kafr El-Sheikh",
    "16": "Gharbia",
    "17": "Menoufia",
    "18": "Beheira",
    "19": "Ismailia",
    "21": "Giza",
    "22": "Beni Suef",
    "23": "Fayoum",
    "24": "Minya",
    "25": "Asyut",
    "26": "Sohag",
    "27": "Qena",
    "28": "Aswan",
    "29": "Luxor",
    "31": "Red Sea",
    "32": "New Valley",
    "33": "Matrouh",
    "34": "North Sinai",
    "35": "South Sinai",
    "88": "Outside Egypt"
}


# Request Models
class NationalIDRequest(BaseModel):
    """Request model for national ID validation/extraction"""
    national_id: str = Field(
        ...,
        description="Egyptian National ID (14 digits)",
        example="29501011234567"
    )

    @validator('national_id')
    def validate_id_format(cls, v):
        """Validate basic format"""
        v = v.strip()
        if not re.match(r'^\d{14}$', v):
            raise ValueError("National ID must be exactly 14 digits")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "29501011234567"
            }
        }


class BulkNationalIDRequest(BaseModel):
    """Request model for bulk validation"""
    national_ids: list[str] = Field(
        ...,
        description="List of Egyptian National IDs",
        max_length=100
    )

    @validator('national_ids')
    def validate_bulk_size(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 IDs per request")
        return v


# Response Models
class DateOfBirth(BaseModel):
    """Date of birth information"""
    full_date: date
    year: int
    month: int
    day: int
    age: int


class Location(BaseModel):
    """Birth location information"""
    governorate_code: str
    governorate_name: str


class NationalIDData(BaseModel):
    """Extracted national ID data"""
    national_id: str
    is_valid: bool
    date_of_birth: Optional[DateOfBirth] = None
    gender: Optional[Gender] = None
    location: Optional[Location] = None
    sequence_number: Optional[str] = None
    century: Optional[int] = None
    errors: list[str] = Field(default_factory=list)


class ValidationResponse(BaseModel):
    """API response for single validation"""
    success: bool
    data: NationalIDData
    message: str


class BulkValidationResponse(BaseModel):
    """API response for bulk validation"""
    success: bool
    total: int
    valid_count: int
    invalid_count: int
    results: list[NationalIDData]



# Core Validator Class
class EgyptianNationalIDValidator:
    """Egyptian National ID validator and data extractor"""

    @staticmethod
    def extract_century(national_id: str) -> int:
        """Extract century from first digit"""
        first_digit = int(national_id[0])
        if first_digit == 2:
            return 1900
        elif first_digit == 3:
            return 2000
        else:
            raise ValueError(f"Invalid century indicator: {first_digit}")

    @staticmethod
    def extract_date_of_birth(national_id: str) -> DateOfBirth:
        """Extract and validate date of birth"""
        try:
            century = EgyptianNationalIDValidator.extract_century(national_id)
            year = century + int(national_id[1:3])
            month = int(national_id[3:5])
            day = int(national_id[5:7])

            # Validate date
            birth_date = date(year, month, day)

            # Calculate age
            today = date.today()
            age = today.year - birth_date.year - (
                    (today.month, today.day) < (birth_date.month, birth_date.day)
            )

            return DateOfBirth(
                full_date=birth_date,
                year=year,
                month=month,
                day=day,
                age=age
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date of birth: {str(e)}")

    @staticmethod
    def extract_governorate(national_id: str) -> Location:
        """Extract governorate information"""
        gov_code = national_id[7:9]

        if gov_code not in GOVERNORATE_NAMES:
            raise ValueError(f"Invalid governorate code: {gov_code}")

        return Location(
            governorate_code=gov_code,
            governorate_name=GOVERNORATE_NAMES[gov_code]
        )

    @staticmethod
    def extract_gender(national_id: str) -> Gender:
        """Extract gender from sequence number"""
        sequence = int(national_id[9:13])
        return Gender.MALE if sequence % 2 == 1 else Gender.FEMALE

    @staticmethod
    def validate_checksum(national_id: str) -> bool:
        """
        Validate checksum (last digit)
        Note: The actual Egyptian ID checksum algorithm may vary
        This is a placeholder for demonstration
        """
        # Implement actual checksum validation if known
        # For now, we'll return True as the algorithm isn't publicly documented
        return True

    @classmethod
    def validate_and_extract(cls, national_id: str) -> NationalIDData:
        """Main validation and extraction method"""
        errors = []
        data = NationalIDData(
            national_id=national_id,
            is_valid=False
        )

        try:
            # Extract date of birth
            try:
                data.date_of_birth = cls.extract_date_of_birth(national_id)

                # Additional date validations
                if data.date_of_birth.full_date > date.today():
                    errors.append("Birth date cannot be in the future")

                if data.date_of_birth.age > 150:
                    errors.append("Age exceeds reasonable limit")

            except ValueError as e:
                errors.append(str(e))

            # Extract governorate
            try:
                data.location = cls.extract_governorate(national_id)
            except ValueError as e:
                errors.append(str(e))

            # Extract gender
            try:
                data.gender = cls.extract_gender(national_id)
            except Exception as e:
                errors.append(f"Failed to extract gender: {str(e)}")

            # Extract sequence and century
            try:
                data.sequence_number = national_id[9:13]
                data.century = cls.extract_century(national_id)
            except Exception as e:
                errors.append(f"Failed to extract metadata: {str(e)}")

            # Validate checksum
            if not cls.validate_checksum(national_id):
                errors.append("Invalid checksum")

            # Set validity
            data.is_valid = len(errors) == 0
            data.errors = errors

        except Exception as e:
            logger.error(f"Unexpected error validating ID {national_id}: {str(e)}")
            data.errors = [f"Validation error: {str(e)}"]

        return data

