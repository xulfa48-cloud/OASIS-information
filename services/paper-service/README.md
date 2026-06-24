# Paper Service

The Paper Service ingests, processes, and serves metadata and content for academic papers and documents within OASIS. Responsibilities:

- Ingest paper records from uploads, crawlers, and integration services.
- Extract metadata (title, authors, abstract, published_at) and produce normalized records.
- Generate and store embeddings via the novelty/gap engines.
- Expose search and retrieval API for frontend and downstream services.
- Emit events: paper.ingested, paper.updated, paper.deleted.

Architecture
- Node.js + TypeScript using Express for HTTP APIs.
- PostgreSQL as primary storage, with Redis for caching and short-lived queues.
- Uses pgvector for vector storage or an external vector DB via adapter.
- Publishes events to Kafka.
- Runs background workers for ingestion pipelines.

API contract (base /api/v1/papers)
- POST /api/v1/papers
  Request: { "title": "", "authors": [""], "abstract": "", "published_at": "ISO8601", "external_id": "" }
  Response: 201 -> { "id": "uuid", "status": "created" }

- GET /api/v1/papers/{id}
  Response: 200 -> full paper record

- POST /api/v1/papers/search
  Request: { "query": "text", "k": 10 }
  Response: 200 -> list of matches

Health & metrics
- /api/v1/health (liveness)
- /api/v1/ready (readiness: DB + Redis + Kafka)
- /metrics (Prometheus)

Environment
- PAPER_PORT=8082
- PAPER_ENV=production
- PAPER_DATABASE_URL=postgres://user:pass@host:5432/paperdb
- PAPER_REDIS_URL=redis://host:6379/0
- PAPER_KAFKA_BROKERS=broker1,broker2
- PAPER_LOG_LEVEL=info

Run locally
- cp .env.example .env
- docker-compose up -d postgres redis
- npm install
- npm run build
- npm start
