from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.User.model import Friendship, UserModel
from src.User.Schema.friend_list_Schema import FriendProfileResponse, MutualFriendDetail
from src.User.Controller.WebSocketController.WebSocketPresenceController import presence_controller

def get_friends_list_controller(
    limit: int,
    offset: int,
    db: Session,
    current_user_id: int
) -> list[FriendProfileResponse]:
    """Handles business logic for retrieving a user's active friend list with full mutual profile arrays."""
    
    # 1. Fetch the friendship rows along with the user profiles
    direct_friends_raw = db.query(
        UserModel.id,
        UserModel.firstname,
        UserModel.email,
        UserModel.profile_image_url,
        UserModel.is_online,
        UserModel.status_presence,
        Friendship.created_at
    ).join(
        Friendship, UserModel.id == Friendship.friend_id
    ).filter(
        Friendship.user_id == current_user_id,
        Friendship.is_deleted == False
    ).all()
    
    # Early exit: If no friends exist, return empty array immediately
    if not direct_friends_raw:
        return []

    # Extract the numerical IDs of your direct friends
    direct_friend_ids = [row.id for row in direct_friends_raw]

    # =========================================================================
    # 🚀 ENTERPRISE BRIDGE FETCHING (Finds who bridges which friend)
    # =========================================================================
    # 2. Find rows where a friend of yours is also friends with another friend of yours
    bridges_raw = db.query(
        Friendship.user_id.label("friend_id"),      # The friend you are browsing
        Friendship.friend_id.label("mutual_id")     # The shared connection ID
    ).filter(
        Friendship.user_id.in_(direct_friend_ids),
        Friendship.friend_id.in_(direct_friend_ids),
        Friendship.friend_id != current_user_id,
        Friendship.is_deleted == False
    ).all()

    # Gather every unique mutual friend ID across the entire batch list
    all_mutual_ids = list(set([row.mutual_id for row in bridges_raw]))

    # 3. ⚡ BATCH FETCH PROFILES: One single trip to get all mutual friend details
    mutual_profiles_dict = {}
    if all_mutual_ids:
        # Adjust 'localization' if your model uses a different property name like 'place' or 'location'
        mutual_users_raw = db.query(
            UserModel.id, UserModel.firstname, UserModel.profile_image_url, UserModel.localization
        ).filter(
            UserModel.id.in_(all_mutual_ids)
        ).all()
        
        # Save into a fast-lookup dict map
        mutual_profiles_dict = {
            u.id: {
                "id": u.id,
                "firstname": u.firstname,
                "profile_image_url": u.profile_image_url or "",
                "localization": u.localization or "Unknown"
            } for u in mutual_users_raw
        }

    # 4. Map the bridges into a relational dictionary grouping: { friend_id: [ mutual_profile_objects ] }
    mutual_mapping = {fid: [] for fid in direct_friend_ids}
    for row in bridges_raw:
        if row.mutual_id in mutual_profiles_dict:
            mutual_mapping[row.friend_id].append(mutual_profiles_dict[row.mutual_id])

    # =========================================================================
    # 📝 MAP RESULTS INTO FINAL OUTPUT SCHEMAS
    # =========================================================================
    friends_list = [
        FriendProfileResponse(
            friend_id=row.id,
            firstname=row.firstname,
            email=row.email,
            profile_image_url=row.profile_image_url or "",
            friends_since=row.created_at,
            is_online=row.id in presence_controller.active_connections or bool(row.is_online),
            status_presence="online" if row.id in presence_controller.active_connections else (row.status_presence or "offline"),
            
            # Extract calculations from our mapping table dictionaries natively
            mutual_friends_count=len(mutual_mapping.get(row.id, [])),
            mutual_friends=[
                MutualFriendDetail(
                    id=m["id"],
                    firstname=m["firstname"],
                    profile_image_url=m["profile_image_url"],
                    localization=m["localization"]
                ) for m in mutual_mapping.get(row.id, [])
            ]
        )
        for row in direct_friends_raw
    ]

    # 5. Sort by highest mutual friend count first
    friends_list.sort(key=lambda x: x.mutual_friends_count, reverse=True)
    
    # 6. Apply pagination constraints via list slicing
    paginated_friends = friends_list[offset : offset + limit]
    
    return paginated_friends
