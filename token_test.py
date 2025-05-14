import os
from jose import jwt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get secret key from environment variable
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def decode_token(token_string):
    print("Decoding token...")
    try:
        # Decode the token
        payload = jwt.decode(token_string, SECRET_KEY, algorithms=[ALGORITHM])
        print("Token decoded successfully!")
        print("\nToken payload:")
        for key, value in payload.items():
            print(f"  {key}: {value}")
        
        # Check for 'sub' field
        email = payload.get("sub")
        if email:
            print(f"\nUser email from token: {email}")
        else:
            print("\nWARNING: No 'sub' field found in token!")
        
        return payload
    except Exception as e:
        print(f"Error decoding token: {str(e)}")
        return None

if __name__ == "__main__":
    # Get token from user input
    token = input("Paste your JWT token: ").strip()
    if token:
        decode_token(token)
    else:
        print("No token provided.") 