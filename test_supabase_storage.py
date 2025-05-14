import os
import requests
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def test_list_buckets():
    """Test listing Supabase storage buckets"""
    print(f"Testing connection to Supabase storage at {SUPABASE_URL}...")
    print(f"Using key starting with: {SUPABASE_KEY[:20]}...")
    
    url = f"{SUPABASE_URL}/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Sending GET request to {url}")
        response = requests.get(url, headers=headers)
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            buckets = response.json()
            print(f"\n✅ Successfully connected to Supabase storage!")
            print(f"Found {len(buckets)} buckets:")
            for bucket in buckets:
                print(f"  - {bucket['name']} (public: {bucket['public']})")
            
            # Check for required buckets
            required_buckets = ["journal-media", "profile-pics"]
            missing_buckets = [b for b in required_buckets if not any(x['name'] == b for x in buckets)]
            
            if missing_buckets:
                print("\n⚠️ Warning: The following required buckets are missing:")
                for bucket in missing_buckets:
                    print(f"  - {bucket}")
                print("\nPlease create these buckets in the Supabase dashboard:")
                print("1. Go to your Supabase project dashboard")
                print("2. Navigate to Storage in the sidebar")
                print("3. Click 'New bucket' for each missing bucket")
                print("4. Make sure to set each bucket to public")
            else:
                print("\n✅ All required buckets exist!")
        else:
            print(f"\n❌ Failed to list buckets: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 403:
                print("\n🔑 Authentication issue detected!")
                print("Your current key may not have sufficient permissions.")
                print("Please follow the instructions in SUPABASE_KEYS.md to get the service_role key.")
                print("The service_role key provides more permissions and can bypass RLS policies.")
    
    except Exception as e:
        print(f"\n❌ Error connecting to Supabase: {str(e)}")

def test_upload_file():
    """Test uploading a file to Supabase storage"""
    bucket_name = "profile-pics"
    filename = f"test_{int(time.time())}.txt"
    content = b"This is a test file for Supabase storage."
    
    print(f"\nTesting file upload to '{bucket_name}' bucket...")
    
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{filename}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "text/plain"
    }
    
    try:
        print(f"Sending POST request to {url}")
        print(f"Content type: text/plain")
        print(f"Content length: {len(content)} bytes")
        
        response = requests.post(url, data=content, headers=headers)
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            print(f"✅ Successfully uploaded test file!")
            print(f"File URL: {SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}")
            
            # Try to retrieve the file to verify it's accessible
            print("\nVerifying file access...")
            get_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
            get_response = requests.get(get_url)
            
            if get_response.status_code == 200:
                print(f"✅ Successfully retrieved the uploaded file!")
            else:
                print(f"⚠️ Could not retrieve the file: {get_response.status_code}")
                print(f"Response: {get_response.text}")
        else:
            print(f"❌ Failed to upload file: {response.status_code}")
            print(f"Response: {response.text}")
            
            try:
                error_json = json.loads(response.text)
                if "message" in error_json:
                    print(f"Error message: {error_json['message']}")
                    
                    if "invalid signature" in error_json.get("message", ""):
                        print("\n🔑 Invalid signature detected!")
                        print("This usually means your SUPABASE_KEY is invalid or lacks sufficient permissions.")
                        print("Please get the service_role key from your Supabase dashboard.")
            except:
                pass
    
    except Exception as e:
        print(f"❌ Error uploading file: {str(e)}")

def create_test_bucket():
    """Try to create a test bucket to check permissions"""
    test_bucket_name = f"test-bucket-{int(time.time())}"
    
    print(f"\nTrying to create a test bucket '{test_bucket_name}'...")
    
    url = f"{SUPABASE_URL}/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "name": test_bucket_name,
        "public": True
    }
    
    try:
        print(f"Sending POST request to {url}")
        print(f"Request data: {data}")
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Successfully created test bucket!")
            print("This confirms your key has administrative permissions.")
            
            # Clean up by deleting the test bucket
            print(f"Cleaning up by deleting the test bucket...")
            delete_url = f"{SUPABASE_URL}/storage/v1/bucket/{test_bucket_name}"
            delete_response = requests.delete(delete_url, headers=headers)
            
            if delete_response.status_code in (200, 204):
                print(f"✅ Successfully deleted test bucket!")
            else:
                print(f"⚠️ Could not delete test bucket: {delete_response.status_code}")
        else:
            print(f"❌ Failed to create test bucket: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 403:
                print("\n🔑 Permission denied!")
                print("Your current key does not have permission to create buckets.")
                print("This confirms you're using the anon key, not the service_role key.")
                print("Please follow the instructions in SUPABASE_KEYS.md to get the service_role key.")
    
    except Exception as e:
        print(f"❌ Error creating test bucket: {str(e)}")

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in your .env file")
    else:
        test_list_buckets()
        test_upload_file()
        create_test_bucket() 