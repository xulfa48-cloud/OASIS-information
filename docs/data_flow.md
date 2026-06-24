# Data Flow

Key data flows:
- Ingestion: External ingestion -> paper-service -> store in Postgres -> emit paper.ingested -> consumers (kg, analytics)
- KG updates: paper-service transforms -> knowledge-graph-service creates nodes/edges -> emit kg.node.created
- Search: frontend -> gateway -> paper-service/knowledge-graph-service -> results returned

Backups
- Daily DB snapshots for Postgres.
- Objects in S3 have lifecycle rules and cross-region replication for DR.
