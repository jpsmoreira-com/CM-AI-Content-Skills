from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from tfs_dashboard import TfsClient, fetch_dashboard_rows, fetch_my_assigned_work_items, fmt_date, parse_branch_chain


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config" / "tfs_dashboard.json"
APP_DATA_VERSION = 2
AUTH_OPTIONS = ["Windows Credentials", "Git Credentials", "PAT"]
PORTAL_TEMPLATE = {
    "base_url": "",
    "project": "",
    "repository": "",
    "api_version": "6.0",
    "branch_chain": [],
    "lookback_days": 7,
    "max_prs_per_branch": 150,
    "verify_work_items_via_api": True,
    "auth_mode": "Windows Credentials",
}
DEFAULT_CONFIG = {
    "DEFAULT_PORTAL": "",
    "portals": [],
}
STATUS_CLASS = {
    "Done": "done",
    "Open": "open",
    "Abandoned": "abandoned",
    "Missing": "missing",
    "New": "new",
    "Active": "active",
    "Resolved": "resolved",
    "Closed": "closed",
}
DASHBOARD_SEVERITY_RANK = {"Missing": 0, "Open": 1, "Abandoned": 2, "Done": 3}
WORK_ITEM_STATE_RANK = {"Active": 0, "New": 1, "Resolved": 2, "Closed": 3}
CHERRY_PICK_SORT_OPTIONS = [
    "Severity",
    "Original Branch",
    "Work Item",
    "Original Author",
    "Title",
    "Missing Targets",
    "Open PRs",
    "Original PR Created",
]
WORK_ITEM_SORT_OPTIONS = [
    "Changed",
    "ID",
    "State",
    "Title",
    "Type",
    "Iteration / Sprint",
]


def load_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def normalize_portal_config(portal: Any, fallback_repository: Optional[str] = None) -> Dict[str, Any]:
    source = portal if isinstance(portal, dict) else {}
    repository = str(source.get("repository") or fallback_repository or PORTAL_TEMPLATE["repository"]).strip()
    branch_chain_raw = source.get("branch_chain", PORTAL_TEMPLATE["branch_chain"])
    if isinstance(branch_chain_raw, str):
        branch_chain = parse_branch_chain(branch_chain_raw)
    else:
        branch_chain = [str(branch).strip() for branch in branch_chain_raw or [] if str(branch).strip()]

    auth_mode = str(source.get("auth_mode", PORTAL_TEMPLATE["auth_mode"])).strip()
    if auth_mode not in AUTH_OPTIONS:
        auth_mode = PORTAL_TEMPLATE["auth_mode"]

    return {
        "base_url": str(source.get("base_url", PORTAL_TEMPLATE["base_url"])).strip().rstrip("/"),
        "project": str(source.get("project", PORTAL_TEMPLATE["project"])).strip(),
        "repository": repository,
        "api_version": str(source.get("api_version", PORTAL_TEMPLATE["api_version"])).strip() or PORTAL_TEMPLATE["api_version"],
        "branch_chain": branch_chain,
        "lookback_days": int(source.get("lookback_days", PORTAL_TEMPLATE["lookback_days"])),
        "max_prs_per_branch": int(source.get("max_prs_per_branch", PORTAL_TEMPLATE["max_prs_per_branch"])),
        "verify_work_items_via_api": bool(source.get("verify_work_items_via_api", PORTAL_TEMPLATE["verify_work_items_via_api"])),
        "auth_mode": auth_mode,
    }


def normalize_app_config(raw_config: Any) -> Dict[str, Any]:
    raw = raw_config if isinstance(raw_config, dict) else {}
    if "portals" not in raw:
        portal = normalize_portal_config(raw)
        return {
            "DEFAULT_PORTAL": portal["repository"],
            "portals": [portal],
        }

    portals: List[Dict[str, Any]] = []
    seen_repositories = set()
    for index, portal in enumerate(raw.get("portals", []), start=1):
        normalized = normalize_portal_config(portal, fallback_repository=f"Portal {index}")
        repository = normalized["repository"]
        if repository in seen_repositories:
            continue
        seen_repositories.add(repository)
        portals.append(normalized)

    if not portals:
        fallback_portal = normalize_portal_config({}, fallback_repository="Portal 1")
        portals = [fallback_portal]

    default_portal = str(raw.get("DEFAULT_PORTAL") or raw.get("default_portal") or raw.get("active_repository") or portals[0]["repository"]).strip()
    if default_portal not in {portal["repository"] for portal in portals}:
        default_portal = portals[0]["repository"]

    return {
        "DEFAULT_PORTAL": default_portal,
        "portals": portals,
    }


def save_app_config(config: Dict[str, Any]) -> None:
    normalized = normalize_app_config(config)
    save_json(CONFIG_PATH, normalized)


def get_portal_names(config: Dict[str, Any]) -> List[str]:
    return [portal["repository"] for portal in config["portals"]]


def get_portal_config(config: Dict[str, Any], repository: str) -> Dict[str, Any]:
    for portal in config["portals"]:
        if portal["repository"] == repository:
            return portal
    return config["portals"][0]


def resolve_portal_selector_state(config: Dict[str, Any]) -> str:
    portal_names = get_portal_names(config)
    pending_repository = st.session_state.pop("cp_pending_repository", None)
    if pending_repository in portal_names:
        st.session_state["cp_portal_selector"] = pending_repository
    elif st.session_state.get("cp_portal_selector") not in portal_names:
        st.session_state["cp_portal_selector"] = config["DEFAULT_PORTAL"]
    return st.session_state["cp_portal_selector"]


