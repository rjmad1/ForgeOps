# ForgeOps Governance Handbook

This handbook defines the engineering standards, architecture principles, code review checklists, and release requirements for the **ForgeOps** project.

---

## 1. Core Architecture Principles

1. **Local-First Executions**: Runtimes must bind to loopback interfaces. Network calls should not leave the workstation boundaries unless explicitly configured by the developer.
2. **Subprocess Decoupling**: Runtimes must run as isolated processes managed by the orchestrator. Core daemon crashes must not leave orphan processes.
3. **Configuration Synthesis**: Never require developers to write YAML files manually. The backend dynamically writes configuration parameters based on system scans.
4. **Resiliency & Self-Healing**: Use exponential backoffs and circuit breakers to recover from crashes automatically.
5. **No Code Modification for Plugins**: System extensions must inherit from `RuntimePlugin` and register with the kernel dynamically.

---

## 2. Coding & Quality Standards

### Python (Backend & CLI)
* **Style**: Enforce PEP 8 conventions.
* **Typing**: Use static type annotations for all function signatures.
* **Validation**: Define API input schemas using Pydantic models.
* **Testing**: Write unit tests for all domain models and integration tests for workflow steps. Maintain a Code-to-Test LOC ratio of at least `3.5 : 1`.

### TypeScript / React (Frontend)
* **Style**: Enforce ES6 coding standards and oxlint formatting rules.
* **State Management**: Use React state hooks (`useState`, `useEffect`) and avoid excessive global state dependencies.
* **Visuals**: Enforce strict dark-mode-first styling. All controls must support clear focus indicators and Lucide icon assets.

---

## 3. Contribution Workflow

To submit changes to the codebase:
```
  1. Clone v1.1-dev Branch  ──►  2. Implement Feature in feature/* Branch
                                                   │
  4. Merge to v1.1-dev      ◄──  3. Submit PR & Complete Peer Review
```

1. **Branch**: Spawn a branch named `feature/issue-title` or `hotfix/issue-title` from the active development branch.
2. **Implement**: Develop changes without modifying core class interfaces. Write matching unit tests.
3. **Validate**: Run the validation suite locally:
   ```powershell
   .\.venv\Scripts\python.exe scripts\validate_system.py --dev
   ```
4. **Pull Request**: Open a PR targeting the active development branch. Ensure all checks pass.

---

## 4. Operational Checklists

### Code Review Checklist
* [ ] Does the change introduce external network dependencies? (Forbidden)
* [ ] Do all new functions have complete type annotations?
* [ ] Have new configurations been registered with Pydantic and SQLite schemas?
* [ ] Are file paths resolved using OS-agnostic library calls?
* [ ] Do child processes close cleanly on exit?
* [ ] Have unit/integration tests been added?

### Release Checklist
* [ ] Bump version strings in `pyproject.toml`, `package.json`, and database tables.
* [ ] Execute the full validation suite:
   ```powershell
   .\.venv\Scripts\python.exe scripts\validate_system.py --dev
   ```
* [ ] Ensure all 32 REST endpoints and 13 CLI commands return expected output.
* [ ] Generate the release report:
   ```powershell
   # Saved at C:\ProgramData\AIRuntimeManager\validation_report.md
   ```
* [ ] Tag release in Git: `git tag -a v1.0.0 -m "Release version 1.0.0"`.

---

## 5. Definition of Ready (DoR) and Done (DoD)

### Definition of Ready (DoR)
A backlog item is ready for development if it has:
1. A clear **Problem Statement** and **User Value** description.
2. Estimated effort and priority.
3. Identified technical dependencies.
4. Defined acceptance criteria.

### Definition of Done (DoD)
A feature is complete when:
1. The code builds without syntax errors or linter warnings.
2. Unit tests verify the new functions.
3. The system validation suite passes with a **100% success rate**.
4. Documentation has been updated to reflect the new capabilities.
5. Code has been reviewed and approved by at least one peer.
