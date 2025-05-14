import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKETS = ["journal-media", "profile-pics"]

def create_bucket(bucket_name):
    """Create a bucket in Supabase Storage"""
    print(f"Creating bucket '{bucket_name}'...")
    
    url = f"{SUPABASE_URL}/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "name": bucket_name,
        "public": True
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"Bucket '{bucket_name}' created successfully!")
        return True
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"Bucket '{bucket_name}' already exists.")
        return True
    else:
        print(f"Failed to create bucket '{bucket_name}': {response.text}")
        return False

def main():
    """Set up Supabase storage buckets"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in your .env file")
        return
    
    print(f"Setting up Supabase storage at {SUPABASE_URL}...")
    
    for bucket in BUCKETS:
        create_bucket(bucket)
    
    print("\nSetup complete!")
    print("Make sure your Supabase storage security settings are configured properly.")
    print("For this app, profile-pics and journal-media buckets should have RLS policies that:")
    print("1. Allow authenticated users to upload files")
    print("2. Allow anonymous users to download files")

if __name__ == "__main__":
    main() 