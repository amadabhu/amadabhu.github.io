---
order: 1
slug: enterprise-rag
name: Enterprise RAG
status: shipped
highlight: false
one_liner: A configurable, containerized RAG stack designed for secure (IL4/IL5) enterprise deployment.
stack:
  - Python 3.12
  - Chainlit
  - LangChain
  - AWS Bedrock
  - PostgreSQL / pgvector
  - BM25 hybrid search
  - Docker Compose
  - Helm / EKS
  - MinIO
links:
  - { label: "Repo (private)" }
---

A two-service RAG system: a **Chainlit** chat UI plus REST API, and a separate
**embedder** pipeline that loads, extracts, chunks, and stores documents.
Retrieval runs against **PostgreSQL/pgvector** with a custom `langchain-postgres`
fork that adds **BM25 + hybrid search** with a tunable semantic-weight knob. All
LLM and embedding inference is delegated to **AWS Bedrock** (Nova, Titan) — the
core containers don't need a GPU, which keeps the production footprint cheap and
portable.

Operationally the stack is built to be moved between environments without
rewrites: **Docker Compose** for local dev, a **Helm chart on EKS** for
production, MinIO for object storage, and a config
layer that flips between environments.
