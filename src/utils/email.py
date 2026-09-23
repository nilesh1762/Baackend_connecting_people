from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr

from typing import List



config = ConnectionConfig(
        MAIL_USERNAME = "kumarnile@gmail.com",
        MAIL_PASSWORD = "shpj sukw nrjv qrgt", 
        MAIL_FROM = "kumarnile@gmail.com",
        MAIL_PORT = 587,
        MAIL_SERVER = "smtp.gmail.com",
        MAIL_STARTTLS = True,
        MAIL_SSL_TLS= False,
        MAIL_FROM_NAME = "Coonecting User",
        VALIDATE_CERTS = True,
        USE_CREDENTIALS = True
    )

  
async def send_email(email: List[str], token: str):
    print("Sending email to:", email, token)
    # reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    reset_url = f"https://mailtrap.io/?token={token}"  # Replace with your actual token generation logic

    html_content = f"""
    <p>You requested a password reset. Click the link below to set a new password:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>This link will expire in 15 minutes.</p>
    """

    message = MessageSchema(
            subject="Coonecting people with FastAPI",
            recipients=email,
            body=html_content,
            subtype="html"
        )

    fm = FastMail(config)
    await fm.send_message(message)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Email has been sent"})