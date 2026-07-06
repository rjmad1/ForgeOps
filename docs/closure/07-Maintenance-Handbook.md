# ForgeOps Maintenance Handbook

This handbook defines the long-term maintenance policies, support SLAs, versioning criteria, branching strategies, and incident response procedures for the **ForgeOps** ecosystem.

---

## 1. Maintenance & Support Policies

### Maintenance Policy
ForgeOps Version 1.0 is declared complete and enters **Maintenance Mode**.
* **Scope**: Maintenance is limited to release-critical bug fixes, database schema repairs, and security vulnerability patching.
* **Duration**: Version 1.0 will receive active maintenance patches for 12 months (until July 2027), followed by an additional 12 months of security-only patches.

### Support Policy
* **Tier 1 (Internal IT / Helpdesk)**: Initial triage, verifying prerequisites (Python, node), check for port conflicts, and generate support bundles.
* **Tier 2 (Systems Administrators / Operations)**: Service registration repairs, NTFS permission adjustments, database vacuuming, and restoring backups.
* **Tier 3 (Core engineering team)**: Addressing verified framework defects or security vulnerabilities.
* **SLA Guidelines**:
  * Critical Security Vulnerability: Patch deployed within 48 hours.
  * System Outage (Orchestrator fails to boot): Workaround or fix provided within 5 business days.
  * Non-Critical Bug: Addressed in scheduled maintenance rollups.

---

## 2. Release & Versioning Policies

### Versioning Policy
The platform strictly follows **Semantic Versioning 2.0.0 (SemVer)**:
* **MAJOR (x.0.0)**: Incompatibility API changes (e.g. database schema change without backward compatibility).
* **MINOR (0.y.0)**: New backward-compatible feature additions (e.g. adding a new default runtime plugin).
* **PATCH (0.0.z)**: Backward-compatible bug fixes and security hotfixes.

### Release Policy
* Patch releases are rolled out as needed for critical fixes.
* Minor releases are scheduled on a quarterly cycle.
* Every release must pass the `scripts/validate_system.py` test suite.

### Deprecation Policy
* Deprecated features or plugins will be announced one minor release in advance.
* Deprecated methods will be decorated with `@deprecation` warnings in code.

---

## 3. Branching & Development Strategy

We use a modified Git Flow branching strategy:

```
  main (v1.0.0 Release) ───────────────────────────────────► [Stable Release]
    ▲
    │ Hotfix Merge
  hotfix/v1.0.1 ─────────────────────────────────
    ▲                                           │
    └─────────── Pull Request                   ▼
  v1.1-dev (Future Development) ────────────────┴───────────► [Active Development]
```

### Active Branches:
* **`main`**: Reflects the production-ready state. Only hotfixes or release merges are committed here.
* **`v1.1-dev`**: The active integration branch for Version 1.1 feature backlogs.
* **`feature/*`**: Short-lived branches spawned from `v1.1-dev` for individual backlog items.
* **`hotfix/*`**: Branches spawned from `main` to address critical production issues, merged back to both `main` and `v1.1-dev`.

---

## 4. Issue Triage & Bug Classification

### Issue Triage Steps
1. **Reproduce**: Verify the bug exists on a clean Windows 11 workstation.
2. **Logs Audit**: Request the user generate a support bundle:
   ```powershell
   arm support-bundle
   ```
3. **Classify**: Assign priority based on the Bug Classification matrix.

### Bug Classification Matrix
| Class | Severity | Description | Target Resolution |
|---|---|---|---|
| **Class A** | Critical | Security vulnerability (RCE, API Key bypass) or database corruption. | Immediate Hotfix (<48h) |
| **Class B** | High | Orchestrator fails to boot or a plugin fails to start its subprocess. | Next Patch Release (<10 days) |
| **Class C** | Medium | Metrics calculation errors or minor UI dashboard display anomalies. | Next Scheduled Patch |
| **Class D** | Low | Typos in documentation or minor cosmetic UI padding issues. | Next Minor Release |

---

## 5. Security Response Policy

If a security vulnerability is reported:
1. **Embargo**: Keep the issue details private until a patch is developed.
2. **Develop**: Create a fix in a private security fork.
3. **Release**: Merge into `main` and draft a security advisory detailing the vulnerability and the fix.
4. **Deploy**: Push version update notifications to clients via the updates registry.

---

## 6. Plugin Compatibility Policy
* Plugins built for Version 1.0 must remain backward compatible with all `v1.x.y` releases.
* Changing abstract methods in the `RuntimePlugin` base class is prohibited in patch releases.
