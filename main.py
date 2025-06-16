# main.py
# Enhanced DocSync with self-critique technology and simplified UI

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

# Import enhanced services
from services.sync_service import SyncService
from services.enhanced_alignment_service import EnhancedAlignmentService
from services.document_manager import DocumentManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "20 per hour"]
)

# Initialize integrations
google_docs = GoogleDocsIntegration()
jira = JiraIntegration()
linear = LinearIntegration()
confluence = ConfluenceIntegration()

# Initialize enhanced services
sync_service = SyncService()
enhanced_alignment_service = EnhancedAlignmentService()
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
    """Main dashboard showing alignment results"""
    try:
        # Get the current project and latest alignment results
        project = Project.query.order_by(Project.timestamp.desc()).first()

        # Get latest alignment analysis
        alignment_results = None
        alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()

        if alignment and alignment.suggestions:
            try:
                # Try to parse enhanced alignment data
                suggestions_data = json.loads(alignment.suggestions)
                impact_data = json.loads(alignment.impact_analysis) if alignment.impact_analysis else {}

                # Check if this is new enhanced format
                if isinstance(suggestions_data, dict) and 'analysis' in suggestions_data:
                    alignment_results = suggestions_data
                else:
                    # Legacy format - convert to new format
                    alignment_results = {
                        'analysis': {
                            'alignment_score': 7,
                            'critical_misalignments': [],
                            'suggestions': suggestions_data if isinstance(suggestions_data, list) else [],
                            'overall_assessment': 'Legacy analysis format - consider re-running analysis for enhanced results'
                        },
                        'processing_method': 'legacy',
                        'api_calls_used': 1,
                        'enhancement_suggestions': []
                    }
            except json.JSONDecodeError:
                alignment_results = None

        return render_template('index.html', 
                             project=project,
                             alignment_results=alignment_results)

    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('index.html', project=None, alignment_results=None)

@app.route('/setup')
def setup():
    """Setup page for connecting documents"""
    project = Project.query.order_by(Project.timestamp.desc()).first()
    return render_template('setup.html', project=project)

@app.route('/analyze')
def analyze():
    """Analysis page for running alignment checks"""
    project = Project.query.order_by(Project.timestamp.desc()).first()

    # Get last analysis info
    last_analysis = None
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    if alignment:
        try:
            suggestions_data = json.loads(alignment.suggestions)
            if isinstance(suggestions_data, dict):
                last_analysis = {
                    'timestamp': alignment.timestamp,
                    'processing_method': suggestions_data.get('processing_method', 'unknown'),
                    'api_calls_used': suggestions_data.get('api_calls_used', 'unknown')
                }
        except:
            pass

    return render_template('analyze.html', project=project, last_analysis=last_analysis)

@app.route('/auth/google')
@limiter.limit("10 per hour")
def google_auth():
    return google_docs.authorize()

@app.route('/auth/callback')
def google_callback():
    token = google_docs.callback(request.args)
    session['google_token'] = token
    return redirect(url_for('setup'))

@app.route('/connect', methods=['POST'])
@limiter.limit("10 per hour")
def connect_document():
    """Connect a document to the project with enhanced processing"""
    try:
        doc_type = request.form.get('type')
        doc_id = request.form.get('id')
        doc_subtype = request.form.get('doc_type')  # For Google Docs

        # Connect the document
        success = False
        if doc_type == 'google_docs':
            success = google_docs.connect_document(doc_id)
            # Override the document type based on user selection
            if success and doc_subtype:
                # Update the document type in connected docs
                for doc in google_docs.connected_docs:
                    if doc['id'] == doc_id:
                        doc['type'] = doc_subtype
                        break
        elif doc_type == 'jira':
            success = jira.connect_project(doc_id)
        elif doc_type == 'linear':
            success = linear.connect_project(doc_id)
        elif doc_type == 'confluence':
            success = confluence.connect_page(doc_id)

        if not success:
            flash(f'Failed to connect {doc_type} document/project', 'error')
            return redirect(url_for('setup'))

        # Process document using enhanced document manager
        processed_doc = None
        if doc_type == 'google_docs' and doc_subtype:
            processed_doc = document_manager.process_document(
                doc_id=doc_id,
                doc_type=doc_subtype,
                integration_type=doc_type
            )

            # Log validation results
            if processed_doc and 'validation' in processed_doc:
                validation = processed_doc['validation']
                suggestions = processed_doc.get('suggestions', [])

                if suggestions:
                    flash(f"Document connected! Consider: {suggestions[0].get('suggestion', 'reviewing document structure')}", 'warning')
                else:
                    flash('Document connected successfully!', 'success')
            else:
                flash('Document connected successfully!', 'success')
        else:
            flash(f'{doc_type.title()} connected successfully!', 'success')

        # Update project content
        project_content = sync_service.collect_all_content()

        # Save or update project
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project:
            project.content = project_content
            project.timestamp = datetime.utcnow()
        else:
            project = Project(
                content=project_content,
                timestamp=datetime.utcnow()
            )
            db.session.add(project)

        db.session.commit()

        return redirect(url_for('setup'))

    except Exception as e:
        logger.error(f"Error connecting document: {str(e)}")
        flash(f'Error connecting document: {str(e)}', 'error')
        return redirect(url_for('setup'))

