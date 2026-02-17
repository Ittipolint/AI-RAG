# Init System Script

# 1. Setup Environment Variables
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env"
}

# 2. Start Docker Containers
Write-Host "Starting Docker containers..."
docker-compose up -d

# 3. Wait for Services
Write-Host "Waiting for services to be ready..."
Start-Sleep -Seconds 30

# 4. Initialize Keycloak
# We need to use the admin CLI or REST API to create the realm and client.
# Doing this via a temporary container using kcadm.sh is often cleanest.

Write-Host "Initializing Keycloak..."
docker exec rag_keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password SuperSecureKeycloakPass123!
docker exec rag_keycloak /opt/keycloak/bin/kcadm.sh create realms -s realm=rag-realm -s enabled=true
docker exec rag_keycloak /opt/keycloak/bin/kcadm.sh create clients -r rag-realm -s clientId=rag-client -s enabled=true -s publicClient=true -s "redirectUris=[\"*\"]" -s "webOrigins=[\"*\"]"
# Create a test user
docker exec rag_keycloak /opt/keycloak/bin/kcadm.sh create users -r rag-realm -s username=user -s enabled=true
docker exec rag_keycloak /opt/keycloak/bin/kcadm.sh set-password -r rag-realm --username user --new-password password

# 5. Initialize MinIO
# MinIO bucket creation is handled lazily in code, but good to be explicit.
# We can use mc (MinIO Client) but for simplicity we rely on the app logic or manual check.
# The app creates 'rag-documents' on upload if missing.

# 6. Pull Ollama Model
Write-Host "Pulling Ollama model (mistral)..."
docker exec rag_ollama ollama pull mistral

Write-Host "System Initialization Complete!"
Write-Host "Web UI: http://localhost/ui"
Write-Host "Keycloak: http://localhost/auth"
Write-Host "API: http://localhost/api"
