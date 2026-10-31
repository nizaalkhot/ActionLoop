from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BasePMIntegration(ABC):
    @abstractmethod
    def get_members(self) -> List[Dict]:
        """Returns list of workspace users: [{'id': ..., 'name': ..., 'email': ..., 'avatar_url': ...}]"""
        pass

    @abstractmethod
    def get_open_tickets(self, project_id: Optional[str] = None) -> List[Dict]:
        """Returns list of active/open issues: [{'id': ..., 'title': ..., 'status': ..., 'assignee_name': ...}]"""
        pass

    @abstractmethod
    def lookup_issue_by_fingerprint(self, task_fingerprint: str) -> Optional[Dict]:
        """
        Looks up an issue in the PM tool by its unique task fingerprint before retrying creation.
        Returns {'ticket_id': ..., 'ticket_url': ...} if found, or None.
        """
        pass

    @abstractmethod
    def create_task(self, title: str, description: str, assignee_id: Optional[str] = None, 
                    due_date: Optional[str] = None, project_id: Optional[str] = None,
                    supporting_quote: Optional[str] = None, meeting_title: Optional[str] = None,
                    task_fingerprint: Optional[str] = None) -> Dict:
        """Creates an issue in the PM tool and returns {'ticket_id': ..., 'ticket_url': ...}"""
        pass
