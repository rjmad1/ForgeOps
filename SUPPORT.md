# Support Policy & Guidelines

This document details the support policies, SLA guidelines, and maintenance procedures for the **ForgeOps (AI Runtime Manager)** platform.

## Maintenance Policy

ForgeOps Version 1.0.0 is declared complete and enters **Maintenance Mode**:
* **Scope**: Support is limited to release-critical bug fixes, database schema repairs, and security vulnerability patches.
* **Active Support**: Version 1.0.0 will receive active maintenance patches for 12 months (until July 2027), followed by an additional 12 months of security-only patches.

## SLA Guidelines

We adhere to the following target response and resolution times:
* **Critical Security Vulnerability**: Coordinated patch deployed within **48 hours**.
* **System Outage** (Orchestrator failing to boot/run): Workaround or patch provided within **5 business days**.
* **Non-Critical Bug**: Addressed in scheduled quarterly maintenance rollups.

## Support Tiers

To streamline operations, support requests follow a tiered path:

### Tier 1: Helpdesk / IT Support
* **Focus**: Initial triage, verifying prerequisites (Python 3.10+, Node 18+), checking port conflicts (ports `8088`, `8000`, `11434`, `8080`), and generating support bundles.
* **Troubleshooting Action**:
  ```powershell
  # Generate diagnostic details for support teams
  arm diagnostics
  arm support-bundle --output "C:\users\public\support_bundle.zip"
  ```

### Tier 2: Systems Administration / Operations
* **Focus**: Windows service registration repairs, NTFS permission adjustments, database vacuuming, and restoring configuration/database backups.
* **Troubleshooting Action**:
  ```powershell
  # Backup configuration and database state
  arm backup
  # Restore to a previously known healthy state
  arm restore --file "C:\ProgramData\AIRuntimeManager\backups\<backup_dir>\arm.db"
  ```

### Tier 3: Core Engineering
* **Focus**: Resolving framework-level defects, driver incompatibilities, or security vulnerabilities in the orchestrator or default plugins.

## Contact

* **Security Vulnerabilities**: Email **security@forgeops.io** (do not file public GitHub issues for security flaws).
* **General Technical Support**: File a ticket on the GitHub Issue tracker or contact your internal IT team for Tier 1 triage.
