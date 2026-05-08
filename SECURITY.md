# 🔒 Security Policy

This document defines how **Moztopia** projects handle security issues.  
It is private and intended for **Moztopia developers only**.

---

## 📢 Reporting a Vulnerability

All vulnerabilities must be reported **internally**.  
Notify one of the maintainers directly:

- James Hunter  
- Bruce Anwyl  

Do not disclose vulnerabilities publicly or outside Moztopia.

---

## 🛠️ Handling Vulnerabilities

- Issues are tracked privately and patched as soon as possible.  
- Fixes must be applied in a dedicated branch:
  - `hotfix/<id>` → urgent production fixes  
  - `ai/<name>` → changes to AI instructional framework (if relevant)  
- All fixes must pass CI checks before merging into `main`.

---

## 🚫 Confidentiality

- Secrets, credentials, and tokens must **never** be committed.  
- Use `.env.example` to document required environment variables.  
- Rotate credentials immediately if exposure is suspected.  
- Sensitive discussions remain internal to Moztopia.

---

## ✅ Enforcement

- Branch protections prevent direct pushes to `main`.  
- CI/CD workflows enforce tests and linting.  
- CODEOWNERS ensures both maintainers review sensitive changes.  
- Violations of this policy may result in revoked repo access.

---

## 📌 Notes

- For AI‑related security rules, see **moztopia/artificial-intelligence**.  
- This policy evolves as Moztopia projects grow.
