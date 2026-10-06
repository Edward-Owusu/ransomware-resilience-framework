# Ransomware recovery readiness: Riverbend Components (fictional)

As of 2026-10-06 | 7 systems | Generated 2026-10-06 18:14 UTC

- Readiness: **29/100 (Highly vulnerable)** (systems 30, practices 26)
- Systems that would miss their downtime target: **3**
- Systems without a backup copy ransomware cannot reach: **5**
- Systems with no restore test in the last year: **5**

## Recovery timeline

| System | Criticality | Recovery | Target | Status |
|---|---|---|---|---|
| ERP server | critical | 28 h | 24 h | Misses target |
| Active Directory | critical | 12 h | 8 h | Misses target |
| CNC program PC | high | cannot recover | 12 h | Misses target |
| Accounting workstation | high | 18 h | 24 h | Within target |
| File server | high | 22 h | 24 h | Within target |
| Email and files (cloud) | high | 4 h | 8 h | Within target |
| Payroll (vendor hosted) | medium | 8 h | 72 h | Within target |

## Findings

- **[CRITICAL] RR-01 CNC program PC: No backup.** This system has no backup at all. Fix: Start backing up this system now, with at least one copy kept offline or immutable. _(CP-9)_
- **[CRITICAL] RR-02 Accounting workstation: No offline or immutable backup copy.** All backup copies are online and writable, so ransomware could encrypt or delete them. Fix: Keep at least one backup copy that ransomware cannot reach: offline media, an immutable cloud bucket, or a backup service with object lock. _(CP-9)_
- **[CRITICAL] RR-02 Active Directory: No offline or immutable backup copy.** All backup copies are online and writable, so ransomware could encrypt or delete them. Fix: Keep at least one backup copy that ransomware cannot reach: offline media, an immutable cloud bucket, or a backup service with object lock. _(CP-9)_
- **[CRITICAL] RR-02 ERP server: No offline or immutable backup copy.** All backup copies are online and writable, so ransomware could encrypt or delete them. Fix: Keep at least one backup copy that ransomware cannot reach: offline media, an immutable cloud bucket, or a backup service with object lock. _(CP-9)_
- **[CRITICAL] RR-02 File server: No offline or immutable backup copy.** All backup copies are online and writable, so ransomware could encrypt or delete them. Fix: Keep at least one backup copy that ransomware cannot reach: offline media, an immutable cloud bucket, or a backup service with object lock. _(CP-9)_
- **[CRITICAL] RR-04 Active Directory: Recovery would take longer than the business can be down.** Recovery takes about 12 h; the business can be down at most 8 h. Fix: Shorten recovery: restore from local snapshots, pre-build replacement servers, document the restore steps, or agree a realistic downtime target with the business. _(CP-10, CP-2)_
- **[CRITICAL] RR-04 ERP server: Recovery would take longer than the business can be down.** Recovery takes about 28 h including 12 h waiting for Active Directory to be restored first; the business can be down at most 24 h. Fix: Shorten recovery: restore from local snapshots, pre-build replacement servers, document the restore steps, or agree a realistic downtime target with the business. _(CP-10, CP-2)_
- **[HIGH] RR-03 Accounting workstation: Backups run less often than the data you can afford to lose.** Backups every 168 h, but at most 24 h of data can be lost. Fix: Increase backup frequency, or use snapshots or replication, so the backup interval is within the recovery point objective. _(CP-9, CP-2)_
- **[HIGH] RR-03 ERP server: Backups run less often than the data you can afford to lose.** Backups every 24 h, but at most 4 h of data can be lost. Fix: Increase backup frequency, or use snapshots or replication, so the backup interval is within the recovery point objective. _(CP-9, CP-2)_
- **[HIGH] RR-05 Accounting workstation: Restore not tested in the last 12 months.** Restore has never been tested. Fix: Restore this system to a test environment, confirm the data is usable, and record how long it took. _(CP-4, CP-9(1))_
- **[HIGH] RR-05 Active Directory: Restore not tested in the last 12 months.** Restore has never been tested. Fix: Restore this system to a test environment, confirm the data is usable, and record how long it took. _(CP-4, CP-9(1))_
- **[HIGH] RR-05 ERP server: Restore not tested in the last 12 months.** Last restore test was 603 days ago. Fix: Restore this system to a test environment, confirm the data is usable, and record how long it took. _(CP-4, CP-9(1))_
- **[HIGH] RR-05 File server: Restore not tested in the last 12 months.** Restore has never been tested. Fix: Restore this system to a test environment, confirm the data is usable, and record how long it took. _(CP-4, CP-9(1))_
- **[HIGH] RR-05 Payroll (vendor hosted): Restore not tested in the last 12 months.** Restore has never been tested. Fix: Restore this system to a test environment, confirm the data is usable, and record how long it took. _(CP-4, CP-9(1))_
- **[HIGH] RR-07 Accounting workstation: Backups use the same credentials as production.** Someone who takes over a production admin account could also delete the backups. Fix: Give the backup system its own accounts, not joined to the production domain, protected with MFA. _(AC-6, CP-9)_
- **[HIGH] RR-07 Active Directory: Backups use the same credentials as production.** Someone who takes over a production admin account could also delete the backups. Fix: Give the backup system its own accounts, not joined to the production domain, protected with MFA. _(AC-6, CP-9)_
- **[HIGH] RR-07 ERP server: Backups use the same credentials as production.** Someone who takes over a production admin account could also delete the backups. Fix: Give the backup system its own accounts, not joined to the production domain, protected with MFA. _(AC-6, CP-9)_
- **[HIGH] RR-07 File server: Backups use the same credentials as production.** Someone who takes over a production admin account could also delete the backups. Fix: Give the backup system its own accounts, not joined to the production domain, protected with MFA. _(AC-6, CP-9)_
- **[MEDIUM] RR-06 Accounting workstation: Recovery time is an estimate, not measured.** The 6 h restore time has not been confirmed by a timed test. Fix: Time a real restore so the recovery plan is based on evidence rather than a guess. _(CP-4)_
- **[MEDIUM] RR-06 Active Directory: Recovery time is an estimate, not measured.** The 12 h restore time has not been confirmed by a timed test. Fix: Time a real restore so the recovery plan is based on evidence rather than a guess. _(CP-4)_
- **[MEDIUM] RR-06 File server: Recovery time is an estimate, not measured.** The 10 h restore time has not been confirmed by a timed test. Fix: Time a real restore so the recovery plan is based on evidence rather than a guess. _(CP-4)_
- **[MEDIUM] RR-06 Payroll (vendor hosted): Recovery time is an estimate, not measured.** The 8 h restore time has not been confirmed by a timed test. Fix: Time a real restore so the recovery plan is based on evidence rather than a guess. _(CP-4)_
- **[MEDIUM] RR-08 Accounting workstation: Backup jobs are not monitored for failures.** Failed backups could go unnoticed. Fix: Turn on backup failure alerts and have someone review them daily. _(CP-9)_
- **[MEDIUM] RR-08 Active Directory: Backup jobs are not monitored for failures.** Failed backups could go unnoticed. Fix: Turn on backup failure alerts and have someone review them daily. _(CP-9)_
- **[MEDIUM] RR-09 Accounting workstation: Backups are not encrypted.** Backup copies are stored unencrypted. Fix: Encrypt backups so a stolen copy cannot be read or used for extortion. _(CP-9(8), SC-28)_
- **[MEDIUM] RR-09 Active Directory: Backups are not encrypted.** Backup copies are stored unencrypted. Fix: Encrypt backups so a stolen copy cannot be read or used for extortion. _(CP-9(8), SC-28)_
- **[MEDIUM] RR-09 ERP server: Backups are not encrypted.** Backup copies are stored unencrypted. Fix: Encrypt backups so a stolen copy cannot be read or used for extortion. _(CP-9(8), SC-28)_
- **[MEDIUM] RR-09 File server: Backups are not encrypted.** Backup copies are stored unencrypted. Fix: Encrypt backups so a stolen copy cannot be read or used for extortion. _(CP-9(8), SC-28)_

## Organization-wide practices

| Practice | Status | Controls |
|---|---|---|
| Incident response plan with a ransomware playbook | Not in place | IR-8, IR-4 |
| Offline or printed copy of the response plan and key contacts | Not in place | IR-8, CP-2 |
| MFA on remote access and email | Partly | IA-2(1), IA-2(2), AC-17 |
| MFA and separate accounts for backup administration | Not in place | AC-6, IA-2(1) |
| Endpoint protection on all computers and servers | Partly | SI-3 |
| Internet-facing systems (VPN, firewall, remote access) patched promptly | Partly | SI-2, RA-5 |
| Email filtering and phishing awareness training | In place | SI-8, AT-2 |
| Network segmentation separating backups and critical systems | Not in place | SC-7 |
| Administrator accounts separate from everyday accounts | Not in place | AC-6 |
| Ransomware tabletop exercise in the last 12 months | Not in place | IR-3, CP-4 |

_This is a planning aid based on the information supplied. Recovery times are taken from the inventory and should be confirmed by timed restore tests. It does not replace an incident response plan, legal counsel, or professional incident response support._
