import re

import cloudinary.uploader
import os

# 1. Helper function to extract Cloudinary Public ID from a URL string
# Cloudinary requires the Public ID (filename without extension) to delete a file
def extract_cloudinary_public_id(url: str) -> str:
    if not url or "cloudinary.com" not in url:
        return None
    # Extracts the file name between the last slash and the file extension
    match = re.search(r"/([^/]+)\.[^/.]+$", url)
    return match.group(1) if match else None


# 2. Async Worker function to handle hard deleting the physical files
def clean_up_media_storage(media_url: str, thumbnail_url: str):
    print(f"Starting background hard-delete for: {media_url}")
    
    # --- Part A: Handle Cloudinary File Removals ---
    public_id = extract_cloudinary_public_id(media_url)
    if public_id:
        try:
            # Destroys the asset securely in your Cloudinary bucket
            cloudinary.uploader.destroy(public_id)
            print(f"Successfully deleted {public_id} from Cloudinary.")
        except Exception as e:
            print(f"Cloudinary deletion failed: {str(e)}")

    # Delete video thumbnail from Cloudinary if it exists
    thumb_id = extract_cloudinary_public_id(thumbnail_url)
    if thumb_id:
        try:
            cloudinary.uploader.destroy(thumb_id)
        except Exception:
            pass

    # --- Part B: Handle Local Storage File Removals ---
    # If you save files locally on your disk, delete them like this:
    if media_url and "static/uploads" in media_url:
        local_path = media_url.split("http://127.0.0")[-1]
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"Deleted local file from disk: {local_path}")