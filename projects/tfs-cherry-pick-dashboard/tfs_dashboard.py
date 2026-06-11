from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse, urlencode

import requests
from requests_ntlm import HttpNtlmAuth


STATUS_PRIORITY = {"completed": 3, "active": 2, "abandoned": 1}
STATUS_LABELS = {
    "completed": "Done",
    "active": "Open",
    "abandoned": "Abandoned",
    "missing": "Missing",
}


class TfsApiError(RuntimeError):
    pass


def normalize_base_url(value: str) -> str:
    return value.strip().rstrip("/")


def clean_branch(value: str) -> str:
    return value.replace("refs/heads/", "").strip()


def branch_ref(value: str) -> str:
    return value if value.startswith("refs/heads/") else f"refs/heads/{value}"


def branch_token(value: str) -> str:
    return clean_branch(value).replace("/", "-")


def parse_branch_chain(value: str) -> List[str]:
    items: List[str] = []
    for line in value.replace(",", "\n").splitlines():
        branch = clean_branch(line)
        if branch and branch not in items:
            items.append(branch)
    return items


def extract_work_item_ids_from_branch(branch_name: str) -> List[int]:
    match = re.search(r"/(\d+)(?:-|$)", branch_name)
    if match:
        return [int(match.group(1))]
    return []


def normalize_source_branch(source_branch: str, branch_chain: List[str]) -> str:
    normalized = clean_branch(source_branch)
    for branch in branch_chain:
        suffix = f"-on-{branch_token(branch)}"
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_date(value: Optional[str]) -> str:
    parsed = parse_iso_date(value)
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M") if parsed else "-"


def severity_rank(status: str) -> int:
    return {"Missing": 0, "Open": 1, "Abandoned": 2, "Done": 3}.get(status, 9)


