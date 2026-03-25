#!/usr/bin/env python3
"""
Newsletter Generator Module (v2 with Template Support)
Formats extracted knowledge into enterprise-ready newsletter formats using Microsoft-style templates
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from rag_engine import ExtractedKnowledge


class NewsletterGenerator:
    """Generate enterprise-grade technology newsletters with Microsoft-style or storytelling templates"""

    def __init__(self, output_dir: str = "./output", template_dir: str = None,
                 template: str = "storytelling"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Set template directory
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to templates folder in project root
            self.template_dir = Path(__file__).parent.parent / "templates"

        # Choose which template to load
        self.template_name = template
        if template == "storytelling":
            preferred = "storytelling_newsletter_template.html"
            fallback  = "microsoft_newsletter_template.html"
        else:
            preferred = "microsoft_newsletter_template.html"
            fallback  = "storytelling_newsletter_template.html"

        template_path = self.template_dir / preferred
        if not template_path.exists():
            template_path = self.template_dir / fallback

        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                self.html_template = f.read()
            print(f"  ✓ Loaded template: {template_path.name}")
            self.template_path = template_path
        else:
            print(f"  ⚠ Template not found in: {self.template_dir}")
            self.html_template = None
            self.template_path = None

    def generate_newsletter(self, knowledge: ExtractedKnowledge,
                            title: str = "Technology Newsletter",
                            subtitle: str = "Enterprise IT Update",
                            diagrams: List = None) -> Dict[str, str]:
        """
        Generate newsletter in multiple formats with embedded diagrams.

        Args:
            knowledge: Extracted knowledge from RAG engine
            title: Newsletter title
            subtitle: Newsletter subtitle
            diagrams: List of DiagramSpec objects to embed (optional)

        Returns:
            Dictionary with paths to generated files
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        print("\n📝 Generating Newsletter Outputs")
        print("-" * 70)

        # Generate Markdown
        md_path = self._generate_markdown(knowledge, title, subtitle, timestamp, diagrams)
        print(f"  ✓ Markdown: {md_path.name}")

        # Generate HTML (with template and diagrams)
        html_path = self._generate_html_from_template(knowledge, title, subtitle, timestamp, diagrams)
        template_label = "Storytelling" if self.template_name == "storytelling" else "Microsoft"
        print(f"  ✓ HTML ({template_label} Template + Diagrams): {html_path.name}")

        # Generate JSON
        json_path = self._generate_json(knowledge, title, subtitle, timestamp, diagrams)
        print(f"  ✓ JSON: {json_path.name}")

        return {
            'markdown': str(md_path),
            'html': str(html_path),
            'json': str(json_path),
            'title': title,
            'subtitle': subtitle,
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_html_from_template(self, knowledge: ExtractedKnowledge,
                                     title: str, subtitle: str, timestamp: str,
                                     diagrams: List = None) -> Path:
        """Generate HTML newsletter using the active template with embedded diagrams"""

        if not self.html_template:
            # Fallback to inline generation if template not found
            return self._generate_html_inline(knowledge, title, subtitle, timestamp)

        is_storytelling = (
            self.template_path is not None
            and 'storytelling' in str(self.template_path)
        )

        # ── Build shared components ──────────────────────────────────────
        executive_summary_html = self._build_executive_summary(knowledge.executive_summary, is_storytelling)
        metrics_dashboard_html = self._build_metrics_dashboard(knowledge, is_storytelling)
        strategic_insights_html = self._build_strategic_insights_section(
            knowledge.strategic_insights if hasattr(knowledge, 'strategic_insights') else {},
            is_storytelling,
        )
        key_highlights_html = self._build_key_highlights(knowledge.key_highlights, is_storytelling)
        feature_articles_html = self._build_feature_articles(knowledge.feature_articles, is_storytelling)
        quick_bites_html = self._build_quick_bites(knowledge.quick_bites, is_storytelling)
        action_items_html = self._build_action_items(knowledge.action_items, is_storytelling)
        technologies_html = self._build_technologies(knowledge.technologies, is_storytelling)
        best_practices_html = self._build_best_practices(knowledge.best_practices, is_storytelling)
        diagrams_html = self._build_diagrams_section(diagrams, is_storytelling)

        # ── Replace placeholders ─────────────────────────────────────────
        html_content = self.html_template
        html_content = html_content.replace('{{TITLE}}', title)
        html_content = html_content.replace('{{SUBTITLE}}', subtitle)
        html_content = html_content.replace('{{DATE}}', datetime.now().strftime('%B %d, %Y'))
        html_content = html_content.replace('{{EXECUTIVE_SUMMARY}}', executive_summary_html)
        html_content = html_content.replace('{{METRICS_DASHBOARD}}', metrics_dashboard_html)
        html_content = html_content.replace('{{STRATEGIC_INSIGHTS}}', strategic_insights_html)
        html_content = html_content.replace('{{KEY_HIGHLIGHTS}}', key_highlights_html)
        html_content = html_content.replace('{{FEATURE_ARTICLES}}', feature_articles_html)
        html_content = html_content.replace('{{QUICK_BITES}}', quick_bites_html)
        html_content = html_content.replace('{{ACTION_ITEMS}}', action_items_html)
        html_content = html_content.replace('{{DIAGRAMS}}', diagrams_html)
        html_content = html_content.replace('{{TECHNOLOGIES}}', technologies_html)
        html_content = html_content.replace('{{BEST_PRACTICES}}', best_practices_html)
        html_content = html_content.replace('{{FOOTER_DATE}}', datetime.now().strftime('%B %d, %Y at %I:%M %p'))

        # ── Storytelling-specific placeholders ──────────────────────────
        if is_storytelling:
            narrative_intro_html = self._build_narrative_intro(
                getattr(knowledge, 'narrative_intro', '')
            )
            industry_perspective_html = self._build_industry_perspective(
                getattr(knowledge, 'industry_perspective', {})
            )
            section_intros = getattr(knowledge, 'section_intros', {}) or {}
            html_content = html_content.replace('{{NARRATIVE_INTRO}}', narrative_intro_html)
            html_content = html_content.replace('{{INDUSTRY_PERSPECTIVE}}', industry_perspective_html)
            html_content = html_content.replace(
                '{{SECTION_INTRO_HIGHLIGHTS}}',
                self._build_section_intro(section_intros.get('highlights', ''))
            )
            html_content = html_content.replace(
                '{{SECTION_INTRO_FEATURES}}',
                self._build_section_intro(section_intros.get('features', ''))
            )
            html_content = html_content.replace(
                '{{SECTION_INTRO_QUICK_BITES}}',
                self._build_section_intro(section_intros.get('quick_bites', ''))
            )
            html_content = html_content.replace(
                '{{SECTION_INTRO_ACTION_ITEMS}}',
                self._build_section_intro(section_intros.get('action_items', ''))
            )

        # Write to file
        html_path = self.output_dir / f"newsletter_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return html_path
    
    def _build_executive_summary(self, summary: str, is_storytelling: bool = False) -> str:
        """Build executive summary HTML"""
        if not summary:
            return "<p>No executive summary available.</p>"

        paragraphs = summary.split('\n\n') if '\n\n' in summary else [summary]
        html = ""
        for para in paragraphs:
            if para.strip():
                html += f"<p>{para.strip()}</p>\n"
        return html
    
    def _build_key_highlights(self, highlights: List, is_storytelling: bool = False) -> str:
        """Build key highlights HTML"""
        if not highlights:
            return "<p>No highlights available.</p>"

        if is_storytelling:
            return self._build_key_highlights_storytelling(highlights)

        html = ""
        for highlight in highlights:
            if isinstance(highlight, dict):
                title = highlight.get('title', 'Highlight')
                description = highlight.get('description', '')
                html += f"""
                <div class="highlight-card">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """
            else:
                html += f"""
                <div class="highlight-card">
                    <p>{highlight}</p>
                </div>
                """
        return html

    def _build_key_highlights_storytelling(self, highlights: List) -> str:
        """Build storytelling-style highlight cards with category stripes and 'why it matters'"""
        html = ""
        category_map = {
            'risk factor': 'risk',
            'risk': 'risk',
            'strategic opportunity': 'opportunity',
            'opportunity': 'opportunity',
            'technical achievement': 'technical',
            'technical': 'technical',
        }
        for highlight in highlights:
            if isinstance(highlight, dict):
                title = highlight.get('title', 'Highlight')
                description = highlight.get('description', '')
                category = highlight.get('category', 'Business Impact')
                why = highlight.get('why_it_matters', '')
                css_class = category_map.get(category.lower(), '')
                tag_class = css_class
                stripe_class = f'st-highlight-stripe {css_class}'.strip()
                tag_html = f'<span class="st-highlight-tag {tag_class}">{category}</span>' if category else ''
                why_html = f'<div class="st-why-it-matters">{why}</div>' if why else ''
                html += f"""
<div class="st-highlight-card">
    <div class="{stripe_class}"></div>
    <div class="st-highlight-body">
        <div class="st-highlight-meta">{tag_html}</div>
        <div class="st-highlight-title">{title}</div>
        <div class="st-highlight-desc">{description}</div>
        {why_html}
    </div>
</div>
"""
            else:
                html += f'<div class="st-highlight-card"><div class="st-highlight-stripe"></div><div class="st-highlight-body"><div class="st-highlight-desc">{highlight}</div></div></div>\n'
        return html

    def _build_feature_articles(self, articles: List, is_storytelling: bool = False) -> str:
        """Build feature articles HTML"""
        if not articles:
            return ""

        if is_storytelling:
            return self._build_feature_articles_storytelling(articles)

        html = '<h2 class="section-header">Feature Articles / Deep Dives</h2>\n'

        for article in articles:
            if isinstance(article, dict):
                html += '<div class="feature-article">\n'
                html += f'<h3>{article.get("title", "Feature Article")}</h3>\n'

                if article.get('context'):
                    html += '<div class="feature-section">\n'
                    html += '<h4>Context / Problem Statement</h4>\n'
                    html += f'<p>{article["context"]}</p>\n'
                    html += '</div>\n'

                if article.get('key_ideas'):
                    html += '<div class="feature-section">\n'
                    html += '<h4>Key Ideas or Architecture</h4>\n'
                    html += f'<p>{article["key_ideas"]}</p>\n'
                    html += '</div>\n'

                if article.get('benefits'):
                    html += '<div class="feature-section">\n'
                    html += '<h4>Benefits & Trade-offs</h4>\n'
                    html += f'<p>{article["benefits"]}</p>\n'
                    html += '</div>\n'

                if article.get('best_practices'):
                    html += '<div class="feature-section">\n'
                    html += '<h4>Recommended Best Practices</h4>\n'
                    html += f'<p>{article["best_practices"]}</p>\n'
                    html += '</div>\n'

                if article.get('call_to_action'):
                    html += '<div class="cta-box">\n'
                    html += '<strong>Call to Action</strong>\n'
                    html += f'<p>{article["call_to_action"]}</p>\n'
                    html += '</div>\n'

                html += '</div>\n'

        return html

    def _build_feature_articles_storytelling(self, articles: List) -> str:
        """Build storytelling story-arc feature articles"""
        html = ""
        for i, article in enumerate(articles, 1):
            if not isinstance(article, dict):
                continue
            title = article.get('title', f'Deep Dive {i}')
            hook = article.get('hook', '') or article.get('context', '')
            context = article.get('context', '')
            key_ideas = article.get('key_ideas', '')
            benefits = article.get('benefits', '')
            what_this_means = article.get('what_this_means', '')
            best_practices = article.get('best_practices', '')
            cta = article.get('call_to_action', '')

            # Render best_practices as list if it's a list
            if isinstance(best_practices, list):
                bp_items = ''.join(f'<li>{p}</li>' for p in best_practices)
                bp_html = f'<ul>{bp_items}</ul>'
            else:
                bp_html = f'<p>{best_practices}</p>' if best_practices else ''

            html += f"""
<div class="st-story-arc">
    <div class="st-story-header">
        <div class="st-story-chapter">Chapter {i}</div>
        <div class="st-story-title">{title}</div>
        {f'<div class="st-story-hook">{hook}</div>' if hook else ''}
    </div>
    <div class="st-story-body">
"""
            if context and context != hook:
                html += f"""
        <div class="st-story-section">
            <div class="st-story-section-label">The Challenge</div>
            <p>{context}</p>
        </div>
"""
            if key_ideas:
                html += f"""
        <div class="st-story-section">
            <div class="st-story-section-label">The Approach</div>
            <p>{key_ideas}</p>
        </div>
"""
            if benefits:
                html += f"""
        <div class="st-story-section">
            <div class="st-story-section-label">Business Impact</div>
            <p>{benefits}</p>
        </div>
"""
            if what_this_means:
                html += f"""
        <div class="st-what-this-means">
            <div class="st-what-this-means-label">What This Means</div>
            <p>{what_this_means}</p>
        </div>
"""
            if bp_html:
                html += f"""
        <div class="st-story-section">
            <div class="st-story-section-label">Recommended Actions</div>
            {bp_html}
        </div>
"""
            if cta:
                html += f"""
        <div class="st-cta-strip">
            <div class="st-cta-icon">→</div>
            <div class="st-cta-content">
                <div class="st-cta-label">Your Next Step</div>
                <div class="st-cta-text">{cta}</div>
            </div>
        </div>
"""
            html += "    </div>\n</div>\n"
        return html

    def _build_quick_bites(self, quick_bites: List, is_storytelling: bool = False) -> str:
        """Build quick bites HTML"""
        if not quick_bites:
            return ""

        if is_storytelling:
            html = '<div class="st-quick-bites"><ul>\n'
            for bite in quick_bites:
                html += f'<li>{bite}</li>\n'
            html += '</ul></div>\n'
            return html

        html = '<h2 class="section-header">Quick Bites / Short Updates</h2>\n'
        html += '<div class="quick-bites">\n<ul>\n'
        for bite in quick_bites:
            html += f'<li>{bite}</li>\n'
        html += '</ul>\n</div>\n'
        return html

    def _build_action_items(self, action_items: Dict, is_storytelling: bool = False) -> str:
        """Build action items HTML"""
        if not action_items or not isinstance(action_items, dict):
            return ""

        if is_storytelling:
            html = '<div class="st-action-items">\n'
            group_labels = {
                'engineering_teams': '⚙️  Engineering Teams',
                'architecture_teams': '🏛️  Architecture & Strategy',
                'leadership': '📌  Leadership & Decision Makers',
            }
            for key, label in group_labels.items():
                if action_items.get(key):
                    html += f'<div class="st-action-group"><div class="st-action-group-title">{label}</div><ul>\n'
                    for item in action_items[key]:
                        html += f'<li>{item}</li>\n'
                    html += '</ul></div>\n'
            html += '</div>\n'
            return html

        html = '<h2 class="section-header">Action Items / Next Steps</h2>\n'
        html += '<div class="action-items">\n'
        if action_items.get('engineering_teams'):
            html += '<h4>For Engineering Teams</h4>\n<ul>\n'
            for item in action_items['engineering_teams']:
                html += f'<li>{item}</li>\n'
            html += '</ul>\n'
        if action_items.get('architecture_teams'):
            html += '<h4>For Architecture / Strategy Teams</h4>\n<ul>\n'
            for item in action_items['architecture_teams']:
                html += f'<li>{item}</li>\n'
            html += '</ul>\n'
        if action_items.get('leadership'):
            html += '<h4>For Leadership / Decision Makers</h4>\n<ul>\n'
            for item in action_items['leadership']:
                html += f'<li>{item}</li>\n'
            html += '</ul>\n'
        html += '</div>\n'
        return html

    def _build_technologies(self, technologies: List, is_storytelling: bool = False) -> str:
        """Build technologies HTML"""
        if not technologies:
            return ""

        if is_storytelling:
            html = '<div class="st-section-label">Technologies</div>\n'
            html += '<div class="st-tech-tags">\n'
            for tech in technologies:
                html += f'<span class="st-tech-tag">{tech}</span>\n'
            html += '</div>\n'
            return html

        html = '<h2 class="section-header">Technologies Mentioned</h2>\n'
        html += '<div class="tech-tags">\n'
        for tech in technologies:
            html += f'<span class="tech-tag">{tech}</span>\n'
        html += '</div>\n'
        return html

    def _build_best_practices(self, best_practices: List, is_storytelling: bool = False) -> str:
        """Build best practices HTML"""
        if not best_practices:
            return ""

        if is_storytelling:
            html = '<div class="st-section-label">Best Practices</div>\n'
            html += '<div class="st-best-practices"><ul>\n'
            for practice in best_practices:
                html += f'<li>{practice}</li>\n'
            html += '</ul></div>\n'
            return html

        html = '<h2 class="section-header">Best Practices & Recommendations</h2>\n'
        html += '<div class="best-practices">\n<ul>\n'
        for practice in best_practices:
            html += f'<li>{practice}</li>\n'
        html += '</ul>\n</div>\n'
        return html

    def _build_diagrams_section(self, diagrams: List, is_storytelling: bool = False) -> str:
        """Build HTML section for diagrams with Eraser.io images"""
        if not diagrams:
            return ""

        if is_storytelling:
            html = '<div class="st-diagrams">\n'
            html += '<div class="st-section-label">Technical Diagrams</div>\n'
            for diagram in diagrams:
                html += '<div class="st-diagram-card">\n'
                html += f'  <div class="st-diagram-card-header"><h3>{diagram.title}</h3>'
                html += f'  <div class="st-diagram-card-purpose">{diagram.purpose}</div></div>\n'
                html += '  <div class="st-diagram-card-body">\n'
                if hasattr(diagram, 'eraser_image_path') and diagram.eraser_image_path:
                    html += f'    <img src="{diagram.eraser_image_path}" alt="{diagram.title}" />\n'
                    if hasattr(diagram, 'eraser_edit_url') and diagram.eraser_edit_url:
                        html += f'    <a href="{diagram.eraser_edit_url}" class="st-diagram-edit-link" target="_blank">✏️ Edit Diagram</a>\n'
                elif hasattr(diagram, 'mermaid_code') and diagram.mermaid_code:
                    html += f'    <div class="mermaid">\n{diagram.mermaid_code}\n    </div>\n'
                html += f'    <p class="st-diagram-desc">{diagram.description}</p>\n'
                html += '  </div>\n</div>\n'
            html += '</div>\n'
            return html

        html = '<div class="section diagrams-section">\n'
        html += '  <h2 class="section-header">📊 Technical Architecture & Diagrams</h2>\n'
        
        for diagram in diagrams:
            html += '<div class="diagram-container">\n'
            html += f'  <h3>{diagram.title}</h3>\n'
            html += f'  <p class="diagram-purpose">{diagram.purpose}</p>\n'
            
            # Use Eraser image if available, otherwise Mermaid
            if hasattr(diagram, 'eraser_image_path') and diagram.eraser_image_path:
                # Eraser.io professional diagram
                html += f'  <img src="{diagram.eraser_image_path}" alt="{diagram.title}" class="diagram-image" />\n'
                
                # Add edit link if available
                if hasattr(diagram, 'eraser_edit_url') and diagram.eraser_edit_url:
                    html += f'  <a href="{diagram.eraser_edit_url}" class="diagram-edit-link" target="_blank">✏️ Edit Diagram</a>\n'
            elif hasattr(diagram, 'mermaid_code') and diagram.mermaid_code:
                # Mermaid.js fallback
                html += f'  <div class="mermaid">\n{diagram.mermaid_code}\n  </div>\n'
            
            html += f'  <p class="diagram-description">{diagram.description}</p>\n'
            html += '</div>\n'
        
        html += '</div>\n'
        return html
    
    def _build_strategic_insights_section(self, strategic_insights: Dict,
                                          is_storytelling: bool = False) -> str:
        """Build strategic insights section"""
        if not strategic_insights:
            return ""

        if is_storytelling:
            html = '<div class="st-strategic">\n'
            if strategic_insights.get('business_impact'):
                html += '<div class="st-insight-card impact">\n'
                html += '<div class="st-insight-title">💼 Business Impact</div>\n'
                html += f'<p>{strategic_insights["business_impact"]}</p>\n'
                html += '</div>\n'
            if strategic_insights.get('risk_factors'):
                html += '<div class="st-insight-card risk">\n'
                html += '<div class="st-insight-title">⚠️ Risk Factors</div>\n'
                html += f'<p>{strategic_insights["risk_factors"]}</p>\n'
                html += '</div>\n'
            if strategic_insights.get('strategic_opportunities'):
                html += '<div class="st-insight-card opportunity">\n'
                html += '<div class="st-insight-title">🚀 Strategic Opportunities</div>\n'
                html += f'<p>{strategic_insights["strategic_opportunities"]}</p>\n'
                html += '</div>\n'
            html += '</div>\n'
            return html

        html = '<div class="section strategic-insights">\n'
        html += '  <h2 class="section-header">Strategic Insights</h2>\n'
        if strategic_insights.get('business_impact'):
            html += '<div class="insight-card impact">\n'
            html += '  <h4>💼 Business Impact</h4>\n'
            html += f'  <p>{strategic_insights["business_impact"]}</p>\n'
            html += '</div>\n'
        if strategic_insights.get('risk_factors'):
            html += '<div class="insight-card risk">\n'
            html += '  <h4>⚠️ Risk Factors</h4>\n'
            html += f'  <p>{strategic_insights["risk_factors"]}</p>\n'
            html += '</div>\n'
        if strategic_insights.get('strategic_opportunities'):
            html += '<div class="insight-card opportunity">\n'
            html += '  <h4>🚀 Strategic Opportunities</h4>\n'
            html += f'  <p>{strategic_insights["strategic_opportunities"]}</p>\n'
            html += '</div>\n'
        html += '</div>\n'
        return html

    def _build_metrics_dashboard(self, knowledge, is_storytelling: bool = False) -> str:
        """Build metrics dashboard from extracted data"""
        metrics = []
        
        # Extract metrics from content
        if hasattr(knowledge, 'key_highlights') and knowledge.key_highlights:
            metrics.append({
                'value': len(knowledge.key_highlights),
                'label': 'Key Insights'
            })
        
        if hasattr(knowledge, 'technologies') and knowledge.technologies:
            metrics.append({
                'value': len(knowledge.technologies),
                'label': 'Technologies'
            })
        
        if hasattr(knowledge, 'feature_articles') and knowledge.feature_articles:
            metrics.append({
                'value': len(knowledge.feature_articles),
                'label': 'Deep Dives'
            })
        
        # Look for numerical metrics in strategic insights
        if hasattr(knowledge, 'strategic_insights') and knowledge.strategic_insights:
            if knowledge.strategic_insights.get('key_metrics'):
                for metric in knowledge.strategic_insights['key_metrics']:
                    if isinstance(metric, dict):
                        metrics.append(metric)
        
        if not metrics:
            return ""

        if is_storytelling:
            html = '<div class="st-metrics">\n'
            for metric in metrics[:4]:
                html += f'<div class="st-metric">\n'
                html += f'  <span class="st-metric-value">{metric["value"]}</span>\n'
                html += f'  <span class="st-metric-label">{metric["label"]}</span>\n'
                html += '</div>\n'
            html += '</div>\n'
            return html

        html = '<div class="metrics-dashboard">\n'
        for metric in metrics[:4]:  # Max 4 metrics
            html += f'  <div class="metric-card">\n'
            html += f'    <span class="metric-value">{metric["value"]}</span>\n'
            html += f'    <span class="metric-label">{metric["label"]}</span>\n'
            html += f'  </div>\n'
        html += '</div>\n'
        return html

    # ── Storytelling-specific section builders ──────────────────────────

    def _build_narrative_intro(self, narrative_intro: str) -> str:
        """Build the narrative intro banner for the storytelling template"""
        if not narrative_intro:
            return ""
        return f'<div class="st-narrative-intro"><p>{narrative_intro}</p></div>\n'

    def _build_industry_perspective(self, industry_perspective: Dict) -> str:
        """Build the Industry Perspective section for the storytelling template"""
        if not industry_perspective:
            return ""
        headline = industry_perspective.get('headline', '')
        perspective = industry_perspective.get('perspective', '')
        bold_prediction = industry_perspective.get('bold_prediction', '')
        recommendation = industry_perspective.get('recommendation', '')

        if not any([headline, perspective, bold_prediction, recommendation]):
            return ""

        html = '<section id="industry-perspective" class="st-industry-perspective">\n'
        html += '  <div class="st-ip-header">\n'
        html += '    <div class="st-ip-eyebrow">Industry Perspective</div>\n'
        if headline:
            html += f'    <div class="st-ip-headline">{headline}</div>\n'
        html += '  </div>\n'
        html += '  <div class="st-ip-body">\n'
        if perspective:
            html += f'    <p class="st-ip-perspective">{perspective}</p>\n'
        if bold_prediction:
            html += '    <div class="st-ip-prediction">\n'
            html += '      <div class="st-ip-prediction-label">12–18 Month Outlook</div>\n'
            html += f'      <p>{bold_prediction}</p>\n'
            html += '    </div>\n'
        if recommendation:
            html += '    <div class="st-ip-recommendation">\n'
            html += '      <div class="st-ip-rec-label">Expert Recommendation</div>\n'
            html += f'      <p>{recommendation}</p>\n'
            html += '    </div>\n'
        html += '  </div>\n'
        html += '</section>\n'
        return html

    def _build_section_intro(self, intro_text: str) -> str:
        """Build a section intro paragraph for the storytelling template"""
        if not intro_text:
            return ""
        return f'<p class="st-section-intro">{intro_text}</p>\n'
    
    def _build_diagrams_markdown(self, diagrams: List) -> str:
        """Build Markdown section for diagrams"""
        if not diagrams:
            return ""
        
        md = "\n\n## 📊 Technical Architecture & Diagrams\n\n"
        
        for diagram in diagrams:
            md += f"### {diagram.title}\n\n"
            md += f"**Purpose:** {diagram.purpose}\n\n"
            
            if hasattr(diagram, 'mermaid_code') and diagram.mermaid_code:
                md += f"```mermaid\n{diagram.mermaid_code}\n```\n\n"
            
            md += f"*{diagram.description}*\n\n"
            md += "---\n\n"
        
        return md
    
    def _generate_markdown(self, knowledge: ExtractedKnowledge, 
                          title: str, subtitle: str, timestamp: str,
                          diagrams: List = None) -> Path:  # NEW: diagrams param
        """Generate Markdown newsletter with embedded diagrams"""
        
        md_content = f"""# {title}

**{subtitle}**

*Generated: {datetime.now().strftime('%B %d, %Y')}*

---

## Executive Summary

{knowledge.executive_summary}

---

## Key Highlights / What's New

"""
        
        # Add key highlights
        for i, highlight in enumerate(knowledge.key_highlights, 1):
            if isinstance(highlight, dict):
                md_content += f"### {i}. {highlight.get('title', 'Highlight')}\n\n"
                md_content += f"{highlight.get('description', '')}\n\n"
            else:
                md_content += f"### {i}. {highlight}\n\n"
        
        # Add feature articles
        if knowledge.feature_articles:
            md_content += "\n---\n\n## Feature Articles / Deep Dives\n\n"
            
            for article in knowledge.feature_articles:
                if isinstance(article, dict):
                    md_content += f"### {article.get('title', 'Feature')}\n\n"
                    
                    if article.get('context'):
                        md_content += f"**Context / Problem Statement**\n\n{article['context']}\n\n"
                    
                    if article.get('key_ideas'):
                        md_content += f"**Key Ideas or Architecture**\n\n{article['key_ideas']}\n\n"
                    
                    if article.get('benefits'):
                        md_content += f"**Benefits & Trade-offs**\n\n{article['benefits']}\n\n"
                    
                    if article.get('best_practices'):
                        md_content += f"**Recommended Best Practices**\n\n{article['best_practices']}\n\n"
                    
                    if article.get('call_to_action'):
                        md_content += f"**Call to Action**\n\n{article['call_to_action']}\n\n"
                    
                    md_content += "---\n\n"
        
        # Add quick bites
        if knowledge.quick_bites:
            md_content += "\n## Quick Bites / Short Updates\n\n"
            for bite in knowledge.quick_bites:
                md_content += f"- {bite}\n"
            md_content += "\n"
        
        # Add action items
        if knowledge.action_items:
            md_content += "\n---\n\n## Action Items / Next Steps\n\n"
            
            if isinstance(knowledge.action_items, dict):
                if knowledge.action_items.get('engineering_teams'):
                    md_content += "### For Engineering Teams\n\n"
                    for item in knowledge.action_items['engineering_teams']:
                        md_content += f"- {item}\n"
                    md_content += "\n"
                
                if knowledge.action_items.get('architecture_teams'):
                    md_content += "### For Architecture / Strategy Teams\n\n"
                    for item in knowledge.action_items['architecture_teams']:
                        md_content += f"- {item}\n"
                    md_content += "\n"
                
                if knowledge.action_items.get('leadership'):
                    md_content += "### For Leadership / Decision Makers\n\n"
                    for item in knowledge.action_items['leadership']:
                        md_content += f"- {item}\n"
                    md_content += "\n"
        
        # Add diagrams (NEW)
        if diagrams:
            md_content += self._build_diagrams_markdown(diagrams)
        
        # Add technologies
        if knowledge.technologies:
            md_content += "\n---\n\n## Technologies Mentioned\n\n"
            md_content += ", ".join(knowledge.technologies)
            md_content += "\n\n"
        
        # Add best practices
        if knowledge.best_practices:
            md_content += "\n## Best Practices & Recommendations\n\n"
            for practice in knowledge.best_practices:
                md_content += f"- {practice}\n"
            md_content += "\n"
        
        # Add diagrams section (NEW)
        if diagrams:
            md_content += self._build_diagrams_markdown(diagrams)
        
        # Write to file
        md_path = self.output_dir / f"newsletter_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return md_path
    
    def _build_diagrams_markdown(self, diagrams: List) -> str:
        """
        Build Markdown section for diagrams with Mermaid.js code blocks
        
        Args:
            diagrams: List of DiagramSpec objects
        
        Returns:
            Markdown string with Mermaid code blocks
        """
        if not diagrams:
            return ""
        
        md = "\n\n## 📊 Technical Architecture & Diagrams\n\n"
        
        for diagram in diagrams:
            md += f"### {diagram.title}\n\n"
            md += f"**Purpose:** {diagram.purpose}\n\n"
            
            # mermaid_code is Optional[str], truthiness check skips None and empty strings
            if diagram.mermaid_code:
                md += f"```mermaid\n{diagram.mermaid_code}\n```\n\n"
            
            md += f"*{diagram.description}*\n\n---\n\n"
        
        return md
    
    def _generate_json(self, knowledge: ExtractedKnowledge, 
                      title: str, subtitle: str, timestamp: str,
                      diagrams: List = None) -> Path:  # NEW: diagrams param
        """Generate JSON newsletter data with diagrams"""
        
        # Build diagrams data for JSON
        diagrams_data = []
        if diagrams:
            for diagram in diagrams:
                diagram_dict = {
                    'title': diagram.title,
                    'type': diagram.diagram_type,
                    'purpose': diagram.purpose,
                    'elements': diagram.elements,
                    'description': diagram.description
                }
                if hasattr(diagram, 'mermaid_code') and diagram.mermaid_code:
                    diagram_dict['mermaid_code'] = diagram.mermaid_code
                diagrams_data.append(diagram_dict)
        
        json_data = {
            'title': title,
            'subtitle': subtitle,
            'generated_at': datetime.now().isoformat(),
            'executive_summary': knowledge.executive_summary,
            'key_highlights': knowledge.key_highlights,
            'feature_articles': knowledge.feature_articles,
            'quick_bites': knowledge.quick_bites,
            'action_items': knowledge.action_items,
            'technologies': knowledge.technologies,
            'architectures': knowledge.architectures,
            'best_practices': knowledge.best_practices,
            'diagrams': diagrams_data,  # NEW: Include diagrams
            'diagram_suggestions': knowledge.diagram_suggestions,
            'metadata': knowledge.metadata
        }
        
        # Add diagrams array (NEW)
        if diagrams:
            json_data['diagrams'] = [
                {
                    'title': d.title,
                    'diagram_type': d.diagram_type,
                    'purpose': d.purpose,
                    'elements': d.elements,
                    'description': d.description,
                    'mermaid_code': d.mermaid_code,
                    'eraser_code': d.eraser_code,
                    'image_path': d.image_path
                } for d in diagrams
            ]
        
        # Write to file
        json_path = self.output_dir / f"newsletter_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return json_path
    
    def _generate_html_inline(self, knowledge: ExtractedKnowledge, 
                             title: str, subtitle: str, timestamp: str) -> Path:
        """Fallback inline HTML generation (if template not found)"""
        # This is the old method - kept as fallback
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}</style>
</head>
<body>
    <h1>{title}</h1>
    <h2>{subtitle}</h2>
    <p><em>{datetime.now().strftime('%B %d, %Y')}</em></p>
    <h2>Executive Summary</h2>
    <p>{knowledge.executive_summary}</p>
</body>
</html>"""
        
        html_path = self.output_dir / f"newsletter_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path


if __name__ == "__main__":
    print("Newsletter Generator v2 (with Template Support) loaded successfully!")
