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
    strategic_insights: Dict = field(default_factory=dict)
    # Storytelling enhancements
    narrative_intro: str = ""           # Compelling opening hook for the newsletter
    industry_perspective: Dict = field(default_factory=dict)  # Thought-leadership section


class RAGEngine:
    """
    RAG Engine - FIXED VERSION
    Direct LLM extraction without vector database dependency
    """
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        """Initialize RAG engine with enhanced parameters"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize OpenAI with API key from environment
        if OPENAI_AVAILABLE:
            try:
                api_key = os.environ.get('OPENAI_API_KEY', 'api_key_placeholder')
                self.client = OpenAI(api_key=api_key)
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
        
        # Business and technical keywords for re-ranking
        self.business_keywords = [
            'impact', 'cost', 'revenue', 'efficiency', 'risk', 'strategic', 
            'roi', 'opportunity', 'growth', 'competitive', 'advantage', 'savings',
            'investment', 'business', 'customer', 'market', 'value'
        ]
        self.technical_keywords = [
            'architecture', 'scalability', 'performance', 'security', 
            'reliability', 'availability', 'integration', 'deployment',
            'infrastructure', 'system', 'platform', 'service', 'api'
        ]
    
    def chunk_document_recursive(self, content: str) -> List[Dict]:
        """
        Chunk document using recursive character-based splitting with semantic boundaries
        Preserves paragraph and sentence structure
        """
        separators = ["\n\n", "\n", ". ", " ", ""]
        chunks = []
        
        print(f"  📊 Chunking: {len(content):,} chars → ", end='')
        
        def split_text(text: str, separators: List[str]) -> List[str]:
            """Recursively split text using separators"""
            if not separators:
                return [text]
            
            separator = separators[0]
            splits = text.split(separator)
            
            result = []
            for split in splits:
                if len(split) > self.chunk_size and len(separators) > 1:
                    # Continue splitting with next separator
                    result.extend(split_text(split, separators[1:]))
                elif split:
                    result.append(split)
            
            return result
        
        # Split content
        text_splits = split_text(content, separators)
        
        # Combine splits into chunks with overlap
        current_chunk = ""
        for i, split in enumerate(text_splits):
            if len(current_chunk) + len(split) < self.chunk_size:
                current_chunk += split + " "
            else:
                if current_chunk:
                    # Determine position (early/middle/late)
                    position_pct = i / len(text_splits)
                    if position_pct < 0.33:
                        position = "early"
                    elif position_pct < 0.67:
                        position = "middle"
                    else:
                        position = "late"
                    
                    chunks.append({
                        'text': current_chunk.strip(),
                        'chunk_id': len(chunks),
                        'char_count': len(current_chunk),
                        'position': position,
                        'position_pct': position_pct
                    })
                
                # Start new chunk with overlap
                if len(chunks) > 0 and self.chunk_overlap > 0:
                    # Take last N characters as overlap
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap_text + split + " "
                else:
                    current_chunk = split + " "
        
        # Add last chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_id': len(chunks),
                'char_count': len(current_chunk),
                'position': 'late',
                'position_pct': 1.0
            })
        
        print(f"{len(chunks)} chunks")
        return chunks
    
    def re_rank_chunks(self, chunks: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Re-rank chunks by business impact and technical relevance
        Business keywords weighted 2x higher than technical keywords
        """
        print(f"  🎯 Re-ranking {len(chunks)} chunks by business impact...")
        
        for chunk in chunks:
            text_lower = chunk['text'].lower()
            
            # Score business keywords (weight = 2)
            business_score = sum(2 for keyword in self.business_keywords if keyword in text_lower)
            
            # Score technical keywords (weight = 1)
            technical_score = sum(1 for keyword in self.technical_keywords if keyword in text_lower)
            
            # Combined score
            chunk['relevance_score'] = business_score + technical_score
        
        # Sort by relevance score (descending)
        ranked_chunks = sorted(chunks, key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top K chunks
        top_chunks = ranked_chunks[:top_k]
        print(f"    Top chunk scores: {[c['relevance_score'] for c in top_chunks[:5]]}")
        
        return top_chunks
    
    def chunk_document(self, content: str) -> List[Dict]:
        """Chunk document into overlapping segments (legacy method for compatibility)"""
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
        """Extract structured knowledge using multi-pass extraction strategy"""
        total_chars = len(content)
        total_words = len(content.split())
        
        print(f"\n🧠 RAG Knowledge Extraction (Multi-Pass Strategy)")
        print(f"  Document: {total_chars:,} chars, {total_words:,} words")
        
        # Chunk the document using recursive chunking
        chunks = self.chunk_document_recursive(content)
        
        # Re-rank chunks for business impact
        ranked_chunks = self.re_rank_chunks(chunks, top_k=10)
        
        print(f"\n  🔍 Multi-Pass Extraction:")
        
        # Pass 1: Strategic Executive Summary (early + late chunks, up to 8000 chars)
        print(f"    • Pass 1: Strategic Executive Summary...", end='', flush=True)
        executive_summary = self._extract_executive_summary(chunks, content[:8000])
        print(f" ✓")
        
        # Pass 2: Key Highlights (re-ranked chunks, up to 8000 chars)
        print(f"    • Pass 2: Key Highlights (Re-ranked)...", end='', flush=True)
        key_highlights = self._extract_key_highlights(ranked_chunks[:5], content[:8000])
        print(f" ✓")
        
        # Pass 3: Feature Articles (middle chunks, up to 10000 chars)
        print(f"    • Pass 3: Feature Articles (Deep-dive)...", end='', flush=True)
        feature_articles = self._extract_feature_articles(chunks, content[:10000])
        print(f" ✓")
        
        # Pass 4: Supporting Content (first 4-6 chunks)
        print(f"    • Pass 4: Supporting Content...", end='', flush=True)
        quick_bites = self._extract_quick_bites(chunks[:6], content[:6000])
        action_items = self._extract_action_items(chunks[:6], content[:6000])
        technologies = self._extract_technologies(chunks[:6], content[:6000])
        architectures = self._extract_architectures(chunks[:6], content[:6000])
        best_practices = self._extract_best_practices(chunks[:6], content[:6000])
        diagrams = self._extract_diagrams(chunks[:6], content[:6000])
        print(f" ✓")

        # Pass 5: Strategic Insights
        print(f"    • Pass 5: Strategic Insights...", end='', flush=True)
        strategic_insights = self._extract_strategic_insights(content[:8000])
        print(f" ✓")

        # Pass 6: Narrative Intro (storytelling hook)
        print(f"    • Pass 6: Narrative Intro...", end='', flush=True)
        narrative_intro = self._extract_narrative_intro(executive_summary, strategic_insights)
        print(f" ✓")

        # Pass 7: Industry Perspective (thought leadership)
        print(f"    • Pass 7: Industry Perspective...", end='', flush=True)
        industry_perspective = self._extract_industry_perspective(
            content[:6000], technologies, strategic_insights
        )
        print(f" ✓")

        # Build ExtractedKnowledge object
        knowledge = ExtractedKnowledge(
            executive_summary=executive_summary,
            key_highlights=key_highlights,
            feature_articles=feature_articles,
            quick_bites=quick_bites,
            action_items=action_items,
            technologies=technologies,
            architectures=architectures,
            best_practices=best_practices,
            diagram_suggestions=diagrams,
            metadata={'total_words': total_words, 'total_chars': total_chars},
            strategic_insights=strategic_insights,
            narrative_intro=narrative_intro,
            industry_perspective=industry_perspective,
        )

        return knowledge
    
    def _extract_executive_summary(self, chunks: List[Dict], context: str) -> str:
        """Pass 1: Strategic Executive Summary with business impact framing"""
        # Use early + late chunks for context
        early_chunks = [c for c in chunks if c['position'] == 'early'][:2]
        late_chunks = [c for c in chunks if c['position'] == 'late'][:2]
        combined_chunks = early_chunks + late_chunks
        
        chunk_text = "\n\n".join([c['text'] for c in combined_chunks])
        context_text = chunk_text[:8000] if len(chunk_text) > 8000 else chunk_text
        
        prompt = f"""Based on the following content, write a strategic executive summary (3-5 paragraphs) that a C-suite technology leader would send to the board.

REQUIREMENTS:
- Paragraph 1 — Lead with the single most important business signal from this content. What is the strategic implication RIGHT NOW?
- Paragraph 2 — Articulate the core problem or opportunity with precision. Use specific examples and data points from the content.
- Paragraph 3 — Describe the solution or approach being taken. What makes it differentiated? Be specific.
- Paragraph 4 — Quantify the business impact: cost savings, time reduction, risk mitigation, revenue opportunity. Use numbers from the content where available.
- Paragraph 5 (optional) — Issue a bold, clear recommendation. What must leadership do in the next 30/60/90 days?

TONE: Authoritative, analytical, executive-grade. Active voice throughout. No hedging phrases (might, could, possibly). No passive constructions. Every sentence must add insight.

AVOID:
- Opening with "This document covers..." or "The content discusses..."
- Filler phrases: "basically", "actually", "you know"
- Speculative language: "might", "could", "possibly", "perhaps", "probably"
- Vague generalities without supporting specifics

Content:
{context_text}

Strategic Executive Summary:"""
        
        return self._extract_with_llm_v2('executive_summary', prompt, max_tokens=1200, temperature=0.5)
    
    def _extract_key_highlights(self, ranked_chunks: List[Dict], context: str) -> List[Dict]:
        """Pass 2: Key Highlights with re-ranked chunks"""
        chunk_text = "\n\n".join([c['text'] for c in ranked_chunks])
        context_text = chunk_text[:8000] if len(chunk_text) > 8000 else chunk_text

        prompt = f"""Based on the following high-impact content, extract 5-7 key highlights.

For each highlight, provide:
- title: Assertive, impact-led title (7-12 words) that states a clear finding — NOT a vague label
- description: 3-4 sentences. Start with the business consequence, then provide specific context and at least one concrete example or data point from the content.
- category: One of "Business Impact" | "Risk Factor" | "Strategic Opportunity" | "Technical Achievement"
- why_it_matters: 1 sentence explaining the "so what?" for a senior technology leader

REQUIREMENTS:
- Every title must communicate an insight, not just a topic (e.g. "AI Code Review Cuts Defect Rate by 30%" NOT "AI Code Review")
- Descriptions must use active voice and confident, present-tense assertions
- Include numbers, percentages, or timeframes wherever the source contains them

AVOID:
- Passive voice ("is being", "was implemented")
- Speculative language (might, could, possibly, maybe, perhaps)
- Generic statements without supporting detail

Return as JSON array of objects with "title", "description", "category", and "why_it_matters" keys.

Content:
{context_text}

Key Highlights (JSON):"""

        result = self._extract_with_llm_v2('key_highlights', prompt, max_tokens=2000, temperature=0.4)
        return self._parse_json_safe(result, [])

    def _extract_feature_articles(self, chunks: List[Dict], context: str) -> List[Dict]:
        """Pass 3: Feature Articles with deep-dive focus and narrative arc"""
        # Focus on middle chunks for technical depth
        middle_chunks = [c for c in chunks if c['position'] == 'middle'][:4]
        if len(middle_chunks) < 2:
            middle_chunks = chunks[:4]

        chunk_text = "\n\n".join([c['text'] for c in middle_chunks])
        context_text = chunk_text[:10000] if len(chunk_text) > 10000 else chunk_text

        prompt = f"""Based on the following content, write 2-4 deep-dive feature articles with a compelling narrative arc.

Each article must follow this structure (Problem → Solution → Impact):
- title: Bold, specific headline that states the core finding (not just the topic)
- hook: 1-2 powerful opening sentences that grab attention and state the stakes immediately
- context: 2-3 sentences framing the problem or opportunity with business urgency and specific examples
- key_ideas: 3-4 sentences on the technical solution or approach. Name specific tools, architectures, or methodologies. Be precise.
- benefits: 2-3 sentences with quantified business outcomes (use numbers from the source). Describe who benefits and how.
- what_this_means: 2 sentences bridging technical detail to business value. Format: "For [audience], this means [specific outcome]."
- best_practices: 3-5 specific, actionable best practices. Each starts with a strong verb.
- call_to_action: 1 bold recommendation with a specific timeline (e.g. "30 days", "this quarter", "Q2").

REQUIREMENTS:
- Each article must deliver UNIQUE insights — no overlap between articles
- Use active voice and assertive, analytical language throughout
- Ground every claim in content from the source material
- No hedging, no passive voice, no speculative language

Return as JSON array of objects.

Content:
{context_text}

Feature Articles (JSON):"""
        
        result = self._extract_with_llm_v2('feature_articles', prompt, max_tokens=3500, temperature=0.4)
        return self._parse_json_safe(result, [])
    
    def _extract_quick_bites(self, chunks: List[Dict], context: str) -> List[str]:
        """Pass 4: Quick Bites"""
        chunk_text = "\n\n".join([c['text'] for c in chunks])
        context_text = chunk_text[:6000] if len(chunk_text) > 6000 else chunk_text
        
        prompt = f"""Based on the following content, list 3-5 short updates, tips, or minor announcements (1-2 sentences each).

Use assertive language and be specific.

Content:
{context_text}

Quick Bites:"""
        
        result = self._extract_with_llm_v2('quick_bites', prompt, max_tokens=800, temperature=0.4)
        return self._parse_list(result)
    
    def _extract_action_items(self, chunks: List[Dict], context: str) -> Dict:
        """Pass 4: Action Items"""
        chunk_text = "\n\n".join([c['text'] for c in chunks])
        context_text = chunk_text[:6000] if len(chunk_text) > 6000 else chunk_text
        
        prompt = f"""Based on the following content, identify concrete action items for:
- engineering_teams: Specific actions for developers and engineers
- architecture_teams: Specific actions for architects and strategy teams
- leadership: Specific actions for decision makers and leadership

Return as JSON object with these three keys, each containing an array of action items.

Content:
{context_text}

Action Items (JSON):"""
        
        result = self._extract_with_llm_v2('action_items', prompt, max_tokens=1000, temperature=0.4)
        return self._parse_json_safe(result, {})
    
    def _extract_technologies(self, chunks: List[Dict], context: str) -> List[str]:
        """Pass 4: Technologies"""
        chunk_text = "\n\n".join([c['text'] for c in chunks])
        context_text = chunk_text[:6000] if len(chunk_text) > 6000 else chunk_text
        
        prompt = f"""Based on the following content, list all technologies, tools, platforms, and services mentioned.

Return as JSON array of strings.

Content:
{context_text}

Technologies (JSON):"""
        
        result = self._extract_with_llm_v2('technologies', prompt, max_tokens=500, temperature=0.3)
        return self._parse_json_safe(result, [])
    
    def _extract_architectures(self, chunks: List[Dict], context: str) -> List[Dict]:
        """Pass 4: Architectures"""
        chunk_text = "\n\n".join([c['text'] for c in chunks])
        context_text = chunk_text[:6000] if len(chunk_text) > 6000 else chunk_text
        
        prompt = f"""Based on the following content, identify key architectures or design patterns. For each, provide:
- name: Architecture or pattern name
- description: Brief description
- components: Key components or services
- use_case: When to use this

Return as JSON array of objects.

Content:
{context_text}

Architectures (JSON):"""
        
        result = self._extract_with_llm_v2('architectures', prompt, max_tokens=1200, temperature=0.4)
        return self._parse_json_safe(result, [])
    
    def _extract_best_practices(self, chunks: List[Dict], context: str) -> List[str]:
        """Pass 4: Best Practices"""
        chunk_text = "\n\n".join([c['text'] for c in chunks])
        context_text = chunk_text[:6000] if len(chunk_text) > 6000 else chunk_text
        
        prompt = f"""Based on the following content, list 4-6 best practices or recommendations mentioned.

Be specific and actionable.

Content:
{context_text}

Best Practices:"""
        
        result = self._extract_with_llm_v2('best_practices', prompt, max_tokens=800, temperature=0.4)
        return self._parse_list(result)
    
    def _extract_diagrams(self, chunks: List[Dict], context: str) -> List[Dict]:
        """Pass 4: Diagram Suggestions"""
        chunk_text = "\n\n".join([c['text'] for c in chunks])
        context_text = chunk_text[:6000] if len(chunk_text) > 6000 else chunk_text
        
        prompt = f"""Based on the following content, suggest 3-4 technical diagrams that would help explain the content. For each:
- type: "architecture" | "workflow" | "integration" | "security"
- title: Diagram title
- purpose: What it explains and who it's for
- elements: List of key components/nodes
- description: How to recreate it

Return as JSON array of objects.

Content:
{context_text}

Diagrams (JSON):"""
        
        result = self._extract_with_llm_v2('diagrams', prompt, max_tokens=1200, temperature=0.4)
        return self._parse_json_safe(result, [])
    
    def _extract_strategic_insights(self, context: str) -> Dict:
        """Pass 5: Strategic Insights"""
        prompt = f"""Analyze the following content for strategic framing. Extract:
- business_impact: 2-3 sentences on how this directly impacts business outcomes (revenue, cost, efficiency, time-to-market). Be specific — name the mechanism, not just the outcome.
- risk_factors: 2-3 sentences identifying the most material risks or challenges. State the consequence of inaction.
- strategic_opportunities: 2-3 sentences on the most actionable opportunities for growth or competitive advantage. Be specific about the window of opportunity.
- key_metrics: A list of specific KPIs, percentages, or quantitative measures mentioned in the content. If none are explicit, derive reasonable proxy metrics.

TONE: Authoritative, analytical. No hedging. Active voice.

Return as JSON object with these four keys.

Content:
{context[:8000]}

Strategic Insights (JSON):"""

        result = self._extract_with_llm_v2('strategic_insights', prompt, max_tokens=1000, temperature=0.4)
        return self._parse_json_safe(result, {})

    def _extract_narrative_intro(self, executive_summary: str, strategic_insights: Dict) -> str:
        """Pass 6: Generate a compelling narrative hook for the newsletter opening"""
        business_impact = strategic_insights.get('business_impact', '') if strategic_insights else ''
        opportunities = strategic_insights.get('strategic_opportunities', '') if strategic_insights else ''

        prompt = f"""Write a compelling 2-3 sentence opening hook for an enterprise technology newsletter.

EXECUTIVE SUMMARY:
{executive_summary[:1500]}

BUSINESS IMPACT:
{business_impact}

STRATEGIC OPPORTUNITIES:
{opportunities}

REQUIREMENTS:
- Start with a bold, provocative statement about the current state of enterprise technology — NOT "This newsletter covers..."
- Immediately frame the reader's challenge or opportunity
- End by asserting why THIS edition's content is essential reading right now
- Confident, authoritative tone. Present tense. Active voice. No hedging.

Newsletter Opening Hook (plain text):"""

        return self._extract_with_llm_v2('narrative_intro', prompt, max_tokens=200, temperature=0.5)

    def _extract_industry_perspective(self, context: str, technologies: List[str],
                                      strategic_insights: Dict) -> Dict:
        """Pass 7: Industry Perspective — thought leadership section"""
        tech_list = ', '.join(technologies[:10]) if technologies else 'various technologies'
        business_impact = strategic_insights.get('business_impact', '') if strategic_insights else ''
        opportunities = strategic_insights.get('strategic_opportunities', '') if strategic_insights else ''

        prompt = f"""Based on the following content and context, write an authoritative "Industry Perspective" section for an enterprise technology newsletter.

CONTENT SUMMARY:
{context[:3000]}

TECHNOLOGIES DISCUSSED: {tech_list}
BUSINESS IMPACT CONTEXT: {business_impact}
STRATEGIC OPPORTUNITIES: {opportunities}

Return a JSON object with these exact keys:
- headline: A bold, declarative 8-12 word headline stating a clear industry position (NOT a question, NOT vague)
- perspective: 3-4 sentences of expert analysis that place these developments in the broader industry macro-trend. Name the trend. Be opinionated.
- bold_prediction: 1-2 sentences stating a confident, specific prediction about where this is heading in the next 12-18 months. No hedging.
- recommendation: 1 clear, actionable recommendation for enterprise decision-makers. Start with a strong imperative verb (e.g. "Mandate", "Establish", "Accelerate").

TONE: Senior analyst / industry thought leader. Authoritative. Opinionated. Active voice. No hedging.

Industry Perspective (JSON):"""

        result = self._extract_with_llm_v2('industry_perspective', prompt, max_tokens=700, temperature=0.5)
        return self._parse_json_safe(result, {})
    
    def _extract_with_llm_v2(self, category: str, prompt: str, max_tokens: int = 2000, temperature: float = 0.4) -> str:
        """Extract using LLM with enhanced system prompt and configurable parameters"""
        if not self.llm_available:
            return ""
        
        system_prompt = """You are a senior executive technology analyst and strategic content writer.

WRITING STYLE:
- Assertive and analytical (not passive or speculative)
- Lead with impact and "so what?"
- Use specific data points and concrete examples
- Executive-grade prose with authority

AVOID:
- Speculative language (might, could, possibly, maybe)
- Vague generalities
- Repetitive content
- Safe/passive voice"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=60
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"\n    Error in {category}: {e}")
            return ""
    
    def _extract_with_llm(self, category: str, prompt: str) -> str:
        """Extract using LLM (legacy method for compatibility)"""
        if not self.llm_available:
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert enterprise technology analyst and technical writer. Extract only factual information from the content provided."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                timeout=60
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"\n    Error in {category}: {e}")
            return ""
    
    def _parse_json_safe(self, text: str, default):
        """Safely parse JSON from LLM response with enhanced handling"""
        if isinstance(text, (list, dict)):
            return text
        
        if not text or not isinstance(text, str):
            return default
        
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                # Try to find JSON array or object
                json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
                if json_match:
                    text = json_match.group(1)
            
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"\n    ⚠ JSON parse error: {e}")
            return default
        except Exception as e:
            print(f"\n    ⚠ Unexpected error in JSON parsing: {e}")
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