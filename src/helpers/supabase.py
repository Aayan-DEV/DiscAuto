import uuid
from django.conf import settings
from supabase import create_client, Client

# Here we initialize the Supabase client
supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)

def upload_to_supabase(file, folder='images'):
    try:
        # Create a unique file name
        file_extension = file.name.split('.')[-1]
        file_name = f"{folder}/{uuid.uuid4()}.{file_extension}"

        # Read file content
        file_content = file.read()
        file.seek(0)  # Reset file pointer

        # Upload file to Supabase storage
        response = supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file_content)

        # Use getattr to check for an error attribute safely
        error_obj = getattr(response, "error", None)
        if error_obj:
            # If error_obj is a dict, try to get its message; otherwise, cast to string.
            error_message = error_obj.get("message", "Unknown error") if isinstance(error_obj, dict) else str(error_obj)
            raise Exception(f"Failed to upload to Supabase: {error_message}")

        # Get the public URL for the uploaded file
        public_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_name)
        if not public_url:
            raise Exception("Failed to retrieve the public URL for the uploaded file.")

        print(f"Public URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"Error during upload: {e}")
        raise
