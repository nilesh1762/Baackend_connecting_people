from typing import List, Dict, Any
# 🚀 CHANGE 1: Import 'or_', 'case', and 'func' for multi-field and location matching logic [1]
from sqlalchemy import or_, case, func 
from sqlalchemy.orm import Session
# 🚀 CHANGE 2: Import Friendship instead of FollowModel [1]
from src.User.model import UserModel, BlockList, Friendship 
from cachetools import TTLCache 

DEFAULT_AVATAR_URL = "https://your-cdn-domain.com"
search_memory_cache = TTLCache(maxsize=500, ttl=60)


def search_users_by_username_controller(
    db: Session, 
    query_string: str, 
    current_user_id: int
) -> List[Dict[str, Any]]:
    """
    Executes a multi-field user search for autocomplete dropdowns.
    Prioritises accounts from the same city first, then the same country.
    Calculates dynamic mutual friend metrics strictly using the Friendship schema mapping.
    """
    print(f"[DEBUG CONTROLLER] received query_string: '{query_string}'")
    
    # 1. Edge Case: If input is empty, return empty list instantly
    if not query_string or not query_string.strip():
        return []

    search_term = query_string.strip().lower()
    
    # CACHE CHECK
    cache_key = f"search:mutual:{current_user_id}:{search_term}"
    if cache_key in search_memory_cache:
        return search_memory_cache[cache_key]

    # Fetch current logged-in user's location profile to use as a ranking anchor
    current_user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    my_city = getattr(current_user, "city", None) or ""
    my_country = getattr(current_user, "country", None) or ""

    clean_query = f"%{search_term}%"

    # 2. Main Search Query Base Configuration
    query = (
        db.query(UserModel)
        .filter(UserModel.id != current_user_id)
    )

    # Upgrade single column match to multi-field OR logic (username OR first_name OR last_name) [1]
    query = query.filter(
        or_(
           
            UserModel.firstname.ilike(clean_query),
            UserModel.lastname.ilike(clean_query)
        )
    )

    # Filter out accounts blocked by current user
    query = query.filter(
        ~db.query(BlockList.id)
        .filter(BlockList.blocker_id == current_user_id, BlockList.blocked_id == UserModel.id)
        .exists()
    )

    # Filter out accounts who blocked the current user
    query = query.filter(
        ~db.query(BlockList.id)
        .filter(BlockList.blocked_id == current_user_id, BlockList.blocker_id == UserModel.id)
        .exists()
    )

    # Create a priority scoring weight scheme based on geographical proximity
    geo_ordering = case(
        (func.lower(UserModel.city) == my_city.lower(), 1),        # Same City -> Rank 1 (Top)
        (func.lower(UserModel.country) == my_country.lower(), 2),  # Same Country -> Rank 2 (Middle)
        else_=3                                                   # Different Location -> Rank 3 (Bottom)
    )

    matched_users = query.order_by(geo_ordering, UserModel.firstname.asc()).limit(10).all()
    
    # 🚀 CHANGE 3: Pull active friend IDs for the CURRENT logged-in user [1]
    # Uses list comprehension to maintain broad compatibility across SQLAlchemy versions [1]
    my_friends_set = set([
        row.friend_id for row in db.query(Friendship.friend_id).filter(
            Friendship.user_id == current_user_id,
            Friendship.is_deleted == False
        ).all()
    ])

    # 3. Format Response Payload
    results = []
    for user in matched_users:
        # 🚀 CHANGE 4: Pull active friend IDs for each MATCHED user item inside the loop [1]
        target_friends_set = set([
            row.friend_id for row in db.query(Friendship.friend_id).filter(
                Friendship.user_id == user.id,
                Friendship.is_deleted == False
            ).all()
        ])

        # 🚀 CHANGE 5: Run python set intersection to evaluate mutual friends count metrics [1]
        mutual_count = len(my_friends_set.intersection(target_friends_set))

        f_name = getattr(user, "first_name", "") or ""
        l_name = getattr(user, "last_name", "") or ""
        full_display_name = f"{f_name} {l_name}".strip() or getattr(user, "firstname", "User")
        user_location = f"{user.city}, {user.country}" if user.city and user.country else (user.country or user.city or "")

        results.append({
            "id": user.id,
            "firstname": getattr(user, "firstname", "Unknown User"),
            "display_name": full_display_name,  
            "location_context": user_location,  
            # 🚀 CHANGE 6: Expose the final mutual calculation to the response map object [1]
            "mutual_connections_count": mutual_count,
            "profile_image_url": user.profile_image_url if user.profile_image_url else DEFAULT_AVATAR_URL
        })

    # SAVE TO CACHE
    search_memory_cache[cache_key] = results

    return results
