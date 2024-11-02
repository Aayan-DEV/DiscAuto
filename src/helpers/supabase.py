import uuid
from django.conf import settings
from supabase import create_client, Client

# Initialize the Supabase client
supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)

def upload_to_supabase(file, folder='images'):
    try:
        # Create a unique file name
        file_extension = file.name.split('.')[-1]
        file_name = f"{folder}/{uuid.uuid4()}.{file_extension}"

        # Read the file content for uploading
        file_content = file.read()
        file.seek(0)  # Reset file pointer after reading

        # Upload file to Supabase storage
        response = supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file_content)

        # Check if the upload was successful
        if response.status_code != 200:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            raise Exception(f"Failed to upload to Supabase: {error_message}")

        # Get the public URL directly
        public_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_name)

        if not public_url:
            raise Exception("Failed to retrieve the public URL for the uploaded file.")

        print(f"Public URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"Error during upload: {e}")
        raise
