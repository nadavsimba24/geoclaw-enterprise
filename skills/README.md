# Skills Guide

Drop a Python module into this folder and expose `SKILL`. Each skill should:

```python
from pydantic import BaseModel
from . import Skill

class Args(BaseModel):
    field: str

def handler(field: str) -> str:
    return "..."

SKILL = Skill("name", "description", Args, handler)
```

## Suggested Hive Skills
- `map_normalize` – ensures every report has lat/lon, threat level, attachments.
- `memory_log` – appends structured JSON to `data/hive-stream.ndjson`.
- `slack_alert` – posts summaries to #hive-alerts with signed webhooks.

Use the examples (`geo_analyst`, `osint_station`) as templates.
