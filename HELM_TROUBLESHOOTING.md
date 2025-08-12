# Helm Deployment Troubleshooting

## Issue: POLYGON_API_KEY environment variable is not set

### Problem
Your Helm chart is using `envFrom` with a secret reference, but the secret key name doesn't match what the application expects.

### Solution

#### Option 1: Update your HelmRelease (Recommended)

Replace your current `env` and `envFrom` configuration with this:

```yaml
env:
  POLYGON_API_KEY:
    valueFrom:
      secretKeyRef:
        name: mcp-polygon
        key: POLYGON_API_KEY
  MCP_HTTP_TRANSPORT: "true"
  PORT: "8000"
```

#### Option 2: Update your Secret

Make sure your secret `mcp-polygon` contains the key `POLYGON_API_KEY`:

```bash
# Delete the old secret
kubectl delete secret mcp-polygon -n datasci

# Create the new secret with the correct key name
kubectl create secret generic mcp-polygon \
  --from-literal=POLYGON_API_KEY=your_polygon_api_key_here \
  -n datasci
```

#### Option 3: Use the provided secret example

1. Copy `k8s-secret-example.yaml`
2. Replace `<base64-encoded-api-key>` with your encoded API key:
   ```bash
   echo -n "your_polygon_api_key_here" | base64
   ```
3. Apply the secret:
   ```bash
   kubectl apply -f k8s-secret-example.yaml
   ```

### Complete HelmRelease Example

```yaml
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: &app mcp-polygon
spec:
  interval: 5m
  chart:
    spec:
      chart: app-template
      version: 3.7.3
      sourceRef:
        kind: HelmRepository
        name: bjw-s
        namespace: flux-system
  install:
    remediation:
      retries: -1
  upgrade:
    cleanupOnFail: true
    remediation:
      retries: 3
  values:
    controllers:
      mcp-polygon:
        annotations:
          reloader.stakater.com/auto: "true"
        containers:
          app:
            image:
              repository: ghcr.io/ekenheim/mcp-polygon
              tag: v1.5.1  # Use specific version for production stability
            env:
              POLYGON_API_KEY:
                valueFrom:
                  secretKeyRef:
                    name: mcp-polygon
                    key: POLYGON_API_KEY
              MCP_HTTP_TRANSPORT: "true"
              PORT: "8000"
              LOG_LEVEL: info
            resources:
              requests:
                cpu: 100m
                memory: 128Mi
              limits:
                cpu: 500m
                memory: 512Mi
    service:
      app:
        controller: *app
        ports:
          http:
            port: &port 8000
    ingress:
      app:
        className: internal
        annotations:
          gethomepage.dev/enabled: "true"
          gethomepage.dev/group: Data Science
          gethomepage.dev/name: MCP Polygon
          gethomepage.dev/icon: polygon.png
          gethomepage.dev/description: MCP Server for Polygon.io Financial Data
          external-dns.alpha.kubernetes.io/target: internal.${SECRET_DOMAIN}
        hosts:
        - host: "{{ .Release.Name }}.${SECRET_DOMAIN}"
          paths:
          - path: /
            service:
              identifier: app
              port: http
    persistence:
      config:
        enabled: true
        existingClaim: *app
        globalMounts:
          - path: /app/data
```

### Verification Steps

1. **Check if the secret exists**:
   ```bash
   kubectl get secret mcp-polygon -n datasci -o yaml
   ```

2. **Check if the secret has the correct key**:
   ```bash
   kubectl get secret mcp-polygon -n datasci -o jsonpath='{.data.POLYGON_API_KEY}' | base64 -d
   ```

3. **Check the pod environment variables**:
   ```bash
   kubectl exec -n datasci deployment/mcp-polygon -- env | grep POLYGON
   ```

4. **Check the logs**:
   ```bash
   kubectl logs -n datasci deployment/mcp-polygon
   ```

### Common Issues

1. **Secret key name mismatch**: The application expects `POLYGON_API_KEY`, not `api-key`
2. **Namespace mismatch**: Make sure the secret is in the same namespace as the deployment
3. **Base64 encoding**: Ensure your API key is properly base64 encoded
4. **Secret not created**: The secret must exist before the deployment starts