def build_runtime_signature(portal: Dict[str, Any], pat: str) -> str:
    signature = {
        "app_data_version": APP_DATA_VERSION,
        "base_url": portal["base_url"],
        "project": portal["project"],
        "repository": portal["repository"],
        "api_version": portal["api_version"],
        "branch_chain": portal["branch_chain"],
        "lookback_days": int(portal["lookback_days"]),
        "max_prs_per_branch": int(portal["max_prs_per_branch"]),
        "verify_work_items_via_api": bool(portal["verify_work_items_via_api"]),
        "auth_mode": portal["auth_mode"],
        "pat": pat if portal["auth_mode"] == "PAT" else "",
    }
    return json.dumps(signature, sort_keys=True)


def build_runtime_portal(portal: Dict[str, Any]) -> Dict[str, Any]:
    runtime_portal = dict(portal)
    auth_override = os.environ.get("TFS_DASHBOARD_AUTH_MODE", "").strip()
    if auth_override in AUTH_OPTIONS:
        runtime_portal["auth_mode"] = auth_override
    return runtime_portal


def html_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def badge_html(
    label: str,
    href: Optional[str] = None,
    extra: str = "",
    tone: Optional[str] = None,
    title: Optional[str] = None,
) -> str:
    css_class = STATUS_CLASS.get(tone or label, "missing")
    text = f"{html_escape(label)}{extra}"
    title_attr = f' title="{html_escape(title)}"' if title else ""
    if href:
        return (
            f'<a class="status-badge {css_class}" href="{html_escape(href)}" '
            f'target="_blank"{title_attr}>{text}</a>'
        )
    return f'<span class="status-badge {css_class}">{text}</span>'


def summary_dataframe(rows: List[Dict[str, Any]], branch_chain: List[str]) -> pd.DataFrame:
    items: List[Dict[str, Any]] = []
    for row in rows:
        entry: Dict[str, Any] = {
            "Work Item": row["work_items_label"],
            "Original": row["original_target"],
            "Original PR Status": row["original_status_label"],
            "Original PR Author": row.get("original_created_by", ""),
            "Propagation Status": row["overall"],
            "Branch Family": row["family_branch"],
            "Original PR": f"#{row['original_pr']['pull_request_id']}",
        }
        for branch in branch_chain:
            if branch == row["original_target"]:
                entry[branch] = "Original"
            elif branch in row["statuses"]:
                entry[branch] = row["statuses"][branch]["label"]
            else:
                entry[branch] = "-"
        items.append(entry)
    return pd.DataFrame(items)


def combine_row_statuses(rows: List[Dict[str, Any]]) -> str:
    if any(row["missing"] for row in rows):
        return "Missing"
    if any(row["open"] for row in rows):
        return "Open"
    if any(row["abandoned"] for row in rows):
        return "Abandoned"
    if rows:
        return "Done"
    return "-"


def short_iteration_name(value: str) -> str:
    if not value:
        return ""
    return value.split("\\")[-1]


def parse_sort_timestamp(value: Any) -> float:
    if not value:
        return 0.0
    try:
        normalized = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return 0.0


def first_work_item_id(row: Dict[str, Any]) -> int:
    items = row.get("work_items", [])
    return min(items) if items else 0


def dashboard_sort_key(row: Dict[str, Any], sort_by: str, branch_chain: List[str]) -> Any:
    branch_index = {branch: index for index, branch in enumerate(branch_chain)}
    title = (row.get("title") or row.get("family_branch") or "").lower()
    work_item = first_work_item_id(row)

    if sort_by == "Original Branch":
        return (branch_index.get(row["original_target"], 999), DASHBOARD_SEVERITY_RANK.get(row["overall"], 99), work_item, title)
    if sort_by == "Work Item":
        return (work_item, branch_index.get(row["original_target"], 999), title)
    if sort_by == "Original Author":
        return ((row.get("original_created_by") or "").lower(), work_item, title)
    if sort_by == "Title":
        return (title, work_item, branch_index.get(row["original_target"], 999))
    if sort_by == "Missing Targets":
        return (len(row["missing"]), len(row["open"]), work_item, title)
    if sort_by == "Open PRs":
        return (len(row["open"]), len(row["missing"]), work_item, title)
    if sort_by == "Original PR Created":
        return (parse_sort_timestamp(row["original_pr"].get("creation_date")), work_item, title)
    return (DASHBOARD_SEVERITY_RANK.get(row["overall"], 99), branch_index.get(row["original_target"], 999), work_item, title)


def row_matches_cherry_pick_filter(row: Dict[str, Any], later_branch: str, allowed_statuses: List[str]) -> bool:
    if not allowed_statuses:
        return False
    if later_branch == "Any later branch":
        labels = [summary["label"] for summary in row["statuses"].values()]
        return any(label in allowed_statuses for label in labels)
    summary = row["statuses"].get(later_branch)
    return bool(summary and summary["label"] in allowed_statuses)


def sort_dashboard_rows(rows: List[Dict[str, Any]], sort_by: str, descending: bool, branch_chain: List[str]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda row: dashboard_sort_key(row, sort_by, branch_chain), reverse=descending)


