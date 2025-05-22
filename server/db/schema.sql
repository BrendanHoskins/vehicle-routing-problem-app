-- Table for caching uploaded files with a TTL
CREATE TABLE IF NOT EXISTS cached_files (
    id TEXT PRIMARY KEY,         -- Unique identifier for the cached file
    filename TEXT,               -- Original filename
    file_content BLOB NOT NULL,  -- The actual file content
    mime_type TEXT,              -- MIME type of the file (e.g., 'application/vnd.ms-excel')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL -- Timestamp when this cache entry should expire
);

-- Table for caching Google Routes API responses
CREATE TABLE IF NOT EXISTS api_responses (
    request_hash TEXT PRIMARY KEY, -- A unique hash representing the API request parameters
    response_data TEXT NOT NULL,   -- The JSON response from the API
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
