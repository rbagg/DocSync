# models/project.py
from . import db
from datetime import datetime
import json

class Project(db.Model):
    """
    Project model for storing project content.

    This model represents a snapshot of a project's documents at a specific point in time.
    """
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # JSON string of all project content
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_content_dict(self):
        """Return content as a dictionary"""
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:
            # Return empty dict if content is invalid JSON
            return {}

    def __repr__(self):
        return f'<Project {self.id} {self.timestamp}>'