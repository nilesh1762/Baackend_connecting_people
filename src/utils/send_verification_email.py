from fastapi_mail import FastMail, MessageSchema, MessageType,ConnectionConfig
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, status

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

async def send_verification_email(email: str, activation_link: str, firstname: str):
    """
    Asynchronously builds and delivers a professional HTML account 
    activation email to the registered user's inbox.
    """
    print(f"Dispatching verification mail to: {email}")

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Welcome to our platform, {firstname}!</h2>
            <p>Thank you for creating an account. Please click the button below to verify your email address and activate your profile details:</p>
            <p style="margin: 30px 0;">
                <a href="{activation_link}" style="background-color: #4CAF50; color: white; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block;">Verify My Account</a>
            </p>
            <p>This verification link will expire in exactly 15 minutes.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;" />
            <p style="font-size: 0.8em; color: #aaa;">If you did not perform this registration action, you can safely ignore this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Activate Your Account - FastAPI System",
        recipients=[email],  
        body=html_content,
        subtype="html"  # Swapping to plain text string removes package version runtime mismatches
    )

    # Use your central configuration instance variable
    fm = FastMail(config)
    await fm.send_message(message)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Email has been sent"})
