#!/usr/bin/env python3
"""
RAG Engine Module - FIXED VERSION
Handles document chunking and knowledge extraction with direct LLM calls (no vector DB)
"""

import os
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class ExtractedKnowledge:
    """Container for extracted knowledge from documents"""
    executive_summary: str = ""
    key_highlights: List[Dict] = field(default_factory=list)
    feature_articles: List[Dict] = field(default_factory=list)
    quick_bites: List[str] = field(default_factory=list)
    action_items: Dict = field(default_factory=dict)
    technologies: List[str] = field(default_factory=list)
    architectures: List[Dict] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    diagram_suggestions: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class RAGEngine:
    """
    RAG Engine - FIXED VERSION
    Direct LLM extraction without vector database dependency
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize RAG engine"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key="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")
                self.llm_available = True
                print("✓ OpenAI LLM initialized")
            except Exception as e:
                print(f"⚠ OpenAI initialization failed: {e}")
                self.llm_available = False
        else:
            self.llm_available = False
            print("⚠ OpenAI not available")
        
        # Skip vector DB initialization
        self.chroma_client = None
        self.collection = None
        print("✓ Vector database skipped (using direct LLM extraction)")
    
    def chunk_document(self, content: str) -> List[Dict]:
        """Chunk document into overlapping segments"""
        words = content.split()
        total_words = len(words)
        chunks = []
        
        print(f"  📊 Chunking: {total_words:,} words → ", end='')
        
        for i in range(0, total_words, self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'start_word': i,
                'end_word': i + len(chunk_words),
                'chunk_id': len(chunks),
                'word_count': len(chunk_words)
            })
        
        print(f"{len(chunks)} chunks")
        return chunks
    
    def extract_knowledge(self, content: str, metadata: Dict = None) -> ExtractedKnowledge:
        """Extract structured knowledge using direct LLM calls"""
        total_chars = len(content)
        total_words = len(content.split())
        
        print(f"\n🧠 RAG Knowledge Extraction")
        print(f"  Document: {total_chars:,} chars, {total_words:,} words")
        
        # Chunk the document
        chunks = self.chunk_document(content)
        
        # Use full content for extraction (no vector DB)
        print(f"\n  🔍 Extracting with direct LLM:")
        
        # Define extraction tasks
        extraction_tasks = {
            'executive_summary': {
                'prompt': '''Based on the following content, provide a 2-3 paragraph executive summary focusing on:
- What this content covers
- Why it matters for enterprise IT decision makers
- Key business and technical value

Content:
{content}

Executive Summary:'''
            },
            'key_highlights': {
                'prompt': '''Based on the following content, list 5-7 key highlights. For each, provide:
- title: Short impactful title (5-8 words)
- description: 1-2 line explanation of impact and relevance

Return as JSON array of objects with "title" and "description" keys.

Content:
{content}

Key Highlights (JSON):'''
            },
            'feature_articles': {
                'prompt': '''Based on the following content, identify 2-4 major topics for deep dive feature articles. For each, provide:
- title: Section title
- context: Problem statement or background
- key_ideas: Main architectural or technical concepts
- benefits: Business and technical benefits
- best_practices: Recommended practices
- call_to_action: Concrete next step

Return as JSON array of objects.

Content:
{content}

Feature Articles (JSON):'''
            },
            'quick_bites': {
                'prompt': '''Based on the following content, list 3-5 short updates, tips, or minor announcements (1-2 sentences each).

Content:
{content}

Quick Bites:'''
            },
            'action_items': {
                'prompt': '''Based on the following content, identify concrete action items for:
- engineering_teams: Actions for developers and engineers
- architecture_teams: Actions for architects and strategy teams
- leadership: Actions for decision makers and leadership

Return as JSON object with these three keys, each containing an array of action items.

Content:
{content}

Action Items (JSON):'''
            },
            'technologies': {
                'prompt': '''Based on the following content, list all technologies, tools, platforms, and services mentioned. 
Return as JSON array of strings.

Content:
{content}

Technologies (JSON):'''
            },
            'architectures': {
                'prompt': '''Based on the following content, identify key architectures or design patterns. For each, provide:
- name: Architecture or pattern name
- description: Brief description
- components: Key components or services
- use_case: When to use this

Return as JSON array of objects.

Content:
{content}

Architectures (JSON):'''
            },
            'best_practices': {
                'prompt': '''Based on the following content, list 4-6 best practices or recommendations mentioned.

Content:
{content}

Best Practices:'''
            },
            'diagrams': {
                'prompt': '''Based on the following content, suggest 3-4 technical diagrams that would help explain the content. For each:
- type: "architecture" | "workflow" | "integration" | "security"
- title: Diagram title
- purpose: What it explains and who it's for
- elements: List of key components/nodes
- description: How to recreate it

Return as JSON array of objects.

Content:
{content}

Diagrams (JSON):'''
            }
        }
        
        extracted_data = {}
        
        for category, config in extraction_tasks.items():
            print(f"    • {category}: ", end='', flush=True)
            
            # Prepare prompt with content
            prompt = config['prompt'].format(content=content[:3000])  # Limit content to 3000 chars to fit in token limit
            
            # Extract using LLM
            result = self._extract_with_llm(category, prompt)
            extracted_data[category] = result
            
            if result:
                print(f"✓ ({len(str(result))} chars)")
            else:
                print(f"⚠ (empty)")
        
        # Build ExtractedKnowledge object
        knowledge = ExtractedKnowledge(
            executive_summary=extracted_data.get('executive_summary', ''),
            key_highlights=self._parse_json_safe(extracted_data.get('key_highlights', []), []),
            feature_articles=self._parse_json_safe(extracted_data.get('feature_articles', []), []),
            quick_bites=self._parse_list(extracted_data.get('quick_bites', '')),
            action_items=self._parse_json_safe(extracted_data.get('action_items', {}), {}),
            technologies=self._parse_json_safe(extracted_data.get('technologies', []), []),
            architectures=self._parse_json_safe(extracted_data.get('architectures', []), []),
            best_practices=self._parse_list(extracted_data.get('best_practices', '')),
            diagram_suggestions=self._parse_json_safe(extracted_data.get('diagrams', []), []),
            metadata={'total_words': total_words, 'total_chars': total_chars}
        )
        
        return knowledge
    
    def _extract_with_llm(self, category: str, prompt: str) -> str:
        """Extract using LLM"""
        if not self.llm_available:
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert enterprise technology analyst and technical writer. Extract only factual information from the content provided."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                timeout=30
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"\n    Error in {category}: {e}")
            return ""
    
    def _parse_json_safe(self, text: str, default):
        """Safely parse JSON from LLM response"""
        if isinstance(text, (list, dict)):
            return text
        
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            
            return json.loads(text)
        except:
            return default
    
    def _parse_list(self, text: str) -> List[str]:
        """Parse list from text"""
        if isinstance(text, list):
            return text
        
        # Split by newlines and clean
        items = [line.strip() for line in text.split('\n') if line.strip()]
        # Remove bullet points and numbering
        items = [re.sub(r'^[\d\-\*\•]+[\.\)]\s*', '', item) for item in items]
        return [item for item in items if item]


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RAG ENGINE - FIXED VERSION (Direct LLM, No Vector DB)")
    print("=" * 70)
    
    rag = RAGEngine()
    print("\n✓ RAG Engine initialized successfully!")