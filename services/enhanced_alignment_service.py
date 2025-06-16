# services/enhanced_alignment_service.py
import json
import logging
import requests
from datetime import datetime
from models import db, Alignment, Project
from flask import current_app

logger = logging.getLogger(__name__)

class EnhancedAlignmentService:
    """
    Enhanced alignment service using self-critique technology
    for higher quality document alignment analysis
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_alignment_with_critique(self, project_content):
        """
        Analyze document alignment using self-critique for enhanced quality

        Args:
            project_content (str): JSON string of all project content

        Returns:
            dict: Enhanced alignment analysis with processing metadata
        """
        try:
            content_dict = json.loads(project_content)

            # Determine processing method based on content complexity
            processing_method = self._determine_processing_method(content_dict)

            if processing_method == "simple":
                return self._simple_alignment_analysis(content_dict)
            else:
                return self._self_critique_alignment_analysis(content_dict)

        except Exception as e:
            self.logger.error(f"Error in enhanced alignment analysis: {str(e)}")
            return self._fallback_analysis()

    def _determine_processing_method(self, content_dict):
        """Determine if content needs simple or self-critique processing"""
        # Count total content sections across all document types
        total_sections = 0
        has_multiple_doc_types = 0

        for doc_type, content in content_dict.items():
            if doc_type == 'tickets':
                total_sections += len(content) if isinstance(content, list) else 0
                if content:
                    has_multiple_doc_types += 1
            else:
                total_sections += len(content) if isinstance(content, dict) else 0
                if content:
                    has_multiple_doc_types += 1

        # Use simple processing for minimal content
        if total_sections < 5 or has_multiple_doc_types < 2:
            return "simple"

        return "self_critique"

    def _simple_alignment_analysis(self, content_dict):
        """Simple single-call alignment analysis"""
        self.logger.info("Using simple alignment analysis")

        prompt = self._create_alignment_prompt(content_dict)
        response = self._call_claude_api(prompt)

        if response:
            analysis_json = self._extract_json_from_response(response)
            return {
                'analysis': analysis_json,
                'processing_method': 'simple',
                'api_calls_used': 1,
                'enhancement_suggestions': self._check_for_enhancement_needs(content_dict)
            }

        return self._fallback_analysis()

    def _self_critique_alignment_analysis(self, content_dict):
        """Self-critique alignment analysis for higher quality"""
        self.logger.info("Using self-critique alignment analysis")

        try:
            # Step 1: Initial alignment analysis
            initial_prompt = self._create_alignment_prompt(content_dict)
            initial_response = self._call_claude_api(initial_prompt)

            if not initial_response:
                return self._fallback_analysis()

            initial_text = initial_response['content'][0]['text']

            # Step 2: Self-critique
            critique_prompt = f"""
You previously generated this document alignment analysis:

{initial_text}

For this project content:
{json.dumps(content_dict, indent=2)[:2000]}...

Critically evaluate your alignment analysis:

1. **Accuracy**: Are the identified misalignments actually present in the documents?
2. **Completeness**: What important alignment issues did you miss?
3. **Specificity**: Are your suggestions specific enough to be actionable?
4. **Prioritization**: Did you focus on the most critical alignment issues?
5. **Cross-Document Relationships**: Did you properly analyze relationships between different document types?

Focus on genuine improvements to make the alignment analysis more accurate and actionable.
Be honest about what could be better.
"""

            critique_response = self._call_claude_api(critique_prompt, max_tokens=1000)
            if not critique_response:
                return self._package_simple_result(initial_text, content_dict, 2)

            critique_text = critique_response['content'][0]['text']

            # Step 3: Enhanced analysis
            enhanced_prompt = f"""
Original alignment analysis:
{initial_text}

Self-critique identifying areas for improvement:
{critique_text}

Project content:
{json.dumps(content_dict, indent=2)[:2000]}...

Provide an enhanced alignment analysis that addresses the critique while maintaining the same JSON format.

Focus on:
- More accurate identification of real misalignments
- More specific, actionable suggestions
- Better prioritization of critical alignment issues
- Complete coverage of document relationships

Ensure all suggestions are specific and implementable.
"""

            enhanced_response = self._call_claude_api(enhanced_prompt)
            if not enhanced_response:
                return self._package_simple_result(initial_text, content_dict, 3)

            enhanced_text = enhanced_response['content'][0]['text']

            # Package results with process metadata
            analysis_json = self._extract_json_from_response(enhanced_text)

            return {
                'analysis': analysis_json,
                'processing_method': 'self_critique',
                'api_calls_used': 3,
                'enhancement_suggestions': self._check_for_enhancement_needs(content_dict),
                'process_details': {
                    'initial_response': initial_text[:500] + "...",
                    'critique': critique_text,
                    'enhanced_response': enhanced_text[:500] + "..."
                }
            }

        except Exception as e:
            self.logger.error(f"Error in self-critique analysis: {str(e)}")
            return self._fallback_analysis()

    def _create_alignment_prompt(self, content_dict):
        """Create the core alignment analysis prompt"""
        return f"""
