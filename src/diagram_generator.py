#!/usr/bin/env python3
"""
Diagram Generator Module
Generates technical diagrams using Eraser.io API or creates diagram specifications
"""

import os
import json
import requests
import html
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
    mermaid_code: Optional[str] = None  # NEW: Mermaid.js diagram code
    eraser_code: Optional[str] = None
    embed_html: Optional[str] = None  # NEW: HTML wrapper for embedding
    image_path: Optional[str] = None


class DiagramGenerator:
    """
    Generate technical diagrams for enterprise newsletters
    Supports Eraser.io diagram-as-code format
    """
    
    # Configuration constants
    MAX_CONTEXT_TECHNOLOGIES = 5
    MAX_CONTEXT_ARCHITECTURES = 3
    MAX_DIAGRAM_NODES = 15
    MAX_FALLBACK_ELEMENTS = 5
    MAX_LABEL_LENGTH = 50
    
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
        Generate diagram specification from RAG suggestion
        
        Args:
            suggestion: Dictionary with diagram details from RAG engine
            context: Optional context dict with technologies, architectures, full_content
        
        Returns:
            DiagramSpec object with diagram details including Mermaid.js code
        """
        title = suggestion.get('title', 'Technical Diagram')
        diagram_type = suggestion.get('type', 'architecture')
        purpose = suggestion.get('purpose', '')
        elements = suggestion.get('elements', [])
        description = suggestion.get('description', '')
        
        print(f"\n  🎨 Generating diagram: {title}")
        print(f"     Type: {diagram_type}")
        
        # Generate Eraser.io diagram code
        eraser_code = self._generate_eraser_code(
            title=title,
            diagram_type=diagram_type,
            elements=elements,
            description=description
        )
        
        # Generate Mermaid.js diagram code (NEW)
        mermaid_code = self._generate_mermaid_diagram(
            title=title,
            diagram_type=diagram_type,
            elements=elements,
            description=description,
            context=context
        )
        
        # Generate embeddable HTML (NEW)
        embed_html = self._generate_embed_html(
            title=title,
            purpose=purpose,
            mermaid_code=mermaid_code,
            description=description
        )
        
        # Save diagram code to files
        code_file = self._save_diagram_code(title, eraser_code)
        self._save_mermaid_code(title, mermaid_code)
        
        return DiagramSpec(
            title=title,
            diagram_type=diagram_type,
            purpose=purpose,
            elements=elements if isinstance(elements, list) else [],
            description=description,
            mermaid_code=mermaid_code,  # NEW
            eraser_code=eraser_code,
            embed_html=embed_html,  # NEW
            image_path=str(code_file)
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
    
    def _save_diagram_code(self, title: str, code: str) -> Path:
        """Save diagram code to file"""
        # Clean filename
        filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        filename = filename.replace(' ', '_').lower()
        
        file_path = self.output_dir / f"{filename}.eraser"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"     ✓ Saved diagram code: {file_path.name}")
        return file_path
    
    def _save_mermaid_code(self, title: str, code: str) -> Path:
        """Save Mermaid.js diagram code to file"""
        # Clean filename
        filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        filename = filename.replace(' ', '_').lower()
        
        file_path = self.output_dir / f"{filename}.mmd"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"     ✓ Saved Mermaid diagram: {file_path.name}")
        return file_path
    
    def _generate_mermaid_diagram(self, title: str, diagram_type: str, 
                                  elements: List[str], description: str,
                                  context: Dict = None) -> str:
        """
        Generate Mermaid.js diagram code using LLM
        
        Args:
            title: Diagram title
            diagram_type: Type of diagram (architecture, workflow, integration, security)
            elements: List of key elements to include
            description: Diagram description
            context: Optional context with technologies, architectures, content
        
        Returns:
            Mermaid.js diagram code
        """
        if not self.llm_available:
            return self._generate_fallback_mermaid(title, diagram_type, elements)
        
        # Map diagram types to Mermaid syntax
        mermaid_type_map = {
            'architecture': 'graph TD',
            'workflow': 'sequenceDiagram',
            'integration': 'graph LR',
            'security': 'graph TB'
        }
        
        mermaid_syntax = mermaid_type_map.get(diagram_type, 'graph TD')
        
        # Build context information if available
        context_info = ""
        if context:
            if context.get('technologies'):
                # Ensure technologies is a list of strings
                techs = context['technologies']
                if isinstance(techs, list):
                    tech_strs = [str(t) for t in techs[:self.MAX_CONTEXT_TECHNOLOGIES] if t]
                    if tech_strs:
                        context_info += f"\nTechnologies: {', '.join(tech_strs)}"
            
            if context.get('architectures'):
                archs = context['architectures']
                if isinstance(archs, list):
                    arch_names = [str(a.get('name', '')) for a in archs[:self.MAX_CONTEXT_ARCHITECTURES] if isinstance(a, dict) and a.get('name')]
                    if arch_names:
                        context_info += f"\nArchitectures: {', '.join(arch_names)}"
        
        # Create prompt for LLM
        prompt = f"""Generate a professional Mermaid.js diagram for a technical newsletter.

