from bson import ObjectId
from datetime import datetime, timedelta

from .init_db import get_db

def cache_excel_file_and_cleanup_expired_files(file):
    db = get_db()
    file_id = ObjectId()
    cursor = db.cursor()
    cursor.execute('BEGIN')
    cursor.execute('INSERT INTO cached_files VALUES (?, ?, ?, ?, ?, ?)', (file_id, file.filename, file.read(), file.mimetype, datetime.now(), datetime.now() + timedelta(seconds=1000)))
    cursor.execute("DELETE FROM cached_files WHERE expires_at <= CURRENT_TIMESTAMP")
    db.commit()
    return file_id


def get_cached_file_and_cleanup_expired_files(file_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("BEGIN")

    result = cursor.execute("""
        DELETE FROM cached_files
        WHERE id = ?
        RETURNING filename, file_content
    """, (file_id,))

    file_data = result.fetchone()

    cursor.execute("DELETE FROM cached_files WHERE expires_at <= CURRENT_TIMESTAMP")

    db.commit()

    return file_data['filename'], file_data['file_content']


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