import requests
from typing import Dict, List, Optional
from services.integrations.base import BasePMIntegration
from config import settings

class LinearProvider(BasePMIntegration):
    GRAPHQL_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.linear_api_key

    def _execute(self, query: str, variables: Optional[Dict] = None) -> Dict:
        if not self.api_key:
            raise ValueError("LINEAR_API_KEY is not set.")
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        resp = requests.post(self.GRAPHQL_URL, json={"query": query, "variables": variables or {}}, headers=headers, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise RuntimeError(f"Linear GraphQL error: {result['errors']}")
        return result.get("data", {})

    def get_members(self) -> List[Dict]:
        query = """
        query {
          users {
            nodes {
              id
              name
              email
              avatarUrl
            }
          }
        }
        """
        try:
            data = self._execute(query)
            users = data.get("users", {}).get("nodes", [])
            return [{"id": u["id"], "name": u["name"], "email": u["email"], "avatar_url": u.get("avatarUrl")} for u in users]
        except Exception:
            return []

    def get_open_tickets(self, project_id: Optional[str] = None) -> List[Dict]:
        query = """
        query {
          issues(first: 50, filter: { state: { type: { nin: ["completed", "canceled"] } } }) {
            nodes {
              id
              identifier
              title
              state { name }
              assignee { name }
            }
          }
        }
        """
        try:
            data = self._execute(query)
            issues = data.get("issues", {}).get("nodes", [])
            return [{
                "id": i["identifier"],
                "title": i["title"],
                "status": i.get("state", {}).get("name", "Open"),
                "assignee_name": (i.get("assignee") or {}).get("name")
            } for i in issues]
        except Exception:
            return []

    def lookup_issue_by_fingerprint(self, task_fingerprint: str) -> Optional[Dict]:
        """
        Searches Linear for issues containing the task fingerprint backlink.
        Prevents duplicate issue creation if network dropped during initial push.
        """
        if not task_fingerprint:
            return None
        search_term = f"actionloop-fp:{task_fingerprint}"
        query = """
        query SearchIssueByFingerprint($term: String!) {
          issueSearch(query: $term, first: 1) {
            nodes {
              id
              identifier
              url
            }
          }
        }
        """
        try:
            data = self._execute(query, {"term": search_term})
            nodes = data.get("issueSearch", {}).get("nodes", [])
            if nodes:
                issue = nodes[0]
                return {
                    "ticket_id": issue.get("identifier", issue.get("id")),
                    "ticket_url": issue.get("url", "https://linear.app"),
                    "status": "already_exists"
                }
        except Exception:
            pass
        return None

    def create_task(self, title: str, description: str, assignee_id: Optional[str] = None, 
                    due_date: Optional[str] = None, project_id: Optional[str] = None,
                    supporting_quote: Optional[str] = None, meeting_title: Optional[str] = None,
                    task_fingerprint: Optional[str] = None) -> Dict:
        # 1. Lookup before retry
        if task_fingerprint:
            existing = self.lookup_issue_by_fingerprint(task_fingerprint)
            if existing:
                return existing

        team_id = settings.linear_team_id
        
        body_parts = [description or ""]
        if supporting_quote:
            body_parts.append(f"\n\n> **Source Quote from {meeting_title or 'Meeting'}:**\n> \"{supporting_quote}\"")

        if task_fingerprint:
            body_parts.append(f"\n\n<!-- actionloop-fp:{task_fingerprint} -->")

        full_description = "\n".join(body_parts).strip()

        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              identifier
              url
            }
          }
        }
        """
        variables = {
            "input": {
                "teamId": team_id,
                "title": title,
                "description": full_description,
            }
        }
        if assignee_id:
            variables["input"]["assigneeId"] = assignee_id
        if due_date:
            variables["input"]["dueDate"] = due_date
        if project_id:
            variables["input"]["projectId"] = project_id

        data = self._execute(mutation, variables)
        issue = data.get("issueCreate", {}).get("issue", {})
        return {
            "ticket_id": issue.get("identifier", "LIN-CREATED"),
            "ticket_url": issue.get("url", "https://linear.app"),
            "status": "created"
        }
