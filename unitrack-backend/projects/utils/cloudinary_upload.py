import cloudinary.uploader

def upload_file_to_cloudinary(file, folder="submissions"):
   
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="auto",  
    )

    return result.get("secure_url")
