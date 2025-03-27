import secrets
import base64

def generate_secret_key():
    """Generate a secure secret key for Flask."""
    # Generate 32 random bytes and convert to base64
    random_bytes = secrets.token_bytes(32)
    secret_key = base64.b64encode(random_bytes).decode('utf-8')
    return secret_key

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print("\nGenerated Secret Key:")
    print("====================")
    print(secret_key)
    print("\nAdd this to your .env file as:")
    print(f"FLASK_SECRET_KEY={secret_key}")
    print("\nWARNING: Keep this key secret! Never commit it to version control.") 