def best_pr(prs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not prs:
        return None

    def sort_key(pr: Dict[str, Any]):
        date_value = parse_iso_date(pr.get("closed_date") or pr.get("creation_date"))
        stamp = date_value.timestamp() if date_value else 0
        return (STATUS_PRIORITY.get(pr.get("status", ""), 0), stamp)

    return max(prs, key=sort_key)


def summarize_target(prs: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not prs:
        return {"label": "Missing", "prs": [], "best_pr": None}
    selected = best_pr(prs)
    label = STATUS_LABELS.get(selected.get("status", ""), "Missing") if selected else "Missing"
    return {"label": label, "prs": prs, "best_pr": selected}


def short_source_label(source_branch: str) -> str:
    return clean_branch(source_branch).split("/")[-1]


def build_pr_web_url(base_url: str, project: str, repository: str, pr_id: int) -> str:
    return f"{normalize_base_url(base_url)}/{project}/_git/{repository}/pullrequest/{pr_id}"


def build_work_item_web_url(base_url: str, project: str, work_item_id: int) -> str:
    return f"{normalize_base_url(base_url)}/{project}/_workitems/edit/{work_item_id}"


def build_repository_web_url(base_url: str, project: str, repository: str) -> str:
    return f"{normalize_base_url(base_url)}/{project}/_git/{repository}"


def chunked(items: List[int], size: int) -> List[List[int]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def pull_request_time_range_types(min_time: Optional[str]) -> List[Optional[str]]:
    return ["created", "closed"] if min_time else [None]


def canonical_identity_token(value: Any) -> str:
    text = str(value or "").strip().casefold()
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def identity_property_value(properties: Dict[str, Any], key: str) -> str:
    value = properties.get(key)
    if isinstance(value, dict):
        return str(value.get("$value") or "")
    return str(value or "")


def identity_tokens(value: Any) -> Set[str]:
    tokens: Set[str] = set()
    if isinstance(value, dict):
        for key in (
            "id",
            "descriptor",
            "subjectDescriptor",
            "displayName",
            "providerDisplayName",
            "uniqueName",
            "mail",
            "principalName",
        ):
            token = canonical_identity_token(value.get(key))
            if token:
                tokens.add(token)

        properties = value.get("properties")
        if isinstance(properties, dict):
            for key in ("Account", "Domain", "Mail", "DisplayName"):
                token = canonical_identity_token(identity_property_value(properties, key))
                if token:
                    tokens.add(token)
    else:
        token = canonical_identity_token(value)
        if token:
            tokens.add(token)
    return tokens


def git_credential_values(url: str) -> Dict[str, str]:
    git = shutil.which("git")
    if not git:
        raise TfsApiError("Git executable was not found. Install Git or use PAT authentication.")

    result = subprocess.run(
        [git, "credential", "fill"],
        input=f"url={url}\n\n",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise TfsApiError(result.stderr.strip() or "Git credential lookup failed.")

    values: Dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value

    username = values.get("username", "")
    password = values.get("password", "")
    if not password:
        parsed = urlparse(url)
        raise TfsApiError(
            f"No Git credential password/token was found for {parsed.netloc}. "
            "Run a Git command against this repository first or configure a credential helper."
        )

    return {
        "username": username,
        "password": password,
    }


def powershell_json_request(url: str, method: str = "GET", body_json: Optional[str] = None) -> Any:
    shell = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
    body_block = ""
    invoke_args = f'-Uri "{url}" -Method {method} -Headers @{{ Accept = \'application/json\' }}'
    if body_json is not None:
        body_block = f"""
$body = @'
{body_json}
'@
"""
        invoke_args += " -ContentType 'application/json' -Body $body"

    script = f"""
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
{body_block}
try {{
    $response = Invoke-RestMethod {invoke_args} -UseDefaultCredentials
    $response | ConvertTo-Json -Depth 100
}} catch {{
    $message = $_.Exception.Message
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {{
        $message = $message + "`n" + $_.ErrorDetails.Message
    }}
    Write-Error $message
    exit 1
}}
"""
    result = subprocess.run(
        [shell, "-NoProfile", "-Command", script],
        capture_output=True,
    )
    stdout = result.stdout
    stderr = result.stderr
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if result.returncode != 0:
        raise TfsApiError(stderr.strip() or stdout.strip() or "Failed to call PowerShell.")
    output = stdout.strip()
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise TfsApiError(f"Invalid JSON response from the API: {exc}") from exc


def powershell_json_get(url: str) -> Any:
    return powershell_json_request(url, "GET")


def powershell_json_post(url: str, body: Any) -> Any:
    return powershell_json_request(url, "POST", json.dumps(body))


def powershell_json_get_many(urls: List[str]) -> Dict[str, Any]:
    if not urls:
        return {}

    shell = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
    urls_json = json.dumps(urls)
    script = f"""
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$urls = @'
{urls_json}
'@ | ConvertFrom-Json
$results = [ordered]@{{}}
try {{
    foreach ($url in $urls) {{
        $response = Invoke-RestMethod -Uri $url -Method Get -UseDefaultCredentials -Headers @{{ Accept = 'application/json' }}
        $results[$url] = $response
    }}
    $results | ConvertTo-Json -Depth 100
}} catch {{
    $message = $_.Exception.Message
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {{
        $message = $message + "`n" + $_.ErrorDetails.Message
    }}
    Write-Error $message
    exit 1
}}
"""
    result = subprocess.run(
        [shell, "-NoProfile", "-Command", script],
        capture_output=True,
    )
    stdout = result.stdout
    stderr = result.stderr
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if result.returncode != 0:
        raise TfsApiError(stderr.strip() or stdout.strip() or "Failed to call PowerShell.")
    output = stdout.strip()
    if not output:
        return {}
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise TfsApiError(f"Invalid JSON response from the API: {exc}") from exc
    return data if isinstance(data, dict) else {}


class TfsClient:
    def __init__(
        self,
        *,
        base_url: str,
        project: str,
        repository: str,
        api_version: str,
        auth_mode: str,
        pat: str = "",
        timeout_seconds: int = 60,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.project = project.strip()
        self.repository = repository.strip()
        self.api_version = api_version.strip()
        self.auth_mode = auth_mode
        self.pat = pat.strip()
        self.timeout_seconds = timeout_seconds
        self._git_auth: Optional[HttpNtlmAuth] = None

    def build_url(self, path: str, **params: Any) -> str:
        query = {"api-version": self.api_version}
        for key, value in params.items():
            if value is None or value == "":
                continue
            query[key] = value
        encoded = urlencode(query)
        return f"{self.base_url}/{self.project}/_apis/{path}?{encoded}"

    def build_collection_url(self, path: str, api_version: Optional[str] = None, **params: Any) -> str:
        query = {"api-version": api_version or self.api_version}
        for key, value in params.items():
            if value is None or value == "":
                continue
            query[key] = value
        encoded = urlencode(query)
        return f"{self.base_url}/_apis/{path}?{encoded}"

    def request_headers(self, *, content_type: Optional[str] = None) -> Optional[Dict[str, str]]:
        if self.auth_mode == "pat":
            token = base64.b64encode(f":{self.pat}".encode("ascii")).decode("ascii")
            headers = {
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
            }
        elif self.auth_mode == "git_credentials":
            headers = {"Accept": "application/json"}
        else:
            return None

        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def request_auth(self) -> Optional[HttpNtlmAuth]:
        if self.auth_mode != "git_credentials":
            return None
        if not self._git_auth:
            credentials = git_credential_values(
                build_repository_web_url(self.base_url, self.project, self.repository)
            )
            self._git_auth = HttpNtlmAuth(credentials["username"], credentials["password"])
        return self._git_auth

    def request_json(self, method: str, url: str, body: Any = None) -> Any:
        headers = self.request_headers(content_type="application/json" if body is not None else None)
        if headers is None:
            if method == "POST":
                return powershell_json_post(url, body)
            return powershell_json_get(url)

        response = requests.request(
            method,
            url,
            headers=headers,
            auth=self.request_auth(),
            json=body,
            timeout=self.timeout_seconds,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:800]
            raise TfsApiError(f"{exc}\n{detail}") from exc
        return response.json() if response.content else None

    def get_json(self, url: str) -> Any:
        if self.auth_mode in {"pat", "git_credentials"}:
            return self.request_json("GET", url)
        return powershell_json_get(url)

    def post_json(self, url: str, body: Any) -> Any:
        if self.auth_mode in {"pat", "git_credentials"}:
            return self.request_json("POST", url, body)
        return powershell_json_post(url, body)

    def get_json_many(self, urls: List[str]) -> Dict[str, Any]:
        if self.auth_mode in {"pat", "git_credentials"}:
            results: Dict[str, Any] = {}
            headers = self.request_headers()
            for url in urls:
                response = requests.get(url, headers=headers, auth=self.request_auth(), timeout=self.timeout_seconds)
                try:
                    response.raise_for_status()
                except requests.HTTPError as exc:
                    detail = response.text[:800]
                    raise TfsApiError(f"{exc}\n{detail}") from exc
                results[url] = response.json()
            return results
        return powershell_json_get_many(urls)

    def resolve_repository(self) -> Dict[str, Any]:
        url = self.build_url("git/repositories")
        payload = self.get_json(url) or {}
        repos = payload.get("value", []) if isinstance(payload, dict) else payload
        wanted = self.repository.lower()
        for repo in repos:
            if str(repo.get("name", "")).lower() == wanted or str(repo.get("id", "")).lower() == wanted:
                return repo
        raise TfsApiError(f"Repository '{self.repository}' was not found.")

    def get_pull_requests_for_target(
        self,
        repository_id: str,
        target_branch: str,
        max_items: int,
        lookback_days: int,
    ) -> List[Dict[str, Any]]:
        page_size = min(max_items, 100)
        skip = 0
        rows: List[Dict[str, Any]] = []
        min_time = None
        if lookback_days > 0:
            min_time = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

        by_id: Dict[int, Dict[str, Any]] = {}
        for query_time_range_type in pull_request_time_range_types(min_time):
            skip = 0
            while len(by_id) < max_items:
                url = self.build_url(
                    f"git/repositories/{repository_id}/pullrequests",
                    **{
                        "searchCriteria.status": "all",
                        "searchCriteria.targetRefName": branch_ref(target_branch),
                        "searchCriteria.minTime": min_time,
                        "searchCriteria.queryTimeRangeType": query_time_range_type,
                        "$top": page_size,
                        "$skip": skip,
                    },
                )
                payload = self.get_json(url) or {}
                batch = payload.get("value", []) if isinstance(payload, dict) else payload
                if not batch:
                    break
                for pr in batch:
                    by_id[int(pr["pullRequestId"])] = pr
                if len(batch) < page_size:
                    break
                skip += len(batch)
        rows = list(by_id.values())
        return rows[:max_items]

    def get_pr_work_items(self, repository_id: str, pr_id: int) -> List[int]:
        url = self.build_url(f"git/repositories/{repository_id}/pullRequests/{pr_id}/workitems")
        payload = self.get_json(url) or {}
        rows = payload.get("value", []) if isinstance(payload, dict) else payload
        work_item_ids = []
        for item in rows:
            try:
                work_item_ids.append(int(item.get("id")))
            except (TypeError, ValueError):
                continue
        return sorted(set(work_item_ids))

    def query_by_wiql(self, query: str, top: Optional[int] = None) -> Dict[str, Any]:
        url = self.build_url("wit/wiql", **{"$top": top})
        return self.post_json(url, {"query": query}) or {}

    def get_work_items_batch(self, ids: List[int], fields: List[str], error_policy: str = "Omit") -> List[Dict[str, Any]]:
        if not ids:
            return []
        url = self.build_url("wit/workitemsbatch")
        payload = self.post_json(
            url,
            {
                "ids": ids,
                "fields": fields,
                "errorPolicy": error_policy,
            },
        ) or {}
        return payload.get("value", []) if isinstance(payload, dict) else payload

    def get_current_user(self) -> Dict[str, Any]:
        url = self.build_collection_url("connectionData", api_version="1.0")
        payload = self.get_json(url) or {}
        user = payload.get("authenticatedUser", {}) if isinstance(payload, dict) else {}
        return {
            "display_name": normalize_identity(user),
            "tokens": sorted(identity_tokens(user)),
        }


def enrich_pr(
    pr: Dict[str, Any],
    client: TfsClient,
    repository_id: str,
    branch_chain: List[str],
    verify_work_items_via_api: bool,
) -> Dict[str, Any]:
    source_branch = clean_branch(pr.get("sourceRefName", ""))
    normalized_source = normalize_source_branch(source_branch, branch_chain)
    work_item_ids: List[int] = []
    if verify_work_items_via_api:
        try:
            work_item_ids = client.get_pr_work_items(repository_id, int(pr["pullRequestId"]))
        except Exception:
            work_item_ids = []
    else:
        work_item_ids = extract_work_item_ids_from_branch(normalized_source) or extract_work_item_ids_from_branch(source_branch)

    return {
        "pull_request_id": int(pr["pullRequestId"]),
        "title": pr.get("title", ""),
        "status": str(pr.get("status", "")).lower(),
        "creation_date": pr.get("creationDate"),
        "closed_date": pr.get("closedDate"),
        "created_by": normalize_identity(pr.get("createdBy")),
        "created_by_tokens": sorted(identity_tokens(pr.get("createdBy"))),
        "source_branch": source_branch,
        "target_branch": clean_branch(pr.get("targetRefName", "")),
        "normalized_source_branch": normalized_source,
        "work_item_ids": work_item_ids,
        "url": pr.get("_links", {}).get("web", {}).get("href"),
    }


def fetch_dashboard_rows(
    *,
    client: TfsClient,
    branch_chain: List[str],
    lookback_days: int,
    max_prs_per_branch: int,
    verify_work_items_via_api: bool,
) -> Dict[str, Any]:
    repository_url = client.build_url("git/repositories")
    repository = client.get_json(repository_url)
    repos = repository.get("value", []) if isinstance(repository, dict) else repository
    wanted = client.repository.lower()
    repository = None
    for repo in repos:
        if str(repo.get("name", "")).lower() == wanted or str(repo.get("id", "")).lower() == wanted:
            repository = repo
            break
    if repository is None:
        raise TfsApiError(f"Repository '{client.repository}' was not found.")
    repository_id = str(repository["id"])
    repository_name = repository.get("name", client.repository)
    try:
        current_user = client.get_current_user()
    except Exception as exc:
        current_user = {"display_name": "", "tokens": [], "error": str(exc)}

    min_time = (
        (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if lookback_days > 0
        else None
    )
    pull_request_urls: List[str] = []
    branch_page_urls: Dict[str, List[List[str]]] = {}
    for branch in branch_chain:
        branch_page_urls[branch] = []
        for query_time_range_type in pull_request_time_range_types(min_time):
            page_urls: List[str] = []
            remaining = max_prs_per_branch
            skip = 0
            while remaining > 0:
                top = min(remaining, 100)
                url = client.build_url(
                    f"git/repositories/{repository_id}/pullrequests",
                    **{
                        "searchCriteria.status": "all",
                        "searchCriteria.targetRefName": branch_ref(branch),
                        "searchCriteria.minTime": min_time,
                        "searchCriteria.queryTimeRangeType": query_time_range_type,
                        "$top": top,
                        "$skip": skip,
                    },
                )
                page_urls.append(url)
                pull_request_urls.append(url)
                remaining -= top
                skip += top
            branch_page_urls[branch].append(page_urls)

    pull_request_payloads = client.get_json_many(pull_request_urls)
    all_pull_requests: List[Dict[str, Any]] = []
    for branch in branch_chain:
        branch_rows_by_id: Dict[int, Dict[str, Any]] = {}
        for page_urls in branch_page_urls[branch]:
            for url in page_urls:
                payload = pull_request_payloads.get(url) or {}
                batch = payload.get("value", []) if isinstance(payload, dict) else payload
                if not batch:
                    break
                for pr in batch:
                    branch_rows_by_id[int(pr["pullRequestId"])] = pr
                if len(batch) < 100:
                    break
        all_pull_requests.extend(list(branch_rows_by_id.values())[:max_prs_per_branch])

    deduped = {int(pr["pullRequestId"]): pr for pr in all_pull_requests}
    work_item_url_map: Dict[int, str] = {}
    if verify_work_items_via_api:
        for pr_id, pr in deduped.items():
            work_item_url_map[pr_id] = client.build_url(f"git/repositories/{repository_id}/pullRequests/{pr_id}/workitems")
    work_item_payloads = client.get_json_many(list(work_item_url_map.values())) if work_item_url_map else {}

    enriched: List[Dict[str, Any]] = []
    for pr_id, pr in deduped.items():
        source_branch = clean_branch(pr.get("sourceRefName", ""))
        normalized_source = normalize_source_branch(source_branch, branch_chain)
        work_item_ids: List[int] = []
        if verify_work_items_via_api and pr_id in work_item_url_map:
            payload = work_item_payloads.get(work_item_url_map[pr_id]) or {}
            rows = payload.get("value", []) if isinstance(payload, dict) else payload
            parsed_ids = []
            for item in rows:
                try:
                    parsed_ids.append(int(item.get("id")))
                except (TypeError, ValueError):
                    continue
            work_item_ids = sorted(set(parsed_ids))
        elif not verify_work_items_via_api:
            work_item_ids = extract_work_item_ids_from_branch(normalized_source) or extract_work_item_ids_from_branch(source_branch)

        enriched.append(
            {
                "pull_request_id": int(pr["pullRequestId"]),
                "title": pr.get("title", ""),
                "status": str(pr.get("status", "")).lower(),
                "creation_date": pr.get("creationDate"),
                "closed_date": pr.get("closedDate"),
                "created_by": normalize_identity(pr.get("createdBy")),
                "created_by_tokens": sorted(identity_tokens(pr.get("createdBy"))),
                "source_branch": source_branch,
                "target_branch": clean_branch(pr.get("targetRefName", "")),
                "normalized_source_branch": normalized_source,
                "work_item_ids": work_item_ids,
                "url": pr.get("_links", {}).get("web", {}).get("href"),
            }
        )

    branch_index = {branch: idx for idx, branch in enumerate(branch_chain)}
    groups: Dict[str, Dict[str, Any]] = {}
    for pr in enriched:
        if pr["target_branch"] not in branch_index:
            continue
        if pr["work_item_ids"]:
            tracking_keys = [(f"wi:{work_item_id}", [work_item_id], "work_item") for work_item_id in pr["work_item_ids"]]
        else:
            tracking_keys = [
                (
                    f"branch:{pr['normalized_source_branch']}",
                    [],
                    "branch_fallback",
                )
            ]

        for key, work_item_ids, tracking_mode in tracking_keys:
            group = groups.setdefault(
                key,
                {
                    "key": key,
                    "work_item_ids": work_item_ids,
                    "tracking_mode": tracking_mode,
                    "prs": [],
                },
            )
            group["prs"].append(pr)

    rows: List[Dict[str, Any]] = []
    for group in groups.values():
        prs = group["prs"]
        if not prs:
            continue

        original_candidates = [
            pr
            for pr in prs
            if pr["source_branch"] == pr["normalized_source_branch"] and pr["target_branch"] in branch_index
        ]
        if original_candidates:
            original = min(
                original_candidates,
                key=lambda pr: (
                    branch_index.get(pr["target_branch"], 999),
                    -STATUS_PRIORITY.get(pr["status"], 0),
                    parse_iso_date(pr.get("creation_date")).timestamp() if parse_iso_date(pr.get("creation_date")) else 0,
                ),
            )
        else:
            original = min(
                prs,
                key=lambda pr: (
                    branch_index.get(pr["target_branch"], 999),
                    parse_iso_date(pr.get("creation_date")).timestamp() if parse_iso_date(pr.get("creation_date")) else 0,
                ),
            )

        original_target = original["target_branch"]
        original_index = branch_index.get(original_target)
        if original_index is None:
            continue

        expected_branches = branch_chain[original_index + 1 :]
        statuses: Dict[str, Dict[str, Any]] = {}
        for target in expected_branches:
            target_prs = [pr for pr in prs if pr["target_branch"] == target]
            summary = summarize_target(target_prs)
            best = summary["best_pr"]
            if best and not best.get("url"):
                best["url"] = build_pr_web_url(client.base_url, client.project, repository_name, best["pull_request_id"])
            statuses[target] = summary

        missing = [branch for branch, summary in statuses.items() if summary["label"] == "Missing"]
        open_branches = [branch for branch, summary in statuses.items() if summary["label"] == "Open"]
        abandoned = [branch for branch, summary in statuses.items() if summary["label"] == "Abandoned"]
        done = [branch for branch, summary in statuses.items() if summary["label"] == "Done"]

        if missing:
            overall = "Missing"
        elif open_branches:
            overall = "Open"
        elif abandoned:
            overall = "Abandoned"
        else:
            overall = "Done"

        original_url = original.get("url") or build_pr_web_url(
            client.base_url,
            client.project,
            repository_name,
            original["pull_request_id"],
        )
        rows.append(
            {
                "key": group["key"],
                "work_items": group["work_item_ids"],
                "work_items_label": ", ".join(str(item) for item in group["work_item_ids"]) or "-",
                "family_branch": original["normalized_source_branch"],
                "family_label": short_source_label(original["normalized_source_branch"]),
                "tracking_mode": group["tracking_mode"],
                "title": original.get("title", ""),
                "original_pr": original,
                "original_created_by": original.get("created_by", ""),
                "original_created_by_tokens": original.get("created_by_tokens", []),
                "original_pr_url": original_url,
                "original_target": original_target,
                "original_status_label": STATUS_LABELS.get(original.get("status", ""), original.get("status", "-").title()),
                "expected_branches": expected_branches,
                "statuses": statuses,
                "missing": missing,
                "open": open_branches,
                "abandoned": abandoned,
                "done": done,
                "overall": overall,
            }
        )

    rows.sort(
        key=lambda row: (
            severity_rank(row["overall"]),
            branch_index.get(row["original_target"], 999),
            row["work_items_label"],
            row["family_branch"],
        )
    )

    return {
        "repository_id": repository_id,
        "repository_name": repository_name,
        "rows": rows,
        "pull_request_count": len(enriched),
        "current_user": current_user,
    }


def normalize_identity(value: Any) -> str:
    if isinstance(value, dict):
        return value.get("displayName") or value.get("providerDisplayName") or value.get("uniqueName") or ""
    return str(value or "")


def fetch_my_assigned_work_items(
    *,
    client: TfsClient,
    project: str,
    top: int = 200,
) -> Dict[str, Any]:
    wiql = """
Select [System.Id]
From WorkItems
Where
    [System.TeamProject] = @project
    And [System.AssignedTo] = @Me
    And [System.State] <> 'Removed'
Order By [System.ChangedDate] Desc
""".strip()
    wiql_payload = client.query_by_wiql(wiql, top=top)
    work_item_refs = wiql_payload.get("workItems", []) if isinstance(wiql_payload, dict) else []
    ordered_ids = [int(item["id"]) for item in work_item_refs if "id" in item]
    if not ordered_ids:
        return {"items": [], "work_item_ids": set()}

    fields = [
        "System.Id",
        "System.WorkItemType",
        "System.Title",
        "System.State",
        "System.Tags",
        "System.IterationPath",
        "System.AssignedTo",
        "System.ChangedDate",
    ]
    batch_rows: List[Dict[str, Any]] = []
    for id_chunk in chunked(ordered_ids, 200):
        batch_rows.extend(client.get_work_items_batch(id_chunk, fields))

    by_id: Dict[int, Dict[str, Any]] = {}
    for row in batch_rows:
        fields_map = row.get("fields", {}) or {}
        work_item_id = row.get("id")
        if not work_item_id:
            continue
        by_id[int(work_item_id)] = {
            "id": int(work_item_id),
            "type": fields_map.get("System.WorkItemType", ""),
            "title": fields_map.get("System.Title", ""),
            "state": fields_map.get("System.State", ""),
            "tags": fields_map.get("System.Tags", ""),
            "iteration_path": fields_map.get("System.IterationPath", ""),
            "assigned_to": normalize_identity(fields_map.get("System.AssignedTo")),
            "changed_date": fields_map.get("System.ChangedDate"),
            "url": build_work_item_web_url(client.base_url, project, int(work_item_id)),
        }

    ordered_items = [by_id[work_item_id] for work_item_id in ordered_ids if work_item_id in by_id]
    return {
        "items": ordered_items,
        "work_item_ids": set(ordered_ids),
    }
