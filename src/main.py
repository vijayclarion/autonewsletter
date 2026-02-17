#!/usr/bin/env python3
"""
Enterprise Newsletter Generator - Main Orchestrator (UPDATED)
Includes Step 3 (Refinement & Polish) and Step 4 (Technical Accuracy Review)
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict
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
        
        # NEW Step 2.5: Quality Validation
        print("\n🔍 Step 2.5: Quality Validation")
        print("-" * 70)
        quality_score = self._validate_extraction_quality(knowledge, combined_doc.content)
        print(f"  Quality Score: {quality_score:.1%}")
        
        if quality_score < 0.7:
            print("  ⚠ Quality below threshold, but continuing with current extraction...")
            # Note: In a full implementation, you could trigger re-extraction here
        
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
                    # Pass additional context for better diagram generation
                    diagram = self.diagram_generator.generate_diagram_from_suggestion(
                        suggestion=suggestion,
                        context={
                            'technologies': knowledge.technologies,
                            'architectures': knowledge.architectures,
                            'full_content': combined_doc.content[:5000]
                        }
                    )
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
            subtitle=subtitle,
            diagrams=diagrams  # NEW: Pass diagrams for embedding
        )
        
        # Add metadata about refinement
        newsletter_files['refinement_results'] = processing_results['refinement_results']
        
        # NEW Step 6: Generate Quality Report
        print("\n📊 Step 6: Quality Metrics Report")
        print("-" * 70)
        quality_report = self._generate_quality_report(
            knowledge=knowledge,
            diagrams=diagrams,
            quality_score=quality_score,
            processing_results=processing_results
        )
        
        print(f"  Overall Quality Score: {quality_report['overall_score']:.1%}")
        print(f"  Content Metrics:")
        for key, value in quality_report['content_metrics'].items():
            print(f"    - {key}: {value}")
        print(f"  Quality Gates:")
        for key, value in quality_report['quality_gates'].items():
            status = '✓' if value else '✗'
            print(f"    {status} {key}: {value}")
        
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
        print(f"   • Overall Score: {quality_report['overall_score']:.1%}")
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
            'quality_report': quality_report,  # NEW
            'summary': {
                'input_files': len(input_files),
                'total_words': combined_doc.word_count,
                'diagrams_generated': len(diagrams),
                'quality_score': quality_score,  # NEW
                'generated_at': datetime.now().isoformat()
            }
        }
    
    def _validate_extraction_quality(self, knowledge, source_content: str) -> float:
        """Validate extraction quality with scoring"""
        score = 1.0
        
        # Check executive summary length
        if len(knowledge.executive_summary) < 500:
            score -= 0.2
        
        # Check for specific examples (numbers, metrics)
        if not re.search(r'\d+', knowledge.executive_summary):
            score -= 0.15
        
        # Check highlight depth
        if knowledge.key_highlights:
            avg_desc_length = sum(len(h.get('description', '')) for h in knowledge.key_highlights) / len(knowledge.key_highlights)
            if avg_desc_length < 100:
                score -= 0.15
        
        # Check for strategic insights
        if not hasattr(knowledge, 'strategic_insights') or not knowledge.strategic_insights or not knowledge.strategic_insights.get('business_impact'):
            score -= 0.2
        
        # Check diagram suggestions
        if not knowledge.diagram_suggestions or len(knowledge.diagram_suggestions) < 2:
            score -= 0.1
        
        return max(0.0, score)
    
    def _generate_quality_report(self, knowledge, diagrams, quality_score, processing_results) -> Dict:
        """Generate comprehensive quality metrics report"""
        return {
            'overall_score': quality_score,
            'content_metrics': {
                'executive_summary_length': len(knowledge.executive_summary),
                'key_highlights_count': len(knowledge.key_highlights),
                'feature_articles_count': len(knowledge.feature_articles),
                'diagrams_generated': len(diagrams),
                'has_strategic_insights': hasattr(knowledge, 'strategic_insights') and bool(knowledge.strategic_insights)
            },
            'quality_gates': {
                'depth_check': quality_score >= 0.7,
                'strategic_framing': hasattr(knowledge, 'strategic_insights') and bool(knowledge.strategic_insights),
                'diagrams_present': len(diagrams) > 0,
                'accuracy_validated': processing_results.get('accuracy_review', {}).get('is_accurate', False) if isinstance(processing_results.get('accuracy_review'), dict) else False
            },
            'recommendations': processing_results.get('warnings', [])
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
