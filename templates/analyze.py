<!-- templates/analyze.html -->
{% extends "base.html" %}

{% block content %}

<h2>Analyze Document Alignment</h2>

{% if project %}
    {% set content = project.get_content_dict() %}

    <div class="content-section">
        <h3>Connected Documents</h3>
        <div class="connection-status">
            <div class="connection-item {% if content.prd %}connected{% endif %}">
                <strong>PRD:</strong> {% if content.prd %}{{ content.prd|length }} sections{% else %}Not connected{% endif %}
            </div>
            <div class="connection-item {% if content.prfaq %}connected{% endif %}">
                <strong>PRFAQ:</strong> {% if content.prfaq %}{{ content.prfaq|length }} sections{% else %}Not connected{% endif %}
            </div>
            <div class="connection-item {% if content.strategy %}connected{% endif %}">
                <strong>Strategy:</strong> {% if content.strategy %}{{ content.strategy|length }} sections{% else %}Not connected{% endif %}
            </div>
            <div class="connection-item {% if content.tickets %}connected{% endif %}">
                <strong>Tickets:</strong> {% if content.tickets %}{{ content.tickets|length }} items{% else %}None connected{% endif %}
            </div>
        </div>
    </div>

    {% if (content.prd and content.tickets) or (content.strategy and content.prd) or (content.prfaq and content.prd) %}
        <div class="content-section">
            <h3>AI-Powered Alignment Analysis</h3>
            <div class="processing-info">
                <p><strong>Smart Processing:</strong> DocSync will automatically choose the best analysis method:</p>
                <ul>
                    <li><strong>Simple Analysis:</strong> Fast alignment check for basic projects (1 API call)</li>
                    <li><strong>Self-Critique Enhancement:</strong> AI generates → critiques → improves analysis (3 API calls)</li>
                </ul>
                <p><em>Analysis will focus on alignment between your connected document types</em></p>
            </div>

            <form action="{{ url_for('manual_update') }}" method="post">
                <button type="submit" class="button">Analyze Document Alignment</button>
            </form>
        </div>

        <div class="content-section">
            <h3>What We'll Analyze</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
                {% if content.prd and content.tickets %}
                    <p>✓ <strong>PRD ↔ Tickets:</strong> Check if implementation tickets match PRD requirements</p>
                {% endif %}
                {% if content.strategy and content.prd %}
                    <p>✓ <strong>Strategy ↔ PRD:</strong> Verify business goals align with product features</p>
                {% endif %}
                {% if content.prfaq and content.prd %}
                    <p>✓ <strong>PRFAQ ↔ PRD:</strong> Ensure customer messaging matches actual functionality</p>
                {% endif %}
                {% if content.strategy and content.prfaq %}
                    <p>✓ <strong>Strategy ↔ PRFAQ:</strong> Confirm messaging aligns with business strategy</p>
                {% endif %}
                <p>✓ <strong>Cross-Document Consistency:</strong> Timeline, priority, and scope alignment</p>
            </div>
        </div>

        {% if last_analysis %}
            <div class="content-section">
                <h3>Previous Analysis Results</h3>
                <div style="background-color: #e7f3ff; padding: 15px; border-radius: 6px;">
                    <p><strong>Last analyzed:</strong> {{ last_analysis.timestamp.strftime('%Y-%m-%d %H:%M') }}</p>
                    <p><strong>Processing method:</strong> {{ last_analysis.processing_method.replace('_', ' ').title() }}</p>
                    <p><strong>API calls used:</strong> {{ last_analysis.api_calls_used }}</p>
                    <a href="{{ url_for('index') }}" class="button button-secondary">View Results</a>
                </div>
            </div>
        {% endif %}

    {% else %}
        <div class="content-section">
            <div class="misalignment-warning">
                <h3>Need More Documents</h3>
                <p>You need at least 2 different document types for meaningful alignment analysis.</p>
                <p><strong>Current status:</strong></p>
                <ul>
                    <li>PRD: {% if content.prd %}✓ Connected{% else %}✗ Not connected{% endif %}</li>
                    <li>Tickets: {% if content.tickets %}✓ Connected{% else %}✗ Not connected{% endif %}</li>
                    <li>Strategy: {% if content.strategy %}✓ Connected{% else %}✗ Not connected{% endif %}</li>
                    <li>PRFAQ: {% if content.prfaq %}✓ Connected{% else %}✗ Not connected{% endif %}</li>
                </ul>
                <a href="{{ url_for('setup') }}" class="button">Connect More Documents</a>
            </div>
        </div>
    {% endif %}

{% else %}
    <div class="empty-state">
        <h3>No Documents Connected</h3>
        <p>Connect your project documents first to analyze their alignment.</p>
        <a href="{{ url_for('setup') }}" class="button">Connect Documents</a>
    </div>
{% endif %}

<div class="content-section">
    <h3>💡 Enhance Individual Documents</h3>
    <div class="enhancement-suggestion">
        <p>For even better alignment results, consider enhancing individual documents first:</p>
        <p><strong><a href="https://docmint.repl.co" target="_blank">DocMint</a></strong> can help improve document clarity, structure, and completeness before alignment analysis.</p>
        <p><em>Better individual documents → Better alignment analysis</em></p>
    </div>
</div>

{% endblock %}