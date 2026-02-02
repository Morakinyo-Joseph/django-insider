import logging
import requests
from .base import BaseIntegration

logger = logging.getLogger(__name__)

class GithubIntegration(BaseIntegration):
    identifier = "github"
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c2/GitHub_Invertocat_Logo.svg"
    
    config_definition = {
        "repo_owner": {
            "label": "Repository Owner",
            "type": "STRING",
            "required": True,
            "help_text": "The organization or username (e.g., 'facebook')"
        },
        "repo_name": {
            "label": "Repository Name",
            "type": "STRING",
            "required": True,
            "help_text": "The repository slug (e.g., 'react')"
        },
        "access_token": {
            "label": "Personal Access Token",
            "type": "PASSWORD",
            "required": True,
            "help_text": "Generate a Classic Token with 'repo' scope."
        },
        "labels": {
            "label": "Issue Labels",
            "type": "STRING",
            "required": False,
            "default": "bug,insider",
            "help_text": "Comma-separated labels to apply (e.g. 'bug, urgent')"
        }
    }

    
    def run(self, footprint, context):
        config = self.get_config()
        
        owner = config.get("repo_owner")
        repo = config.get("repo_name")
        token = config.get("access_token")
        
        if not (owner and repo and token):
            logger.warning("INSIDER: GitHub integration missing required config.")
            return

        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        
        title = f"[Insider] Error {footprint.status_code}: {footprint.request_path}"

        if hasattr(footprint, 'incidence') and footprint.incidence:
             title = f"[Insider] {footprint.incidence.title}"

        body = f"""
            ### 🚨 Insider Alert
            **Path:** `{footprint.request_method} {footprint.request_path}`
            **User:** {footprint.request_user or 'Anonymous'}
            **Time:** {footprint.created_at}

            <details>
            <summary><b>Stack Trace</b></summary>

            ```python
            {self._format_stack_trace(footprint)}
            </details>

            See full details in Insider Dashboard. 
        """

        labels_str = config.get("labels", "bug,insider")
        labels = [l.strip() for l in labels_str.split(",") if l.strip()]

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "title": title,
            "body": body,
            "labels": labels
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            issue_url = data.get("html_url")
            logger.info(f"INSIDER: Created GitHub Issue: {issue_url}")
            
            return {"github_issue_url": issue_url}

        except Exception as e:
            logger.error(f"INSIDER: Failed to create GitHub issue: {e}")
            return {}

    def _format_stack_trace(self, footprint):
        """
        Helper to extract a clean string from the stack trace list.
        """

        if not footprint.stack_trace:
            return "No stack trace available."
        
        if isinstance(footprint.stack_trace, str):
            return footprint.stack_trace

        lines = []
        for frame in footprint.stack_trace:
            func = frame.get('function') if isinstance(frame, dict) else frame.function
            line = frame.get('line') if isinstance(frame, dict) else frame.line
            code = frame.get('code', '').strip() if isinstance(frame, dict) else frame.code.strip()
            lines.append(f"File: {frame.get('file')}, Line {line}, in {func}\n  {code}")
        
        return "\n".join(lines)
    

