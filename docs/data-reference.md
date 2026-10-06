# Input reference

## Systems inventory (CSV)

One row per critical system. Start from `samples/systems_template.csv`.

| Column | Values | Notes |
|---|---|---|
| `system` | text | Required, unique |
| `owner`, `business_function` | text | Who owns it and what the business uses it for |
| `criticality` | critical, high, medium, low | Required |
| `rto_hours` | number | Required. Longest the business can be without the system |
| `rpo_hours` | number | Required. Most data, in hours, the business can afford to lose |
| `backup_type` | image, file, saas, replica, none | Required. `saas` means backed up by the provider or a SaaS backup service |
| `backup_frequency_hours` | number | Hours between backups (24 for nightly) |
| `offline_or_immutable` | true, false | At least one copy is offline, air-gapped, or immutable |
| `backup_encrypted` | true, false | |
| `separate_backup_credentials` | true, false | Backup system uses accounts separate from the production domain |
| `backup_monitored` | true, false | Someone is alerted when backups fail |
| `last_restore_test_date` | YYYY-MM-DD | Blank if never tested |
| `restore_time_hours` | number | Hours to restore this system |
| `restore_time_measured` | true, false | The restore time comes from a timed test |
| `depends_on` | semicolon-separated system names | Systems that must be restored first |

Blank true/false values are treated as not in place.

## Practices (JSON)

Start from `samples/practices_template.json`. Answer each practice `yes`, `partial`, or `no`:

| Id | Practice |
|---|---|
| P-01 | Incident response plan with a ransomware playbook |
| P-02 | Offline or printed copy of the response plan and key contacts |
| P-03 | MFA on remote access and email |
| P-04 | MFA and separate accounts for backup administration |
| P-05 | Endpoint protection on all computers and servers |
| P-06 | Internet-facing systems patched promptly |
| P-07 | Email filtering and phishing awareness training |
| P-08 | Network segmentation separating backups and critical systems |
| P-09 | Administrator accounts separate from everyday accounts |
| P-10 | Ransomware tabletop exercise in the last 12 months |

In the dashboard, practices can also be set directly in the sidebar and downloaded as a file.

These files describe your weaknesses. Store them and the reports securely.