def row_opened_by_current_user(row: Dict[str, Any], current_user: Dict[str, Any]) -> bool:
    current_tokens = set(current_user.get("tokens", []))
    author_tokens = set(row.get("original_created_by_tokens", []))
    return bool(current_tokens and author_tokens and current_tokens.intersection(author_tokens))


def my_work_items_dataframe(my_items: List[Dict[str, Any]], dashboard_rows: List[Dict[str, Any]]) -> pd.DataFrame:
    dashboard_by_work_item: Dict[int, List[Dict[str, Any]]] = {}
    for row in dashboard_rows:
        for work_item_id in row["work_items"]:
            dashboard_by_work_item.setdefault(work_item_id, []).append(row)

    records: List[Dict[str, Any]] = []
    for item in my_items:
        related_rows = dashboard_by_work_item.get(item["id"], [])
        primary_row = related_rows[0] if related_rows else None
        dashboard_status = combine_row_statuses(related_rows)
        missing_targets = sorted({branch for row in related_rows for branch in row["missing"]})
        branch_families = sorted({row["family_branch"] for row in related_rows})
        records.append(
            {
                "ID": item["id"],
                "ID URL": primary_row["original_pr_url"] if primary_row else item["url"],
                "ID Tone": dashboard_status if related_rows else item["state"],
                "ID Title": "Open original PR" if primary_row else "Open work item",
                "Type": item["type"],
                "Title": item["title"],
                "State": item["state"],
                "State Rank": WORK_ITEM_STATE_RANK.get(item["state"], 99),
                "Iteration / Sprint": short_iteration_name(item["iteration_path"]),
                "Tags": item["tags"] or "-",
                "Dashboard Status": dashboard_status,
                "Missing Targets": ", ".join(missing_targets) if missing_targets else "-",
                "Branch Families": len(branch_families),
                "Changed": fmt_date(item["changed_date"]),
                "Changed Sort": parse_sort_timestamp(item["changed_date"]),
            }
        )
    return pd.DataFrame(records)


def ordered_state_options(items: List[Dict[str, Any]]) -> List[str]:
    priority = {"New": 0, "Active": 1, "Resolved": 2, "Closed": 3}
    states = {item["state"] for item in items if item.get("state")}
    return sorted(states, key=lambda state: (priority.get(state, 99), state))


