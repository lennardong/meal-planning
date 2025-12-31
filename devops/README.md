# DevOps: Deploying Palatte

> A narrative guide to deploying Palatte to the cloud. Written for future-you who's forgotten everything.

---

## What We're Building

```
                    You push code
                         │
                         ▼
              ┌─────────────────────┐
              │   GitHub Release    │
              │     (e.g. v1.0.0)   │
              └──────────┬──────────┘
                         │ triggers
                         ▼
              ┌─────────────────────┐
              │   GitHub Actions    │
              │   (build & push)    │
              └──────────┬──────────┘
                         │ pushes image to
                         ▼
              ┌─────────────────────┐
              │  Artifact Registry  │
              │  (container store)  │
              └──────────┬──────────┘
                         │ deploys to
                         ▼
              ┌─────────────────────┐
              │     Cloud Run       │◄──── runtime-palatte
              │  (runs your app)    │      (service account)
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  palatte.dudleyong  │
              │       .com          │
              └─────────────────────┘
```

**Cost:** $0-5/month (scales to zero when idle)

---

## Base Requirements

Before choosing any architecture, we defined what we needed:

| Requirement | Why |
|-------------|-----|
| **Container hosting** | We have a Dockerfile, need somewhere to run it |
| **CI/CD on release** | Don't want to manually deploy every time |
| **Custom domain** | palatte.dudleyong.com looks professional |
| **KISS** | This is a personal project, not a startup |
| **Low cost** | Ideally free or near-free for light usage |
| **Minimal ops** | No servers to patch, no clusters to manage |

---

## Architecture Decisions

### Container Hosting: Why Cloud Run?

We considered several options. Here's the honest evaluation:

```
┌────────────────────┬──────────┬─────────────────────────────────────────┐
│ Option             │ Verdict  │ Reasoning                               │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ GKE (Kubernetes)   │ REJECTED │ Massive overkill. You'd spend more time │
│                    │          │ managing the cluster than building the  │
│                    │          │ app. K8s is for teams, not solo devs.   │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ Compute Engine     │ REJECTED │ It's just a VM. You'd have to:          │
│ (VM)               │          │ - Keep it running 24/7 ($$$)            │
│                    │          │ - Patch the OS                          │
│                    │          │ - Handle crashes/restarts               │
│                    │          │ - Set up nginx, SSL, etc.               │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ App Engine         │ REJECTED │ Works, but more opinionated than Cloud  │
│                    │          │ Run. Less control over container config.│
│                    │          │ Cloud Run is the modern successor.      │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ Cloud Run          │ CHOSEN   │ - Serverless: no infra to manage        │
│                    │          │ - Scales to zero: pay nothing when idle │
│                    │          │ - One command deploy                    │
│                    │          │ - Free SSL certificates                 │
│                    │          │ - Custom domains supported              │
└────────────────────┴──────────┴─────────────────────────────────────────┘
```

**The key insight:** Cloud Run is "containers without the container orchestration." You give it a Docker image, it runs it. That's it.

---

### CI/CD: Why GitHub Actions?

```
┌────────────────────┬──────────┬─────────────────────────────────────────┐
│ Option             │ Verdict  │ Reasoning                               │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ Cloud Build        │ REJECTED │ GCP-native, but requires clicking       │
│                    │          │ around in the console to set up         │
│                    │          │ triggers. Config lives outside the repo.│
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ Jenkins            │ REJECTED │ Self-hosted = another thing to maintain.│
│                    │          │ Great for enterprises, overkill here.   │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ CircleCI / Travis  │ REJECTED │ External service, another account.      │
│                    │          │ GitHub Actions does the same thing.     │
├────────────────────┼──────────┼─────────────────────────────────────────┤
│ GitHub Actions     │ CHOSEN   │ - Config lives in the repo (.yml file)  │
│                    │          │ - Free for public repos                 │
│                    │          │ - Triggers on releases (what we want)   │
│                    │          │ - Portable: move repo, CI moves too     │
└────────────────────┴──────────┴─────────────────────────────────────────┘
```

**The key insight:** Your CI/CD config should live with your code. When you clone the repo, everything needed to deploy should be there.

---

### Security: Why Two Service Accounts?

This is the one area where we didn't take the "simplest" option:

