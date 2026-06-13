# demo-dab-multi-workspace

A demo that proves you do **not** need to copy code, notebooks, or job
definitions across Databricks workspaces. One commit in GitHub fans out to
three workspaces via Databricks Asset Bundles + GitHub Actions.

> **Running the demo live?** Open [DEMO_SCENARIOS.md](DEMO_SCENARIOS.md) — four copy-paste scenarios with exact validation steps.

---

## 1. What this demo proves

1. A developer edits in the **Databricks UI** inside a Git folder (UAT).
2. Changes are committed and pushed back to **GitHub**.
3. A PR is merged on `main`.
4. **GitHub Actions** deploys the right bundles to the right workspaces.
5. **Shared code** propagates everywhere it's needed.
6. **Workspace-specific jobs** only deploy where they belong.

---

## 2. Workspaces & bundle map

| Workspace | Host | Region | Role | Bundles deployed |
|---|---|---|---|---|
| **UAT** | `dbc-51b48072-8f2d.cloud.databricks.com` | ap-south-1 | Developer / validation | `common_jobs` |
| **US1** | `dbc-20e51d9a-9bed.cloud.databricks.com` | us-east-1 | Regional prod | `common_jobs`, `us_only` |
| **ELT** | `dbc-776b219b-58bd.cloud.databricks.com` | ap-south-1 | Specialized prod | `common_jobs`, `elt_only` |

All three workspaces are **serverless-only**. The bundles do not declare
`new_cluster` or `job_cluster_key`, so notebook tasks run on serverless
notebook compute by default.

---

## 3. Repo structure

```
demo-dab-multi-workspace/
├── README.md
├── .github/workflows/
│   ├── deploy-common.yml         # matrix: uat, us1, elt
│   ├── deploy-us-only.yml        # us1 only
│   └── deploy-elt-only.yml       # elt only
├── bundles/
│   ├── common_jobs/
│   │   ├── databricks.yml        # targets: uat, us1, elt
│   │   ├── resources/jobs.yml    # common_demo_job
│   │   └── src/notebooks/common_job.py
│   ├── us_only/
│   │   ├── databricks.yml        # target: us1
│   │   ├── resources/jobs.yml    # us_regional_job
│   │   └── src/notebooks/us_job.py
│   └── elt_only/
│       ├── databricks.yml        # target: elt
│       ├── resources/jobs.yml    # elt_specialized_job
│       └── src/notebooks/elt_job.py
└── shared/
    ├── python/common_utils.py    # imported by every bundle notebook
    └── notebooks/shared_helper.py
```

**Shared code propagation:** each bundle declares
`sync.paths: [., ../../shared]`. On every `databricks bundle deploy`,
the `shared/` tree is copied into the workspace alongside the bundle.
Notebooks receive `shared_path = ${workspace.file_path}/shared/python`
as a job parameter and `sys.path.insert(0, shared_path)` to import.

---

## 4. One-time setup

### 4a. Create the `dab_demo` catalog in each workspace

The bundles default to the catalog `dab_demo`. Open the **SQL editor** in each of UAT, US1, ELT and run:

```sql
CREATE CATALOG IF NOT EXISTS dab_demo
  COMMENT 'Catalog for the multi-workspace DAB demo';
GRANT USE CATALOG, USE SCHEMA, CREATE SCHEMA, CREATE TABLE, MODIFY
  ON CATALOG dab_demo TO `account users`;
```

Schemas under it (`dab_demo_uat`, `dab_demo_us1`, `dab_demo_elt`) are created by the notebooks at run time. If you'd rather reuse an existing catalog, override the `catalog` variable per target in each `bundles/*/databricks.yml`.

### 4b. Create service principals (one per workspace)

For each workspace, create a service principal with `CAN_MANAGE` on the
bundle root path (or workspace admin for the demo) and generate an
**OAuth M2M secret**.

In each workspace UI:
1. Top-right user menu → **Settings** → **Identity and access** → **Service principals** → **Add service principal**.
2. Name it `gha-dab-deployer`.
3. Click into the SP → **Secrets** tab → **Generate secret**.
4. Copy the **Client ID** and **Secret** (secret shown once — save it).
5. Grant the SP workspace admin for the demo (Settings → Identity and access → Groups → `admins` → add member).

> Production tip: scope the SP to the specific bundle root paths rather than admin. For the demo, admin keeps the click-path short.

### 4c. Add GitHub repo secrets

