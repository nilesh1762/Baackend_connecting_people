# Baackend_connecting_people
A modern community-driven platform that makes it easy for individuals to connect, chat, and share experiences.

## Post media moderation

For now, image, GIF, and video posts are saved as `approved` and can appear in
feeds immediately. The moderation status column and moderator endpoints remain
available for a future review workflow; they do not automatically identify
nudity or other explicit content.

If manual moderation is enabled later, set `CONTENT_MODERATOR_USER_IDS` in the
app environment to a comma-separated allowlist of existing user IDs (for
example, `12,34`). Moderators can view pending posts at
`GET /user/moderation/posts/pending`, and approve or reject them at
`POST /user/moderation/posts/{post_id}/approve` or
`POST /user/moderation/posts/{post_id}/reject`. These endpoints require a
moderator's normal bearer token.

Apply the database migration before deploying the change:

```powershell
alembic upgrade head
```
