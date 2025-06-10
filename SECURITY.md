

# Security Policy

## Supported Versions

The ARIES project follows a rolling release model, with continuous updates applied through commits. Security support is provided based on the number of commits from the latest main branch. Below is the support status for recent commits:

| Commit Range (from latest) | Supported          |
|----------------------------|--------------------|
| Latest 100 commits         | :white_check_mark: |
| 101–200 commits            | :x:                |
| 201–300 commits            | :white_check_mark: |
| > 300 commits              | :x:                |

We ensure security updates are prioritized for the most recent 100 commits and selectively backported to the 201–300 commit range if critical vulnerabilities are identified. Older commits (>300) are not supported for security updates, and users are encouraged to update to the latest commit to maintain a secure environment.

## Reporting a Vulnerability

If you discover a security vulnerability in ARIES, we encourage responsible disclosure. Please follow these steps to report it:

1. **Where to Report**: Submit vulnerability details to our private issue tracker at [https://github.com/Chieko-Seren/ARIES/issues/new](https://github.com/Chieko-Seren/ARIES/issues/new) with the label "Security". Alternatively, email us at chieko.seren@icloud.com for sensitive issues.
2. **Information to Provide**: Include a detailed description of the vulnerability, steps to reproduce, potential impact, and any suggested mitigations.
3. **Response Timeline**:
  - **Acknowledgment**: You will receive a confirmation within 48 hours of submission.
  - **Initial Assessment**: We will evaluate the vulnerability within 7 days and provide an update on its validity and severity.
  - **Resolution**: If accepted, we aim to release a fix within 14–30 days, depending on complexity. You will be notified of progress weekly.
  - **Declined Vulnerabilities**: If the vulnerability is not applicable or low-impact, we will provide a detailed explanation and close the issue.
4. **Confidentiality**: Please do not disclose the vulnerability publicly until we have had a chance to address it and coordinate a responsible disclosure.
5. **Recognition**: With your consent, we will credit you in our release notes for reporting the vulnerability.

We value the security community’s contributions and are committed to addressing vulnerabilities promptly to ensure the safety of ARIES users.


