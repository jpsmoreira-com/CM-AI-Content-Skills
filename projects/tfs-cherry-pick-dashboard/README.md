# TFS Cherry-Pick Dashboard

Streamlit dashboard for checking whether documentation PRs have already been propagated to later branches.

The app is read-only. It queries TFS/Azure DevOps Server APIs and does not create cherry-picks, update pull requests, change branches, or modify work items.

## What it tracks

- Pull requests created or closed within the configured lookback window.
- Linked work item IDs across the configured branch chain.
- Propagation state for each later branch: `Done`, `Open`, `Abandoned`, or `Missing`.
- Original PR author, so the dashboard can filter between `Mine` and `All`.
- Assigned work items, including state, tags, and iteration/sprint.

## Project structure

```text
tfs-cherry-pick-dashboard/
  app.py
  tfs_dashboard.py
  requirements.txt
  run_dashboard.ps1
  .env.example
  config/
    tfs_dashboard.example.json
  certs/
    .gitkeep
  devcontainer-integration/
    README.md
    post-create-dashboard.sh
```

## Local quick start

```powershell
cd C:\CM-REPO\Content\CM-AI-Content-Skills\projects\tfs-cherry-pick-dashboard
Copy-Item config\tfs_dashboard.example.json config\tfs_dashboard.json
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

Or use:

```powershell
.\run_dashboard.ps1
```

## Configuration

Runtime portal definitions are stored in `config/tfs_dashboard.json`.

That file is intentionally ignored by Git because it can contain internal server URLs and local authentication choices. Start from `config/tfs_dashboard.example.json` and edit your local copy.

Example shape:

```json
{
  "DEFAULT_PORTAL": "ExampleDocumentationPortal",
  "portals": [
    {
      "base_url": "https://tfs.example.com/Collection",
      "project": "ProjectName",
      "repository": "ExampleDocumentationPortal",
      "api_version": "6.0",
      "branch_chain": ["11.1/dev", "11.2/dev", "11.3/dev", "12.0/dev"],
      "lookback_days": 7,
      "max_prs_per_branch": 150,
      "verify_work_items_via_api": true,
      "auth_mode": "Git Credentials"
    }
  ]
}
```

`DEFAULT_PORTAL` must match one `repository` value from `portals`.

## Authentication

Supported modes:

- `Windows Credentials`: useful when running locally on Windows with integrated authentication.
- `Git Credentials`: useful in WSL/dev containers when Git credentials are already configured.
- `PAT`: session-only in the Streamlit UI; PAT values are not written to disk by the app.

For dev containers, prefer `Git Credentials` and pass `TFS_DASHBOARD_AUTH_MODE=Git Credentials` through the task environment.

## Dev container task

The `devcontainer-integration` folder contains the setup script and task snippets needed to run this dashboard from a Linux/dev-container workspace.

The expected dev-container flow is:

1. Mount or include this project in the container workspace.
2. Run `devcontainer-integration/post-create-dashboard.sh` during `postCreateCommand` or as a setup task.
3. Start the dashboard with the provided VS Code task snippet.
4. Open the forwarded Streamlit port `8501`.

See `devcontainer-integration/README.md` for copy-ready snippets.

## Security notes

- Do not commit `config/tfs_dashboard.json`.
- Do not commit `.env`, Streamlit secrets, PATs, exported credential stores, or personal certificates.
- `certs/` is kept only as a placeholder; real certificate files are ignored by default.
