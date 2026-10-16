import os
from pathlib import Path
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"csv"}

def validate_uploaded_file(file: Optional[FileStorage], max_size_bytes: int = 16 * 1024 * 1024) -> Tuple[bool, str, Optional[str]]:
    """
    Validates an uploaded file.
    
    Returns:
        (is_valid, error_message, sanitized_filename)
    """
    if file is None or file.filename == "":
        return False, "No file was selected. Please choose a CSV file to upload.", None
    
    filename = secure_filename(file.filename)
    if not filename:
        return False, "Invalid filename provided.", None
    
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension '.{extension}'. Only '.csv' files are accepted.", filename
    
    # Check file size by seeking
    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
    except Exception:
        size = 0
        
    if size == 0:
        return False, "The uploaded file is empty (0 bytes). Please upload a valid CSV file.", filename
    
    if size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"File size exceeds the maximum limit of {max_mb:.0f} MB.", filename
    
    return True, "", filename
