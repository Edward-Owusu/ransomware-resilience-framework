# Ransomware recovery readiness: Northfield Cold Logistics (fictional)

As of 2026-10-06 | 6 systems | Generated 2026-10-06 18:57 UTC

- Readiness: **99/100 (Resilient)** (systems 100, practices 97)
- Systems that would miss their downtime target: **0**
- Systems without a backup copy ransomware cannot reach: **0**
- Systems with no restore test in the last year: **0**

## Recovery timeline

| System | Criticality | Recovery | Target | Status |
|---|---|---|---|---|
| Identity (cloud directory) | critical | 2 h | 4 h | Within target |
| Refrigeration monitoring | critical | 1.5 h | 2 h | Within target |
| Warehouse management (WMS) | critical | 6 h | 8 h | Within target |
| Email and files (cloud) | high | 5 h | 8 h | Within target |
| File server | high | 8 h | 24 h | Within target |
| Accounting (cloud) | medium | 6 h | 48 h | Within target |

## Findings


## Organization-wide practices

| Practice | Status | Controls |
|---|---|---|
| Incident response plan with a ransomware playbook | In place | IR-8, IR-4 |
| Offline or printed copy of the response plan and key contacts | In place | IR-8, CP-2 |
| MFA on remote access and email | In place | IA-2(1), IA-2(2), AC-17 |
| MFA and separate accounts for backup administration | In place | AC-6, IA-2(1) |
| Endpoint protection on all computers and servers | In place | SI-3 |
| Internet-facing systems (VPN, firewall, remote access) patched promptly | In place | SI-2, RA-5 |
| Email filtering and phishing awareness training | In place | SI-8, AT-2 |
| Network segmentation separating backups and critical systems | In place | SC-7 |
| Administrator accounts separate from everyday accounts | In place | AC-6 |
| Ransomware tabletop exercise in the last 12 months | Partly | IR-3, CP-4 |

_This is a planning aid based on the information supplied. Recovery times are taken from the inventory and should be confirmed by timed restore tests. It does not replace an incident response plan, legal counsel, or professional incident response support._
