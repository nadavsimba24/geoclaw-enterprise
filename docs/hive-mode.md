# Hive Mode: From Solo Claws to a Living Intelligence Map

Geoclaw Enterprise treats every lightweight agent as a worker bee with reinforced claws. Each one forages, pulls data, and pins discoveries onto a shared map layer. When enough bees report back, the map becomes a living hive—patterns emerge, alerts trigger automatically, and leadership teams see the full picture at a glance.

## Core Metaphor
- **Bees** → Edge agents (laptops, rugged tablets, Raspberry Pis) running Geoclaw with a small skill pack.
- **Claws** → Tool calls: REST APIs, OSINT scrapers, file harvesters, command runners.
- **Hive Map** → Aggregated geospatial workspace; every report is geo-tagged and time-stamped.

## Enterprise Deployment Patterns
| Role | Device | Skill Pack | Output |
|------|--------|-----------|--------|
| Forager (Field Ops) | Rugged tablet | sensors, incident-report, photo-hash | GeoJSON of incidents + images |
| Analyst Bee (OSINT) | Cloud VM | osint_scan, news_digest, compliance_watch | Threat overlays + daily Slack brief |
| Guardian (Security/Facilities) | Mini-PC onsite | uptime_probe, env_monitor, camera_ping | Facility heatmap + escalation triggers |

## How It Works
1. **Persona loads** (e.g., `forager.yaml`) define tone, mission, approved channels.
2. **Skills auto-load** from `skills/` and expose structured tools to the LLM.
3. **Workflow** (see `workflows/hive-map-example.md`) dictates how to route findings:
   - Normalize data (`map_normalize` skill)
   - Attach geo/timestamp
   - Sync to hive storage (S3, PostGIS, even CSV for offline-first)
4. **Map view** (up to you): the `Geo-Intel` tab in `tui.py` can point to a local HTML/Leaflet dashboard or stream updates to whatever GIS platform the org already uses.

## Why Teams Like It
- **Edge ready:** every “bee” can run offline and sync later.
- **Composable:** drop a new skill file → entire hive learns the move.
- **Explainable:** each pin on the map includes the original chat + tool log.
- **Brandable:** swap personas, color palette, or even the bee icon to match your org.

> **Tagline:** *Many claws, one hive mind.*
