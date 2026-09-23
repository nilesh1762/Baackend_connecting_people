from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case, desc
from src.User.model import Friendship, FriendRequest, UserModel, RequestStatus

def get_advanced_friend_suggestions_controller(current_user_id: int, db: Session, limit: int = 10):
    """
    Suggests friends-of-friends or regional creators, returning the actual 
    objects of mutual friends they have in common while strictly filtering out
    pending, accepted, or rejected/dismissed profiles.
    """
    # =========================================================================
    # 🗄️ STEP 1: COMPILE EXCLUSION SUBQUERIES (Database Level)
    # =========================================================================
    # 1. Fetch direct friend IDs safely as a select statement
    friends_sub = db.query(Friendship.friend_id).filter(
        Friendship.user_id == current_user_id,
        Friendship.is_deleted == False
    ).subquery()
    friends_select = db.query(friends_sub.c.friend_id) # 🎯 Extracts the raw select statement

    # 2. Captures Pending requests AND Dismissed/Rejected recommendations cleanly
    interacted_sub = db.query(FriendRequest.sender_id).filter(
        FriendRequest.receiver_id == current_user_id,
        FriendRequest.status.in_([RequestStatus.PENDING, RequestStatus.REJECTED])
    ).subquery()
    interacted_user_ids = db.query(interacted_sub.c.sender_id)

    received_sub = db.query(FriendRequest.receiver_id).filter(
        FriendRequest.sender_id == current_user_id,
        FriendRequest.status.in_([RequestStatus.PENDING, RequestStatus.REJECTED])
    ).subquery()
    received_user_ids = db.query(received_sub.c.receiver_id)

    # Check if user has friends
    has_friends = db.query(Friendship.id).filter(
        Friendship.user_id == current_user_id, 
        Friendship.is_deleted == False
    ).first() is not None

    # =========================================================================
    # 🚀 SCENARIO A: MUTUAL FRIEND GRID LIST COMPILER (ESTABLISHED USERS)
    # =========================================================================
    if has_friends:
        direct_friend_ids = [r[0] for r in db.query(Friendship.friend_id).filter(
            Friendship.user_id == current_user_id, Friendship.is_deleted == False
        ).all()]

        suggestions = db.query(
            UserModel.id, UserModel.email, UserModel.firstname, UserModel.lastname, 
            UserModel.created_at, UserModel.profile_image_url
        ).join(
            Friendship, UserModel.id == Friendship.friend_id
        ).filter(
            Friendship.user_id.in_(friends_select),
            Friendship.is_deleted == False,
            UserModel.id != current_user_id,
            ~UserModel.id.in_(friends_select),
            ~UserModel.id.in_(interacted_user_ids),
            ~UserModel.id.in_(received_user_ids)
        ).group_by(
            UserModel.id, UserModel.email, UserModel.firstname, UserModel.lastname, 
            UserModel.created_at, UserModel.profile_image_url
        ).limit(limit).all()

        if not suggestions:
            return []

        suggested_user_ids = [row.id for row in suggestions]

        bridges = db.query(Friendship.user_id, Friendship.friend_id).filter(
            Friendship.user_id.in_(direct_friend_ids),
            Friendship.friend_id.in_(suggested_user_ids),
            Friendship.is_deleted == False
        ).all()

        mutual_friend_details = {
            u.id: {"id": u.id, "firstname": u.firstname, "lastname": u.lastname, "profile_image_url": u.profile_image_url}
            for u in db.query(UserModel).filter(UserModel.id.in_(direct_friend_ids)).all()
        }

        mutual_mapping = {uid: [] for uid in suggested_user_ids}
        for bridge_friend_id, bridge_suggested_id in bridges:
            if bridge_friend_id in mutual_friend_details:
                mutual_mapping[bridge_suggested_id].append(mutual_friend_details[bridge_friend_id])

        return [
            {
                "user": {
                    "id": row.id, "email": row.email, "firstName": row.firstname, 
                    "lastName": row.lastname, "created_at": row.created_at,
                    "profile_image_url": row.profile_image_url or "https://cloudinary.com"
                },
                "mutualFriends": mutual_mapping[row.id]
            } for row in suggestions
        ]

    # =========================================================================
    # 🚀 SCENARIO B: REGIONAL FALLBACK ENGINE (COLD START / NEW USERS)
    # =========================================================================
    else:
        current_user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
        if not current_user:
            return []

        # 🌟 FIXED: Added case-insensitivity handling to catch mismatched city strings safely
        match_score = case(
            ((UserModel.localization == current_user.localization) & (UserModel.profile_category == current_user.profile_category), 5),
            (UserModel.localization == current_user.localization, 4),
            ((func.lower(func.trim(UserModel.city)) == func.lower(func.trim(current_user.city))) & 
             (UserModel.profile_category == current_user.profile_category), 3),
            (func.lower(func.trim(UserModel.city)) == func.lower(func.trim(current_user.city)), 2),
            (UserModel.profile_category == current_user.profile_category, 1),
            else_=0
        ).label("match_score")

        suggestions = db.query(UserModel, match_score).filter(
            UserModel.id != current_user_id,
            UserModel.is_active == True,
            ~UserModel.id.in_(friends_select),
            ~UserModel.id.in_(interacted_user_ids),
            ~UserModel.id.in_(received_user_ids)
        ).order_by(match_score.desc(), UserModel.id.desc()).limit(limit).all()


        # 🌟 FIXED: Tuple iteration variable names corrected to map data safely
        return [
            {
                "user": {
                    "id": user_obj.id, "email": user_obj.email, "firstName": user_obj.firstname, 
                    "lastName": user_obj.lastname, "created_at": user_obj.created_at,
                    "profile_image_url": user_obj.profile_image_url or "https://cloudinary.com"
                },
                "mutualFriends": [] 
            } for user_obj, score in suggestions if score > 0
        ]
