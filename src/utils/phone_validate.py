# Path: src/utils/phone_validator.py
import phonenumbers
from pydantic_core import PydanticCustomError 

def clean_and_validate_mobile(value: str) -> str:
    """
    Validates a phone number using Google's phonenumbers library and 
    returns it formatted in the standardized E.164 string format.
    """
   
    if value is None:
        raise PydanticCustomError("mobilenumber_error", "Mobile number cannot be null or empty.")
        
    # 1. Enforce international prefix style rule
    if not str(value).startswith('+'):
        raise PydanticCustomError(
            "mobilenumber_error",
            f"'{value}' must begin with a '+' country code prefix. "
            "Examples: +919876543210 (India), +14155552671 (US)"
        )
        
    try:
        # 2. Parse string digits using Google's global tracking directory
        parsed_number = phonenumbers.parse(value, None)
        
        # 3. Check if phone length is structurally possible for the target region
        if not phonenumbers.is_possible_number(parsed_number):
            raise PydanticCustomError(
                "mobilenumber_error",
                f"The length of phone number '{value}' is invalid."
            )
            
        # 4. Deep check digits matching exact country system formatting rules
        if not phonenumbers.is_valid_number(parsed_number):
            raise PydanticCustomError(
                "mobilenumber_error",
                f"'{value}' is not a valid operational number."
            )
        
        # 5. E.164 standardization cleans out spaces/dashes before saving to Oracle
        clean_db_string = phonenumbers.format_number(
            parsed_number, 
            phonenumbers.PhoneNumberFormat.E164
        )
        return clean_db_string

    except phonenumbers.NumberParseException:
        raise PydanticCustomError(
            "mobilenumber_error", 
            f"Failed to parse phone formatting rules for '{value}'."
        )
