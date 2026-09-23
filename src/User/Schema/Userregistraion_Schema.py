from datetime import date, datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, ValidationInfo, field_serializer, field_validator, model_validator

from pydantic_core import PydanticCustomError 

from src.utils.phone_validate import clean_and_validate_mobile

class DateOfBirth(BaseModel):
    birthYear: str
    birthMonth: str
    birthDay: str

    @model_validator(mode='after')
    def validate_age_limits(self) -> 'DateOfBirth':
        """Validates that the parsed date falls within the 5 to 100 years age range."""
        try:
            # 1. Convert incoming string fragments into integers
            year = int(self.birthYear)
            month = int(self.birthMonth)
            day = int(self.birthDay)
            dob = date(year, month, day)
        except ValueError as e:
         raise PydanticCustomError("dateofbirth_error", "Invalid date or empty components provided")

        # 2. Get the exact date of registration (today)
        today = date.today()

        # 3. Calculate exact age accounting for leap years and months
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # 4. Enforce your age boundary constraints
        if age < 5:
            # <-- 3. Change this line
            raise PydanticCustomError("dateofbirth_error", "User must be at least 5 years old to register.")
        if age > 100:
            # <-- 4. Change this line
            raise PydanticCustomError("dateofbirth_error", "User age cannot exceed 100 years.")

        return self

# 1. Base schema containing shared attributes
class UserBase(BaseModel):
    firstname: str = Field(..., min_length=3, max_length=20)
    lastname: str = Field(..., min_length=3, max_length=20)
    email: EmailStr  # Automatically validates email format (e.g., user@domain.com)
    dateofbirth: DateOfBirth
    gender: str = Field(..., min_length=1, max_length=10)
    mobilenumber: str
    country: str

    @field_validator('email', mode='before')
    @classmethod
    def validate_email_custom(cls, value: str) -> str:
        # Check if blank first
        if value is None or str(value).strip() == "":
            raise PydanticCustomError("email_error", "email field cannot be blank or empty")
        
        # If it has content but lacks an @ sign, throw a clean custom error
        if "@" not in str(value):
            raise PydanticCustomError("email_error", "Please provide a valid email address with an '@' symbol")
            
        return str(value).strip()
    
    @field_validator('firstname', 'lastname', 'gender', 'country',  mode='before')
    @classmethod
    def validate_fields_not_empty(cls, value: str, info: ValidationInfo) -> str:
        """Validates that text fields are explicitly provided and not empty spaces."""
        
        if value is None or str(value).strip() == "":
            # info.field_name will now dynamically extract 'firstname', 'lastname', etc.
            error_key = f"{info.field_name}_error"
            raise PydanticCustomError(
                error_key,
                f"{info.field_name} field cannot be blank or empty"
            )
            
        return str(value).strip()
     # Validates mobile number format using regex
    @field_validator('mobilenumber')
    @classmethod
    def validate_mobile(cls, value: str) -> str:
         return clean_and_validate_mobile(value)

# 2. Schema used specifically for User Registration (Signup Input)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plain text password")
    confirmpassword: str = Field(..., min_length=8)
    
    main_focus: str = Field(default="PURPOSE")      # PURPOSE, LOVE, FAMILY, LONELINESS
    current_feeling: str = Field(default="PEACEFUL") # STRESSED, SEEKING, PEACEFUL, ENERGETIC
    my_interest: str = Field(default="READING")      # READING, BUSINESS, ART, NEIGHBORHOOD
    biggest_wish: str = Field(default="MIND_PEACE")

    @field_validator('password', 'confirmpassword', mode='before')
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        """Validates that the password is at least 8 characters long."""
        if len(value) < 8:
            raise PydanticCustomError(
                "password_error", 
                "Password should be least 8 characters "
            )
        return value

    # Validates that both passwords match before hitting the controller
    @model_validator(mode='after')
    def verify_passwords_match(self) -> 'UserCreate':
        if self.password != self.confirmpassword:
            raise PydanticCustomError("confirmpassword_error", "password and confirmpassword do not match")
        return self

class EducationItemResponse(BaseModel):
    id: int
    user_id: int
    institution_name: str
    education_level: str
    degree_title: Optional[str] = None
    specialization: Optional[str] = None
    start_date: date                # Renders cleanly as standard 'YYYY-MM-DD'
    end_date: Optional[date] = None # Leaving it None handles 'Present' / Ongoing statuses
    grade_or_gpa: Optional[str] = None

    class Config:
        from_attributes = True

# 3. Schema used for returning data safely back to the client (Output/Response)
class UserResponse(UserBase):
    id: int
    is_active: bool

    # Tells Pydantic to read data seamlessly from ORM models (like your SQLAlchemy UserModel)
    class Config:
        from_attributes = True    

class UserResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    
    # Simple Onboarding Configuration Metrics
    main_focus: str = Field(default="PURPOSE")     
    current_feeling: str = Field(default="PEACEFUL") 
    my_interest: str = Field(default="READING")     
    biggest_wish: str = Field(default="MIND_PEACE")   
    
    # Multimedia Assets Mapping Links
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_video_url: Optional[str] = None
    
    # Standard Structural Base Profile Metadata
    dateofbirth: DateOfBirth  # Assumes DateOfBirth Pydantic model is imported above
    gender: str
    mobilenumber: str
    is_active: bool
    created_at: datetime
    
    # Optional Extended Profile Fields 
    bio: Optional[str] = None
    localization: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    userrelationship: Optional[str] = None
    website_url: Optional[str] = None
    location_name: Optional[str] = None
    profile_category: Optional[str] = None
    
    # System Visibility Parameters
    is_online: bool = Field(default=True)
    
    # 🟢 FIXED: Unified to match your Oracle column string casing perfectly!
    # Outputs to React as camelCase 'statusPresence' smoothly using serialization_alias.
    status_presence: str = Field(
        default="offline", 
        serialization_alias="statusPresence", 
        validation_alias="status_presence"
    )
    
    # 🟢 FIXED: Kept ONLY the clean, structured list, removing the duplicate string line!
    education: List[EducationItemResponse] = []

    # Enforces strict automated mapping configurations from SQLAlchemy objects
    model_config = {
        "from_attributes": True,
        "populate_by_name": True # Lets you read and write variables safely by aliases strings
    }

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info):
        """Forces output to explicitly render both the date and time."""
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    
def format_datetime_to_string(v: any) -> str:
    """Pre-validator that guarantees the datetime safely converts into an ISO string format."""
    if isinstance(v, datetime):
        return v.strftime('%Y-%m-%dT%H:%M:%S')
    return str(v)
    
class AuthUser(BaseModel):

        # This configuration is required so Pydantic can read attributes from your UserModel
    model_config = ConfigDict(from_attributes=True)

    id: int
    firstname: str
    lastname: str
    email: EmailStr
    dateofbirth: DateOfBirth
    gender: str
    mobilenumber: str
    is_active: bool
    created_at: Annotated[str, BeforeValidator(format_datetime_to_string)]
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_video_url: Optional[str] = None
    userrelationship: Optional[str] = None
    website_url: Optional[str] = None
    location_name: Optional[str] = None
    profile_category: Optional[str] = None
    bio:  Optional[str] = None
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info):
        """Forces custom format without breaking internal string conversions."""
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        return dt   