Go to `github.com/navdalal/demo-dab-multi-workspace` → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Add nine secrets:

| Secret name | Value |
|---|---|
| `DATABRICKS_HOST_UAT` | `https://dbc-51b48072-8f2d.cloud.databricks.com` |
| `DATABRICKS_CLIENT_ID_UAT` | client id from UAT SP |
| `DATABRICKS_CLIENT_SECRET_UAT` | client secret from UAT SP |
| `DATABRICKS_HOST_US1` | `https://dbc-20e51d9a-9bed.cloud.databricks.com` |
| `DATABRICKS_CLIENT_ID_US1` | client id from US1 SP |
| `DATABRICKS_CLIENT_SECRET_US1` | client secret from US1 SP |
| `DATABRICKS_HOST_ELT` | `https://dbc-776b219b-58bd.cloud.databricks.com` |
| `DATABRICKS_CLIENT_ID_ELT` | client id from ELT SP |
| `DATABRICKS_CLIENT_SECRET_ELT` | client secret from ELT SP |

### 4d. Link GitHub to Databricks (UAT only — the dev workspace)

Generate a GitHub PAT (`Settings → Developer settings → Personal access tokens → Tokens (classic)` with `repo` scope), then in the **UAT** workspace UI:
1. Top-right avatar → **Settings** → **Linked accounts** (or **User Settings** → **Git Integration**).
2. **Git provider** = GitHub. Paste username + PAT. Save.

### 4e. Create the Git folder in UAT

In UAT workspace:
1. Left nav → **Workspace** → your home folder.
2. **Add ▸ Git folder**.
3. **Git repository URL**: `https://github.com/navdalal/demo-dab-multi-workspace`.
4. **Git provider**: GitHub. **Branch**: `main`. Click **Create Git folder**.
5. The folder appears in your workspace tree.

---

## 5. Demo flow (the exact sequence to perform live)

### Step 1 — open the bundle in UAT
- In UAT workspace, navigate to the Git folder.
- Open `bundles/common_jobs/databricks.yml`.
- Workspace UI auto-detects this is a bundle root and shows the **Bundle** side panel on the right.

### Step 2 — show the Bundle panel
On the right side of the editor:
- **Bundle resources** section lists `common_demo_job`. Click it — shows tasks, parameters, target.
- **Deployments** section shows current deployment status and recent runs.
- Top of the panel: target selector (defaults to `uat`).

> If the panel is collapsed, click the cube icon in the right gutter or use **View ▸ Show bundle panel**.

### Step 3 — make a small shared-code change
Open `shared/python/common_utils.py`. Change `SHARED_VERSION = "1.0.0"` to `"1.0.1"`. Save.

### Step 4 — deploy `common_jobs` to UAT from the UI
- In the Bundle panel, confirm target = `uat`.
- Click **Deploy**. Watch the deployment log appear at the bottom.
- When deploy completes, click into `common_demo_job` in the Bundle resources list.

### Step 5 — run the job from the UI
- In `common_demo_job`, click **Run now**.
- Click the run link → watch the notebook output: it prints `[shared_utils v1.0.1] hello from workspace 'uat' ...`.
- This proves the shared code propagated.

### Step 6 — commit and push from Databricks
- Bottom-left of the workspace UI: click the **Git** branch indicator (shows `main` and dirty indicator).
- In the Git dialog: review changes (`shared/python/common_utils.py`).
- Enter commit message: `bump shared_utils to 1.0.1`.
- Click **Commit & push**.

### Step 7 — merge in GitHub (or push directly if demoing trunk-based)
If you committed directly to `main`, the push triggers Actions immediately. If on a branch, open the PR in GitHub and merge.

### Step 8 — watch GitHub Actions fan out
Go to `github.com/navdalal/demo-dab-multi-workspace/actions`. You should see:
- `deploy-common` workflow runs (matrix: uat, us1, elt — three deploys in parallel).
- `deploy-us-only` and `deploy-elt-only` also fire because `shared/**` changed.

### Step 9 — verify in each workspace
- UAT: re-open the job — version stamped on the run history.
- US1: navigate to **Workflows** → `common_demo_job` and `us_regional_job` both exist; `elt_specialized_job` does **not**.
- ELT: **Workflows** → `common_demo_job` and `elt_specialized_job` both exist; `us_regional_job` does **not**.

This visually proves the per-bundle, per-target deployment model.

---

## 6. Talk track (3 minutes, live)

