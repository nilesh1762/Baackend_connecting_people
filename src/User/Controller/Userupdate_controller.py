from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.utils.db import init_db
from src.User.model import UserModel, UpdateUserProfile
from src.utils.security import get_current_user_id


from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import UserModel, UserEducationModel # Import both your models here

async def update_profile_controller(
    body: UpdateUserProfile, 
    db: Session, 
    current_user_id: int
):
    # 1. Fetch targeted user entry from Oracle
    user = db.query(UserModel).filter(UserModel.id == current_user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User profile not found."
        )

    # 2. Extract ONLY fields explicitly sent in request (skips omitted optional fields)
    update_data = body.model_dump(exclude_unset=True)
    print("edu==", update_data)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No patch field values provided."
        )

    # 3. Guardrail: If email is changing, ensure new email isn't already taken
    if "email" in update_data and update_data["email"] != user.email:
        email_check = db.query(UserModel).filter(UserModel.email == update_data["email"].lower()).first()
        if email_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="This email address is already tied to another account."
            )
        update_data["email"] = update_data["email"].lower()

    try:
        # 🟢 4. PROCESS NESTED EDUCATION RECORDS EXPLICITLY
        if "education" in update_data:
            education_list = update_data.pop("education") # Pull out array list to keep it away from setattr
            
            # Extract existing education record database IDs for comparison
            existing_edus = {edu.id: edu for edu in user.education}
            incoming_ids = []

            for edu_data in education_list:
                edu_id = edu_data.get("id") # Frontend sends 'id' for existing items, none for new ones
                
                if edu_id and edu_id in existing_edus:
                    # CASE A: RECORD EXISTS -> UPDATE IT
                    incoming_ids.append(edu_id)
                    existing_item = existing_edus[edu_id] 
                    for edu_key, edu_val in edu_data.items():
                        if edu_key != "id": # Do not overwrite primary identifier columns
                            setattr(existing_item, edu_key, edu_val)
                else:
                    # CASE B: NEW RECORD -> INITIALIZE AND APPEND IT
                    new_edu = UserEducationModel(
                        user_id=current_user_id,
                        institution_name=edu_data["institution_name"],
                        education_level=edu_data["education_level"],
                        degree_title=edu_data.get("degree_title"),
                        specialization=edu_data.get("specialization"),
                        start_date=edu_data["start_date"],
                        end_date=edu_data.get("end_date"),
                        grade_or_gpa=edu_data.get("grade_or_gpa")
                    )
                    db.add(new_edu) # Registers the sub-record with your session driver

            # CASE C: DELETION GUARD (Optional)
            # If an item exists in the DB but is missing from the incoming frontend payload array list,
            # it means the user hit the delete button. Remove it automatically:
            for old_id, old_obj in existing_edus.items():
                if old_id not in incoming_ids and incoming_ids: # Safety threshold check
                    db.delete(old_obj)

        # 5. Process remaining standard text/date column attributes automatically
        for key, value in update_data.items():
            setattr(user, key, value)

        # 6. Save the transaction straight into Oracle
        db.commit()
        db.refresh(user)

    except Exception as db_err:
        db.rollback()
        print(f"Database Error during dynamic profile modification: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database profile details."
        )

    return user

