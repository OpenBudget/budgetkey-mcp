# Kubernetes Installation Instructions for BudgetKey MCP Server

This document provides instructions for an agent to deploy the BudgetKey MCP Server to the OpenBudget Kubernetes cluster.

## Overview

The BudgetKey MCP Server will be deployed to the Kubernetes cluster managed at `/Users/adam/Code/obudget/budgetkey-k8s`. The service will be accessible at `next.obudget.org/mcp`.

## Prerequisites

- Access to the `budgetkey-k8s` repository
- Docker image: `budgetkey/budgetkey-mcp:latest`
- The CI/CD pipeline automatically builds and pushes new versions

## Deployment Steps

### 1. Create Helm Chart

Create a new Helm chart in the `budgetkey-k8s` repository for the MCP server:

**Location:** `budgetkey-k8s/charts/mcp/`

**Files to create:**

#### `Chart.yaml`
```yaml
apiVersion: v2
name: mcp
description: BudgetKey MCP Server
type: application
version: 0.1.0
appVersion: "1.0"
```

#### `values.yaml`
```yaml
replicaCount: 1

image:
  repository: budgetkey/budgetkey-mcp
  tag: latest
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8000
  targetPort: 8000

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

env:
  BUDGETKEY_API_BASE: "https://next.obudget.org"
```

#### `values.auto-updated.yaml`
```yaml
# This file is automatically updated by CI/CD
mcp:
  image: budgetkey/budgetkey-mcp:latest
```

#### `templates/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "mcp.fullname" . }}
  labels:
    app: {{ include "mcp.name" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "mcp.name" . }}
  template:
    metadata:
      labels:
        app: {{ include "mcp.name" . }}
    spec:
      containers:
      - name: mcp
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
          protocol: TCP
        env:
        - name: BUDGETKEY_API_BASE
          value: {{ .Values.env.BUDGETKEY_API_BASE | quote }}
        livenessProbe:
          httpGet:
            path: /mcp/health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /mcp/health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
```

#### `templates/service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "mcp.fullname" . }}
  labels:
    app: {{ include "mcp.name" . }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
      name: http
  selector:
    app: {{ include "mcp.name" . }}
```

#### `templates/_helpers.tpl`
```yaml
{{- define "mcp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mcp.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}
```

### 2. Configure Ingress

Add the MCP service to the existing ingress configuration to expose it at `next.obudget.org/mcp`.

**Update the ingress configuration** (typically in `budgetkey-k8s/charts/traefik/values.yaml` or similar):

```yaml
ingress:
  rules:
    - host: next.obudget.org
      http:
        paths:
          # ... existing paths ...
          - path: /mcp
            pathType: Prefix
            backend:
              service:
                name: mcp
                port:
                  number: 8000
```

### 3. Deploy to Kubernetes

From the `budgetkey-k8s` directory:

```bash
# Install/upgrade the mcp chart
helm upgrade --install mcp ./charts/mcp \
  --namespace budgetkey \
  --create-namespace \
  --values ./charts/mcp/values.yaml \
  --values ./charts/mcp/values.auto-updated.yaml
```

### 4. Verify Deployment

```bash
# Check pods are running
kubectl get pods -n budgetkey -l app=mcp

# Check service is created
kubectl get svc -n budgetkey -l app=mcp

# Check logs
kubectl logs -n budgetkey -l app=mcp --tail=50

# Test the health check endpoint
curl https://next.obudget.org/mcp/health
```

## CI/CD Integration

The GitHub Actions workflow in `.github/workflows/deploy.yml` automatically:

1. Builds the Docker image on every push to `main`
2. Pushes the image to Docker Hub as `budgetkey/budgetkey-mcp:latest` and `budgetkey/budgetkey-mcp:${GITHUB_SHA}`
3. Updates `values.auto-updated.yaml` in the `budgetkey-k8s` repository with the new image tag

The Kubernetes cluster should have ArgoCD or a similar GitOps tool watching the `budgetkey-k8s` repository to automatically deploy updates.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BUDGETKEY_API_BASE` | Base URL for BudgetKey API | `https://next.obudget.org` |

### Resource Limits

Current settings:
- **Requests**: 250m CPU, 256Mi memory
- **Limits**: 500m CPU, 512Mi memory

Adjust these in `values.yaml` based on actual usage.

### Scaling

To scale horizontally:

```bash
kubectl scale deployment mcp --replicas=3 -n budgetkey
```

Or update `replicaCount` in `values.yaml`.

## Monitoring

### Health Checks

The server exposes health check endpoints:
- Liveness probe: `GET /mcp/health`
- Readiness probe: `GET /mcp/health`

### Logs

View logs:
```bash
kubectl logs -f -n budgetkey -l app=mcp
```

### Metrics

Consider adding Prometheus metrics if needed by updating the server to expose `/metrics`.

## Troubleshooting

### Pod not starting

```bash
# Describe the pod
kubectl describe pod -n budgetkey -l app=mcp

# Check events
kubectl get events -n budgetkey --sort-by='.lastTimestamp'
```

### Connection issues

```bash
# Test internal service connectivity (health check)
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n budgetkey -- \
  curl http://mcp:8000/mcp/health

# For full MCP protocol testing, configure an MCP client to connect to the service
```

### Image pull errors

Ensure Docker Hub credentials are configured if using a private repository:

```bash
kubectl create secret docker-registry dockerhub \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=$DOCKER_USERNAME \
  --docker-password=$DOCKER_PASSWORD \
  --namespace=budgetkey
```

Then reference in `values.yaml`:
```yaml
imagePullSecrets:
  - name: dockerhub
```

## Rollback

If a deployment fails:

```bash
# Rollback to previous version
helm rollback mcp -n budgetkey

# Or manually set a specific image tag
helm upgrade mcp ./charts/mcp \
  --namespace budgetkey \
  --set image.tag=<previous-git-sha>
```

## Maintenance

### Updating the server

Updates are automatic via CI/CD. To manually update:

```bash
cd budgetkey-k8s
# Edit values.auto-updated.yaml to use a specific image tag
helm upgrade mcp ./charts/mcp -n budgetkey
```

### Backup considerations

The MCP server is stateless and doesn't require backups. All data comes from the BudgetKey API.

## Security Considerations

1. The server is exposed publicly at `next.obudget.org/mcp`
2. No authentication is required (consistent with the public BudgetKey API)
3. Consider adding rate limiting at the ingress level if needed
4. SSL/TLS is handled by the ingress controller

## Next Steps

After deployment:

1. Test the MCP server with Claude Desktop using the URL `https://next.obudget.org/mcp`
2. Monitor logs and resource usage
3. Add monitoring/alerting if needed
4. Document any issues or improvements

## Support

For issues with Kubernetes deployment:
- Check the `budgetkey-k8s` repository
- Review Kubernetes cluster logs
- Contact the infrastructure team

For issues with the MCP server itself:
- Check the `budgetkey-mcp` repository
- Review application logs
- Open an issue on GitHub
