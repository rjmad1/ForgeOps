# Contributing to ForgeOps

Thank you for your interest in contributing to ForgeOps! To ensure a smooth collaboration, please follow the guidelines below.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing issues to verify the bug has not already been reported.
- Open a new issue using our **Bug Report Template** and provide all requested logs and reproduction steps.

### 2. Suggesting Enhancements
- Open a new issue using our **Feature Request Template** outlining the proposed changes, dependencies, and use cases.

### 3. Submitting Pull Requests
- Fork the repository and create your branch from `main`.
- Ensure your changes follow our coding standards.
- Write unit tests for any new logic or bug fixes.
- Verify that the entire validation suite passes successfully before submitting.

---

## Coding Standards

### Backend (Python)
- **Formatting**: Adhere to PEP 8 standards. Use `black` or `ruff` for linting and formatting.
- **Type Hints**: Type annotations are required on all new functions and public APIs.
- **Database**: When querying SQLite, always ensure you close cursors and connections properly (using context managers or explicit `close()` calls) to prevent file lock contentions on Windows.

### Frontend (React/TypeScript)
- **State Management**: Use functional components and custom hooks for business logic.
- **Styling**: Adhere to the established CSS token system in `index.css`. Avoid ad-hoc inline styles.
- **Typing**: Strict TypeScript typings must be maintained. Avoid the use of `any`.

---

## Testing & System Verification

Before submitting any Pull Request, you **must** run and pass the full verification pipeline:

### 1. Run Unit Tests
```bash
.venv\Scripts\pytest
```

### 2. Run System Validation Suite
Run the system validation suite to check install, database, security, API, CLI, and advanced process lifecycle mechanics on Windows:
```bash
.venv\Scripts\python scripts/validate_system.py
```
*Note: Make sure port 8088 is not bound by any leftover background processes before running the validator.*
