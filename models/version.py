# models/version.py
from . import db
from datetime import datetime

class Version(db.Model):
    """
    Version model for tracking document version history.

    This model stores historical versions of documents for change tracking.
    """
    __tablename__ = 'versions'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # Document content
    document_id = db.Column(db.String(255), nullable=False)  # ID of the document
    document_type = db.Column(db.String(50), nullable=False)  # Type of document (prd, prfaq, etc.)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Version {self.id} {self.document_type} {self.document_id} {self.timestamp}>'