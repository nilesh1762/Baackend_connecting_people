from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class AuthorSchema(BaseModel):
    id: int
    name: str
    avatar: str

class EngagementSchema(BaseModel):
    likes_count: int
    has_liked: bool
    comments_count: int

class TextLayerSchema(BaseModel):
    body: Optional[str] = None

class MediaLayerSchema(BaseModel):
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    aspect_ratio: str

class QuoteLayerSchema(BaseModel):
    text: Optional[str] = None
    author: str

class ComponentLayersSchema(BaseModel):
    text_layer: TextLayerSchema
    media_layer: Optional[MediaLayerSchema] = None
    quote_layer: Optional[QuoteLayerSchema] = None


class CommentItemSchema(BaseModel):
    id: int
    text: Optional[str] = None
    media_url: Optional[str] = None
    gif_url: Optional[str] = None
    author_name: str
    author_avatar: Optional[str] = None
    created_at: datetime
    parent_comment_id: Optional[int] = None 
    author_id: int
    
    class Config:
        from_attributes = True

class FeedItemSchema(BaseModel):
    post_id: int
    layout_type: str
    score_weight: int
    created_at: datetime
    author: dict
    engagement: dict
    components: dict
    # 🎯 🌟 THE FIX: Inform Pydantic that a post houses an array of comment objects!
    comments: List[CommentItemSchema] 

class DashboardFeedResponseSchema(BaseModel):
    user_segment: str
    feed: List[FeedItemSchema]
    has_more: bool      # 🎯 TRUE if there are more matching items in the DB
    next_offset: int



        