```
┌─────────────────────────┬──────────┬────────────────────────────────────┐
│ Option                  │ Verdict  │ Reasoning                          │
├─────────────────────────┼──────────┼────────────────────────────────────┤
│ Single service account  │ REJECTED │ Violates principle of least        │
│ for everything          │          │ privilege. If the running container│
│                         │          │ is compromised, attacker gets      │
│                         │          │ deploy permissions too.            │
├─────────────────────────┼──────────┼────────────────────────────────────┤
│ Workload Identity       │ REJECTED │ The "proper" way for production.   │
│ Federation              │          │ No keys to manage. But adds        │
│                         │          │ complexity and GCP-specific config.│
│                         │          │ Overkill for a personal project.   │
├─────────────────────────┼──────────┼────────────────────────────────────┤
│ Two accounts:           │ CHOSEN   │ Right balance of security vs       │
│ deployer + runtime      │          │ simplicity. 5 extra lines of       │
│                         │          │ script, significant security gain. │
└─────────────────────────┴──────────┴────────────────────────────────────┘
```

**The two accounts:**

| Account | Purpose | Permissions |
|---------|---------|-------------|
| `deployer-github-actions` | Used by CI/CD to push images and deploy | Can write to Artifact Registry, can deploy to Cloud Run |
| `runtime-palatte` | Used by Cloud Run to run the service | Minimal (none for this app) |

**The key insight:** If someone hacks your running container, they only get the runtime account's permissions (which is nothing for this app). They can't push malicious images or redeploy.

---

### What We Intentionally Skipped

Things that would be "best practice" in production but are overkill here:

| Feature | Why We Skipped It |
|---------|-------------------|
| **Persistent storage** | Data is ephemeral. Resets on deploy. This is fine for a meal planner - we use default sample data. |
| **Database (Cloud SQL)** | No user accounts, no data that needs to survive restarts. JSON files are enough. |
| **Cloud Monitoring alerts** | Nice to have, but we'll just check if it's up occasionally. |
| **Multiple environments** | No staging/prod split. It's a personal project, we test locally. |
| **Terraform/Pulumi** | Infrastructure as Code is great, but we only have 3 scripts. Not worth the abstraction layer. |

---

## Folder Structure

```
devops/
├── README.md              ← You are here
├── todo.md                ← Deployment checklist
├── cloud/                 ← Cloud deployment scripts
│   ├── config.env         ← Shared configuration
│   ├── 01-setup-project.sh    ← One-time GCP setup
│   ├── 02-manual-deploy.sh    ← Manual deploy (testing)
│   └── 03-setup-domain.sh     ← Custom domain setup
├── docker/
│   └── Dockerfile.dash-app    ← The container definition
└── scripts/
    └── ...                    ← Other dev scripts
```

---

## Script Reference

### `cloud/config.env`
Shared configuration. All scripts source this file. Edit here to change project ID, region, service names, etc.

### `cloud/01-setup-project.sh`
**Run once** when setting up a new GCP project. Creates:
- Artifact Registry repository
- Two service accounts (deployer + runtime)
- IAM permissions
- Exports key file for GitHub Actions

### `cloud/02-manual-deploy.sh`
Manual deployment for testing. Useful when:
- First deploy to verify setup works
- Hotfixes that can't wait for a release
- Debugging deployment issues

Usage:
```bash
./02-manual-deploy.sh          # Auto-generates version
./02-manual-deploy.sh v1.0.0   # Specific version
```

### `cloud/03-setup-domain.sh`
Maps a custom domain to Cloud Run. Tells you what DNS records to add.

Usage:
```bash
./03-setup-domain.sh                       # Uses default domain
./03-setup-domain.sh myapp.example.com     # Custom domain
```

---

## The GitHub Actions Workflow

Located at `.github/workflows/deploy.yml`

**Trigger:** Publishing a GitHub release

**What it does:**
1. Checks out code
2. Authenticates to GCP using `GCP_SA_KEY` secret
3. Builds Docker image
4. Pushes to Artifact Registry (tagged with release version)
5. Deploys to Cloud Run
6. Outputs service URL in GitHub Actions summary

---

## Cost Breakdown

| Service | Free Tier | Our Usage | Cost |
|---------|-----------|-----------|------|
| Cloud Run | 2M requests/month, 360k GB-seconds | Minimal | $0 |
| Artifact Registry | 500MB storage | ~200MB image | $0 |
| GitHub Actions | 2000 min/month (public) | ~2 min/deploy | $0 |

**Total: $0-5/month** depending on traffic spikes.

The `--max-instances=2` setting caps costs even if traffic spikes unexpectedly.

---

## Security Summary

| Aspect | Status |
|--------|--------|
| HTTPS | Automatic via Cloud Run |
| Authentication | Public (intentional for this app) |
| Service accounts | Separated (deployer vs runtime) |
| Secrets | Only `GCP_SA_KEY` in GitHub, no app secrets |
| Key file | In `.gitignore`, never committed |

---

## Next Steps

See `todo.md` for the deployment checklist.
