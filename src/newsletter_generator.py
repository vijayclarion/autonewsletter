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
    """Generate enterprise-grade technology newsletters with Microsoft-style templates"""
    
    def __init__(self, output_dir: str = "./output", template_dir: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Set template directory
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to templates folder in project root
            self.template_dir = Path(__file__).parent.parent / "templates"
        
        # Load template
        self.template_path = self.template_dir / "microsoft_newsletter_template.html"
        if self.template_path.exists():
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.html_template = f.read()
            print(f"  ✓ Loaded Microsoft template: {self.template_path.name}")
        else:
            print(f"  ⚠ Template not found: {self.template_path}")
            self.html_template = None
    
    def generate_newsletter(self, knowledge: ExtractedKnowledge, 
                          title: str = "Technology Newsletter",
                          subtitle: str = "Enterprise IT Update",
                          diagrams: List = None) -> Dict[str, str]:  # NEW: diagrams param
        """
        Generate newsletter in multiple formats with embedded diagrams
        
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
        print(f"  ✓ HTML (Microsoft Template + Diagrams): {html_path.name}")
        
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
                                     diagrams: List = None) -> Path:  # NEW: diagrams param
        """Generate HTML newsletter using Microsoft template with embedded diagrams"""
        
        if not self.html_template:
            # Fallback to inline generation if template not found
            return self._generate_html_inline(knowledge, title, subtitle, timestamp)
        
        # Build components
        executive_summary_html = self._build_executive_summary(knowledge.executive_summary)
        key_highlights_html = self._build_key_highlights(knowledge.key_highlights)
        feature_articles_html = self._build_feature_articles(knowledge.feature_articles)
        quick_bites_html = self._build_quick_bites(knowledge.quick_bites)
        action_items_html = self._build_action_items(knowledge.action_items)
        technologies_html = self._build_technologies(knowledge.technologies)
        best_practices_html = self._build_best_practices(knowledge.best_practices)
        diagrams_html = self._build_diagrams_section(diagrams)  # NEW
        
        # Replace placeholders in template
        html_content = self.html_template
        html_content = html_content.replace('{{TITLE}}', title)
        html_content = html_content.replace('{{SUBTITLE}}', subtitle)
        html_content = html_content.replace('{{DATE}}', datetime.now().strftime('%B %d, %Y'))
        html_content = html_content.replace('{{EXECUTIVE_SUMMARY}}', executive_summary_html)
        html_content = html_content.replace('{{KEY_HIGHLIGHTS}}', key_highlights_html)
        html_content = html_content.replace('{{FEATURE_ARTICLES}}', feature_articles_html)
        html_content = html_content.replace('{{QUICK_BITES}}', quick_bites_html)
        html_content = html_content.replace('{{ACTION_ITEMS}}', action_items_html)
        html_content = html_content.replace('{{DIAGRAMS}}', diagrams_html)  # NEW
        html_content = html_content.replace('{{TECHNOLOGIES}}', technologies_html)
        html_content = html_content.replace('{{BEST_PRACTICES}}', best_practices_html)
        html_content = html_content.replace('{{DIAGRAMS}}', diagrams_html)  # NEW
        html_content = html_content.replace('{{FOOTER_DATE}}', datetime.now().strftime('%B %d, %Y at %I:%M %p'))
        
        # Write to file
        html_path = self.output_dir / f"newsletter_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _build_executive_summary(self, summary: str) -> str:
        """Build executive summary HTML"""
        if not summary:
            return "<p>No executive summary available.</p>"
        
        # Split into paragraphs
        paragraphs = summary.split('\n\n') if '\n\n' in summary else [summary]
        html = ""
        for para in paragraphs:
            if para.strip():
                html += f"<p>{para.strip()}</p>\n"
        
        return html
    
    def _build_key_highlights(self, highlights: List) -> str:
        """Build key highlights HTML"""
        if not highlights:
            return "<p>No highlights available.</p>"
        
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
    
    def _build_feature_articles(self, articles: List) -> str:
        """Build feature articles HTML"""
        if not articles:
            return ""
        
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
    
    def _build_quick_bites(self, quick_bites: List) -> str:
        """Build quick bites HTML"""
        if not quick_bites:
            return ""
        
        html = '<h2 class="section-header">Quick Bites / Short Updates</h2>\n'
        html += '<div class="quick-bites">\n<ul>\n'
        
        for bite in quick_bites:
            html += f'<li>{bite}</li>\n'
        
        html += '</ul>\n</div>\n'
        return html
    
    def _build_action_items(self, action_items: Dict) -> str:
        """Build action items HTML"""
        if not action_items or not isinstance(action_items, dict):
            return ""
        
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
    
    def _build_technologies(self, technologies: List) -> str:
        """Build technologies HTML"""
        if not technologies:
            return ""
        
        html = '<h2 class="section-header">Technologies Mentioned</h2>\n'
        html += '<div class="tech-tags">\n'
        
        for tech in technologies:
            html += f'<span class="tech-tag">{tech}</span>\n'
        
        html += '</div>\n'
        return html
    
    def _build_best_practices(self, best_practices: List) -> str:
        """Build best practices HTML"""
        if not best_practices:
            return ""
        
        html = '<h2 class="section-header">Best Practices & Recommendations</h2>\n'
        html += '<div class="best-practices">\n<ul>\n'
        
        for practice in best_practices:
            html += f'<li>{practice}</li>\n'
        
        html += '</ul>\n</div>\n'
        return html
    
    def _build_diagrams_section(self, diagrams: List) -> str:
        """Build HTML section for diagrams"""
        if not diagrams:
            return ""
        
        html = '<div class="section diagrams-section">\n'
        html += '  <h2 class="section-header">📊 Technical Architecture & Diagrams</h2>\n'
        
        for diagram in diagrams:
            if hasattr(diagram, 'embed_html') and diagram.embed_html:
                html += diagram.embed_html + '\n'
        
        html += '</div>\n'
        return html
    
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
