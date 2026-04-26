# Internal Utility Service — Production Deployment

[![CI/CD Pipeline](https://github.com/gbadedata/internal-utility-service/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/gbadedata/internal-utility-service/actions/workflows/ci-cd.yml)

A production-hardened, containerised Flask web service deployed on AWS EC2 with full CI/CD automation, HTTPS, secrets management, and zero-downtime updates.

## Architecture

```
Developer → GitHub → GitHub Actions → Docker Hub → AWS EC2
                                                    ├── Nginx (reverse proxy, HTTPS)
                                                    ├── Flask App (non-root container)
                                                    └── AWS Secrets Manager
```

## Quick Start (local)

```bash
git clone https://github.com/gbadedata/internal-utility-service.git
cd internal-utility-service
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

## Dockerfile Structure

Multi-stage build with two stages:
- **Builder stage**: installs all dependencies using `pip install --prefix=/install` to a separate directory
- **Production stage**: copies only the installed packages and app source — no build tools, no cache, minimal attack surface
- Runs as non-root user (uid 1001)
- Includes `HEALTHCHECK` that polls `/health` every 30 seconds

**Why multi-stage?** Reduces the final image size by ~60% and eliminates build tools (gcc, pip cache) from production.

## Tagging Strategy

| Tag | When applied | Purpose |
|-----|-------------|---------|
| `latest` | Every push to main | Quick pull for deployment |
| `v1.0.<run_number>` | Every push to main | Semantic version for releases |
| `<7-char SHA>` | Every push to main | Pinned to exact commit for rollback |

## Secret Injection Strategy

- **GitHub Secrets** → used only during CI (Docker Hub credentials, EC2 SSH key, app secret key). Never appear in logs or image layers.
- **AWS Secrets Manager** → stores runtime secrets. The EC2 instance has an IAM role granting read access. The app reads secrets via boto3 at startup.
- No secrets exist in source code, Dockerfile, or commit history.

## CI/CD Workflow

1. **Test job**: Runs `flake8` linting then `pytest` with all 8 tests. Build is BLOCKED if any test fails.
2. **Build job**: Builds multi-stage Docker image, pushes 3 tags to Docker Hub. Only runs on push to `main`.
3. **Deploy job**: SSHes into EC2, pulls new image, restarts container. No manual intervention required.

## HTTPS Setup

- Nginx listens on port 443 with Let's Encrypt certificate
- HTTP (port 80) permanently redirects to HTTPS
- Auto-renewal configured via `certbot.timer` systemd service
- Certificate renews automatically every 60 days

## Update Strategy: Blue-Green Deployment

1. **Blue** (current) serves production traffic
2. Pull new image, start **Green** on port 5001
3. Health check Green — if passing, switch Nginx upstream to Green
4. Rename containers: Green becomes the new Blue
5. Old Blue kept as standby for instant rollback

**Rollback**: `docker start flask_app_blue` — zero downtime.

## Scaling Beyond One Instance

To scale to multiple EC2 instances:
1. Place an Application Load Balancer (ALB) in front
2. Use an Auto Scaling Group with launch templates referencing the Docker image
3. Use Amazon ECS or EKS to manage containers declaratively
4. Move from Secrets Manager per-instance to a centralised parameter store

## Trade-offs Made

| Decision | Trade-off |
|----------|-----------|
| Single EC2 instance | Simple but no HA — acceptable for a class project |
| nip.io domain | No custom domain cost — real production uses Route 53 |
| gunicorn 2 workers | Sufficient for low traffic — scale workers with load |
| SSH-based deploy | Simple but not GitOps — ECS/EKS would be more robust |

## Reflection Answers

**1. Dockerfile structure?** Multi-stage keeps production image lean and removes build tools from the attack surface.

**2. Multi-stage?** The builder installs everything including gcc; production only copies the result. Eliminates build-time dependencies from the shipped image.

**3. Tagging strategy?** `latest` for automation speed, semver for releases, SHA tag for auditability and exact rollback.

**4. GitHub Secrets + AWS Secrets Manager split?** GitHub Secrets are scoped to CI — they only exist inside the Actions runner. AWS Secrets Manager is scoped to the running application — the EC2 IAM role grants access without any credentials being stored anywhere.

**5. Avoiding downtime?** Blue-green: new version is fully healthy before any traffic switches. Rollback is instant.

**6. Scale to multiple EC2?** ALB + Auto Scaling Group + ECS or Kubernetes.

**7. Remaining security risks?** No WAF, no container image signing, EC2 SSH key must be rotated, no network egress filtering.

**8. Path to Kubernetes?** Replace Docker run commands with Kubernetes Deployments, use a Helm chart, migrate secrets to Kubernetes Secrets or External Secrets Operator backed by AWS Secrets Manager.

## Security Checklist

- [x] Non-root container user
- [x] No secrets in source code or image layers
- [x] EC2 Security Groups: only ports 22, 80, 443 open
- [x] HTTPS enforced, HTTP redirects
- [x] Container auto-restarts on crash
- [x] HEALTHCHECK in Dockerfile
- [x] .dockerignore prevents leaking files into image
