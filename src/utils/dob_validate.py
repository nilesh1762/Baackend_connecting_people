# Path: src/utils/dob_validator.py
from datetime import date

def convert_dict_to_date(dob_dict) -> date:
    """
    Converts an incoming dictionary layout {"birthYear": "2011", ...} 
    into a standardized Python date object.
    """
    if isinstance(dob_dict, dict):
        try:
            return date(
                year=int(dob_dict["birthYear"]),
                month=int(dob_dict["birthMonth"]),
                day=int(dob_dict["birthDay"])
            )
        except (KeyError, ValueError, TypeError) as err:
            raise ValueError(f"Invalid date dictionary keys or values provided: {err}")
    
    # If it is already a date object, return it directly
    if isinstance(dob_dict, date):
        return dob_dict
        
    raise ValueError("Input must be a valid dictionary or a date object.")


def convert_date_to_dict(date_obj: date) -> dict | None:
    """
    Converts a standard database Date column value into 
    the frontend schema dictionary layout.
    """
    if date_obj is None:
        return None
    return {
        "birthYear": str(date_obj.year),
        "birthMonth": f"{date_obj.month:02d}",
        "birthDay": f"{date_obj.day:02d}"
    }
