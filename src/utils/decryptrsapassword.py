# app/utils/security.py
import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA1 # 🔴 CRITICAL IMPORT: Needed to match browser encryption hashes
from fastapi import HTTPException, status

def decrypt_rsa_password(encrypted_password_b64: str) -> str:
    try:
        # Calculate absolute file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        private_key_path = os.path.abspath(os.path.join(current_dir, "..", "..", "private_key.pem"))
        
        print(f"Cryptographic Node: Reading private key from absolute path: {private_key_path}")

        # 1. Read your genuine private key file
        with open(private_key_path, "r") as key_file:
            private_key = RSA.import_key(key_file.read())
        
        # 2. Decode incoming base64 ciphertext packet bytes
        encrypted_data = base64.b64decode(encrypted_password_b64)
        
        # 3. 🚀 THE CRITICAL BACKEND MATRIX FIX:
        # We explicitly inject hash=SHA1.new() into the OAEP initialization.
        # This gives your backend the exact same cryptographic key combination rules 
        # as the native browser Web Crypto framework!
        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA1)
        
        # 4. Decrypt the binary arrays natively
        decrypted_bytes = cipher.decrypt(encrypted_data)
            
        return decrypted_bytes.decode("utf-8")
        
    except Exception as e:
        print("\n=== 🚨 FASTAPI CRYPTO DEBUGGER ===")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {str(e)}")
        print(f"Incoming String Length: {len(encrypted_password_b64) if encrypted_password_b64 else 0} chars")
        print("===================================\n")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not securely process login payload. Communication channel corrupted."
        )
