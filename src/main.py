#!/usr/bin/env python3
"""
Enterprise Newsletter Generator - Main Orchestrator (UPDATED)
Includes Step 3 (Refinement & Polish) and Step 4 (Technical Accuracy Review)
"""

import os
import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Import all modules
from document_preprocessor import DocumentPreprocessor, ProcessedDocument
from rag_engine import RAGEngine, ExtractedKnowledge
from content_refinement import NewsletterContentProcessor
from newsletter_generator import NewsletterGenerator
from diagram_generator import DiagramGenerator, DiagramSpec


class EnterpriseNewsletterGenerator:
    """
    Main orchestrator for enterprise newsletter generation
    Now includes refinement and technical accuracy review steps
    """
    
    def __init__(self, output_dir: str = "./output"):
        """Initialize all components"""
        print("\n" + "=" * 70)
        print("ENTERPRISE NEWSLETTER GENERATOR")
        print("=" * 70)
        print("\n🚀 Initializing components...")
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize all components
        self.preprocessor = DocumentPreprocessor()
        print("  ✓ Document Preprocessor")
        
        self.rag_engine = RAGEngine(chunk_size=500, chunk_overlap=50)
        print("  ✓ RAG Engine")
        
        self.content_processor = NewsletterContentProcessor()
        print("  ✓ Content Refinement & Accuracy Review")
        
        self.newsletter_generator = NewsletterGenerator(output_dir=output_dir)
        print("  ✓ Newsletter Generator")
        
        self.diagram_generator = DiagramGenerator(output_dir=f"{output_dir}/diagrams")
        print("  ✓ Diagram Generator")
        
        print("\n✓ All components initialized successfully!\n")
    
    def generate_newsletter(self, 
                          input_files: List[str],
                          title: str = "Technology Newsletter",
                          subtitle: str = "Enterprise IT Update") -> dict:
        """
        Generate complete newsletter from input files with refinement and accuracy review
        
        Args:
            input_files: List of file paths to process
            title: Newsletter title
            subtitle: Newsletter subtitle
        
        Returns:
            Dictionary with paths to all generated files
        """
        print("=" * 70)
        print(f"GENERATING NEWSLETTER: {title}")
        print("=" * 70)
        
        # Step 1: Process all input documents
        print("\n📄 Step 1: Processing Input Documents")
        print("-" * 70)
        
        processed_docs = []
        for file_path in input_files:
            try:
                doc = self.preprocessor.process_document(file_path)
                processed_docs.append(doc)
                print(f"  ✓ {Path(file_path).name}: {doc.word_count:,} words")
            except Exception as e:
                print(f"  ✗ Failed to process {file_path}: {e}")
        
        if not processed_docs:
            raise ValueError("No documents were successfully processed")
        
        # Combine all documents
        if len(processed_docs) > 1:
            print(f"\n  🔗 Combining {len(processed_docs)} documents...")
            combined_doc = self.preprocessor.combine_documents(processed_docs)
        else:
            combined_doc = processed_docs[0]
        
        print(f"  ✓ Total content: {combined_doc.word_count:,} words")
        
        # Step 2: Extract knowledge using RAG
        print("\n🧠 Step 2: Extracting Knowledge with RAG")
        print("-" * 70)
        
        knowledge = self.rag_engine.extract_knowledge(
            content=combined_doc.content,
            metadata=combined_doc.metadata
        )
        
        print(f"\n  ✓ Knowledge extraction complete!")
        print(f"     - Executive Summary: {len(knowledge.executive_summary)} chars")
        print(f"     - Key Highlights: {len(knowledge.key_highlights)}")
        print(f"     - Feature Articles: {len(knowledge.feature_articles)}")
        print(f"     - Technologies: {len(knowledge.technologies)}")
        print(f"     - Diagram Suggestions: {len(knowledge.diagram_suggestions)}")
        
        # ============================================================================
        # STEP 3: REFINEMENT & POLISH 
        # ============================================================================
        processing_results = {'refinement_results': {}, 'issues': [], 'warnings': []}
        processing_results = self.content_processor.process_content(knowledge, combined_doc.content)
        
        # ============================================================================
        # STEP 4: Generate diagrams
        # ============================================================================
        print("\n🎨 Step 4: Generating Technical Diagrams")
        print("-" * 70)
        
        diagrams = []
        if knowledge.diagram_suggestions:
            for suggestion in knowledge.diagram_suggestions:
                try:
                    diagram = self.diagram_generator.generate_diagram_from_suggestion(suggestion)
                    diagrams.append(diagram)
                except Exception as e:
                    print(f"  ⚠ Diagram generation failed: {e}")
        else:
            print("  ℹ No diagram suggestions found")
        
        if diagrams:
            # Save diagram documentation
            self.diagram_generator.save_diagram_documentation(diagrams)
            print(f"\n  ✓ Generated {len(diagrams)} diagram(s)")
        
        # ============================================================================
        # STEP 5: Generate newsletter outputs
        # ============================================================================
        print("\n📝 Step 5: Generating Newsletter Outputs")
        print("-" * 70)
        
        newsletter_files = self.newsletter_generator.generate_newsletter(
            knowledge=knowledge,
            title=title,
            subtitle=subtitle
        )
        
        # Add metadata about refinement
        newsletter_files['refinement_results'] = processing_results['refinement_results']
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ NEWSLETTER GENERATION COMPLETE!")
        print("=" * 70)
        print(f"\n📁 Output Directory: {self.output_dir}")
        print(f"\n📄 Generated Files:")
        print(f"   • Markdown: {Path(newsletter_files['markdown']).name}")
        print(f"   • HTML: {Path(newsletter_files['html']).name}")
        print(f"   • JSON: {Path(newsletter_files['json']).name}")
        
        if diagrams:
            print(f"\n🎨 Diagrams:")
            for diagram in diagrams:
                print(f"   • {diagram.title}: {Path(diagram.image_path).name}")
            print(f"   • Documentation: diagrams_guide.md")
        
        # Quality summary
        print(f"\n📊 Quality Metrics:")
        print(f"   • Refinement: {'✓ Applied' if processing_results['refinement_results'] else '○ None needed'}")
        print(f"   • Issues Found: {len(processing_results['issues'])}")
        print(f"   • Warnings: {len(processing_results['warnings'])}")
        
        print("\n" + "=" * 70)
        
        return {
            'newsletter': newsletter_files,
            'diagrams': [
                {
                    'title': d.title,
                    'type': d.diagram_type,
                    'file': d.image_path
                } for d in diagrams
            ],
            'refinement': processing_results['refinement_results'],
            'summary': {
                'input_files': len(input_files),
                'total_words': combined_doc.word_count,
                'diagrams_generated': len(diagrams),
                'generated_at': datetime.now().isoformat()
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate enterprise technology newsletters from various document sources"
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Input files (VTT, DOCX, PPTX, PDF, TXT, MD)'
    )
    parser.add_argument(
        '--title',
        default='Technology Newsletter',
        help='Newsletter title'
    )
    parser.add_argument(
        '--subtitle',
        default='Enterprise IT Update',
        help='Newsletter subtitle'
    )
    parser.add_argument(
        '--output',
        default='./output',
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
    
    # Generate newsletter
    generator = EnterpriseNewsletterGenerator(output_dir=args.output)
    
    try:
        result = generator.generate_newsletter(
            input_files=args.files,
            title=args.title,
            subtitle=args.subtitle
        )
        
        print("\n✅ Success! Newsletter generated successfully.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