@app.route('/update', methods=['POST'])
@limiter.limit("5 per hour")
def manual_update():
    """Manually trigger enhanced alignment analysis"""
    try:
        # Collect all content
        project_content = sync_service.collect_all_content()

        # Check if we have enough content for analysis
        content_dict = json.loads(project_content)
        connected_types = sum(1 for doc_type, content in content_dict.items() 
                            if content and (isinstance(content, dict) and len(content) > 0 or 
                                          isinstance(content, list) and len(content) > 0))

        if connected_types < 2:
            flash('Connect at least 2 different document types for meaningful alignment analysis.', 'warning')
            return redirect(url_for('analyze'))

        # Run enhanced alignment analysis
        logger.info("Starting enhanced alignment analysis...")
        alignment_results = enhanced_alignment_service.analyze_alignment_with_critique(project_content)

        # Save or update project
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project:
            project.content = project_content
            project.timestamp = datetime.utcnow()
        else:
            project = Project(
                content=project_content,
                timestamp=datetime.utcnow()
            )
            db.session.add(project)

        # Save enhanced alignment results
        alignment = Alignment(
            suggestions=json.dumps(alignment_results),
            impact_analysis=json.dumps(alignment_results.get('analysis', {})),
            timestamp=datetime.utcnow()
        )
        db.session.add(alignment)
        db.session.commit()

        # Show appropriate success message
        processing_method = alignment_results.get('processing_method', 'simple')
        api_calls = alignment_results.get('api_calls_used', 1)

        if processing_method == 'self_critique':
            flash(f'Enhanced alignment analysis completed! Used self-critique processing ({api_calls} API calls) for higher quality results.', 'success')
        else:
            flash(f'Alignment analysis completed using {processing_method} processing ({api_calls} API call{"s" if api_calls != 1 else ""}).', 'success')

        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        flash(f'Error analyzing alignment: {str(e)}', 'error')
        return redirect(url_for('analyze'))

@app.route('/webhook', methods=['POST'])
@limiter.limit("100 per hour")
def webhook():
    """Handle updates from connected platforms with enhanced processing"""
    try:
        data = request.json
        source = data.get('source')

        # Process the update based on source
        changes = None
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

        # If changes were detected, run enhanced analysis
        if changes:
            logger.info(f"Changes detected from {source}, running enhanced alignment analysis")

            # Get the latest project content
            project_content = sync_service.collect_all_content()

            # Run enhanced alignment analysis
            alignment_results = enhanced_alignment_service.analyze_alignment_with_critique(project_content)

            # Save updated project
            project = Project.query.order_by(Project.timestamp.desc()).first()
            if project:
                project.content = project_content
                project.timestamp = datetime.utcnow()
            else:
                project = Project(
                    content=project_content,
                    timestamp=datetime.utcnow()
                )
                db.session.add(project)

            # Save enhanced alignment results
            alignment = Alignment(
                suggestions=json.dumps(alignment_results),
                impact_analysis=json.dumps(alignment_results.get('analysis', {})),
                timestamp=datetime.utcnow()
            )
            db.session.add(alignment)
            db.session.commit()

        return {'status': 'success', 'changes_detected': bool(changes)}, 200

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {'error': str(e)}, 500

# API endpoints for enhanced data
@app.route('/api/alignment', methods=['GET'])
def api_alignment():
    """API endpoint to get latest enhanced alignment analysis"""
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    if alignment and alignment.suggestions:
        try:
            alignment_data = json.loads(alignment.suggestions)
            return jsonify({
        'status': 'active',
        'connected_documents': {
            'prd': len(content.get('prd', {})) if content.get('prd') else 0,
            'prfaq': len(content.get('prfaq', {})) if content.get('prfaq') else 0,
            'strategy': len(content.get('strategy', {})) if content.get('strategy') else 0,
            'tickets': len(content.get('tickets', [])) if content.get('tickets') else 0
        },
        'last_analysis': last_analysis,
        'last_sync': project.timestamp.isoformat()
    })

