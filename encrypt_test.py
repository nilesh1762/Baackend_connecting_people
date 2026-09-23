# encrypt_test.py
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Cipher import PKCS1_OAEP
# 🚀 CHANGE THIS to the exact plain text password you want to test!
PASSWORD_TO_TEST = "12345678" 

try:
    with open("public_key.pem", "r") as key_file:
        public_key = RSA.import_key(key_file.read())
    
    # 👇 Initialize OAEP instead of PKCS1_v1_5
    cipher = PKCS1_OAEP.new(public_key)
    
    encrypted_bytes = cipher.encrypt(PASSWORD_TO_TEST.encode("utf-8"))
    base64_ciphertext = base64.b64encode(encrypted_bytes).decode("utf-8")
    
    print("\n" + "="*60)
    print("📋 COPY THIS OAEP ENCRYPTED STRING FOR YOUR POSTMAN JSON BODY:")
    print("="*60)
    print(base64_ciphertext)
    print("="*60 + "\n")

except FileNotFoundError:
    print("🚨 Error: Ensure 'public_key.pem' file sits inside this exact same folder directory level!")
except Exception as e:
    print(f"🚨 Script execution failure: {str(e)}")
