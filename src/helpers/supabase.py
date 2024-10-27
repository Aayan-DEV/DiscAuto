# utils/supabase.py
import supabase
from django.conf import settings
import uuid

# Initialize the Supabase client
supabase_client = supabase.create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)

def upload_to_supabase(file, folder='images'):
    """
    Uploads the file to Supabase storage and returns a public URL.
    """
    try:
        # Create a unique file name to prevent collisions
        file_extension = file.name.split('.')[-1]
        file_name = f"{folder}/{uuid.uuid4()}.{file_extension}"
        
        # Convert the file to bytes
        file_content = file.read()  # Read the file content into bytes
        file.seek(0)  # Reset the file pointer after reading
        
        # Upload the file to Supabase
        response = supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file_content)

        # Check if the upload was successful
        if response.status_code != 200:
            error_message = response.json().get('error', 'Unknown error occurred')
            raise Exception(f"Failed to upload to Supabase: {error_message}")

        # Generate a public URL
        public_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_name)
        
        if not public_url:
            raise Exception("Failed to retrieve the public URL for the uploaded file.")

        print(f"Public URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"Error during upload: {e}")
        raise
