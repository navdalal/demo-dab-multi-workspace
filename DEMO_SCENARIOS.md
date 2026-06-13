# Demo scenarios — live walkthrough

Four scenarios you can run live, in order. Each one has:
- **Setup** — the file edit (copy-paste ready)
- **Push** — exact click path to commit + push from Databricks
- **What you should see** — GitHub Actions behavior
- **Validate** — exactly where to look in each workspace to prove it worked

> **Architectural reminder for the customer:** in the UAT workspace UI you can only deploy to UAT — that's by design. The Bundle panel uses your UAT identity. For cross-workspace deployment, the source of truth is GitHub + Actions. The 4 scenarios below all use that path.

---

## Scenario 1 — One-line change in shared code fans out to all 3 workspaces

**The headline scenario. Run this first.**

### Setup
In UAT workspace → Git folder → open `shared/python/common_utils.py`.
Change line 11:

```python
SHARED_VERSION = "1.0.0"
```
to:
```python
SHARED_VERSION = "1.1.0"
```

### Push
1. Bottom-left of workspace UI → click the **`main`** branch indicator
2. Git dialog opens. Commit message: `bump shared version to 1.1.0`
3. Click **Commit & push**

### What you should see in GitHub Actions
Go to https://github.com/navdalal/demo-dab-multi-workspace/actions — three workflows fire **in parallel** because `shared/**` matches all three path filters:
- `deploy-common` → matrix of 3 (uat, us1, elt) → 3 deploys
- `deploy-us-only` → 1 deploy to US1
- `deploy-elt-only` → 1 deploy to ELT

Total: **5 deploys from one commit.**

### Validate

| Workspace | Click path | What proves it worked |
|---|---|---|
| **UAT** | Workflows → `common_demo_job` → **Run now** → open run output | Notebook prints `[shared_utils v1.1.0]` |
| **US1** | Workflows → `common_demo_job` → **Run now** | Same `v1.1.0` stamp |
| **US1** | Workflows → `us_regional_job` → **Run now** | Also picks up `v1.1.0` (proves shared code propagated even into the us_only bundle) |
| **ELT** | Workflows → `elt_specialized_job` → **Run now** | Same `v1.1.0` stamp |

**Talking point**: "One line changed. Five jobs across three workspaces now run the new code. Zero manual workspace copying."

---

## Scenario 2 — A US-only feature deploys only to US1

### Setup
In UAT workspace → Git folder → open `bundles/us_only/src/notebooks/us_job.py`.
After the existing import block, add a new cell with a US-specific calculation:

```python
# COMMAND ----------

# US-specific: dollar amounts in cents for IRS reporting
sample_amounts_usd = [19.99, 42.50, 9.95]
sample_amounts_cents = [int(round(x * 100)) for x in sample_amounts_usd]
print(f"US tax cents: {sample_amounts_cents}")
```

### Push
Same Git dialog. Commit message: `us: add IRS cents conversion`. Commit & push.

### What you should see in GitHub Actions
**Only one workflow fires**: `deploy-us-only`. `deploy-common` and `deploy-elt-only` do **not** run because the change touched only `bundles/us_only/**`.

### Validate

| Workspace | Click path | What proves it worked |
|---|---|---|
| **US1** | Workflows → `us_regional_job` → **Run now** → open output | New cell prints `US tax cents: [1999, 4250, 995]` |
| **ELT** | Workflows | `us_regional_job` does **not** exist here |
| **UAT** | Workflows | `us_regional_job` does **not** exist here either |

**Talking point**: "Notice that ELT and UAT didn't redeploy at all. The path filter on the workflow saw that nothing in `shared/` or `bundles/common_jobs/` changed, so it skipped them. The deployment topology is enforced by the repo layout, not by humans choosing the right workspace."

---

## Scenario 3 — An ELT-only schedule

### Setup
In UAT workspace → open `bundles/elt_only/resources/jobs.yml`.
Add a `schedule:` block right after `tags:` and before `tasks:`:

```yaml
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "UTC"
        pause_status: PAUSED
```

The file should look like:
```yaml
resources:
  jobs:
    elt_specialized_job:
      name: elt_specialized_job
      tags:
        bundle: elt_only
        owner: fe-demo
      schedule:                              # ← new
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "UTC"
        pause_status: PAUSED
      tasks:
        ...
```

### Push
Commit message: `elt: add 6 AM UTC daily schedule (paused)`. Commit & push.

### What you should see in GitHub Actions
Only **`deploy-elt-only`** runs. Common and US1 untouched.

### Validate

| Workspace | Click path | What proves it worked |
|---|---|---|
| **ELT** | Workflows → `elt_specialized_job` → **Schedules & triggers** tab | Shows `0 0 6 * * ? UTC` (Paused) |
| **US1** | Workflows → `common_demo_job` → Schedules & triggers | No schedule — proves the change didn't bleed across |
| **UAT** | Workflows → `common_demo_job` → Schedules & triggers | No schedule |

