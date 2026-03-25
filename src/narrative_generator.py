#!/usr/bin/env python3
"""
Narrative Generator Module
Adds storytelling enhancements to the newsletter generation pipeline:
- Story arc generation (problem → solution → impact)
- Section introductions and transition narratives
- Industry perspective / thought leadership
- Narrative quality scoring
- Tone analysis (confidence / authority)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class NarrativeScore:
    """Container for narrative quality scoring results"""
    overall_score: float = 0.0          # 0.0 - 1.0
    authority_score: float = 0.0        # Confidence / authority level
    depth_score: float = 0.0            # Content depth
    flow_score: float = 0.0             # Narrative flow
    engagement_score: float = 0.0       # Reader engagement hooks
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ToneAnalysis:
    """Container for tone analysis results"""
    dominant_tone: str = "neutral"      # confident / authoritative / neutral / passive
    authority_level: str = "medium"     # high / medium / low
    passive_voice_ratio: float = 0.0    # 0.0 - 1.0
    speculative_ratio: float = 0.0      # 0.0 - 1.0
    action_verb_density: float = 0.0    # Higher is better
    issues: List[str] = field(default_factory=list)


@dataclass
class StoryArc:
    """Container for a story arc structure"""
    hook: str = ""                      # Opening hook / attention grabber
    context: str = ""                   # Background and problem framing
    solution: str = ""                  # Solution / innovation narrative
    impact: str = ""                    # Business impact
    what_this_means: str = ""           # Bridge: technical → business value
    call_to_action: str = ""            # Clear, bold recommendation


class NarrativeGenerator:
    """
    Generate storytelling enhancements for newsletter content.

    Provides:
    - Compelling narrative arcs for feature articles
    - Section introductions that hook the reader
    - Transition narratives between topics
    - Industry perspective / thought leadership generation
    - Narrative quality scoring and tone analysis
    """

    # Scoring weights for narrative quality dimensions
    _WEIGHT_AUTHORITY: float = 0.35
    _WEIGHT_DEPTH: float = 0.25
    _WEIGHT_FLOW: float = 0.20
    _WEIGHT_ENGAGEMENT: float = 0.20

    # Weights used when computing authority_score from passive/speculative ratios
    _PASSIVE_VOICE_WEIGHT: float = 0.5
    _SPECULATIVE_WEIGHT: float = 0.5

    def __init__(self):
        """Initialize narrative generator with LLM support"""
        if OPENAI_AVAILABLE:
            try:
                import os
                api_key = os.environ.get('OPENAI_API_KEY', 'api_key_placeholder')
                self.client = OpenAI(api_key=api_key)
                self.llm_available = True
            except Exception:
                self.llm_available = False
        else:
            self.llm_available = False

        # Passive voice indicators
        self._passive_patterns = [
            r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\bhas been\b', r'\bhave been\b', r'\bhad been\b',
        ]

        # Speculative language
        self._speculative_words = [
            'might', 'could', 'possibly', 'perhaps', 'probably', 'maybe',
            'likely', 'seems', 'appears', 'suggests', 'apparently',
        ]

        # Strong action verbs that signal authority
        self._authority_verbs = [
            'drives', 'delivers', 'enables', 'accelerates', 'transforms',
            'mandates', 'requires', 'demands', 'achieves', 'establishes',
            'defines', 'leads', 'powers', 'builds', 'creates', 'generates',
            'produces', 'reduces', 'increases', 'eliminates', 'replaces',
        ]

        # Weak / hedging openers
        self._weak_openers = [
            r'^(this|the)\s+(content|document|newsletter|meeting|presentation)\s+(covers|discusses|presents|reviews)',
            r'^(we|the team)\s+(discussed|talked about|went over)',
            r'^(there (are|were|is|was))',
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_story_arc(self, article: Dict, context: str = "") -> StoryArc:
        """
        Convert a feature article dict into a compelling story arc.

        Args:
            article: Feature article dictionary from RAG engine
            context: Optional broader document context

        Returns:
            StoryArc with structured narrative elements
        """
        if self.llm_available:
            return self._generate_story_arc_llm(article, context)
        return self._generate_story_arc_rules(article)

    def generate_newsletter_hook(self, executive_summary: str, strategic_insights: Dict) -> str:
        """
        Generate a compelling opening hook for the whole newsletter.

        Args:
            executive_summary: Current executive summary text
            strategic_insights: Strategic insights dict from RAG engine

        Returns:
            Short, punchy hook paragraph (2-3 sentences)
        """
        if self.llm_available:
            return self._generate_hook_llm(executive_summary, strategic_insights)
        return self._generate_hook_rules(executive_summary, strategic_insights)

    def generate_section_intro(self, section_type: str, content_preview: str) -> str:
        """
        Generate a reader-engaging introduction for a newsletter section.

        Args:
            section_type: One of 'highlights', 'features', 'quick_bites',
                          'action_items', 'industry_perspective'
            content_preview: A brief preview of section content

        Returns:
            Engaging section introduction (1-2 sentences)
        """
        if self.llm_available:
            return self._generate_section_intro_llm(section_type, content_preview)
        return self._generate_section_intro_rules(section_type)

    def generate_transition(self, from_section: str, to_section: str,
                            context: str = "") -> str:
        """
        Generate a smooth narrative transition between two sections.

        Args:
            from_section: Name of the previous section
            to_section: Name of the next section
            context: Optional content context

        Returns:
            Transition sentence or short paragraph
        """
        transitions = {
            ('highlights', 'features'): (
                "These strategic developments demand deeper examination. "
                "The following deep-dive analyses unpack the mechanics, business implications, "
                "and recommended paths forward for each area."
            ),
            ('features', 'quick_bites'): (
                "Beyond the headline stories, several additional developments "
                "deserve attention as leading indicators of broader industry trends."
            ),
            ('quick_bites', 'action_items'): (
                "Awareness without action yields no business value. "
                "Here is the prioritized agenda for teams across the organization."
            ),
            ('action_items', 'industry_perspective'): (
                "Context is everything. To sharpen these recommendations, "
                "it helps to understand where the industry as a whole is heading."
            ),
        }
        key = (from_section, to_section)
        return transitions.get(key, "")

    def generate_industry_perspective(self, content: str, technologies: List[str],
                                      strategic_insights: Dict) -> Dict:
        """
        Generate an 'Industry Perspective' thought-leadership section.

        Args:
            content: Source content (first 6000 chars)
            technologies: List of technologies extracted
            strategic_insights: Strategic insights from RAG engine

        Returns:
            Dict with 'headline', 'perspective', 'bold_prediction', 'recommendation'
        """
        if self.llm_available:
            return self._generate_industry_perspective_llm(content, technologies, strategic_insights)
        return self._generate_industry_perspective_rules(technologies, strategic_insights)

    def score_narrative(self, text: str) -> NarrativeScore:
        """
        Score the narrative quality of a text block.

        Args:
            text: Text to evaluate

        Returns:
            NarrativeScore with component scores and recommendations
        """
        score = NarrativeScore()

        # Authority score
        tone = self.analyze_tone(text)
        score.authority_score = 1.0 - (
            tone.passive_voice_ratio * self._PASSIVE_VOICE_WEIGHT
            + tone.speculative_ratio * self._SPECULATIVE_WEIGHT
        )

        # Depth score – measured by avg sentence length and specificity indicators
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        if sentences:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            # Ideal range 15-30 words per sentence
            depth = min(1.0, avg_len / 25.0) if avg_len < 25 else max(0.5, 1.0 - (avg_len - 30) / 50)
            score.depth_score = round(depth, 2)
        else:
            score.depth_score = 0.0

        # Flow score – penalize repetition of phrases
        words = text.lower().split()
        unique_ratio = len(set(words)) / max(len(words), 1)
        score.flow_score = round(min(1.0, unique_ratio * 2), 2)

        # Engagement score – presence of hook signals
        engagement_signals = [
            r'\b(critical|urgent|essential|strategic|game-changing|breakthrough)\b',
            r'\b(why this matters|what this means|bottom line|key insight)\b',
            r'\b(organizations that|companies that|teams that)\b',
        ]
        hits = sum(1 for p in engagement_signals if re.search(p, text, re.IGNORECASE))
        score.engagement_score = round(min(1.0, hits / 2), 2)

        # Overall weighted score
        score.overall_score = round(
            score.authority_score * self._WEIGHT_AUTHORITY
            + score.depth_score * self._WEIGHT_DEPTH
            + score.flow_score * self._WEIGHT_FLOW
            + score.engagement_score * self._WEIGHT_ENGAGEMENT,
            2,
        )

        # Issues and recommendations
        if score.authority_score < 0.6:
            score.issues.append("High passive/speculative language ratio")
            score.recommendations.append(
                "Replace passive constructions and hedging words with confident, active voice."
            )
        if score.depth_score < 0.5:
            score.issues.append("Sentences are too short or too long for optimal readability")
            score.recommendations.append(
                "Aim for 15–25 word sentences that balance detail with readability."
            )
        if score.engagement_score < 0.3:
            score.issues.append("Missing engagement hooks and 'why this matters' framing")
            score.recommendations.append(
                "Open each section with a reader hook; close with a 'What This Means' insight."
            )

        return score

    def analyze_tone(self, text: str) -> ToneAnalysis:
        """
        Analyse the tone of a text block for confidence and authority.

        Args:
            text: Text to analyse

        Returns:
            ToneAnalysis with tone metrics
        """
        analysis = ToneAnalysis()
        words = text.lower().split()
        total_words = max(len(words), 1)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
        total_sentences = max(len(sentences), 1)

        # Passive voice
        passive_count = sum(
            len(re.findall(p, text, re.IGNORECASE))
            for p in self._passive_patterns
        )
        analysis.passive_voice_ratio = round(min(1.0, passive_count / total_sentences), 2)

        # Speculative language
        speculative_count = sum(
            1 for w in self._speculative_words if re.search(rf'\b{w}\b', text, re.IGNORECASE)
        )
        analysis.speculative_ratio = round(min(1.0, speculative_count / 10), 2)

        # Action verb density
        authority_count = sum(
            1 for v in self._authority_verbs if re.search(rf'\b{v}s?\b', text, re.IGNORECASE)
        )
        analysis.action_verb_density = round(min(1.0, authority_count / max(total_sentences * 0.3, 1)), 2)

        # Weak opener check
        has_weak_opener = any(
            re.match(p, text.strip(), re.IGNORECASE) for p in self._weak_openers
        )
        if has_weak_opener:
            analysis.issues.append("Opens with a weak, generic statement")

        # Determine tone and authority level
        authority_index = (
            analysis.action_verb_density
            - analysis.passive_voice_ratio * 0.5
            - analysis.speculative_ratio * 0.5
        )
        if authority_index > 0.4:
            analysis.dominant_tone = "authoritative"
            analysis.authority_level = "high"
        elif authority_index > 0.1:
            analysis.dominant_tone = "confident"
            analysis.authority_level = "medium"
        else:
            analysis.dominant_tone = "passive"
            analysis.authority_level = "low"

        return analysis

    # ------------------------------------------------------------------
    # LLM-backed implementations
    # ------------------------------------------------------------------

    def _generate_story_arc_llm(self, article: Dict, context: str) -> StoryArc:
        """Generate story arc using LLM"""
        article_text = f"""Title: {article.get('title', '')}
