# Dev Container Integration

Use these snippets to run the Content Portals Dashboard as a VS Code task inside a dev container.

The examples assume this project lives at:

```text
${workspaceFolder}/projects/tfs-cherry-pick-dashboard
```

If you open the dashboard folder directly as the workspace, use the `.vscode/tasks.json` included in this project instead.

## Dev container settings

Add or merge the Streamlit port configuration into `.devcontainer/devcontainer.json`:

```json
{
  "forwardPorts": [8501],
  "portsAttributes": {
    "8501": {
      "label": "Content Portals Dashboard",
      "onAutoForward": "notify"
    }
  }
}
```

If the dev container already has a `postCreateCommand`, call the setup script from there instead of replacing the existing command:

```json
{
  "postCreateCommand": "bash projects/tfs-cherry-pick-dashboard/devcontainer-integration/post-create-dashboard.sh"
}
```

## Setup script

`post-create-dashboard.sh` creates an isolated virtual environment at:

```text
/home/vscode/.venvs/content-portals-dashboard
```

It resolves the dashboard root from its own location, so it can run from the copied project without hard-coded workspace paths.

## Root workspace task

If the opened VS Code workspace is the parent repository that contains `projects/tfs-cherry-pick-dashboard`, copy this task into the parent `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Content Portals Dashboard - Prepare",
      "type": "shell",
      "command": "bash ${workspaceFolder}/projects/tfs-cherry-pick-dashboard/devcontainer-integration/post-create-dashboard.sh",
      "problemMatcher": []
    },
    {
      "label": "Content Portals Dashboard - Run",
      "type": "shell",
      "command": "DASHBOARD_ROOT=\"${workspaceFolder}/projects/tfs-cherry-pick-dashboard\"; DASHBOARD_VENV=\"${DASHBOARD_VENV:-/home/vscode/.venvs/content-portals-dashboard}\"; if [ ! -x \"$DASHBOARD_VENV/bin/python\" ]; then bash \"$DASHBOARD_ROOT/devcontainer-integration/post-create-dashboard.sh\"; fi; \"$DASHBOARD_VENV/bin/python\" -m streamlit run \"$DASHBOARD_ROOT/app.py\" --server.address 0.0.0.0 --server.port 8501 --server.headless true",
      "isBackground": true,
      "problemMatcher": [],
      "options": {
        "env": {
          "REQUESTS_CA_BUNDLE": "/etc/ssl/certs/ca-certificates.crt",
          "TFS_DASHBOARD_AUTH_MODE": "Git Credentials"
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "clear": true
      }
    },
    {
      "label": "Content Portals Dashboard - Stop",
      "type": "shell",
      "command": "pkill -f 'streamlit run .*tfs-cherry-pick-dashboard.*app.py' || true",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "clear": true
      }
    }
  ]
}
```

## Local configuration inside the container

Create the runtime configuration from the safe example:

```bash
cd "${workspaceFolder}/projects/tfs-cherry-pick-dashboard"
cp config/tfs_dashboard.example.json config/tfs_dashboard.json
```

Then edit `config/tfs_dashboard.json` locally with the real TFS base URL, project, repositories, and branch chains.

## Credentials and certificates

The dev-container task defaults to `Git Credentials` because Windows integrated credentials are not available inside Linux containers.

Do not commit personal certificates, PATs, passwords, `.env`, `config/tfs_dashboard.json`, or exported Git credential stores. If the TFS server requires a company CA certificate, install it in the image or mount it outside the repository.
