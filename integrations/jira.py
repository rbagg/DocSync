# integrations/jira.py
# Jira integration for DocSync

import logging
import json
import requests
from datetime import datetime

class JiraIntegration:
    """
    Integration with Jira issue tracking.

    This class handles authentication, issue retrieval, and webhook processing
    for Jira projects.
    """

    def __init__(self):
        """Initialize the Jira integration"""
        self.logger = logging.getLogger(__name__)
        self.connected_projects = []

        # Sample tickets for demo/testing
        self.tickets = [
            {
                'id': 'PROJ-1',
                'title': 'Implement authentication flow',
                'description': 'Create a secure authentication flow with password reset capability.',
                'status': 'In Progress',
                'priority': 'High',
                'assignee': 'Jane Smith'
            },
            {
                'id': 'PROJ-2',
                'title': 'Design user dashboard',
                'description': 'Create a user-friendly dashboard with key metrics and notifications.',
                'status': 'To Do',
                'priority': 'Medium',
                'assignee': 'John Doe'
            },
            {
                'id': 'PROJ-3',
                'title': 'Optimize database queries',
                'description': 'Improve performance of dashboard queries to reduce page load time.',
                'status': 'Done',
                'priority': 'Medium',
                'assignee': 'Alex Johnson'
            },
            {
                'id': 'PROJ-4',
                'title': 'Fix mobile layout issues',
                'description': 'Address responsive design issues on small screens.',
                'status': 'To Do',
                'priority': 'Low',
                'assignee': 'Sarah Williams'
            },
            {
                'id': 'PROJ-5',
                'title': 'Implement export functionality',
                'description': 'Add ability to export dashboard data to CSV and PDF formats.',
                'status': 'To Do',
                'priority': 'Medium',
                'assignee': 'David Chen'
            }
        ]

    def connect_project(self, project_id):
        """
        Connect to a Jira project

        Args:
            project_id (str): Jira project ID or key

        Returns:
            bool: True if successful
        """
        # In a real implementation, this would validate the project exists
        # and set up a webhook for notifications
        self.connected_projects.append({
            'id': project_id,
            'connected_at': datetime.utcnow()
        })

        self.logger.info(f"Connected to Jira project {project_id}")
        return True

    def get_tickets(self, project_id=None):
        """
        Get all tickets for a project

        In a real implementation, this would fetch tickets from Jira API.

        Args:
            project_id (str, optional): Project ID to filter tickets

        Returns:
            list: Tickets in the project
        """
        # In a real implementation, this would fetch tickets from Jira API
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

        In a real implementation, this would create a webhook in Jira.

        Args:
            project_id (str): Project ID
            callback_url (str): Webhook callback URL

        Returns:
            bool: True if successful
        """
        # In a real implementation, this would create a webhook in Jira
        self.logger.info(f"Created webhook for project {project_id} with callback {callback_url}")
        return True

    def process_webhook(self, payload):
        """
        Process a webhook notification from Jira

        Args:
            payload (dict): Webhook payload

        Returns:
            dict: Processed changes
        """
        # Extract issue information from payload
        try:
            event_type = payload.get('webhookEvent')
            issue_key = payload.get('issue', {}).get('key')

            if not issue_key:
                self.logger.warning("No issue key in webhook payload")
                return None

            if event_type == 'jira:issue_created':
                # New issue created
                return {
                    'tickets': {
                        'added': [issue_key],
                        'modified': [],
                        'removed': []
                    }
                }
            elif event_type == 'jira:issue_updated':
                # Issue updated
                return {
                    'tickets': {
                        'added': [],
                        'modified': [issue_key],
                        'removed': []
                    }
                }
            elif event_type == 'jira:issue_deleted':
                # Issue deleted
                return {
                    'tickets': {
                        'added': [],
                        'modified': [],
                        'removed': [issue_key]
                    }
                }
            else:
                self.logger.info(f"Ignoring webhook event {event_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing Jira webhook: {str(e)}")
            return None

    def create_ticket(self, project_id, title, description, priority='Medium', assignee=None):
        """
        Create a new ticket in Jira

        In a real implementation, this would create a ticket via Jira API.

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
        # In a real implementation, Jira would generate this
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