Context: {article.get('context', '')}
Key Ideas: {article.get('key_ideas', '')}
Benefits: {article.get('benefits', '')}
Best Practices: {article.get('best_practices', '')}
Call to Action: {article.get('call_to_action', '')}"""

        prompt = f"""Transform the following article information into a compelling story arc.

ARTICLE:
{article_text}

BROADER CONTEXT:
{context[:1000] if context else 'Not provided'}

Return a JSON object with these exact keys:
- hook: A powerful 1-2 sentence opening that grabs attention (start with impact, not background)
- context: 2-3 sentences that frame the problem with business urgency
- solution: 2-3 sentences that explain the solution or innovation with specifics
- impact: 2-3 sentences on measurable business outcomes (use numbers where possible)
- what_this_means: 2 sentences bridging technical detail to business value (e.g. "For engineering teams, this means..."; "For leadership, this translates to...")
- call_to_action: 1 bold, specific recommendation starting with a strong verb

TONE: Authoritative, confident, analytical. No hedging. No passive voice.

Story Arc (JSON):"""

        result = self._call_llm(prompt, max_tokens=700, temperature=0.4)
        return self._parse_story_arc(result, article)

    def _generate_hook_llm(self, executive_summary: str, strategic_insights: Dict) -> str:
        """Generate newsletter opening hook using LLM"""
        business_impact = strategic_insights.get('business_impact', '') if strategic_insights else ''
        opportunities = strategic_insights.get('strategic_opportunities', '') if strategic_insights else ''

        prompt = f"""Write a compelling 2-3 sentence opening hook for a technology newsletter.

