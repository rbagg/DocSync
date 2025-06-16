# config.py
import os
from datetime import timedelta

class Config:
    """Enhanced configuration for DocSync with self-critique technology"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-docsync-enhanced')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///docsync.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Claude API settings for enhanced alignment analysis
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-3-sonnet-20240229')

    # Enhanced processing settings
    ENABLE_SELF_CRITIQUE = os.environ.get('ENABLE_SELF_CRITIQUE', 'true').lower() == 'true'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

    # Platform API credentials
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    JIRA_API_KEY = os.environ.get('JIRA_API_KEY')
    JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
    JIRA_DOMAIN = os.environ.get('JIRA_DOMAIN')
    CONFLUENCE_API_TOKEN = os.environ.get('CONFLUENCE_API_TOKEN')
    CONFLUENCE_EMAIL = os.environ.get('CONFLUENCE_EMAIL')
    CONFLUENCE_DOMAIN = os.environ.get('CONFLUENCE_DOMAIN')
    LINEAR_API_KEY = os.environ.get('LINEAR_API_KEY')

    # Processing configuration
    SIMPLE_PROCESSING_THRESHOLD = int(os.environ.get('SIMPLE_PROCESSING_THRESHOLD', '5'))  # sections
    MIN_DOCUMENT_TYPES_FOR_ANALYSIS = int(os.environ.get('MIN_DOCUMENT_TYPES_FOR_ANALYSIS', '2'))

    # Rate limiting settings
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    # DocMint integration settings
    DOCMINT_URL = os.environ.get('DOCMINT_URL', 'https://docmint.repl.co')
    SUGGEST_DOCMINT_ENHANCEMENT = os.environ.get('SUGGEST_DOCMINT_ENHANCEMENT', 'true').lower() == 'true'

    def __init__(self):
        """Initialize config with additional environment checks"""
        # Check for Replit secrets format
        if not self.CLAUDE_API_KEY:
            for env_var in ['REPLIT_CLAUDE_API_KEY', 'CLAUDE_API_KEY_SECRET']:
                if env_var in os.environ:
                    self.CLAUDE_API_KEY = os.environ.get(env_var)
                    break

        # Check for secrets file (older Replit versions)
        if not self.CLAUDE_API_KEY and os.path.exists('/run/secrets/CLAUDE_API_KEY'):
            try:
                with open('/run/secrets/CLAUDE_API_KEY', 'r') as f:
                    self.CLAUDE_API_KEY = f.read().strip()
            except Exception as e:
                print(f"Error reading from secrets file: {e}")

        # Validate required settings
        if not self.CLAUDE_API_KEY:
            print("WARNING: CLAUDE_API_KEY not found. Enhanced alignment analysis will not work.")
            print("Please set CLAUDE_API_KEY in your environment or Replit secrets.")

    @property
    def is_development(self):
        """Check if running in development mode"""
        return os.environ.get('FLASK_ENV') == 'development'

    @property
    def processing_config(self):
        """Get processing configuration summary"""
        return {
            'self_critique_enabled': self.ENABLE_SELF_CRITIQUE,
            'simple_threshold': self.SIMPLE_PROCESSING_THRESHOLD,
            'min_document_types': self.MIN_DOCUMENT_TYPES_FOR_ANALYSIS,
            'claude_model': self.CLAUDE_MODEL,
            'docmint_integration': self.SUGGEST_DOCMINT_ENHANCEMENT
        }