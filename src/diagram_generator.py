#!/usr/bin/env python3
"""
Diagram Generator Module
Generates technical diagrams using Eraser.io API or creates diagram specifications
"""

import os
import json
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
    eraser_code: Optional[str] = None
    image_path: Optional[str] = None


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
    
    def generate_diagram_from_suggestion(self, suggestion: Dict) -> DiagramSpec:
        """
        Generate diagram specification from RAG suggestion
        
        Args:
            suggestion: Dictionary with diagram details from RAG engine
        
        Returns:
            DiagramSpec object with diagram details
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
        
        # Save diagram code to file
        code_file = self._save_diagram_code(title, eraser_code)
        
        return DiagramSpec(
            title=title,
            diagram_type=diagram_type,
            purpose=purpose,
            elements=elements if isinstance(elements, list) else [],
            description=description,
            eraser_code=eraser_code,
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
