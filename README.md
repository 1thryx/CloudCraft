# CloudCrafter Production Capstone

A fully working microservices platform demonstrating production-grade cloud-native development practices.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│  Client                                                        │
│  ↑                                                                 │
│  ┌───────────────────────┐                                       │
│  │  Ingress (NGINX)      │                                       │
│  └───────────────────────┘                                       │
│         ↑       ↑       ↑       ↑                               │
│         ↓       ↓       ↓       ↓                               │
│  ┌───────────────────────┐ ┌───────────────────────┐             │
│  │  users-service        │ │  events-service       │             │
│  │  Port 5000            │ │  Port 5001            │             │
│  └───────────────────────┘ └───────────────────────┘             │
│         ↑                                   ↑                   │
│         ↓                                   ↓                   │
│  ┌───────────────────────┐ ┌───────────────────────┐             │
│  │  tickets-service      │ │  notifications-service│             │
│  │  Port 5002            │ │  Port 5003            │             │
│  └───────────────────────┘ └───────────────────────┘             │
│         ↑                                   ↑                   │
│         └─────────────── Event Flow ────────┘                   │
│                                                          │
│  Ticket Receipt Upload → S3 → Event → Notifications      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Summary

| Service | Port | Description |
|---------|------|-------------|
| users-service | 5000 | User registration, login, password management |
| events-service | 5001 | Event creation and processing |
| tickets-service | 5002 | Ticket creation and receipt upload with event triggering |
| notifications-service | 5003 | Email notifications triggered by ticket events |

### Event Flow

```
Client
  ↓
API / Ingress
  ↓
Tickets API
  ↓
Ticket / Receipt Upload
  ↓
S3-compatible storage (LocalStack)
  ↓
Event (ticket.receipt.uploaded)
  ↓
Notifications Service
  ↓
Notification / Confirmation
```

**Key behavior**: Uploading a ticket receipt automatically triggers the notification flow without manual intervention. The receipt upload endpoint publishes an event to S3, which triggers the notification process.

## Local Setup

### Prerequisites

- Python 3.12+
- pip install Flask Flask-JWT-Extended Flask-CORS requests boto3 localstack

### 1. Native/Local Development

Start all services natively without Docker:

```bash
chmod +x scripts/start-native.sh
./scripts/start-native.sh
```

Or start individual services:

```bash
# Users service
cd services/users && python app.py

# Events service  
cd services/events && python app.py

# Tickets service
cd services/tickets && python app.py

# Notifications service
cd services/notifications && python app.py
```

### 2. LocalStack (AWS Simulated Infrastructure)

Start LocalStack:

```bash
localstack start
```

Configure S3 bucket and events (automatically done by the Tickets service).

### 3. Kubernetes

Deploy to Kubernetes:

```bash
# Using Helm
helm install cloudcrafter charts/cloudcrafter --namespace cloudcrafter

# Or apply raw manifests
kubectl apply -f k8s/cloudcrafter.yaml
```

### 4. Docker

Build and run Docker images (when Docker is available):

```bash
# Build images
docker build -t cloudcrafter/users ./services/users
docker build -t cloudcrafter/events ./services/events
docker build -t cloudcrafter/tickets ./services/tickets
docker build -t cloudcrafter/notifications ./services/notifications

# Run containers
docker run -p 5000:5000 cloudcrafter/users
docker run -p 5001:5001 cloudcrafter/events
docker run -p 5002:5002 cloudcrafter/tickets
docker run -p 5003:5003 cloudcrafter/notifications
```

### 5. Helm

Install the Helm chart:

```bash
helm install cloudcrafter charts/cloudcrafter --namespace cloudcrafter
```

### 6. Argo CD

GitOps deployment via Argo CD:

- Argo CD syncs from the Git repository
- Changes to the repository trigger automatic synchronization
- Helm chart is the source of truth for Kubernetes resources

### 7. Observability

Access dashboards:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100 (for log queries)

### 8. Security

- JWT authentication with key rotation
- Secrets stored in Kubernetes Secrets (not committed to Git)
- Key rotation without downtime

### 9. CI/CD

GitHub Actions pipeline at `.github/workflows/ci-cd.yml`:
- Runs tests on every push
- Validates Kubernetes manifests
- Lints Helm chart
- Builds and publishes Docker images
- Updates Argo CD deployment configuration

## Deployment

### Helm Install

```bash
helm install cloudcrafter charts/cloudcrafter \
  --namespace cloudcrafter \
  --create-namespace
```

### Kubernetes Commands

```bash
kubectl get pods -n cloudcrafter
kubectl get services -n cloudcrafter
kubectl get ingress -n cloudcrafter
kubectl logs -n cloudcrafter -l app=users
kubectl describe pod -n cloudcrafter
```

### Event Flow Validation

```bash
# Create a ticket with receipt upload
curl -X POST http://cloudcrafter.local/tickets \
  -H "Content-Type: application/json" \
  -d '{"user_id": "testuser", "title": "Test Ticket", "description": "Test"}'

# Upload receipt (triggers event flow automatically)
curl -X POST http://cloudcrafter.local/tickets/{ticket_id}/receipt \
  -H "Content-Type: application/json" \
  -d '{"receipt_key": "s3://tickets/receipts/test-123/receipt.pdf"}'
```

## CI/CD

The GitHub Actions pipeline at `.github/workflows/ci-cd.yml` performs:

