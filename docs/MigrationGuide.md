# Migration Guide: Migrating to ForgeOps

This guide describes how to migrate downstream tools, client integrations, and local database scripts to **ForgeOps Version 1.0.0**.

---

## 1. Database Schema Changes

If you are writing direct SQL queries against `arm.db`, please note the following schema layouts:

### Services Table
- The `services` table schema is defined as:
  ```sql
  CREATE TABLE services (
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
  ```
- **Action Required**: Pre-v1.0 schemas that used simple boolean types for status must migrate to the text-based enum statuses: `STOPPED`, `RUNNING`, `STARTING`, `CONFIGURING`, `UPDATING`, `DEGRADED`, `ERROR`.

### Configuration Key
- Configuration keys are stored in `system_config`:
  - `auto_restart_enabled` (boolean text: `'true'` or `'false'`)
  - `auto_restart_limit` (integer text)
  - `litellm_active_requests` (integer text)

---

## 2. API Key Authentication (Migration from Unauthenticated)

In Version 1.0.0, the REST API endpoints are protected by default to secure control operations.

- **Old Endpoint Behavior**: Direct HTTP requests without headers were allowed on all ports.
- **New Behavior**: Requests to `/api/v1/...` require the header:
  ```http
  X-API-Key: <session_token>
  ```
- **How to retrieve token**:
  Your scripts must read the token dynamically from `%PROGRAMDATA%\AIRuntimeManager\.session_api_key` on startup. Do not hardcode this token as it rotates on every daemon boot.
