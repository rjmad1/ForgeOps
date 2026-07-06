# ADR-001: FastAPI for Control Plane API Gateway

## Context and Problem
The AI Control Plane requires a high-performance, developer-friendly local REST API gateway on Windows 11 to interface with local developer environments, CLI scripts, and web UI dashboards. It needs to support asynchronous task management, dynamic schema validation, and automatic API documentation.

## Decisions
Use FastAPI as the core web application framework for the AI Runtime Manager control plane.

## Rationale
- **Performance**: High performance out of the box using Starlette and Pydantic.
- **Asynchronous Lifespan**: Clean support for start/stop hook callbacks (e.g. running startup state discovery).
- **Static Schema**: Simplifies input/output contract enforcement via Pydantic models.
- **Auto-Documentation**: Provides interactive Swagger/ReDoc endpoints, facilitating client integrations.

## Status
Accepted.