1. **Checkout** - Retrieve repository source
2. **Test** - Run application tests for all services
3. **Validate** - Verify Kubernetes manifests and Helm chart structure
4. **Lint** - Helm chart linting
5. **Render** - Render Helm templates for validation
6. **Build** - Build Docker images (when configured)
7. **Deploy** - Update Argo CD configuration for GitOps synchronization

## GitOps

Argo CD synchronizes the application from the Git repository:

```text
Git repository
      ↓
Argo CD
      ↓
Helm template rendering
      ↓
Kubernetes
      ↓
CloudCrafter application
```

- Argo CD application: `argocd/application/cloudcrafter-app.yaml`
- Automatic sync enabled with PR self-heal
- Secrets managed separately, not committed to Git

## Observability

### Prometheus Metrics

The services expose Prometheus-compatible metrics. Key metrics include:

- `up{service="users-service"}` - Service availability
- `http_requests_total` - Request rate by service and status
- `http_request_duration_seconds_bucket` - Latency percentiles

### Grafana Dashboards

Default dashboard includes:

- **Service Availability**: Up status for all four services
- **Request Rates**: Rate of HTTP requests per service
- **Error Rates**: Rate of 5xx errors per service
- **Latency (p95)**: 95th percentile request latency
- **Application Logs**: Log query via Loki

### Loki Log Collection

Application logs are collected by Loki and queryable through Grafana. The notificatons service sends structured logs that include:

- Service name
- Event type
- Ticket ID (when applicable)
- Timestamp

## Security

### JWT Authentication

- Users register at `/api/users/register`
- Users login at `/api/users/login`
- Protected endpoints require `Authorization: Bearer <token>` header
- JWT tokens contain user identity and key ID

### Key Rotation

The system supports automatic JWT key rotation without downtime:

```text
JWT Key A (currently active)
   ↓
rotate
   ↓
JWT Key B (new active key)
   ↓
old key temporarily accepted for existing tokens
```

**Rotation process**:

1. Call `POST /api/users/rotate-key` with valid JWT
2. New key is generated and marked as active
3. Existing keys are marked as inactive but remain valid for tokens already issued
4. New tokens are signed with the new key
5. Old tokens continue working until their natural expiration

**Important**: Secrets are stored in Kubernetes Secrets and never committed to Git.

### Key Rotation API

```http
POST /api/users/rotate-key
Authorization: Bearer <valid-jwt>

Response:
{
  "message": "JWT key rotation initiated",
  "new_key_id": "key-abc12345",
  "old_key_id": "key-def67890",
  "note": "Existing tokens signed with previous keys remain valid until expiration"
}
```

## Docker

### Building Images

```bash
# From repository root
docker build -t cloudcrafter/users ./services/users
docker build -t cloudcrafter/events ./services/events
docker build -t cloudcrafter/tickets ./services/tickets
docker build -t cloudcrafter/notifications ./services/notifications
```

### Running Containers

```bash
docker run -d -p 5000:5000 --name users cloudcrafter/users
docker run -d -p 5001:5001 --name events cloudcrafter/events
docker run -d -p 5002:5002 --name tickets cloudcrafter/tickets
docker run -d -p 5003:5003 --name notifications cloudcrafter/notifications
```

### Image Details

- **Base image**: `python:3.12-slim` (minimal, reproducible)
- **Multi-stage build**: Builder image only used for dependency installation
- **Non-root execution**: Runs as `nonroot:nonroot` user
- **Health checks**: Configured in Dockerfiles and Kubernetes manifests
- **No secrets baked in**: Configuration supplied via environment variables at runtime
- **`.dockerignore`**: Excludes test files, caches, and sensitive data

### Configuration at Runtime

All configuration is supplied through environment variables:

| Variable | Service | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | users | JWT signing key |
| `ENV` | all | Environment (development/production) |
| `USERS_PORT` | users | Service port |
| `EVENTS_PORT` | events | Service port |
| `TICKETS_PORT` | tickets | Service port |
| `NOTIFICATIONS_PORT` | notifications | Service port |
| `S3_ENDPOINT_URL` | tickets | LocalStack/S3 endpoint |
| `S3_BUCKET` | tickets | S3 bucket name |
| `NOTIFICATIONS_URL` | tickets | Notifications service URL |

### Troubleshooting

Common issues and fixes:

1. **Connection refused** - Ensure all services are started before making API calls
2. **Authentication failures** - Verify JWT token is valid and not expired
3. **Event flow not triggering** - Check S3 bucket accessibility and LocalStack status
4. **Key rotation not working** - Ensure the requesting token is valid and not expired
5. **Port conflicts** - Adjust port environment variables

## Troubleshooting

### Common Failures and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `Connection refused` on service endpoint | Service not started | Start the service or check Docker container status |
| `401 Unauthorized` on protected endpoints | Invalid/expired JWT token | Re-authenticate via `/api/users/login` |
| `500 Internal Server Error` | Missing configuration | Check environment variables are set |
| `Event flow not triggering` | S3/LocalStack not accessible | Verify LocalStack is running and bucket exists |
| `Key rotation has no effect` | Using expired token | Generate new token after rotation |
| `Cannot connect to LocalStack` | LocalStack not running | Start LocalStack with `localstack start` |

### Debug Commands

```bash
# Check service health
curl http://localhost:5000/api/users/me (requires auth)
curl http://localhost:5001/api/events

# Check Kubernetes resources
kubectl get pods -n cloudcrafter
kubectl get events -n cloudcrafter

# Check logs
kubectl logs -n cloudcrafter -l app=tickets
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes following the existing architecture
4. Run local tests
5. Submit pull request
6. Ensure CI/CD pipeline passes

## License

This project is licensed under the MIT License.