# Document Alignment Analysis

Analyze these project documents for alignment issues and provide specific, actionable suggestions:

## Project Content:
{json.dumps(content_dict, indent=2)}

Provide analysis as JSON:
{{
    "alignment_score": 1-10,
    "critical_misalignments": [
        {{
            "issue": "Specific misalignment description",
            "documents": ["source_doc", "target_doc"],
            "impact": "High|Medium|Low",
            "suggestion": "Specific action to fix this misalignment"
        }}
    ],
    "suggestions": [
        {{
            "type": "prd_to_tickets|tickets_to_prd|strategy_alignment|prfaq_alignment",
            "action": "create|update|review|remove",
            "description": "Specific actionable suggestion",
            "priority": "High|Medium|Low",
            "source": "Source document type",
            "target": "Target document type"
        }}
    ],
    "overall_assessment": "Brief summary of document alignment status and next steps"
}}

Focus on specific, actionable alignment issues between:
- PRD requirements vs implementation tickets
- Strategy goals vs PRD features  
- Customer messaging (PRFAQ) vs actual functionality
- Timeline consistency across documents
- Missing connections between related concepts

Ensure all suggestions are specific enough to be immediately actionable.
"""

    def _check_for_enhancement_needs(self, content_dict):
        """Check if individual documents need DocMint enhancement"""
        enhancement_suggestions = []

        # Check PRD quality
        prd = content_dict.get('prd', {})
        if prd and len(prd) < 3:
            enhancement_suggestions.append({
                'document_type': 'prd',
                'suggestion': 'PRD appears incomplete. Consider using DocMint to enhance structure and clarity.',
                'priority': 'Medium'
            })

        # Check strategy document quality
        strategy = content_dict.get('strategy', {})
        if strategy and len(strategy) < 2:
            enhancement_suggestions.append({
                'document_type': 'strategy',
                'suggestion': 'Strategy document could be more comprehensive. DocMint can help structure and enhance it.',
                'priority': 'Medium'
            })

        # Check PRFAQ quality
        prfaq = content_dict.get('prfaq', {})
        if prfaq:
            faqs = prfaq.get('frequently_asked_questions', [])
            if isinstance(faqs, list) and len(faqs) < 3:
                enhancement_suggestions.append({
                    'document_type': 'prfaq',
                    'suggestion': 'PRFAQ could benefit from more comprehensive FAQs. DocMint can help generate better customer messaging.',
                    'priority': 'Low'
                })

        return enhancement_suggestions

    def _package_simple_result(self, result_text, content_dict, api_calls):
        """Package a simple result when self-critique fails"""
        analysis_json = self._extract_json_from_response(result_text)
        return {
            'analysis': analysis_json,
            'processing_method': 'simple_fallback',
            'api_calls_used': api_calls,
            'enhancement_suggestions': self._check_for_enhancement_needs(content_dict)
        }

    def _call_claude_api(self, prompt, max_tokens=2000):
        """Call Claude API with proper error handling"""
        try:
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-sonnet-20240229')

            if not api_key:
                self.logger.error("No Claude API key available")
                return None

            headers = {
                'anthropic-version': '2023-06-01',
                'x-api-key': api_key,
                'content-type': 'application/json'
            }

            data = {
                'model': model,
                'max_tokens': max_tokens,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }

            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return None

            return response.json()

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {str(e)}")
            return None

    def _extract_json_from_response(self, response):
        """Extract JSON from Claude's response"""
        import re

        if isinstance(response, dict) and 'content' in response:
            text = response['content'][0]['text']
        else:
            text = str(response)

        # Try to find JSON object
        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback to basic structure
        return {
            "alignment_score": 5,
            "critical_misalignments": [],
            "suggestions": [],
            "overall_assessment": "Alignment analysis completed with basic processing."
        }

    def _fallback_analysis(self):
        """Fallback analysis when all processing fails"""
        return {
            'analysis': {
                "alignment_score": 5,
                "critical_misalignments": [],
                "suggestions": [{
                    "type": "general",
                    "action": "review",
                    "description": "Review all documents for consistency and alignment",
                    "priority": "Medium",
                    "source": "all",
                    "target": "all"
                }],
                "overall_assessment": "Basic alignment check completed. Consider manual review of document consistency."
            },
            'processing_method': 'fallback',
            'api_calls_used': 0,
            'enhancement_suggestions': []
        }