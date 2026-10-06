# Methodology

## Purpose

The tool answers one question for a small or mid-sized organization: **if ransomware encrypted everything tonight, could we recover our critical systems in time?** It combines a system-by-system recovery analysis with a short review of protective practices. Practices are drawn from the CISA #StopRansomware Guide and NIST IR 8374, *Ransomware Risk Management: A Cybersecurity Framework Profile*. Control references are NIST SP 800-53 Rev. 5.

## Recovery targets

For each system, the organization records two business targets:

- **Recovery time objective (RTO):** the longest the business can be without the system.
- **Recovery point objective (RPO):** the most data, measured in hours, the business can afford to lose.

## Effective recovery time and dependencies

Systems often cannot be restored until the systems they depend on are working; for example, a business application usually needs the sign-in directory first. The tool calculates:

```
effective recovery time = own restore time + the slowest effective recovery time among its dependencies
```

If any dependency cannot be recovered (no backup or no recorded restore time), the dependent system cannot be recovered either. Circular dependencies are rejected.

## System checks

| Check | Finding | Penalty | Controls |
|---|---|---|---|
| RR-01 | No backup | 100 | CP-9 |
| RR-02 | No offline or immutable backup copy | 30 | CP-9 |
| RR-03 | Backup interval longer than the RPO | 15 | CP-9, CP-2 |
| RR-04 | Effective recovery time longer than the RTO, or recovery not possible | 20 | CP-10, CP-2 |
| RR-05 | Restore not tested in the last 12 months | 15 | CP-4, CP-9(1) |
| RR-06 | Restore time is an estimate, not measured | 5 | CP-4 |
| RR-07 | Backups use the same credentials as production (not applied to provider-hosted SaaS) | 10 | AC-6, CP-9 |
| RR-08 | Backup jobs not monitored | 5 | CP-9 |
| RR-09 | Backups not encrypted | 5 | CP-9(8), SC-28 |

Each system starts at 100 and loses the penalty for each finding, with a floor of 0. RR-04 is critical for systems rated critical and high otherwise.

## Practices

Ten organization-wide practices are answered In place, Partly, or Not in place, with weights reflecting how directly each prevents or limits a ransomware attack: MFA on remote access and email (3); response plan with a ransomware playbook, MFA and separate accounts for backup administration, endpoint protection, prompt patching of internet-facing systems, and network segmentation (2 each); offline copy of the response plan, email filtering and phishing training, separate administrator accounts, and a tabletop exercise (1 each). Partly counts half; unanswered counts as not in place.

## Readiness score

```
system score   = average of system scores weighted by criticality (critical 4, high 3, medium 2, low 1)
practice score = weighted share of practices in place
readiness      = 0.6 x system score + 0.4 x practice score
```

Bands: 80 or more Resilient, 60 to 79 Partially resilient, 40 to 59 Vulnerable, below 40 Highly vulnerable. Weights, the 12-month test window, and the band thresholds are in `src/ransomware_ready/data/model.json` and can be adjusted with `--model`.

## Limitations

- Restore times are only as reliable as the inventory; timed restore tests are the way to confirm them.
- The score is a transparent planning aid, not a prediction of whether an attack will succeed.
- The tool does not replace an incident response plan, legal counsel, or professional incident response support.
