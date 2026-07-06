import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Any, Dict
from src.backend.app.domain.models import Service, Capability, ServiceStatus, CapabilityType
from src.backend.app.domain.repositories import ServiceRepository, CapabilityRepository, SystemConfigRepository, SystemInventoryRepository, OperationalHistoryRepository
from .sqlite_db import get_connection

def parse_timestamp(ts_str: Any) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        # SQLite raw format might be YYYY-MM-DD HH:MM:SS or ISO format
        if isinstance(ts_str, datetime):
            return ts_str
        return datetime.fromisoformat(ts_str.replace(" ", "T"))
    except Exception:
        return None

class SqliteServiceRepository(ServiceRepository):
    def save(self, service: Service) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        
        args_json = json.dumps(service.args)
        
        cursor.execute("SELECT id FROM services WHERE id = ?;", (service.id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
            UPDATE services 
            SET name = ?, type = ?, port = ?, status = ?, pid = ?, 
                binary_path = ?, args = ?, config_path = ?, auto_start = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """, (
                service.name, service.type, service.port, service.status.value, service.pid,
                service.binary_path, args_json, service.config_path, 1 if service.auto_start else 0,
                service.id
            ))
        else:
            cursor.execute("""
            INSERT INTO services (id, name, type, port, status, pid, binary_path, args, config_path, auto_start)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                service.id, service.name, service.type, service.port, service.status.value, service.pid,
                service.binary_path, args_json, service.config_path, 1 if service.auto_start else 0
            ))
            
        conn.commit()
        conn.close()

    def get_by_id(self, service_id: str) -> Optional[Service]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE id = ?;", (service_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        try:
            args = json.loads(row["args"]) if row["args"] else []
        except Exception:
            args = []
            
        return Service(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            port=row["port"],
            status=ServiceStatus(row["status"]),
            pid=row["pid"],
            binary_path=row["binary_path"],
            args=args,
            config_path=row["config_path"],
            auto_start=bool(row["auto_start"]),
            created_at=parse_timestamp(row["created_at"]),
            updated_at=parse_timestamp(row["updated_at"])
        )

    def get_all(self) -> List[Service]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services;")
        rows = cursor.fetchall()
        conn.close()
        
        services = []
        for row in rows:
            try:
                args = json.loads(row["args"]) if row["args"] else []
            except Exception:
                args = []
                
            services.append(Service(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                port=row["port"],
                status=ServiceStatus(row["status"]),
                pid=row["pid"],
                binary_path=row["binary_path"],
                args=args,
                config_path=row["config_path"],
                auto_start=bool(row["auto_start"]),
                created_at=parse_timestamp(row["created_at"]),
                updated_at=parse_timestamp(row["updated_at"])
            ))
        return services

    def delete(self, service_id: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM services WHERE id = ?;", (service_id,))
        conn.commit()
        conn.close()


class SqliteCapabilityRepository(CapabilityRepository):
    def save(self, capability: Capability) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        
        size_bytes = capability.metadata.get("size_bytes")
        family = capability.metadata.get("family")
        parameter_size = capability.metadata.get("parameter_size")
        
        # Serialize the rest of the metadata dictionary to JSON
        # Filter out keys represented by direct columns to avoid redundancy
        meta_dict = {k: v for k, v in capability.metadata.items() if k not in ["size_bytes", "family", "parameter_size"]}
        meta_json = json.dumps(meta_dict)
        
        cursor.execute("SELECT id FROM models WHERE id = ?;", (capability.id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
            UPDATE models 
            SET name = ?, provider = ?, type = ?, size_bytes = ?, family = ?, parameter_size = ?, meta_json = ?, last_discovered = CURRENT_TIMESTAMP
            WHERE id = ?;
            """, (
                capability.name, capability.provider, capability.type.value, size_bytes, family, parameter_size, meta_json,
                capability.id
            ))
        else:
            cursor.execute("""
            INSERT INTO models (id, name, provider, type, size_bytes, family, parameter_size, meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                capability.id, capability.name, capability.provider, capability.type.value, size_bytes, family, parameter_size, meta_json
            ))
            
        conn.commit()
        conn.close()

    def _row_to_capability(self, row: sqlite3.Row) -> Capability:
        try:
            meta = json.loads(row["meta_json"]) if row["meta_json"] else {}
        except Exception:
            meta = {}
            
        # Add column-level metadata back
        if row["size_bytes"] is not None:
            meta["size_bytes"] = row["size_bytes"]
        if row["family"] is not None:
            meta["family"] = row["family"]
        if row["parameter_size"] is not None:
            meta["parameter_size"] = row["parameter_size"]
            
        return Capability(
            id=row["id"],
            name=row["name"],
            type=CapabilityType(row["type"]),
            provider=row["provider"],
            metadata=meta,
            last_discovered=parse_timestamp(row["last_discovered"])
        )

    def get_by_id(self, capability_id: str) -> Optional[Capability]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE id = ?;", (capability_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        return self._row_to_capability(row)

    def get_all(self) -> List[Capability]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models;")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_capability(row) for row in rows]

    def get_by_provider(self, provider: str) -> List[Capability]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE provider = ?;", (provider,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_capability(row) for row in rows]

    def delete(self, capability_id: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?;", (capability_id,))
        conn.commit()
        conn.close()

    def clear_all(self) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models;")
        conn.commit()
        conn.close()

    def clear_by_provider(self, provider: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE provider = ?;", (provider,))
        conn.commit()
        conn.close()


class SqliteSystemConfigRepository(SystemConfigRepository):
    def get(self, key: str) -> Optional[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = ?;", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["value"]
        return None

    def set(self, key: str, value: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO system_config (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP);
        """, (key, value))
        conn.commit()
        conn.close()


class SqliteSystemInventoryRepository(SystemInventoryRepository):
    def save(self, key: str, category: str, value: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO system_inventory (key, category, value, last_updated)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP);
        """, (key, category, value))
        conn.commit()
        conn.close()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_inventory WHERE key = ?;", (key,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            val = json.loads(row["value"])
        except Exception:
            val = row["value"]
        return {
            "key": row["key"],
            "category": row["category"],
            "value": val,
            "last_updated": row["last_updated"]
        }

    def get_all(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_inventory;")
        rows = cursor.fetchall()
        conn.close()
        items = []
        for row in rows:
            try:
                val = json.loads(row["value"])
            except Exception:
                val = row["value"]
            items.append({
                "key": row["key"],
                "category": row["category"],
                "value": val,
                "last_updated": row["last_updated"]
            })
        return items


class SqliteOperationalHistoryRepository(OperationalHistoryRepository):
    def log(self, event_type: str, severity: str, message: str, service_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        details_json = json.dumps(details) if details is not None else None
        cursor.execute("""
        INSERT INTO operational_history (event_type, service_id, severity, message, details)
        VALUES (?, ?, ?, ?, ?);
        """, (event_type, service_id, severity, message, details_json))
        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM operational_history
        ORDER BY timestamp DESC
        LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        events = []
        for row in rows:
            try:
                details = json.loads(row["details"]) if row["details"] else None
            except Exception:
                details = row["details"]
            events.append({
                "id": row["id"],
                "event_type": row["event_type"],
                "service_id": row["service_id"],
                "severity": row["severity"],
                "message": row["message"],
                "details": details,
                "timestamp": row["timestamp"]
            })
        return events

