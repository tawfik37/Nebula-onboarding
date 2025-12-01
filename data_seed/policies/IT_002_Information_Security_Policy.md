# Nebula Dynamics: Information Security Policy
**Doc ID:** IT-002 | **Last Updated:** Nov 01, 2024 | **Owner:** CISO

## 1. Overview
This policy applies to all employees, contractors, and systems accessing Nebula Dynamics data.

## 2. Identity & Access Management
### 2.1 Password Standards
* **Minimum Length:** 16 characters.
* **Complexity:** Must contain uppercase, lowercase, numbers, and symbols.
* **Rotation:** Passwords do not expire unless a compromise is suspected.
* **Manager:** Use of **1Password** is mandatory for all employees.

### 2.2 Multi-Factor Authentication (MFA)
MFA is enforced on all company accounts (Google Workspace, AWS, GitHub, Okta). Hardware keys (YubiKey) are required for Engineering Leads and Admins.

## 3. Data Classification Standards
Data must be handled according to its sensitivity level:

| Class | Label | Definition | Examples | Handling Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Class 1** | **Public** | Non-sensitive data approved for public release. | Marketing blogs, job descriptions. | No restrictions. |
| **Class 2** | **Internal** | Information for employees only. | Org charts, internal wikis, slack messages. | Do not share externally without NDA. |
| **Class 3** | **Restricted** | Highly sensitive data; compromise causes harm. | Customer PII, source code, production database credentials. | Encrypted at rest/transit. Access on "Need-to-Know" basis only. |

## 4. Device Security
* **Disk Encryption:** FileVault (Mac) or BitLocker (Windows) must be enabled.
* **OS Updates:** Critical security patches must be installed within 48 hours of release.
* **Prohibited Software:** The following tools are banned on company devices due to data privacy concerns:
    * *TikTok*
    * *Personal VPNs*
    * *Unapproved Generative AI tools* (Note: Use `Nebula-Chat-Enterprise` instead of public ChatGPT).