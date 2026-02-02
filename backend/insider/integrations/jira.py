import logging
from atlassian import Jira
from requests.exceptions import HTTPError, ConnectionError, Timeout
from .base import BaseIntegration

logger = logging.getLogger(__name__)

class JiraIntegration(BaseIntegration):
    identifier = "jira"
    logo_url = "https://cdn.simpleicons.org/jira/0052CC"
    
    config_definition = {
        "url": {
            "label": "Jira URL (e.g. https://company.atlassian.net)",
            "type": "STRING",
            "required": True
        },
        "username": {
            "label": "Account Email",
            "type": "STRING",
            "required": True
        },
        "api_token": {
            "label": "API Token",
            "type": "PASSWORD",
            "required": True,
            "help_text": "Create this in your Atlassian Account Settings."
        },
        "project_key": {
            "label": "Project Key (e.g. DEV)",
            "type": "STRING",
            "required": True
        },
        "issue_type": {
            "label": "Issue Type",
            "type": "STRING",
            "required": False,
            "default": "Bug"
        },
        "assignee_id": {
            "label": "Assignee Account ID (Optional)",
            "type": "STRING",
            "required": False,
            "help_text": "The generic account ID to assign issues to."
        }
    }

    def _format_logs(self, logs):
        if not logs: return "N/A"
        return "\n".join(logs) if isinstance(logs, list) else str(logs)

    def run(self, footprint, context):
        url = self.get_config("url")
        username = self.get_config("username")
        token = self.get_config("api_token")
        project_key = self.get_config("project_key")
        issue_type = self.get_config("issue_type", "Bug")
        assignee_id = self.get_config("assignee_id")

        if not all([url, username, token, project_key]):
            logger.warning("INSIDER: Jira Integration enabled but missing credentials.")
            return

        try:
            jira = Jira(
                url=url,
                username=username,
                password=token,
                cloud=True
            )
        except Exception as e:
            logger.error(f"INSIDER: Failed to initialize Jira client: {e}")
            return

        context = context or {}
        summary = context.get("title", f"Insider Error: {footprint.status_code} at {footprint.request_path}")
        
        logs_text = self._format_logs(footprint.system_logs)
        
        description = (
            f"h2. Error Details\n"
            f"||Key||Value||\n"
            f"|*Footprint ID*|{footprint.id}|\n"
            f"|*User*|{footprint.request_user}|\n"
            f"|*Endpoint*|{footprint.request_method.upper()} {footprint.request_path}|\n"
            f"|*Status*|{footprint.status_code}|\n"
            f"|*Occurred At*|{footprint.created_at.isoformat()}|\n\n"
            f"h2. System Logs\n{{noformat}}\n{logs_text}\n{{noformat}}\n\n"
        )

        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }

        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}

        try:
            created_issue = jira.issue_create(fields=fields)
            
            key = created_issue['key']
            issue_url = f"{url}/browse/{key}"

            current_issues = context.get("generated_issues", [])
            
            new_issue = {
                "system": "Jira",
                "url": issue_url,
                "key": key
            }

            return {
                "generated_issues": current_issues + [new_issue],
                "issue_system": "Jira",
                "issue_url": issue_url,
                "issue_key": key
            }

        except (HTTPError, ConnectionError, Timeout) as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'N/A'
            logger.error(f"INSIDER: Jira Creation Failed. Status: {status_code}, Error: {e}")
        
        except Exception as e:
            logger.error(f"INSIDER: Jira Unexpected Error: {e}")
        
        return None