# Remove old routes that are no longer needed
@app.route('/document/inspect', methods=['GET', 'POST'])
def inspect_document():
    """Redirect to DocMint for individual document enhancement"""
    flash('For individual document enhancement, use DocMint. DocSync focuses on alignment between documents.', 'info')
    return redirect('https://docmint.repl.co')

# Legacy API endpoints for backward compatibility
@app.route('/api/suggestions', methods=['GET'])
def api_suggestions():
    """Legacy API endpoint - redirects to new alignment endpoint"""
    return redirect(url_for('api_alignment'))

@app.route('/api/impact', methods=['GET'])
def api_impact_analysis():
    """Legacy API endpoint for impact analysis"""
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    if alignment and alignment.impact_analysis:
        try:
            impact_data = json.loads(alignment.impact_analysis)
            return jsonify({
                'impact': impact_data,
                'timestamp': alignment.timestamp.isoformat()
            })
        except json.JSONDecodeError:
            pass
    return jsonify({'impact': None, 'timestamp': None})

@app.route('/api/sync', methods=['GET'])
def api_sync_status():
    """Legacy API endpoint - redirects to new status endpoint"""
    return redirect(url_for('api_status'))

# Debug endpoint for development
@app.route('/debug')
def debug():
    """Debug information for development"""
    try:
        debug_info = {
            "api_key_configured": bool(app.config.get('CLAUDE_API_KEY')),
            "model": app.config.get('CLAUDE_MODEL'),
            "app_version": "Enhanced DocSync with Self-Critique",
            "database_path": app.config.get('SQLALCHEMY_DATABASE_URI'),
            "processing_methods": {
                "simple": "1 API call - for basic alignment checks",
                "self_critique": "3 API calls - generates → critiques → improves alignment analysis"
            }
        }

        # Test API connection
        api_key = app.config.get('CLAUDE_API_KEY')
        if api_key:
            try:
                import requests
                headers = {
                    'anthropic-version': '2023-06-01',
                    'x-api-key': api_key,
                    'content-type': 'application/json'
                }

                data = {
                    'model': app.config.get('CLAUDE_MODEL', 'claude-3-sonnet-20240229'),
                    'max_tokens': 10,
                    'messages': [
                        {'role': 'user', 'content': 'Say "API test successful"'}
                    ]
                }

                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data,
                    timeout=10
                )

                debug_info["api_test"] = "Success" if response.status_code == 200 else f"Failed: {response.status_code}"
            except Exception as e:
                debug_info["api_test"] = f"Error: {str(e)}"
        else:
            debug_info["api_test"] = "No API key configured"

        # Recent processing stats
        recent_alignments = Alignment.query.order_by(Alignment.timestamp.desc()).limit(5).all()
        processing_stats = []

        for alignment in recent_alignments:
            try:
                data = json.loads(alignment.suggestions)
                processing_stats.append({
                    'timestamp': alignment.timestamp.strftime('%Y-%m-%d %H:%M'),
                    'processing_method': data.get('processing_method', 'unknown'),
                    'api_calls': data.get('api_calls_used', 'unknown'),
                    'alignment_score': data.get('analysis', {}).get('alignment_score', 'unknown')
                })
            except:
                processing_stats.append({
                    'timestamp': alignment.timestamp.strftime('%Y-%m-%d %H:%M'),
                    'processing_method': 'legacy',
                    'api_calls': 'unknown',
                    'alignment_score': 'unknown'
                })

        debug_info["recent_processing"] = processing_stats

        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)ify({
                'alignment_results': alignment_data,
                'timestamp': alignment.timestamp.isoformat()
            })
        except json.JSONDecodeError:
            pass

    return jsonify({'alignment_results': None, 'timestamp': None})

@app.route('/api/status', methods=['GET'])
def api_status():
    """API endpoint to get connection and processing status"""
    project = Project.query.order_by(Project.timestamp.desc()).first()

    if not project:
        return jsonify({
            'status': 'no_project',
            'connected_documents': {},
            'last_analysis': None
        })

    content = project.get_content_dict()

    # Get latest alignment analysis info
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    last_analysis = None

    if alignment:
        try:
            alignment_data = json.loads(alignment.suggestions)
            last_analysis = {
                'timestamp': alignment.timestamp.isoformat(),
                'processing_method': alignment_data.get('processing_method', 'unknown'),
                'api_calls_used': alignment_data.get('api_calls_used', 'unknown'),
                'alignment_score': alignment_data.get('analysis', {}).get('alignment_score', 'unknown')
            }
        except:
            pass

    return json