Diagram Title: {title}
Diagram Type: {diagram_type} (use {mermaid_syntax} syntax)
Key Elements: {', '.join(elements) if isinstance(elements, list) else elements}
Description: {description}{context_info}

REQUIREMENTS:
- Use proper Mermaid.js syntax for {mermaid_syntax}
- Include all key elements from the list
- Show clear relationships and data flow
- Use descriptive labels
- Keep it concise (max {self.MAX_DIAGRAM_NODES} nodes)
- Professional and easy to read
- For sequence diagrams, use proper participant declarations
- For graph diagrams, use meaningful node IDs and labels

Return ONLY the Mermaid.js code, no markdown fences or explanations.

MERMAID.JS CODE:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in creating technical diagrams using Mermaid.js syntax. Generate clean, professional diagrams."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            mermaid_code = response.choices[0].message.content.strip()
            
            # Clean up code blocks if present
            if mermaid_code.startswith('```'):
                lines = mermaid_code.split('\n')
                # Remove first and last lines if they are markdown fences
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                mermaid_code = '\n'.join(lines)
            
            # Remove "mermaid" language identifier if present at start
            if mermaid_code.startswith('mermaid\n'):
                mermaid_code = mermaid_code[8:]
            
            return mermaid_code.strip()
            
        except Exception as e:
            print(f"     ⚠ Mermaid LLM generation failed: {e}")
            return self._generate_fallback_mermaid(title, diagram_type, elements)
    
    def _generate_fallback_mermaid(self, title: str, diagram_type: str, 
                                   elements: List[str]) -> str:
        """
        Generate simple fallback Mermaid.js diagram if LLM fails
        
        Args:
            title: Diagram title
            diagram_type: Type of diagram
            elements: List of elements
        
        Returns:
            Basic Mermaid.js code
        """
        if diagram_type == 'workflow':
            return """sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System-->>User: Response"""
        
        elif diagram_type == 'integration':
            return """graph LR
    A[System A] -->|API| B[Gateway]
    B --> C[System B]
    C --> D[Database]"""
        
        elif diagram_type == 'security':
            return """graph TB
    A[User] --> B[Authentication]
    B --> C[Authorization]
    C --> D[Protected Resource]"""
        
        else:  # architecture or default
            # Try to use elements if available
            if isinstance(elements, list) and len(elements) >= 2:
                code = "graph TD\n"
                for i, element in enumerate(elements[:self.MAX_FALLBACK_ELEMENTS]):
                    safe_id = f"N{i}"
                    safe_label = str(element).replace('"', "'")[:self.MAX_LABEL_LENGTH]
                    code += f"    {safe_id}[{safe_label}]\n"
                
                # Add some connections
                for i in range(min(len(elements) - 1, self.MAX_FALLBACK_ELEMENTS - 1)):
                    code += f"    N{i} --> N{i+1}\n"
                
                return code
            else:
                return """graph TD
    A[Component A] --> B[Component B]
    B --> C[Component C]"""
    
    def _generate_embed_html(self, title: str, purpose: str, 
                            mermaid_code: str, description: str) -> str:
        """
        Generate HTML wrapper for Mermaid diagram embedding
        
        Args:
            title: Diagram title
            purpose: Purpose of the diagram
            mermaid_code: Mermaid.js code
            description: Diagram description
        
        Returns:
            HTML string with diagram container
        """
        # HTML-escape user-controlled fields to prevent XSS
        safe_title = html.escape(title)
        safe_purpose = html.escape(purpose)
        safe_description = html.escape(description)
        # Note: Mermaid code is not HTML-escaped as it needs to be processed by Mermaid.js library
        # The Mermaid.js library handles rendering safely
        
        html_output = f"""<div class="diagram-container">
    <h3>{safe_title}</h3>
    <p class="diagram-purpose">{safe_purpose}</p>
    <div class="mermaid">
{mermaid_code}
    </div>
    <p class="diagram-description">{safe_description}</p>
</div>"""
        
        return html_output
    
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
            
            if diagram.mermaid_code:
                doc += f"**Mermaid.js Code:**\n\n```mermaid\n{diagram.mermaid_code}\n```\n\n"
            
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
