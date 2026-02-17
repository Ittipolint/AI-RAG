# AI-RAG System

This repository contains the configuration and source code for the AI RAG system.

## Setup

1. Copy `.env.example` to `.env` and fill in the required credentials.
2. Run `docker-compose up -d` to start the services.

## Services

- **Nginx**: Reverse proxy and load balancer.
- **Ollama**: LLM inference engine.
- **Qdrant**: Vector database.
- **LlamaIndex**: RAG framework and API.
- **MinIO**: Object storage.
- **Keycloak**: Authentication and authorization.
- **Open WebUI**: User interface.
