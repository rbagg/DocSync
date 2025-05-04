# services/sync_service.py
# Synchronization service for DocSync

import json
import logging
from datetime import datetime

class SyncService:
    """
    Service for synchronizing document changes across different systems.

    This class handles collecting content from all connected integrations,
    processing document changes, and maintaining relationships between documents.
    """

    def __init__(self):
        """Initialize the synchronization service"""
        self.logger = logging.getLogger(__name__)
        # Store references to integration instances (will be set by main.py)
        self.google_docs = None
        self.jira = None
        self.linear = None
        self.confluence = None

    def set_integrations(self, google_docs, jira, linear, confluence):
        """
        Set integration instances

        Args:
            google_docs: Google Docs integration
            jira: Jira integration
            linear: Linear integration
            confluence: Confluence integration
        """
        self.google_docs = google_docs
        self.jira = jira
        self.linear = linear
        self.confluence = confluence

    def collect_all_content(self):
        """
        Collect content from all connected documents

        Returns:
            str: JSON string of all project content
        """
        content = {
            'prd': {},
            'prfaq': {},
            'strategy': {},
            'tickets': []
        }

        # Collect Google Docs content
        if self.google_docs:
            docs = self.google_docs.get_connected_docs()
            for doc in docs:
                doc_id = doc['id']
                doc_type = doc['type']

                # Get document content
                doc_content = self.google_docs.get_document_content(doc_id)

                if doc_content:
                    if doc_type == 'prd':
                        content['prd'] = doc_content
                    elif doc_type == 'prfaq':
                        content['prfaq'] = doc_content
                    elif doc_type == 'strategy':
                        content['strategy'] = doc_content

        # Collect Jira tickets
        if self.jira:
            content['tickets'].extend(self.jira.get_tickets())

        # Collect Linear tickets
        if self.linear:
            content['tickets'].extend(self.linear.get_tickets())

        # Collect content from Confluence
        if self.confluence:
            confluence_pages = self.confluence.get_pages()
            for page in confluence_pages:
                page_id = page['id']

                # Get page to determine its type
                page_content = self.confluence.extract_structured_content(page)

                # Determine document type based on labels
                if 'strategy' in page.get('labels', []):
                    # Merge with existing strategy content
                    self._merge_content(content['strategy'], page_content)

                # Could add other document types here as needed

        return json.dumps(content)

    def _merge_content(self, target, source):
        """
        Merge source content into target

        Args:
            target (dict): Target dictionary
            source (dict): Source dictionary
        """
        if isinstance(source, dict) and isinstance(target, dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    self._merge_content(target[key], value)
                else:
                    target[key] = value

    def handle_jira_update(self, data):
        """
        Handle updates from Jira

        Args:
            data (dict): Webhook payload from Jira

        Returns:
            dict: Changes detected, if any
        """
        if not self.jira:
            self.logger.warning("Jira integration not set up")
            return None

        return self.jira.process_webhook(data)

    def handle_docs_update(self, data):
        """
        Handle updates from Google Docs

        Args:
            data (dict): Webhook payload from Google Docs

        Returns:
            dict: Changes detected, if any
        """
        # Extract document info from payload
        doc_id = data.get('documentId')
        if not doc_id:
            return None

        # Get document type and previous content
        doc_type = self.google_docs.get_document_type(doc_id)
        if not doc_type:
            return None

        # Get updated content
        updated_content = self.google_docs.get_document_content(doc_id)

        # Get previous content (this would typically come from a database)
        # For the demo, we'll just simulate previous content
        previous_content = {}

        # Initialize changes
        changes = {
            doc_type: {
                'added': [],
                'modified': [],
                'removed': []
            }
        }

        # Compare with current content
        for section, text in updated_content.items():
            if section not in previous_content:
                changes[doc_type]['added'].append(section)
            elif previous_content.get(section) != text:
                changes[doc_type]['modified'].append(section)

        # Find removed sections
        for section in previous_content:
            if section not in updated_content:
                changes[doc_type]['removed'].append(section)

        # Only return changes if something changed
        return changes if any(len(c) > 0 for c in changes[doc_type].values()) else None

    def handle_confluence_update(self, data):
        """
        Handle updates from Confluence

        Args:
            data (dict): Webhook payload from Confluence

        Returns:
            dict: Changes detected, if any
        """
        if not self.confluence:
            self.logger.warning("Confluence integration not set up")
            return None

        return self.confluence.process_webhook(data)

    def handle_linear_update(self, data):
        """
        Handle updates from Linear

        Args:
            data (dict): Webhook payload from Linear

        Returns:
            dict: Changes detected, if any
        """
        if not self.linear:
            self.logger.warning("Linear integration not set up")
            return None

        return self.linear.process_webhook(data)