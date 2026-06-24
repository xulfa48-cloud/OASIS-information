# Incident Runbook

This runbook summarises steps to diagnose and respond to incidents affecting OASIS production.

1) Initial triage
- Acknowledge the alert in the incident channel.
- Record time, alert source, and initial symptoms.

2) Determine blast radius
- Which services are affected? (check /health endpoints or Grafana dashboards)
- Are there error spikes in logs? Use log query to find recent errors.

3) Mitigation
- If a single service is unhealthy: scale replicas, roll back recent deployment, or restart pods.
- If DB is failing: failover to replica and open a DB incident with on-call DBA.

4) Post-incident
- Root cause analysis with timeline, impact, and remediation tasks.
- Implement permanent fixes and update runbook.