EXECUTIVE SUMMARY:
{executive_summary[:1500]}

BUSINESS IMPACT:
{business_impact}

STRATEGIC OPPORTUNITIES:
{opportunities}

REQUIREMENTS:
- Start with a bold statement of industry significance — NOT "This newsletter covers..."
- Frame the reader's challenge or opportunity immediately
- End with why THIS edition matters right now
- Confident, authoritative tone. Present tense. Active voice.

Opening Hook (plain text, no JSON):"""

        return self._call_llm(prompt, max_tokens=200, temperature=0.5)

    def _generate_section_intro_llm(self, section_type: str, content_preview: str) -> str:
        """Generate section introduction using LLM"""
        section_descriptions = {
            'highlights': "Key strategic highlights and emerging trends",
            'features': "In-depth feature articles providing deep-dive analysis",
            'quick_bites': "Rapid-fire intelligence updates and minor announcements",
            'action_items': "Prioritised action agenda for engineering, architecture, and leadership teams",
            'industry_perspective': "Expert thought leadership and bold industry predictions",
        }
        section_desc = section_descriptions.get(section_type, section_type)

        prompt = f"""Write a single 1-2 sentence introduction for the "{section_desc}" section of an enterprise technology newsletter.

CONTENT PREVIEW:
{content_preview[:400]}