**Talking point**: "I scheduled a job to run daily at 6 AM UTC — but only in ELT, because that's where the elt_only bundle lives. The schedule is configuration in code; it ships when the bundle ships."

---

## Scenario 4 — Feature branch → PR → merge (the safe-trunk story)

This proves the production-grade flow: branch protection, PR review, then deploy.

### Setup
In UAT workspace:
1. Bottom-left → click `main` branch indicator
2. Click **Create branch**
3. Branch name: `feature/add-greet-stamp`
4. Click **Create**

Now you're on the feature branch in the workspace. Open `shared/python/common_utils.py`. Add a new function at the bottom:

```python
def stamp(workspace_label: str, bundle: str) -> str:
    """Return a single-line audit stamp for any bundle run."""
    return f"audit | ws={workspace_label} | bundle={bundle} | v{SHARED_VERSION}"
```

Now open `bundles/common_jobs/src/notebooks/common_job.py` and add this to the bottom cell, just before `display(...)`:

```python
from common_utils import stamp
print(stamp(workspace_label, "common_jobs"))
```

### Push the branch
1. Bottom-left Git dialog
2. Commit message: `feat: add audit stamp helper`
3. **Commit & push** (pushes the feature branch, not main)

### What should NOT happen
Check GitHub Actions — **nothing fires.** The workflows are configured to trigger only on push to `main`. This is what you want — branches are safe to experiment in.

### Open the PR
1. Browser → https://github.com/navdalal/demo-dab-multi-workspace
2. You'll see a yellow banner: *"feature/add-greet-stamp had recent pushes — Compare & pull request"*
3. Click **Compare & pull request**
4. PR title: `feat: add audit stamp helper`. Click **Create pull request**
5. Click **Merge pull request** → **Confirm merge**

### What you should see after the merge
The merge commit lands on `main` and triggers **all 3 workflows** (because both `shared/**` and `bundles/common_jobs/**` changed):
- `deploy-common` matrix of 3
- `deploy-us-only`
- `deploy-elt-only`

### Validate

| Workspace | Click path | What proves it worked |
|---|---|---|
| **UAT** | Workflows → `common_demo_job` → **Run now** | Output includes `audit | ws=uat | bundle=common_jobs | v1.1.0` |
| **US1** | Workflows → `common_demo_job` → **Run now** | Same audit line, `ws=us1` |
| **ELT** | Workflows → `common_demo_job` → **Run now** | Same audit line, `ws=elt` |
| **All 3** | SQL editor → `SELECT * FROM dab_demo.dab_demo_<ws>.common_runs ORDER BY run_at DESC LIMIT 5` | Run rows visible per workspace |

**Talking point**: "This is the production pattern. Developers work on feature branches without touching prod. Pull requests get reviewed. Merge to main is the deploy trigger. Each workspace is updated automatically, atomically, and identically."

---

## Quick validation reference card

Keep this handy during the demo.

### Where to look in each Databricks workspace
| What | Where |
|---|---|
| Job exists? | Left nav → **Workflows** → search by name |
| Last run output | Click job → **Runs** tab → click latest run → task → **Output** |
| Schedule | Click job → **Schedules & triggers** tab |
| Notebook source | Click job → task → notebook path link |
| Data rows | SQL editor → `SELECT * FROM dab_demo.<schema>.<table>` |

### Where to look in GitHub
| What | Where |
|---|---|
| Workflow runs | https://github.com/navdalal/demo-dab-multi-workspace/actions |
| Which jobs were triggered | Each workflow run → left sidebar shows matrix entries |
| What changed in this commit | Repo → **Commits** → click SHA |
| Path filter behavior | Workflow YAML at top of each `.github/workflows/*.yml` |

### Naming conventions you'll see
| Pattern | Meaning |
|---|---|
| `[dev <user>] <job_name>` | Deployed via UAT in `mode: development` — prefixed per-user |
| `<job_name>` (no prefix) | Deployed via GitHub Actions in `mode: production` |
| `dab_demo_uat`, `dab_demo_us1`, `dab_demo_elt` | Per-workspace schemas inside the `dab_demo` catalog |

---

## What "good" looks like at the end of the demo

After running scenarios 1–4, you should be able to say all of:

- ✅ The notebook output in **all three workspaces** shows the latest `SHARED_VERSION` and the audit stamp.
- ✅ Each workspace **has only the jobs it should have**:
  - UAT: `common_demo_job`
  - US1: `common_demo_job` + `us_regional_job`
  - ELT: `common_demo_job` + `elt_specialized_job`
- ✅ GitHub Actions history shows that the right workflows fired for the right changes (path filters worked).
- ✅ You never logged into US1 or ELT to push code — only GitHub did.
