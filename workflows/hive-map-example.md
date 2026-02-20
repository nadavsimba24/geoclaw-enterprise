# Hive Map Workflow (Example)

1. **Trigger** – Forager persona receives `/survey lat lon` command or scheduled prompt.
2. **Collect** – Runs `geo_analyst` + `osint_scan` + `file_manager` (photo hash) to gather local intel.
3. **Normalize** – Passes results to `map_normalize` (future skill) to enforce schema:
   ```json
   {
     "lat": 32.0853,
     "lon": 34.7818,
     "threat_level": "low",
     "summary": "Harbor calm, patrol spotted",
     "attachments": ["s3://hive-shots/2026-02-20T11-00Z.jpg"]
   }
   ```
4. **Persist** – Writes payload to `data/hive-stream.ndjson` and posts to HQ via Webhook.
5. **Map Update** – Geo-Intel tab refreshes by reading the NDJSON file or subscribing to MQTT topic.
6. **Alerting** – If threat ≥ medium, escalate to Slack channel defined in persona.

> Duplicate this file for each org. The workflow documentation doubles as runbook + audit trail.
