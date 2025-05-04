# main.py
# Main application file for DocSync - Document Synchronization Platform

import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

from config import Config
from models import db, Version, Project, Alignment
from integrations.google_docs import GoogleDocsIntegration
from integrations.jira import JiraIntegration
from integrations.confluence import ConfluenceIntegration
from integrations.linear import LinearIntegration

# Import services
from services.sync_service import SyncService
from services.alignment_service import AlignmentService
from services.change_impact_analyzer import ChangeImpactAnalyzer
from services.document_manager import DocumentManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"]
)

# Initialize integrations
google_docs = GoogleDocsIntegration()
jira = JiraIntegration()
linear = LinearIntegration()
confluence = ConfluenceIntegration()

# Initialize services
sync_service = SyncService()
alignment_service = AlignmentService()
impact_analyzer = ChangeImpactAnalyzer()
document_manager = DocumentManager()

# Connect integrations to sync service
sync_service.set_integrations(google_docs, jira, linear, confluence)

# Register integrations with document manager
document_manager.register_integration('google_docs', google_docs)
document_manager.register_integration('jira', jira)
document_manager.register_integration('linear', linear)
document_manager.register_integration('confluence', confluence)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    if 'google_token' not in session:
        return redirect(url_for('setup'))

    # Get the current project
    project = Project.query.order_by(Project.timestamp.desc()).first()

    # Get latest alignment suggestions
    suggestions = alignment_service.get_suggestions()

    return render_template('index.html', 
                         project=project,
                         suggestions=suggestions)

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/auth/google')
@limiter.limit("10 per hour")
def google_auth():
    return google_docs.authorize()

@app.route('/auth/callback')
def google_callback():
    token = google_docs.callback(request.args)
    session['google_token'] = token
    return redirect(url_for('index'))