REQUIREMENTS:
- Hook the reader with the value they will get from this section
- Confident, present-tense, active voice
- No generic filler phrases ("In this section we will..." / "The following...")
- Should feel like an expert editor wrote it

Section Introduction (plain text):"""

        return self._call_llm(prompt, max_tokens=100, temperature=0.5)

    def _generate_industry_perspective_llm(self, content: str, technologies: List[str],
                                           strategic_insights: Dict) -> Dict:
        """Generate industry perspective using LLM"""
        tech_list = ', '.join(technologies[:10]) if technologies else 'various technologies'
        business_impact = strategic_insights.get('business_impact', '') if strategic_insights else ''
        opportunities = strategic_insights.get('strategic_opportunities', '') if strategic_insights else ''

        prompt = f"""Based on the following content and context, write an authoritative "Industry Perspective" section for an enterprise technology newsletter.

CONTENT SUMMARY:
{content[:3000]}

TECHNOLOGIES DISCUSSED: {tech_list}
BUSINESS IMPACT CONTEXT: {business_impact}
STRATEGIC OPPORTUNITIES: {opportunities}

Return a JSON object with:
- headline: A bold, provocative 8-12 word headline stating a clear position (NOT a question)
- perspective: 3-4 sentences of expert analysis positioning these developments in the broader industry landscape. Name the macro trend. Be opinionated.
- bold_prediction: 1-2 sentences stating a confident, specific prediction about where this is heading in the next 12-18 months
- recommendation: 1 clear, actionable recommendation for enterprise decision-makers. Start with a strong verb.

TONE: Senior analyst / thought leader. Authoritative. Opinionated. No hedging.

