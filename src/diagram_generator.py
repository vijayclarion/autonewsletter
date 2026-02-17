#!/usr/bin/env python3
"""
Diagram Generator Module
Generates technical diagrams using Eraser.io API or creates diagram specifications
"""

import os
import json
import re
import requests
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class DiagramSpec:
    """Specification for a technical diagram"""
    title: str
    diagram_type: str  # architecture, workflow, integration, security
    purpose: str
    elements: List[str]
    description: str
    mermaid_code: Optional[str] = None  # NEW - Mermaid.js diagram code
    eraser_code: Optional[str] = None
    ascii_diagram: Optional[str] = None  # NEW - ASCII diagram for text fallback
    image_path: Optional[str] = None
    embed_html: Optional[str] = None  # NEW - Ready-to-embed HTML


class DiagramGenerator:
    """
    Generate technical diagrams for enterprise newsletters
    Supports Eraser.io diagram-as-code format
    """
    
    def __init__(self, output_dir: str = "./output/diagrams"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize OpenAI for diagram code generation
        if OPENAI_AVAILABLE:
            try:
                self.client = OpenAI()
                self.llm_available = True
            except:
                self.llm_available = False
        else:
            self.llm_available = False
    
    def generate_diagram_from_suggestion(self, suggestion: Dict, context: Dict = None) -> DiagramSpec:
        """
        Generate diagram specification with multiple formats from RAG suggestion
        
        Args:
            suggestion: Dictionary with diagram details from RAG engine
            context: Additional context for better diagram generation (technologies, architectures, content)
        
        Returns:
            DiagramSpec object with diagram details in multiple formats
        """
        title = suggestion.get('title', 'Technical Diagram')
        diagram_type = suggestion.get('type', 'architecture')
        purpose = suggestion.get('purpose', '')
        elements = suggestion.get('elements', [])
        description = suggestion.get('description', '')
        
        print(f"\n  🎨 Generating diagram: {title}")
        print(f"     Type: {diagram_type}")
        
        # Generate Mermaid.js diagram code
        mermaid_code = self._generate_mermaid_diagram(
            title=title,
            diagram_type=diagram_type,
            elements=elements,
            description=description,
            context=context
        )
        
        # Generate Eraser.io diagram code (existing)
        eraser_code = self._generate_eraser_code(
            title=title,
            diagram_type=diagram_type,
            elements=elements,
            description=description
        )
        
        # Generate ASCII diagram (fallback)
        ascii_diagram = self._generate_ascii_diagram(
            title=title,
            diagram_type=diagram_type,
            elements=elements
        )
        
        # Generate embeddable HTML
        embed_html = self._generate_embed_html(
            title=title,
            purpose=purpose,
            mermaid_code=mermaid_code,
            description=description
        )
        
        # Save all diagram formats to files
        self._save_diagram_files(title, mermaid_code, eraser_code, ascii_diagram)
        
        return DiagramSpec(
            title=title,
            diagram_type=diagram_type,
            purpose=purpose,
            elements=elements if isinstance(elements, list) else [],
            description=description,
            mermaid_code=mermaid_code,
            eraser_code=eraser_code,
            ascii_diagram=ascii_diagram,
            embed_html=embed_html,
            image_path=str(self.output_dir / f"{self._sanitize_filename(title)}.mermaid.md")
        )
    
    def _generate_eraser_code(self, title: str, diagram_type: str, 
                             elements: List[str], description: str) -> str:
        """
        Generate Eraser.io diagram-as-code
        
        Eraser.io supports multiple diagram types:
        - Cloud Architecture Diagrams
        - Sequence Diagrams
        - Entity Relationship Diagrams
        - Flowcharts
        """
        
        if not self.llm_available:
            return self._generate_fallback_diagram(title, diagram_type, elements)
        
        # Create prompt for LLM to generate Eraser.io code
        prompt = f"""Generate Eraser.io diagram-as-code for the following technical diagram.

Diagram Title: {title}
Diagram Type: {diagram_type}
Key Elements: {', '.join(elements) if isinstance(elements, list) else elements}
Description: {description}

Eraser.io Syntax Guide:
- For architecture diagrams, use: ComponentName [icon: icon-name]
- Connect components with arrows: Component1 > Component2
- Add labels: Component1 > Component2: "label text"
- Group components: group "Group Name" {{ Component1; Component2 }}
- Use icons from: aws, azure, gcp, kubernetes, database, server, user, etc.

Generate clean, professional Eraser.io diagram code that follows Microsoft-style architecture diagram conventions.
Return ONLY the diagram code, no explanations."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in creating technical architecture diagrams using Eraser.io diagram-as-code syntax."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            eraser_code = response.choices[0].message.content.strip()
            
            # Clean up code blocks if present
            if eraser_code.startswith('```'):
                lines = eraser_code.split('\n')
                eraser_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else eraser_code
            
            return eraser_code
            
        except Exception as e:
            print(f"     ⚠ LLM generation failed: {e}")
            return self._generate_fallback_diagram(title, diagram_type, elements)
    
    def _generate_mermaid_diagram(self, title: str, diagram_type: str, 
                                  elements: List[str], description: str,
                                  context: Dict = None) -> str:
        """
        Generate Mermaid.js diagram code using LLM
        
        Returns valid Mermaid.js syntax based on diagram type
        """
        
        if not self.llm_available:
            return self._generate_fallback_mermaid(title, diagram_type, elements)
        
        # Determine Mermaid diagram type
        mermaid_type_map = {
            'architecture': 'graph TD',
            'workflow': 'sequenceDiagram',
            'integration': 'graph LR',
            'security': 'graph TB'
        }
        
        mermaid_type = mermaid_type_map.get(diagram_type, 'graph TD')
        
        # Build context string
        context_str = ""
        if context:
            if context.get('technologies'):
                context_str += f"\nTechnologies: {', '.join(context['technologies'][:10])}"
            if context.get('architectures'):
                arch_names = [a.get('name', '') for a in context['architectures'][:5] if isinstance(a, dict)]
                if arch_names:
                    context_str += f"\nArchitectures: {', '.join(arch_names)}"
        
        prompt = f"""Generate a Mermaid.js diagram for the following specification.

Diagram Title: {title}
Diagram Type: {diagram_type}
Key Elements: {', '.join(elements) if isinstance(elements, list) else elements}
Description: {description}
{context_str}

REQUIREMENTS:
- Use {mermaid_type} syntax
- Create a clear, readable diagram
- Use actual component names from elements
- Show relationships and data flow
- Keep it concise (max 15 nodes)
- Use descriptive labels

MERMAID.JS SYNTAX GUIDE:
- Architecture: graph TD; A[Component] --> B[Component]
- Workflow: sequenceDiagram; participant A; A->>B: Action
- Integration: graph LR; System1 --> API --> System2
- Security: graph TB; User --> Auth --> Service

Return ONLY the Mermaid.js code, no explanation.

MERMAID.JS DIAGRAM:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in creating technical diagrams using Mermaid.js syntax. Generate clear, accurate diagrams."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                timeout=30
            )
            
            mermaid_code = response.choices[0].message.content.strip()
            
            # Clean up code block markers if present
            mermaid_code = re.sub(r'^```mermaid\s*\n', '', mermaid_code)
            mermaid_code = re.sub(r'\n```\s*$', '', mermaid_code)
            
            return mermaid_code
            
        except Exception as e:
            print(f"  ⚠ Mermaid generation failed: {e}")
            return self._generate_fallback_mermaid(title, diagram_type, elements)
    
    def _generate_fallback_mermaid(self, title: str, diagram_type: str, elements: List[str]) -> str:
        """Generate simple fallback Mermaid diagram"""
        if diagram_type == 'workflow':
            return """sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System-->>User: Response"""
        else:
            # Architecture/Integration/Security
            if isinstance(elements, list) and len(elements) >= 2:
                nodes = '\n    '.join([f"{chr(65+i)}[{elem}]" for i, elem in enumerate(elements[:5])])
                connections = '\n    '.join([f"{chr(65+i)}-->{chr(65+i+1)}" for i in range(min(len(elements)-1, 4))])
                return f"""graph TD
    {nodes}
    {connections}"""
            else:
                return """graph TD
    A[Component A]-->B[Component B]
    B-->C[Component C]"""
    
    def _generate_ascii_diagram(self, title: str, diagram_type: str, elements: List[str]) -> str:
        """Generate simple ASCII diagram for text fallback"""
        if not isinstance(elements, list) or len(elements) < 2:
            return "  [Component A] --> [Component B] --> [Component C]"
        
        return " --> ".join([f"[{elem}]" for elem in elements[:5]])
    
    def _generate_embed_html(self, title: str, purpose: str, 
                           mermaid_code: str, description: str) -> str:
        """Generate ready-to-embed HTML with Mermaid diagram"""
        # Escape HTML in title, purpose, and description
        import html
        title_safe = html.escape(title)
        purpose_safe = html.escape(purpose)
        description_safe = html.escape(description)
        
        return f"""<div class="diagram-container">
    <h3>{title_safe}</h3>
    <p class="diagram-purpose">{purpose_safe}</p>
    <div class="mermaid">
{mermaid_code}
    </div>
    <p class="diagram-description">{description_safe}</p>
</div>"""
    
    def _save_diagram_files(self, title: str, mermaid_code: str, 
                          eraser_code: str, ascii_diagram: str) -> None:
        """Save all diagram formats to files"""
        safe_title = self._sanitize_filename(title)
        
        # Save Mermaid
        mermaid_file = self.output_dir / f"{safe_title}.mermaid.md"
        with open(mermaid_file, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n```mermaid\n{mermaid_code}\n```\n")
        
        # Save Eraser.io
        eraser_file = self.output_dir / f"{safe_title}.eraser"
        with open(eraser_file, 'w', encoding='utf-8') as f:
            f.write(eraser_code)
        
        # Save ASCII
        ascii_file = self.output_dir / f"{safe_title}.txt"
        with open(ascii_file, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n{'=' * len(title)}\n\n{ascii_diagram}\n")
        
        print(f"     ✓ Saved diagram files: {safe_title}.[mermaid.md|eraser|txt]")
    
    def _sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_').lower()
    
    def _generate_fallback_diagram(self, title: str, diagram_type: str, 
                                   elements: List[str]) -> str:
        """Generate basic fallback diagram code"""
        
        if diagram_type == "architecture":
            code = f"""// {title}
// Architecture Diagram

"""
            if isinstance(elements, list) and elements:
                for i, element in enumerate(elements[:10]):  # Limit to 10 elements
                    code += f"{element.replace(' ', '')} [icon: cloud]\n"
                
                # Add some basic connections
                if len(elements) > 1:
                    code += f"\n// Connections\n"
                    for i in range(min(len(elements) - 1, 5)):
                        code += f"{elements[i].replace(' ', '')} > {elements[i+1].replace(' ', '')}\n"
            
            return code
        
        elif diagram_type == "workflow":
            code = f"""// {title}
// Workflow Diagram

Start > Process1
Process1 > Decision
Decision > Process2: "Yes"
Decision > End: "No"
Process2 > End
"""
            return code
        
        elif diagram_type == "integration":
            code = f"""// {title}
// Integration Diagram

System1 [icon: server] > API [icon: cloud]: "REST API"
API > System2 [icon: database]: "Data Flow"
System2 > System3 [icon: cloud]: "Integration"
"""
            return code
        
        else:  # security or default
            code = f"""// {title}
// Technical Diagram

Component1 [icon: user] > Component2 [icon: server]
Component2 > Component3 [icon: database]
"""
            return code
    
    def generate_diagram_documentation(self, diagrams: List[DiagramSpec]) -> str:
        """
        Generate markdown documentation for all diagrams
        
        Args:
            diagrams: List of diagram specifications
        
        Returns:
            Markdown formatted documentation
        """
        doc = "# Technical Diagrams\n\n"
        doc += "This document contains specifications for all suggested technical diagrams.\n\n"
        doc += "---\n\n"
        
        for i, diagram in enumerate(diagrams, 1):
            doc += f"## {i}. {diagram.title}\n\n"
            doc += f"**Type:** {diagram.diagram_type.title()}\n\n"
            doc += f"**Purpose:** {diagram.purpose}\n\n"
            
            if diagram.elements:
                doc += f"**Key Elements:**\n"
                for element in diagram.elements:
                    doc += f"- {element}\n"
                doc += "\n"
            
            doc += f"**Description:**\n\n{diagram.description}\n\n"
            
            if diagram.eraser_code:
                doc += f"**Eraser.io Code:**\n\n```\n{diagram.eraser_code}\n```\n\n"
            
            if diagram.image_path:
                doc += f"**Diagram File:** `{Path(diagram.image_path).name}`\n\n"
            
            doc += "**How to Use:**\n"
            doc += "1. Copy the Eraser.io code above\n"
            doc += "2. Go to [Eraser.io](https://www.eraser.io/)\n"
            doc += "3. Create a new diagram and paste the code\n"
            doc += "4. Customize colors, layout, and styling as needed\n"
            doc += "5. Export as PNG or SVG for the newsletter\n\n"
            doc += "---\n\n"
        
        return doc
    
    def save_diagram_documentation(self, diagrams: List[DiagramSpec], 
                                   filename: str = "diagrams_guide.md") -> Path:
        """Save diagram documentation to file"""
        doc = self.generate_diagram_documentation(diagrams)
        
        doc_path = self.output_dir / filename
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        
        print(f"\n  📋 Diagram documentation saved: {doc_path.name}")
        return doc_path


if __name__ == "__main__":
    print("Diagram Generator module loaded successfully!")
    
    # Test with sample suggestion
    generator = DiagramGenerator()
    
    sample_suggestion = {
        'title': 'Cloud Architecture Overview',
        'type': 'architecture',
        'purpose': 'Show the high-level cloud architecture',
        'elements': ['API Gateway', 'Microservices', 'Database', 'Cache', 'Load Balancer'],
        'description': 'A typical cloud-native architecture with API gateway, microservices, and data layer'
    }
    
    diagram = generator.generate_diagram_from_suggestion(sample_suggestion)
    print(f"\n✓ Test diagram generated: {diagram.title}")