> "I'm in our **UAT workspace** — this is where developers work. We pulled the bundle repo in as a **Git folder**, so editing here is the same as editing in GitHub.
>
> When I open `databricks.yml`, the workspace recognises it's a bundle root and gives me this **Bundle panel** on the right. I can see every resource — here's our `common_demo_job` — and I can deploy and run it without leaving the UI. That's the **inner loop**: edit, deploy to my own workspace, run, iterate.
>
> Now watch — I'll change one line in `shared/python/common_utils.py`, bumping the version. I deploy to UAT, run the job, and the output proves the new shared code ran.
>
> But here's the key idea — **I never deploy from this UI to another workspace.** That's not what the workspace bundle editor is for. The workspace UI is for *this* workspace. For cross-workspace deployment, the source of truth is **GitHub**.
>
> So I commit and push from Databricks. That push hits `main`. GitHub Actions takes over.
>
> Look at the Actions tab. Three workflows fire in parallel — `deploy-common` runs as a **matrix** across UAT, US1, ELT. Path filters mean `us_only` only redeploys when its bundle or shared code changes, same for `elt_only`. Each workflow authenticates as a per-workspace service principal — no PATs, no copy-paste, no manual intervention.
>
> If I now look at US1 — `common_demo_job` is there, `us_regional_job` is there, but `elt_specialized_job` is not. Flip to ELT — opposite. The deployment topology is enforced by the bundle layout in Git, not by humans remembering which workspace gets what.
>
> The win: one change, three workspaces, zero copy-paste. And this pattern scales — to go from three workspaces to nine, we add six rows to the matrix and six secrets. The repo layout doesn't change."

---

## 7. Where stuff lives in the Databricks UI (cheat sheet)

| What you want | Where to click |
|---|---|
| Bundle panel | Open any file under a bundle root; panel on right side of editor. Cube icon in right gutter toggles it. |
| Deployments pane | Bundle panel → **Deployments** section (top half). |
| Bundle resources | Bundle panel → **Bundle resources** section (lists jobs, pipelines, etc.). |
| Deploy button | Bundle panel → **Deploy** button near the top. |
| Run job from UI | Bundle resources → click job → **Run now**. |
| Switch target | Bundle panel → target dropdown at top. (UAT users will only see `uat`.) |
| Git commit/push | Bottom-left status bar → branch name → opens Git dialog. |
| Git folder create | Workspace nav → **Add ▸ Git folder**. |
| Link GitHub | Avatar (top-right) → **Settings** → **Linked accounts** → **Git integration**. |

---

## 8. Constraints & design notes

- **Serverless only**: notebook tasks have no `new_cluster`/`job_cluster_key` — they default to serverless notebook compute. If you add Python wheel tasks later, you'll need a top-level `environments:` block on the job.
- **`sync.paths`** is the mechanism for cross-bundle shared code. It requires a recent Databricks CLI (≥ 0.230). The `databricks/setup-cli@main` action pulls the latest.
- **`mode: development`** on UAT prefixes deployed resource names with the user identity, so multiple devs can deploy the same bundle to UAT without collision.
- **`mode: production`** on US1/ELT pins the deploy under `/Workspace/Shared/.bundle/...` so it's stable and visible.
- **`.py` source notebooks** (with `# Databricks notebook source` header) are used instead of `.ipynb`. The workspace renders them as notebooks but git diffs stay clean — no execution counts, no output blobs. When you edit in the UI and commit, the diff is just the changed lines.
- **Scaling to 9 workspaces**: add rows to the matrix in `deploy-common.yml`, add targets in `bundles/common_jobs/databricks.yml`, and add the workspace-specific bundles as needed. The shape of the demo doesn't change.

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| Bundle panel doesn't appear | Make sure you opened a file *inside* a bundle root (`databricks.yml` exists in that dir or a parent). |
| `Error: cannot find host` in Actions | Secrets not set, or `DATABRICKS_HOST_*` missing the `https://` prefix. |
| `Error: 403 Forbidden` on deploy | Service principal lacks permission on the workspace or bundle root path. Add SP to `admins` for the demo. |
| Notebook can't import `common_utils` | The job param `shared_path` is empty, or `sync.paths` is missing — verify `bundles/<name>/databricks.yml` has the `sync:` block. |
| Wrong job appears in wrong workspace | Check which target the GitHub Actions matrix is using. Only `common_jobs` deploys everywhere; `us_only` should only have a `us1` target. |
