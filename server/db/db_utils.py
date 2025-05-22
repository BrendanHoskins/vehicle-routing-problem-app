from .init_db import get_db

def store_excel_file(file):
    db = get_db()
    db.execute('INSERT INTO ')


def get_cached_file(file_id):
    db = get_db()
    # Check expiration at the SQL level for efficiency
    cursor = db.execute(
        "SELECT id, filename, file_content, mime_type, created_at, expires_at FROM cached_files WHERE id = ? AND expires_at > CURRENT_TIMESTAMP",
        (file_id,)
    )
    file_data = cursor.fetchone()
    return file_data # Will be None if not found or expired

def cleanup_expired_files():
    db = get_db()
    deleted_count = 0
    try:
        cursor = db.execute("DELETE FROM cached_files WHERE expires_at <= CURRENT_TIMESTAMP")
        deleted_count = cursor.rowcount
        db.commit()
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} expired file entries.")
    except Exception as e:
        print(f"Error during cleanup_expired_files: {e}")
    return deleted_count

def store_api_response(request_hash, response_data):
    db = get_db()
    try:
        # INSERT OR REPLACE will update if request_hash already exists, otherwise insert.
        db.execute(
            "INSERT OR REPLACE INTO api_responses (request_hash, response_data) VALUES (?, ?)",
            (request_hash, response_data)
        )
        db.commit()
    except Exception as e:
        print(f"Error storing API response (Hash: {request_hash}): {e}")
        raise

def get_api_response(request_hash):
    db = get_db()
    cursor = db.execute(
        "SELECT response_data, created_at FROM api_responses WHERE request_hash = ?",
        (request_hash,)
    )
    response_row = cursor.fetchone()
    if response_row:
        # Return the raw response data string (e.g., JSON string)
        return response_row['response_data']
    return None