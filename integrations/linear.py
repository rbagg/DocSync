# integrations/linear.py
# Linear integration for DocSync

import logging
import json
from datetime import datetime

class LinearIntegration:
    """
    Integration with Linear task management.

    This class handles authentication, issue retrieval, and webhook processing
    for Linear projects.
    """

    def __init__(self):
        """Initialize the Linear integration"""
        self.logger = logging.getLogger(__name__)
        self.connected_projects = []

        # Sample tickets for demo/testing
        self.tickets = [
            {
                'id': 'LIN-1',
                'title': 'Implement SSO authentication',
                'description': 'Add support for single sign-on using OAuth 2.0.',
                'status': 'In Progress',
                'priority': 'High',
                'assignee': 'Sarah Chen'
            },
            {
                'id': 'LIN-2',
                'title': 'Improve error handling in API',
                'description': 'Add better error messages and exception handling for API endpoints.',
                'status': 'To Do',
                'priority': 'Medium',
                'assignee': 'Mike Johnson'
            },
            {
                'id': 'LIN-3',
                'title': 'Fix mobile navigation issues',
                'description': 'Address issues with the hamburger menu on small screens.',
                'status': 'Done',
                'priority': 'Low',
                'assignee': 'Alex Wong'
            }
        ]

    def connect_project(self, project_id):
        """
        Connect to a Linear project

        Args:
            project_id (str): Linear project ID or key

        Returns:
            bool: True if successful
        """
        # In a real implementation, this would validate the project exists
        # and set up a webhook for notifications
        self.connected_projects.append({
            'id': project_id,
            'connected_at': datetime.utcnow()
        })

        self.logger.info(f"Connected to Linear project {project_id}")
        return True

    def get_tickets(self, project_id=None):
        """
        Get all tickets for a project

        In a real implementation, this would fetch tickets from Linear API.

        Args:
            project_id (str, optional): Project ID to filter tickets

        Returns:
            list: Tickets in the project
        """
        # In a real implementation, this would fetch tickets from Linear API
        # For the demo, we just return sample tickets
        if project_id:
            return [t for t in self.tickets if t['id'].startswith(project_id)]
        return self.tickets

    def get_ticket(self, ticket_id):
        """
        Get a specific ticket

        Args:
            ticket_id (str): Ticket ID

        Returns:
            dict: Ticket data or None if not found
        """
        for ticket in self.tickets:
            if ticket['id'] == ticket_id:
                return ticket
        return None

    def create_webhook(self, project_id, callback_url):
        """
        Set up a webhook for a project

        In a real implementation, this would create a webhook in Linear.

        Args:
            project_id (str): Project ID
            callback_url (str): Webhook callback URL

        Returns:
            bool: True if successful
        """
        # In a real implementation, this would create a webhook in Linear
        self.logger.info(f"Created webhook for project {project_id} with callback {callback_url}")
        return True

    def process_webhook(self, payload):
        """
        Process a webhook notification from Linear

        Args:
            payload (dict): Webhook payload

        Returns:
            dict: Processed changes
        """
        # Extract issue information from payload
        try:
            action = payload.get('action')
            issue_id = payload.get('data', {}).get('id')

            if not issue_id:
                self.logger.warning("No issue id in webhook payload")
                return None

            if action == 'create':
                # New issue created
                return {
                    'tickets': {
                        'added': [issue_id],
                        'modified': [],
                        'removed': []
                    }
                }
            elif action == 'update':
                # Issue updated
                return {
                    'tickets': {
                        'added': [],
                        'modified': [issue_id],
                        'removed': []
                    }
                }
            elif action == 'remove':
                # Issue deleted
                return {
                    'tickets': {
                        'added': [],
                        'modified': [],
                        'removed': [issue_id]
                    }
                }
            else:
                self.logger.info(f"Ignoring webhook action {action}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing Linear webhook: {str(e)}")
            return None

    def create_ticket(self, project_id, title, description, priority='Medium', assignee=None):
        """
        Create a new ticket in Linear

        In a real implementation, this would create a ticket via Linear API.

        Args:
            project_id (str): Project ID
            title (str): Ticket title
            description (str): Ticket description
            priority (str): Ticket priority
            assignee (str): Username to assign the ticket to

        Returns:
            dict: Created ticket
        """
        # Generate ticket ID
        # In a real implementation, Linear would generate this
        ticket_id = f"{project_id}-{len(self.tickets) + 1}"

        # Create new ticket
        ticket = {
            'id': ticket_id,
            'title': title,
            'description': description,
            'status': 'To Do',
            'priority': priority,
            'assignee': assignee
        }

        # Add to tickets
        self.tickets.append(ticket)

        self.logger.info(f"Created ticket {ticket_id}: {title}")
        return ticket