Industry Perspective (JSON):"""

        result = self._call_llm(prompt, max_tokens=600, temperature=0.5)
        return self._parse_industry_perspective(result)

    # ------------------------------------------------------------------
    # Rule-based fallbacks (no LLM required)
    # ------------------------------------------------------------------

    def _generate_story_arc_rules(self, article: Dict) -> StoryArc:
        """Generate a minimal story arc from article fields without LLM"""
        title = article.get('title', 'Technology Development')
        context = article.get('context', '')
        key_ideas = article.get('key_ideas', '')
        benefits = article.get('benefits', '')
        best_practices = article.get('best_practices', '')
        cta = article.get('call_to_action', '')

        hook = (
            f"{title} is reshaping enterprise operations. "
            f"Organizations that act now will establish a durable competitive advantage."
        )

        return StoryArc(
            hook=hook,
            context=context or f"The business challenge around {title.lower()} has reached a critical inflection point.",
            solution=key_ideas or f"{title} provides a structured approach to resolving this challenge.",
            impact=benefits or "Early adopters report measurable gains in efficiency, quality, and time-to-market.",
            what_this_means=(
                f"For engineering teams, this means adopting {title.lower()} as a first-class practice. "
                f"For leadership, this translates to prioritizing investment in capability and tooling."
            ),
            call_to_action=cta or best_practices or f"Pilot {title.lower()} on a high-visibility workload within the next quarter.",
        )

    def _generate_hook_rules(self, executive_summary: str, strategic_insights: Dict) -> str:
        """Generate a hook without LLM"""
        opportunity = (
            strategic_insights.get('strategic_opportunities', '')
            if strategic_insights
            else ''
        )
        if opportunity:
            return (
                f"The enterprise technology landscape is undergoing fundamental change. "
                f"{opportunity[:200].rstrip('.')}. "
                f"This edition distills the key strategic signals your organization must act on now."
            )
        # Derive from executive summary
        first_sentence = re.split(r'[.!?]', executive_summary)[0].strip() if executive_summary else ''
        if first_sentence:
            return (
                f"{first_sentence}. "
                "This edition provides the strategic context, technical depth, and clear recommendations "
                "needed to respond with confidence."
            )
        return (
            "Enterprise technology is advancing faster than most organizations can adapt. "
            "This edition cuts through the noise to deliver the insights and actions that matter most."
        )

    def _generate_section_intro_rules(self, section_type: str) -> str:
        """Generate section intro without LLM"""
        intros = {
            'highlights': (
                "Six strategic developments are reshaping the enterprise technology agenda — "
                "each with direct implications for cost, speed, and competitive positioning."
            ),
            'features': (
                "The following deep-dive analyses examine the most consequential technology developments, "
                "translating technical complexity into clear business impact."
            ),
            'quick_bites': (
                "Beyond the headline stories, these rapid updates flag emerging signals "
                "that deserve a place on your radar."
            ),
            'action_items': (
                "Strategy without execution is noise. "
                "Here is the prioritized action agenda, segmented by role and urgency."
            ),
            'industry_perspective': (
                "Expert analysis positions today's developments within the broader macro-trend arc "
                "shaping enterprise technology over the next 18 months."
            ),
        }
        return intros.get(section_type, "")

    def _generate_industry_perspective_rules(self, technologies: List[str],
                                             strategic_insights: Dict) -> Dict:
        """Generate industry perspective without LLM"""
        tech_focus = technologies[0] if technologies else "enterprise technology"
        opportunities = (
            strategic_insights.get('strategic_opportunities', '')
            if strategic_insights
            else ''
        )
        return {
            'headline': f"{tech_focus.title()} Is No Longer Optional — It Is the New Baseline",
            'perspective': (
                f"The rapid adoption of {tech_focus} signals a structural shift in how enterprises "
                f"build, scale, and govern technology assets. Organizations that treated these capabilities "
                f"as optional are now facing a capability gap that compounds with every quarter of inaction. "
                f"{opportunities[:150] if opportunities else 'The window for differentiation is narrowing as best practices standardise across the industry.'}."
            ),
            'bold_prediction': (
                f"Within 18 months, {tech_focus} proficiency will be a mandatory hiring criterion "
                f"for senior engineering and architecture roles across all major enterprise sectors."
            ),
            'recommendation': (
                f"Establish a dedicated {tech_focus} Centre of Excellence within the next two quarters "
                f"to accelerate adoption, standardise tooling, and build internal expertise before "
                f"the market further tightens the talent supply."
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str, max_tokens: int = 500, temperature: float = 0.4) -> str:
        """Make an LLM call with the narrative storytelling system prompt"""
        system_prompt = (
            "You are a world-class enterprise technology journalist and strategic analyst. "
            "Your writing is authoritative, compelling, and narrative-driven. "
            "You always lead with business impact, use confident active voice, "
            "and never hedge with speculative language. "
            "Every sentence earns its place by adding insight, not just information."
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=60,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  ⚠ Narrative LLM call failed: {e}")
            return ""

    def _parse_story_arc(self, text: str, fallback_article: Dict) -> StoryArc:
        """Parse LLM output into a StoryArc, falling back gracefully"""
        import json
        try:
            json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    text = json_match.group(0)
            data = json.loads(text)
            return StoryArc(
                hook=data.get('hook', ''),
                context=data.get('context', ''),
                solution=data.get('solution', ''),
                impact=data.get('impact', ''),
                what_this_means=data.get('what_this_means', ''),
                call_to_action=data.get('call_to_action', ''),
            )
        except Exception:
            return self._generate_story_arc_rules(fallback_article)

    def _parse_industry_perspective(self, text: str) -> Dict:
        """Parse LLM output into industry perspective dict"""
        import json
        try:
            json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    text = json_match.group(0)
            return json.loads(text)
        except Exception:
            return {
                'headline': '',
                'perspective': text[:400] if text else '',
                'bold_prediction': '',
                'recommendation': '',
            }


if __name__ == "__main__":
    print("Narrative Generator loaded successfully!")
    gen = NarrativeGenerator()
    sample_article = {
        'title': 'AI-Powered Developer Tooling',
        'context': 'Engineering teams are spending 40% of their time on toil and repetitive tasks.',
        'key_ideas': 'LLM-assisted code generation and automated testing pipelines.',
        'benefits': 'Reduces time-to-production by 35% and defect escape rate by 20%.',
        'best_practices': 'Start with code review automation before expanding to generation.',
        'call_to_action': 'Pilot GitHub Copilot on two high-traffic repositories within 30 days.',
    }
    arc = gen.generate_story_arc(sample_article)
    print(f"\n  Hook: {arc.hook}")
    print(f"  What This Means: {arc.what_this_means}")
    score = gen.score_narrative(arc.hook + ' ' + arc.impact)
    print(f"\n  Narrative Score: {score.overall_score:.2f}")
    tone = gen.analyze_tone(arc.context)
    print(f"  Tone: {tone.dominant_tone} / Authority: {tone.authority_level}")
