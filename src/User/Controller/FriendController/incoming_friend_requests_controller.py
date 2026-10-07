from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.User.model import FriendRequest, Friendship, UserModel, RequestStatus  # Adjust paths to match your project

def get_incoming_friend_requests_controller(current_user_id: int, db: Session):
    """
    Fetches all pending incoming friend requests for the logged-in user, 
    calculating mutual friend counts and packing their actual profile objects.
    """
    # 1. 🔍 Fetch rows where current_user_id is the receiver and status is PENDING
    incoming_records = db.query(FriendRequest, UserModel).join(
        UserModel, FriendRequest.sender_id == UserModel.id
    ).filter(
        (FriendRequest.receiver_id == current_user_id) &
        (FriendRequest.status == RequestStatus.PENDING)
    ).order_by(FriendRequest.created_at.desc()).all()

    # If there are no incoming requests, return early to save compute power
    if not incoming_records:
        return []

    # 2. 🗄️ Compile a list of the Current User's active direct friend IDs
    current_user_friend_ids = [
        r[0] for r in db.query(Friendship.friend_id).filter(
            Friendship.user_id == current_user_id,
            Friendship.is_deleted == False
        ).all()
    ]

    response_payload = []

    # 3. 🔄 Loop over requests to calculate mutual friends dynamically per sender
    for req, sender in incoming_records:
        sender_id = sender.id

        # Compile a list of the Sender's active direct friend IDs
        sender_friend_ids = [
            r[0] for r in db.query(Friendship.friend_id).filter(
                Friendship.user_id == sender_id,
                Friendship.is_deleted == False
            ).all()
        ]

        # Find the intersection of both ID lists (the mutual friend IDs)
        mutual_ids = list(set(current_user_friend_ids).intersection(set(sender_friend_ids)))

        mutual_friends_list = []
        if mutual_ids:
            # 🚀 BATCH FETCH: Grab all mutual profiles in one clean trip
            mutual_profiles = db.query(UserModel).filter(
                UserModel.id.in_(mutual_ids)
            ).all()

            # Format the mutual friend profiles to match your UI's expected schema
            for m_user in mutual_profiles:
                mutual_friends_list.append({
                    "id": m_user.id,
                    "firstname": m_user.firstname,
                    "lastname": m_user.lastname,
                    "profile_image_url": m_user.profile_image_url or "https://cloudinary.com"
                })

        # 📦 Append data to your primary payload array
        response_payload.append({
            "id": req.id,                     # 🆔 Friend Request Row Primary Key ID
            "created_at": req.created_at,     # ⏰ Timestamp record
            "sender": {                       # 👤 Sender details
                "id": sender.id,
                "email": sender.email,
                "firstname": sender.firstname,
                "lastname": sender.lastname,
                "profile_image_url": sender.profile_image_url or "https://cloudinary.com"
            },
            "mutual_friends_count": len(mutual_friends_list), # 🔢 Calculated count
            "mutual_friends": mutual_friends_list             # 🟢 Actual array of mutual friend objects!
        })

    return response_payload
