import os
import sqlite3

DEFAULT_DB_DIR = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "arm.db")
DEV_DB_PATH = "arm.db"

def get_db_path() -> str:
    """Returns the database file path, falling back to local file if ProgramData isn't writable."""
    path = os.environ.get("ARM_DB_PATH", DEFAULT_DB_PATH)
    directory = os.path.dirname(path)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
            if not os.access(directory, os.W_OK):
                raise PermissionError("Directory is not writable")
        return path
    except Exception:
        # Fallback to local directory for development/testing if ProgramData is protected
        return DEV_DB_PATH

def get_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the SQLite database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for concurrency safety
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    # Enable foreign keys support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db() -> None:
    """Creates the tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create services table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,
        port INTEGER UNIQUE,
        status TEXT NOT NULL,
        pid INTEGER,
        binary_path TEXT,
        args TEXT,
        config_path TEXT,
        auto_start INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Create models (capabilities) table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS models (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        type TEXT NOT NULL,
        size_bytes INTEGER,
        family TEXT,
        parameter_size TEXT,
        meta_json TEXT,
        last_discovered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, provider)
    );
    """)
    
    # 3. Create performance_metrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        request_path TEXT,
        response_time_ms INTEGER,
        status_code INTEGER,
        vram_used_bytes INTEGER,
        gpu_utilization_pct REAL,
        cpu_utilization_pct REAL,
        ram_used_bytes INTEGER,
        FOREIGN KEY(service_id) REFERENCES services(id)
    );
    """)
    
    # 4. Create system_config table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Create system_inventory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_inventory (
        key TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        value TEXT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Create operational_history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operational_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        service_id TEXT,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at: {get_db_path()}")