@app.route('/connect', methods=['POST'])
@limiter.limit("10 per hour")
def connect_document():
    """Connect a document to the project (PRD, PRFAQ, tickets, etc.)"""
    try:
        doc_type = request.form.get('type')
        doc_id = request.form.get('id')

        # Connect the document
        if doc_type == 'google_docs':
            google_docs.connect_document(doc_id)
        elif doc_type == 'jira':
            jira.connect_project(doc_id)
        elif doc_type == 'linear':
            linear.connect_project(doc_id)
        elif doc_type == 'confluence':
            confluence.connect_page(doc_id)

        # Process document using the document manager for better extraction
        processed_doc = None
        if doc_type == 'google_docs':
            # Determine document type based on naming convention or user selection
            doc_subtype = 'prd'  # Default
            if 'prfaq' in doc_id.lower():
                doc_subtype = 'prfaq'
            elif 'strategy' in doc_id.lower():
                doc_subtype = 'strategy'

            # Process the document
            processed_doc = document_manager.process_document(
                doc_id=doc_id,
                doc_type=doc_subtype,
                integration_type=doc_type
            )

            # Log validation results
            if processed_doc and 'validation' in processed_doc:
                validation = processed_doc['validation']
                if not validation['valid']:
                    logger.info(f"Document validation issues: {validation}")
                    flash_msg = "Document connected, but has some issues: "
                    if validation.get('missing_sections'):
                        flash_msg += f"Missing sections: {', '.join(validation['missing_sections'])}. "
                    flash(flash_msg, 'warning')

        # Analyze the connected document and generate initial alignment
        project_content = sync_service.collect_all_content()

        # Save to project
        project = Project(
            content=project_content,
            timestamp=datetime.utcnow()
        )
        db.session.add(project)
        db.session.commit()

        flash('Document connected successfully!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error connecting document: {str(e)}")
        flash(f'Error connecting document: {str(e)}', 'error')
        return redirect(url_for('setup'))

@app.route('/update', methods=['POST'])
@limiter.limit("10 per hour")
def manual_update():
    """Manually trigger an update and alignment check"""
    try:
        # Collect all content with improved document extraction
        project_content = sync_service.collect_all_content()

        # Analyze changes
        changes = alignment_service.analyze_changes(project_content)
        impact = impact_analyzer.analyze(changes)

        # Save to project
        project = Project(
            content=project_content,
            timestamp=datetime.utcnow()
        )
        db.session.add(project)

        # Save alignment suggestions
        alignment = Alignment(
            suggestions=alignment_service.format_suggestions(changes),
            impact_analysis=impact,
            timestamp=datetime.utcnow()
        )
        db.session.add(alignment)
        db.session.commit()

        flash('Project updated and aligned successfully!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        flash(f'Error updating project: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/document/inspect', methods=['GET', 'POST'])
def inspect_document():
    """
    Inspect document structure using the improved extraction capabilities.
    This allows users to see how the system extracts structured content from documents.
    """
    if request.method == 'POST':
        # Process file upload or text input
        content = ""
        doc_type = request.form.get('doc_type', 'prd')

        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            content = file.read().decode('utf-8')
        elif request.form.get('content'):
            content = request.form.get('content')
        else:
            flash('Please provide either a file or text content', 'error')
            return redirect(url_for('inspect_document'))

        try:
            # Extract structured content with improved generic extractor
            content_extractor = document_manager.content_extractor

            # First try a generic extraction
            structured_content = content_extractor.extract_structure(content)

            # Then use the document type hint for enhanced extraction
            structured_content = content_extractor.extract_structure(content, doc_type)

            # Validate structure with improved flexible validator
            document_validator = document_manager.document_validator
            validation = document_validator.validate_document(structured_content, doc_type)

            # Generate improvement suggestions if needed
            suggestions = document_validator.suggest_improvements(validation, structured_content, doc_type)

            # Calculate metadata
            metadata = {
                'title': structured_content.get('name', doc_type.upper()),
                'length': document_manager._calculate_document_length(structured_content),
                'detected_type': validation.get('identified_type', doc_type)
            }

            # Render the results
            return render_template(
                'document_inspector_results.html',
                raw_content=content,
                structured_content=structured_content,
                validation=validation,
                suggestions=suggestions,
                metadata=metadata,
                doc_type=doc_type
            )

        except Exception as e:
            logger.error(f"Error inspecting document: {str(e)}")
            flash(f'Error inspecting document: {str(e)}', 'error')
            return redirect(url_for('inspect_document'))

    # Show the upload form
    return render_template('document_inspector.html')

@app.route('/webhook', methods=['POST'])
@limiter.limit("100 per hour")
def webhook():
    """Handle updates from connected platforms"""
    try:
        data = request.json
        source = data.get('source')

        # Process the update based on source
        if source == 'jira':
            changes = sync_service.handle_jira_update(data)
        elif source == 'google_docs':
            changes = sync_service.handle_docs_update(data)
        elif source == 'confluence':
            changes = sync_service.handle_confluence_update(data)
        elif source == 'linear':
            changes = sync_service.handle_linear_update(data)
        else:
            return {'error': 'Unknown source'}, 400

        # If changes were detected, analyze and save alignment data
        if changes:
            # Get the latest project content
            project_content = sync_service.collect_all_content()

            # Analyze impact
            impact = impact_analyzer.analyze(changes)

            # Save to project
            project = Project(
                content=project_content,
                timestamp=datetime.utcnow()
            )
            db.session.add(project)

            # Save alignment suggestions
            alignment = Alignment(
                suggestions=alignment_service.format_suggestions(changes),
                impact_analysis=impact,
                timestamp=datetime.utcnow()
            )
            db.session.add(alignment)
            db.session.commit()

        return {'status': 'success', 'changes_detected': bool(changes)}, 200

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/api/suggestions', methods=['GET'])
def api_suggestions():
    """API endpoint to get latest suggestions"""
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    if alignment:
        return jsonify({
            'suggestions': json.loads(alignment.suggestions) if alignment.suggestions else [],
            'impact': json.loads(alignment.impact_analysis) if alignment.impact_analysis else None,
            'timestamp': alignment.timestamp
        })
    return jsonify({'suggestions': [], 'impact': None, 'timestamp': None})

@app.route('/api/impact', methods=['GET'])
def api_impact_analysis():
    """API endpoint to get latest impact analysis"""
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    if alignment and alignment.impact_analysis:
        return jsonify({
            'impact': json.loads(alignment.impact_analysis),
            'timestamp': alignment.timestamp
        })
    return jsonify({'impact': None, 'timestamp': None})

@app.route('/api/sync', methods=['GET'])
def api_sync_status():
    """API endpoint to get document sync status"""
    # Get the current project
    project = Project.query.order_by(Project.timestamp.desc()).first()
    if not project:
        return jsonify({
            'status': 'no_project',
            'documents': [],
            'last_sync': None
        })

    # Get connected documents
    connected_docs = []

    # Get Google Docs
    if google_docs:
        connected_docs.extend([{
            'id': doc['id'],
            'type': doc['type'],
            'source': 'google_docs',
            'connected_at': doc['connected_at']
        } for doc in google_docs.get_connected_docs()])

    # Get Jira projects
    if jira:
        connected_docs.extend([{
            'id': proj['id'],
            'type': 'jira',
            'source': 'jira',
            'connected_at': proj['connected_at']
        } for proj in jira.connected_projects])

    # Get Linear projects
    if linear:
        connected_docs.extend([{
            'id': proj['id'],
            'type': 'linear',
            'source': 'linear',
            'connected_at': proj['connected_at']
        } for proj in linear.connected_projects])

    # Get Confluence pages
    if confluence:
        connected_docs.extend([{
            'id': page['id'],
            'type': 'confluence',
            'source': 'confluence',
            'connected_at': page['connected_at']
        } for page in confluence.connected_pages])

    return jsonify({
        'status': 'active',
        'documents': connected_docs,
        'last_sync': project.timestamp
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)