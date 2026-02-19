# ODGS Demo — Deployment Runbook

> Deploy the ODGS Sovereign Dashboard to `demo.metricprovenance.com` on Hostinger VPS (`145.223.100.34`).

---

## Prerequisites

- Hostinger VPS with Docker installed (or a fresh OS template from the Hostinger panel)
- Domain `metricprovenance.com` with DNS access
- SSH access to the VPS

---

## Step 1: DNS Configuration

Add an **A record** in your domain registrar (Hostinger panel or wherever `metricprovenance.com` is managed):

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `demo` | `145.223.100.34` | 3600 |

> Wait 5-15 minutes for DNS propagation. Verify with: `dig demo.metricprovenance.com`

---

## Step 2: Prepare the VPS

SSH into the VPS:

```bash
ssh root@145.223.100.34
```

If Docker is not installed:
```bash
curl -fsSL https://get.docker.com | sh
```

---

## Step 3: Clone and Deploy

```bash
git clone https://github.com/MetricProvenance/odgs-protocol.git /opt/odgs
cd /opt/odgs
docker compose up -d --build
```

Caddy will automatically provision a Let's Encrypt SSL certificate for `demo.metricprovenance.com`.

---

## Step 4: Verify

```bash
# Check containers are running
docker compose ps

# Check Caddy got the SSL cert
docker compose logs caddy | grep "certificate obtained"

# Test the endpoint
curl -I https://demo.metricprovenance.com
```

Visit **https://demo.metricprovenance.com** in your browser.

---

## Coexistence with n8n

If n8n is currently using ports 80/443 on this VPS, you have two options:

### Option A: Fresh OS (Recommended)
Use the Hostinger panel to switch to a clean Ubuntu + Docker template. Then follow this runbook from Step 2.

### Option B: Shared Caddy
Replace n8n's reverse proxy with the Caddy instance from this compose file. Add n8n's domain to the Caddyfile:

```
demo.metricprovenance.com {
    reverse_proxy odgs-demo:8501
}

n8n.yourdomain.com {
    reverse_proxy n8n:5678
}
```

Then connect n8n to the `odgs-net` Docker network and restart.

---

## Updates

To deploy changes after pushing to the repo:

```bash
cd /opt/odgs
git pull
docker compose up -d --build
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| SSL cert not provisioning | Ensure DNS A record resolves. Check `docker compose logs caddy` |
| Streamlit blank page | Check `docker compose logs odgs-demo` for Python errors |
| Port 80/443 in use | Stop n8n or use Option B above |
| Git errors in container | The Dockerfile initializes a local git repo; ensure `lib/` is copied |

---

*ODGS Protocol v3.3.0 · Sovereign Edition*