def filter_and_sort_work_items_dataframe(
    dataframe: pd.DataFrame,
    *,
    selected_types: List[str],
    available_types: List[str],
    only_with_branch: bool,
    search_text: str,
    sort_by: str,
    descending: bool,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    filtered = dataframe.copy()

    if available_types:
        filtered = filtered[filtered["Type"].isin(selected_types)]
    if only_with_branch:
        filtered = filtered[filtered["Branch Families"] > 0]
    if search_text.strip():
        token = search_text.strip().lower()
        mask = (
            filtered["ID"].astype(str).str.contains(token, case=False, regex=False)
            | filtered["Title"].fillna("").str.lower().str.contains(token, regex=False)
            | filtered["Tags"].fillna("").str.lower().str.contains(token, regex=False)
            | filtered["Iteration / Sprint"].fillna("").str.lower().str.contains(token, regex=False)
        )
        filtered = filtered[mask]

    if filtered.empty:
        return filtered

    if sort_by == "ID":
        by = ["ID", "Changed Sort"]
        ascending = [not descending, False]
    elif sort_by == "State":
        by = ["State Rank", "Changed Sort", "ID"]
        ascending = [not descending, False, False]
    elif sort_by == "Title":
        by = ["Title", "Changed Sort"]
        ascending = [not descending, False]
    elif sort_by == "Type":
        by = ["Type", "Changed Sort"]
        ascending = [not descending, False]
    elif sort_by == "Iteration / Sprint":
        by = ["Iteration / Sprint", "Changed Sort"]
        ascending = [not descending, False]
    else:
        by = ["Changed Sort", "ID"]
        ascending = [not descending, False]

    return filtered.sort_values(by=by, ascending=ascending, kind="mergesort")


def render_tag_pills(tags_value: str) -> str:
    if not tags_value or tags_value == "-":
        return '<span class="muted">-</span>'

    tags = [tag.strip() for tag in tags_value.split(";") if tag.strip()]
    if not tags:
        return '<span class="muted">-</span>'
    return "".join(f'<span class="tag-pill">{html_escape(tag)}</span>' for tag in tags)


def render_my_work_items_table(dataframe: pd.DataFrame) -> str:
    headers = ["ID", "Type", "Title", "State", "Iteration / Sprint", "Tags", "Changed"]
    html = ['<div class="table-scroll"><table class="dashboard-table"><thead><tr>']
    for header in headers:
        html.append(f"<th>{html_escape(header)}</th>")
    html.append("</tr></thead><tbody>")

    for row in dataframe.to_dict(orient="records"):
        html.append("<tr>")
        html.append(
            "<td>"
            f"{badge_html(str(row['ID']), row['ID URL'], tone=str(row['ID Tone']), title=str(row['ID Title']))}"
            "</td>"
        )
        html.append(f"<td>{html_escape(row['Type'])}</td>")
        html.append(
            "<td>"
            f'<div class="wi-cell"><div>{html_escape(row["Title"])}</div></div>'
            "</td>"
        )
        html.append(f"<td>{badge_html(str(row['State']))}</td>")
        html.append(f"<td><code>{html_escape(row['Iteration / Sprint'])}</code></td>")
        html.append(f"<td>{render_tag_pills(str(row['Tags']))}</td>")
        html.append(f"<td>{html_escape(row['Changed'])}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    return "".join(html)


def render_status_table(rows: List[Dict[str, Any]], branch_chain: List[str]) -> str:
    headers = ["Work Item", "Original", "Opened By", "Branch Family"] + [branch for branch in branch_chain[1:]]
    html = ['<table class="dashboard-table">', "<thead><tr>"]
    for header in headers:
        html.append(f"<th>{html_escape(header)}</th>")
    html.append("</tr></thead><tbody>")

    for row in rows:
        html.append("<tr>")
        wi = row["work_items_label"]
        title = row["title"] or row["family_branch"]
        html.append(
            "<td>"
            f'<div class="wi-cell"><strong>{html_escape(wi)}</strong>'
            f'<div class="wi-sub">{html_escape(title)}</div></div>'
            "</td>"
        )
        html.append(
            "<td>"
            f"{badge_html(row['original_status_label'], row['original_pr_url'], ' · ' + html_escape(row['original_target']))}"
            "</td>"
        )
        html.append(f"<td>{html_escape(row.get('original_created_by') or '-')}</td>")
        html.append(f"<td><code>{html_escape(row['family_branch'])}</code></td>")

        for branch in branch_chain[1:]:
            if branch == row["original_target"]:
                html.append(f"<td>{badge_html(row['original_status_label'], row['original_pr_url'], ' · Original')}</td>")
                continue

            summary = row["statuses"].get(branch)
            if not summary:
                html.append("<td><span class=\"muted\">-</span></td>")
                continue

            best = summary["best_pr"]
            extra = ""
            href = None
            if best:
                extra = f" · #{best['pull_request_id']}"
                href = best.get("url")
            html.append(f"<td>{badge_html(summary['label'], href, extra)}</td>")
        html.append("</tr>")

    html.append("</tbody></table>")
    return "".join(html)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --cp-panel: #0f131a;
            --cp-panel-alt: #131923;
            --cp-panel-hover: #18202b;
            --cp-border: rgba(210, 220, 235, 0.12);
            --cp-border-strong: rgba(231, 224, 210, 0.22);
            --cp-header-bg: #e6e0d4;
            --cp-header-fg: #31281f;
            --cp-text: #e6edf7;
            --cp-text-muted: #9ba8bc;
            --cp-code-bg: #1a2330;
            --cp-code-border: rgba(128, 245, 191, 0.16);
            --cp-code-fg: #82e8b8;
            --cp-done-bg: rgba(110, 231, 183, 0.14);
            --cp-done-border: rgba(110, 231, 183, 0.42);
            --cp-done-fg: #9ce6c5;
            --cp-open-bg: rgba(125, 170, 255, 0.12);
            --cp-open-border: rgba(125, 170, 255, 0.34);
            --cp-open-fg: #bdd2ff;
            --cp-abandoned-bg: rgba(230, 184, 92, 0.14);
            --cp-abandoned-border: rgba(230, 184, 92, 0.34);
            --cp-abandoned-fg: #f0d392;
            --cp-missing-bg: rgba(239, 140, 140, 0.12);
            --cp-missing-border: rgba(239, 140, 140, 0.34);
            --cp-missing-fg: #f6b2b2;
        }
        .status-badge {
            display: inline-block;
            padding: 0.33rem 0.72rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.82rem;
            line-height: 1.35;
            text-decoration: none;
            border: 1px solid transparent;
            letter-spacing: 0.01em;
            transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
        }
        .status-badge.done {
            background: var(--cp-done-bg);
            color: var(--cp-done-fg);
            border-color: var(--cp-done-border);
        }
        .status-badge.new {
            background: rgba(194, 160, 255, 0.14);
            color: #d6c2ff;
            border-color: rgba(194, 160, 255, 0.34);
        }
        .status-badge.active {
            background: rgba(96, 165, 250, 0.14);
            color: #bfdbfe;
            border-color: rgba(96, 165, 250, 0.34);
        }
        .status-badge.resolved {
            background: rgba(250, 204, 21, 0.14);
            color: #fde68a;
            border-color: rgba(250, 204, 21, 0.34);
        }
        .status-badge.closed {
            background: rgba(148, 163, 184, 0.12);
            color: #cbd5e1;
            border-color: rgba(148, 163, 184, 0.28);
        }
        .status-badge.open {
            background: var(--cp-open-bg);
            color: var(--cp-open-fg);
            border-color: var(--cp-open-border);
        }
        .status-badge.abandoned {
            background: var(--cp-abandoned-bg);
            color: var(--cp-abandoned-fg);
            border-color: var(--cp-abandoned-border);
        }
        .status-badge.missing {
            background: var(--cp-missing-bg);
            color: var(--cp-missing-fg);
            border-color: var(--cp-missing-border);
        }
        .status-badge:hover {
            transform: translateY(-1px);
        }
        .dashboard-table {
            width: 100%;
            margin-top: 0.5rem;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid var(--cp-border);
            border-radius: 18px;
            background: var(--cp-panel);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
        }
        .dashboard-table th {
            text-align: left;
            background: var(--cp-header-bg);
            color: var(--cp-header-fg);
            padding: 0.85rem 0.9rem;
            border-bottom: 1px solid var(--cp-border-strong);
            position: sticky;
            top: 0;
            font-weight: 700;
        }
        .dashboard-table td {
            padding: 0.9rem 0.85rem;
            border-bottom: 1px solid var(--cp-border);
            border-right: 1px solid var(--cp-border);
            vertical-align: top;
            background: var(--cp-panel);
            color: var(--cp-text);
        }
        .dashboard-table th:not(:last-child),
        .dashboard-table td:not(:last-child) {
            border-right: 1px solid var(--cp-border);
        }
        .dashboard-table tbody tr:nth-child(even) td {
            background: var(--cp-panel-alt);
        }
        .dashboard-table tbody tr:hover td {
            background: var(--cp-panel-hover);
        }
        .dashboard-table tbody tr:last-child td {
            border-bottom: none;
        }
        .dashboard-table tbody tr:last-child td:first-child {
            border-bottom-left-radius: 18px;
        }
        .dashboard-table tbody tr:last-child td:last-child {
            border-bottom-right-radius: 18px;
        }
        .dashboard-table th:first-child {
            border-top-left-radius: 18px;
        }
        .dashboard-table th:last-child {
            border-top-right-radius: 18px;
        }
        .dashboard-table td strong {
            color: #f7fbff;
            font-size: 1.02rem;
        }
        .dashboard-table td code {
            display: inline-block;
            padding: 0.22rem 0.45rem;
            border-radius: 8px;
            background: var(--cp-code-bg);
            border: 1px solid var(--cp-code-border);
            color: var(--cp-code-fg);
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            font-size: 0.83rem;
        }
        .table-scroll {
            overflow-x: auto;
            padding-bottom: 0.2rem;
        }
        .tag-pill {
            display: inline-block;
            margin-right: 0.35rem;
            margin-bottom: 0.3rem;
            padding: 0.2rem 0.5rem;
            border-radius: 999px;
            background: rgba(230, 224, 212, 0.08);
            border: 1px solid rgba(230, 224, 212, 0.12);
            color: #d8dee9;
            font-size: 0.78rem;
            line-height: 1.35;
        }
        .wi-sub {
            color: var(--cp-text-muted);
            margin-top: 0.32rem;
            line-height: 1.55;
        }
        .muted {
            color: #728099;
        }
        .page-title {
            margin: 0;
            color: #f7fbff;
            font-size: 2.8rem;
            line-height: 1.02;
            font-weight: 800;
            letter-spacing: -0.03em;
        }
        div[data-testid="stPopover"] > button,
        div[data-testid="stButton"] > button {
            border-radius: 14px;
            height: 2.55rem;
        }
        div[data-testid="stPopover"] > button {
            min-width: 2.55rem;
            padding-inline: 0.6rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Content Portals Dashboard", layout="wide", initial_sidebar_state="collapsed")
    st.set_option("client.toolbarMode", "minimal")
    inject_css()

    flash_message = st.session_state.pop("cp_flash", "")
    if flash_message:
        st.success(flash_message)

    raw_config = load_json(CONFIG_PATH, DEFAULT_CONFIG)
    config = normalize_app_config(raw_config)
    if raw_config != config:
        save_app_config(config)

    portal_names = get_portal_names(config)
    resolve_portal_selector_state(config)

    title_col, controls_col = st.columns([6.0, 4.0], gap="small", vertical_alignment="top")
    with title_col:
        st.markdown('<h1 class="page-title">Content Portals Dashboard</h1>', unsafe_allow_html=True)
    with controls_col:
        controls_spacer, portal_col, refresh_col, settings_col = st.columns(
            [4, 4, 2, 1],
            gap="small",
            vertical_alignment="top",
        )
    with portal_col:
        selected_repository = st.selectbox(
            "Portal",
            options=portal_names,
            key="cp_portal_selector",
            label_visibility="collapsed",
            width=250,
        )

    if selected_repository != config["DEFAULT_PORTAL"]:
        config["DEFAULT_PORTAL"] = selected_repository
        save_app_config(config)

    active_portal = get_portal_config(config, selected_repository)
    runtime_portal = build_runtime_portal(active_portal)
    with refresh_col:
        refresh_clicked = st.button("Refresh", use_container_width=True)

    with settings_col:
        with st.popover("⚙", help="Portal settings", width="content"):
            st.markdown("**Portal settings**")
            st.caption("Portal definitions are stored in config/tfs_dashboard.json. PAT values stay only in the current session.")
            settings_pat_key = f"cp_pat::{selected_repository}"
            with st.form(f"portal_settings_{selected_repository}", clear_on_submit=False):
                edited_repository = st.text_input("Repository", value=active_portal["repository"])
                edited_base_url = st.text_input("Base URL", value=active_portal["base_url"])
                edited_project = st.text_input("Project", value=active_portal["project"])
                edited_api_version = st.text_input("API Version", value=active_portal["api_version"])
                edited_branch_chain = st.text_area(
                    "Branch Chain",
                    value="\n".join(active_portal["branch_chain"]),
                    height=120,
                    help="One branch per line, in the expected propagation order.",
                )
                edited_lookback_days = st.number_input(
                    "Lookback Days",
                    min_value=0,
                    max_value=5000,
                    value=int(active_portal["lookback_days"]),
                    help="0 means no date filter.",
                )
                edited_max_prs_per_branch = st.number_input(
                    "Max PRs per Branch",
                    min_value=20,
                    max_value=1000,
                    value=int(active_portal["max_prs_per_branch"]),
                    step=10,
                )
                edited_verify_work_items = st.checkbox(
                    "Resolve Work Items via API",
                    value=bool(active_portal["verify_work_items_via_api"]),
                    help="Recommended. If disabled, the app can only fall back to work item IDs inferred from branch names.",
                )
                edited_auth_mode = st.radio(
                    "Authentication",
                    AUTH_OPTIONS,
                    index=AUTH_OPTIONS.index(active_portal["auth_mode"]),
                    horizontal=True,
                )
                edited_pat = st.text_input(
                    "PAT (session only)",
                    type="password",
                    key=settings_pat_key,
                    help="Used only when Authentication is set to PAT. This value is not saved to disk.",
                )

                action_col1, action_col2, action_col3 = st.columns(3)
                save_portal = action_col1.form_submit_button("Save portal", use_container_width=True)
                save_as_new = action_col2.form_submit_button("Save as new", use_container_width=True)
                delete_portal = action_col3.form_submit_button(
                    "Delete",
                    use_container_width=True,
                    disabled=len(portal_names) == 1,
                )

            if save_portal or save_as_new:
                edited_branch_chain_list = parse_branch_chain(edited_branch_chain)
                new_portal = normalize_portal_config(
                    {
                        "base_url": edited_base_url,
                        "project": edited_project,
                        "repository": edited_repository,
                        "api_version": edited_api_version,
                        "branch_chain": edited_branch_chain_list,
                        "lookback_days": int(edited_lookback_days),
                        "max_prs_per_branch": int(edited_max_prs_per_branch),
                        "verify_work_items_via_api": bool(edited_verify_work_items),
                        "auth_mode": edited_auth_mode,
                    },
                    fallback_repository=selected_repository,
                )
                if not edited_branch_chain_list:
                    st.error("Define at least one branch in the propagation chain.")
                elif save_as_new and new_portal["repository"] in portal_names:
                    st.error("A portal with that repository name already exists.")
                elif save_portal and new_portal["repository"] != selected_repository and new_portal["repository"] in portal_names:
                    st.error("A portal with that repository name already exists.")
                else:
                    if save_portal:
                        updated_portals = []
                        for portal in config["portals"]:
                            if portal["repository"] == selected_repository:
                                updated_portals.append(new_portal)
                            else:
                                updated_portals.append(portal)
                        config["portals"] = updated_portals
                        config["DEFAULT_PORTAL"] = new_portal["repository"]
                        st.session_state["cp_flash"] = f"Portal '{new_portal['repository']}' saved."
                    else:
                        config["portals"].append(new_portal)
                        config["DEFAULT_PORTAL"] = new_portal["repository"]
                        st.session_state["cp_flash"] = f"Portal '{new_portal['repository']}' created."
                    if edited_auth_mode == "PAT" and edited_pat:
                        st.session_state[f"cp_pat::{new_portal['repository']}"] = edited_pat
                    save_app_config(config)
                    st.session_state["cp_pending_repository"] = config["DEFAULT_PORTAL"]
                    st.rerun()

            if delete_portal:
                remaining_portals = [portal for portal in config["portals"] if portal["repository"] != selected_repository]
                if not remaining_portals:
                    st.error("At least one portal must remain configured.")
                else:
                    config["portals"] = remaining_portals
                    config["DEFAULT_PORTAL"] = remaining_portals[0]["repository"]
                    save_app_config(config)
                    st.session_state["cp_pending_repository"] = config["DEFAULT_PORTAL"]
                    st.session_state["cp_flash"] = f"Portal '{selected_repository}' removed."
                    st.rerun()

    st.caption("Read-only mode. This app queries the TFS API and does not modify PRs, branches, or work items.")

    branch_chain = runtime_portal["branch_chain"]
    if not branch_chain:
        st.error("Define at least one branch in the propagation chain.")
        return

    auth_mode = runtime_portal["auth_mode"]
    pat_key = f"cp_pat::{selected_repository}"
    pat = st.session_state.get(pat_key, "") if auth_mode == "PAT" else ""
    if auth_mode == "PAT" and not pat:
        st.info("Open the settings button and enter a PAT to load this portal.")
        return

    runtime_signature = build_runtime_signature(runtime_portal, pat)
    refresh = refresh_clicked or runtime_signature != st.session_state.get("cp_dashboard_signature")

    if refresh or "cp_dashboard_payload" not in st.session_state:
        try:
            client = TfsClient(
                base_url=runtime_portal["base_url"],
                project=runtime_portal["project"],
                repository=runtime_portal["repository"],
                api_version=runtime_portal["api_version"],
                auth_mode=(
                    "pat"
                    if auth_mode == "PAT"
                    else "git_credentials"
                    if auth_mode == "Git Credentials"
                    else "default_credentials"
                ),
                pat=pat,
            )
            with st.spinner("Loading PRs and work items from TFS..."):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    dashboard_future = pool.submit(
                        fetch_dashboard_rows,
                        client=client,
                        branch_chain=branch_chain,
                        lookback_days=int(runtime_portal["lookback_days"]),
                        max_prs_per_branch=int(runtime_portal["max_prs_per_branch"]),
                        verify_work_items_via_api=bool(runtime_portal["verify_work_items_via_api"]),
                    )
                    my_work_future = pool.submit(
                        fetch_my_assigned_work_items,
                        client=client,
                        project=runtime_portal["project"],
                        top=200,
                    )

                    st.session_state["cp_dashboard_payload"] = dashboard_future.result()
                    try:
                        st.session_state["cp_my_work_payload"] = my_work_future.result()
                        st.session_state["cp_my_work_error"] = ""
                    except Exception as exc:
                        st.session_state["cp_my_work_payload"] = {"items": [], "work_item_ids": set()}
                        st.session_state["cp_my_work_error"] = str(exc)
                st.session_state["cp_dashboard_loaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state["cp_dashboard_signature"] = runtime_signature
        except Exception as exc:
            st.error(f"Failed to refresh the dashboard: {exc}")
            return

    payload = st.session_state.get("cp_dashboard_payload")
    if not payload:
        st.info("Load the dashboard to view results.")
        return

    rows = payload["rows"]
    repo_name = payload["repository_name"]
    loaded_at = st.session_state.get("cp_dashboard_loaded_at", "-")
    current_user = payload.get("current_user", {})
    my_work_payload = st.session_state.get("cp_my_work_payload", {"items": [], "work_item_ids": set()})
    my_work_error = st.session_state.get("cp_my_work_error", "")
    my_work_items = my_work_payload.get("items", [])
    my_work_item_ids = my_work_payload.get("work_item_ids", set())
    portal_work_item_ids = {work_item_id for row in rows for work_item_id in row["work_items"]}
    my_portal_work_items = [item for item in my_work_items if item["id"] in portal_work_item_ids]

    with st.expander("Filters", expanded=False):
        user_label = current_user.get("display_name") or "Unknown"
        st.caption(
            f"Source: {active_portal['project']}/{repo_name} | User: {user_label} | Updated at {loaded_at} | PRs scanned: {payload['pull_request_count']}"
        )
        scope = st.radio("Scope", options=["Mine", "All"], index=1, horizontal=True)

        filter_col1, filter_col2, filter_col3 = st.columns([1.1, 1.1, 1.2])
        selected_original = filter_col1.selectbox("Filter by Original Branch", options=["All"] + branch_chain, index=0)
        status_filter = filter_col2.multiselect(
            "Show Statuses",
            options=["Missing", "Open", "Abandoned", "Done"],
            default=["Missing", "Open", "Abandoned", "Done"],
        )
        search_text = filter_col3.text_input("Search", value="", placeholder="Work item, title, or branch")

        only_with_targets = st.checkbox(
            "Hide items whose original branch is already the last branch in the chain",
            value=True,
            help="Helps focus on items that can still propagate to later branches.",
        )
        only_completed_original = st.checkbox(
            "Only show completed original PRs",
            value=True,
            help="Avoids showing Missing before the original fix has been merged.",
        )

    status_summary = ", ".join(status_filter) if status_filter else "None"
    search_summary = search_text.strip() or "Any"
    st.caption(
        f"View: {scope} | Original branch: {selected_original} | Statuses: {status_summary} | Search: {search_summary}"
    )

    filtered = rows
    if scope == "Mine":
        if current_user.get("tokens"):
            filtered = [row for row in filtered if row_opened_by_current_user(row, current_user)]
        else:
            st.warning(
                "Could not resolve the current TFS user. Falling back to work items assigned to you for the Mine filter."
            )
            filtered = [
                row for row in filtered if any(work_item_id in my_work_item_ids for work_item_id in row["work_items"])
            ]
    if only_completed_original:
        filtered = [row for row in filtered if row["original_pr"].get("status") == "completed"]
    if selected_original != "All":
        filtered = [row for row in filtered if row["original_target"] == selected_original]
    if status_filter:
        filtered = [row for row in filtered if row["overall"] in status_filter]
    if search_text.strip():
        token = search_text.strip().lower()
        filtered = [
            row
            for row in filtered
            if token in row["work_items_label"].lower()
            or token in row["family_branch"].lower()
            or token in (row["title"] or "").lower()
        ]
    if only_with_targets:
        filtered = [row for row in filtered if row["expected_branches"]]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Visible Families", len(filtered))
    col2.metric("Missing CP", sum(1 for row in filtered if row["missing"]))
    col3.metric("Open PR", sum(1 for row in filtered if row["open"]))
    col4.metric("Fully Propagated", sum(1 for row in filtered if row["overall"] == "Done"))

    overview_tab, details_tab = st.tabs(["Overview", "Details"])

    with overview_tab:
        st.subheader("Cherry-Pick Status")
        cherry_control_col1, cherry_control_col2, cherry_control_col3, cherry_control_col4 = st.columns(
            [1.25, 1.55, 1.2, 0.7]
        )
        later_branch_options = ["Any later branch"] + branch_chain[1:]
        selected_later_branch = cherry_control_col1.selectbox("Later Branch", options=later_branch_options, index=0)
        selected_later_statuses = cherry_control_col2.multiselect(
            "Later Branch Status",
            options=["Missing", "Open", "Abandoned", "Done"],
            default=["Missing", "Open", "Abandoned", "Done"],
        )
        cherry_sort_by = cherry_control_col3.selectbox("Order By", options=CHERRY_PICK_SORT_OPTIONS, index=0)
        cherry_descending = cherry_control_col4.checkbox("Descending", value=False)

        cherry_rows = filtered
        if len(branch_chain) > 1 and (
            selected_later_branch != "Any later branch"
            or selected_later_statuses != ["Missing", "Open", "Abandoned", "Done"]
        ):
            cherry_rows = [
                row
                for row in cherry_rows
                if row_matches_cherry_pick_filter(row, selected_later_branch, selected_later_statuses)
            ]
        cherry_rows = sort_dashboard_rows(cherry_rows, cherry_sort_by, cherry_descending, branch_chain)

        if cherry_rows:
            st.markdown(render_status_table(cherry_rows, branch_chain), unsafe_allow_html=True)
        else:
            st.info("No rows match the current filters.")

        st.subheader("My Assigned Work Items")
        if my_work_error:
            st.warning(f"Failed to load assigned work items: {my_work_error}")
        elif not my_work_items:
            st.info("No work items are currently assigned to you.")
        else:
            portal_only_items = st.checkbox(
                "Only show work items linked to the selected portal",
                value=False,
                help="Useful when you want to focus only on backlog items already connected to the current documentation portal.",
            )
            scoped_my_work_items = my_portal_work_items if portal_only_items else my_work_items

            if not scoped_my_work_items:
                st.info("No assigned work items are currently linked to the selected portal.")
            else:
                state_options = ordered_state_options(scoped_my_work_items)
                type_options = sorted({item["type"] for item in scoped_my_work_items if item.get("type")})
                default_states = [state for state in ["New", "Active", "Resolved"] if state in state_options]
                if not default_states:
                    default_states = [state for state in state_options if state != "Closed"] or state_options

                work_filter_col1, work_filter_col2, work_filter_col3 = st.columns([1.25, 1.25, 1.7])
                selected_item_states = work_filter_col1.multiselect(
                    "Work Item States",
                    options=state_options,
                    default=default_states,
                    help="Closed work items are hidden by default.",
                )
                selected_item_types = work_filter_col2.multiselect(
                    "Types",
                    options=type_options,
                    default=type_options,
                )
                work_item_search = work_filter_col3.text_input(
                    "Search",
                    value="",
                    placeholder="ID, title, tag, or sprint",
                )

                work_option_col1, work_option_col2, work_option_col3 = st.columns([1.15, 0.85, 1.2])
                work_item_sort_by = work_option_col1.selectbox("Order By", options=WORK_ITEM_SORT_OPTIONS, index=0)
                work_item_descending = work_option_col2.checkbox("Descending", value=True)
                only_with_branch = work_option_col3.checkbox(
                    "Only with branch",
                    value=False,
                    help="Show only work items already linked to at least one branch family in the dashboard.",
                )

                visible_my_items = [item for item in scoped_my_work_items if item["state"] in selected_item_states]

                if not visible_my_items:
                    st.info("No assigned work items match the selected states.")
                else:
                    my_df = my_work_items_dataframe(visible_my_items, rows)
                    my_df = filter_and_sort_work_items_dataframe(
                        my_df,
                        selected_types=selected_item_types,
                        available_types=type_options,
                        only_with_branch=only_with_branch,
                        search_text=work_item_search,
                        sort_by=work_item_sort_by,
                        descending=work_item_descending,
                    )

                    if my_df.empty:
                        st.info("No assigned work items match the current table filters.")
                    else:
                        my_col1, my_col2, my_col3, my_col4 = st.columns(4)
                        my_col1.metric("Visible Assigned Items", len(my_df))
                        my_col2.metric("With Branch", int((my_df["Branch Families"] > 0).sum()))
                        my_col3.metric("Needing Propagation", int((my_df["Dashboard Status"] == "Missing").sum()))
                        my_col4.metric("Active", int((my_df["State"] == "Active").sum()))
                        st.markdown(render_my_work_items_table(my_df), unsafe_allow_html=True)

    with details_tab:
        if filtered:
            summary_df = summary_dataframe(filtered, branch_chain)
            st.download_button(
                "Export CSV",
                data=summary_df.to_csv(index=False).encode("utf-8"),
                file_name="cherry-pick-dashboard.csv",
                mime="text/csv",
            )
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            for row in filtered:
                title = row["title"] or row["family_branch"]
                header = (
                    f"WI {row['work_items_label']} | {row['original_target']} | "
                    f"Original {row['original_status_label']} | Propagation {row['overall']} | {title}"
                )
                with st.expander(header):
                    st.markdown(f"**Branch family:** `{row['family_branch']}`")
                    st.markdown(
                        f"**Original PR:** [#{row['original_pr']['pull_request_id']}]({row['original_pr_url']}) "
                        f"in `{row['original_target']}`"
                    )
                    st.markdown(
                        f"**Original PR status:** {row['original_status_label']}  \n"
                        f"**Opened by:** {row.get('original_created_by') or '-'}  \n"
                        f"**Created at:** {fmt_date(row['original_pr'].get('creation_date'))}  \n"
                        f"**Closed at:** {fmt_date(row['original_pr'].get('closed_date'))}"
                    )
                    for branch in row["expected_branches"]:
                        summary = row["statuses"][branch]
                        best = summary["best_pr"]
                        if best:
                            st.markdown(
                                f"- `{branch}`: **{summary['label']}** via "
                                f"[PR #{best['pull_request_id']}]({best.get('url')}) "
                                f"({fmt_date(best.get('creation_date'))})"
                            )
                        else:
                            st.markdown(f"- `{branch}`: **Missing**")
        else:
            st.info("No rows match the current filters.")


if __name__ == "__main__":
    main()
