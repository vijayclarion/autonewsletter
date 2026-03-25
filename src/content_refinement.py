#!/usr/bin/env python3
"""
Content Refinement & Technical Accuracy Review Module
Implements Step 3 and Step 4 of the newsletter generation pipeline:
- Step 3: Refinement & Polish (professional tone, proper formatting)
- Step 4: Technical Accuracy Review (verify against source content)
- Step 5 (new): Narrative Quality Validation (story flow, tone, engagement)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class RefinementResult:
    """Container for refinement results"""
    original_text: str
    refined_text: str
    changes_made: List[str] = field(default_factory=list)
    tone_improved: bool = False
    formatting_improved: bool = False


@dataclass
class TechnicalAccuracyReview:
    """Container for technical accuracy review results"""
    is_accurate: bool = True
    issues_found: List[Dict] = field(default_factory=list)
    speculative_content: List[str] = field(default_factory=list)
    terminology_issues: List[Dict] = field(default_factory=list)
    confidence_score: float = 0.95  # 0.0-1.0
    recommendations: List[str] = field(default_factory=list)


class ContentRefiner:
    """Refine extracted content for professional tone and formatting"""
    
    def __init__(self):
        """Initialize content refiner"""
        self.professional_replacements = {
            r'\bwanna\b': 'want to',
            r'\bgotta\b': 'have to',
            r'\bkinda\b': 'somewhat',
            r'\bsorta\b': 'somewhat',
            r'\bguy[s]?\b': 'team member',
            r'\bstuff\b': 'items',
            r'\bthing[s]?\b': 'components',
            r'\blots?\s+of\b': 'many',
            r'\ba\s+lot\b': 'significantly',
            r'\blike\b': 'such as',  # When used as filler
            r'\byou\s+know\b': '',  # Remove filler phrase
            r'\bI\s+mean\b': '',  # Remove filler phrase
            r'\bbasically\b': '',  # Remove filler phrase
            r'\bactually\b': '',  # Remove filler phrase
        }
        
        self.tone_patterns = {
            'casual': [
                r'\blol\b', r'\bhaha\b', r'\byeah\b', r'\byup\b',
                r'\bnope\b', r'\bkinda\b', r'\bsorta\b'
            ],
            'uncertain': [
                r'\bI\s+think\b', r'\bmaybe\b', r'\bprobably\b',
                r'\bI\s+guess\b', r'\bsomewhat\b'
            ],
            'verbose': [
                r'\b(very|really|quite|extremely)\s+', r'\b(so|such)\s+'
            ]
        }
    
    def refine_executive_summary(self, text: str) -> RefinementResult:
        """
        Refine executive summary for professional tone
        
        Args:
            text: Original executive summary
        
        Returns:
            RefinementResult with refined text and changes made
        """
        refined = text
        changes = []
        
        # Ensure proper capitalization and sentence structure
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', refined) if s.strip()]
        refined_sentences = []
        
        for sentence in sentences:
            # Remove casual language
            refined_sent = self._remove_casual_language(sentence)
            
            # Ensure proper capitalization
            if refined_sent:
                refined_sent = refined_sent[0].upper() + refined_sent[1:]
            
            # Remove trailing filler words
            refined_sent = re.sub(r'\s+(you\s+know|I\s+mean|basically|actually)\s*[.!?]?$', '.', refined_sent)
            
            if refined_sent != sentence:
                changes.append(f"Refined: '{sentence[:50]}...' → '{refined_sent[:50]}...'")
            
            refined_sentences.append(refined_sent)
        
        refined = ' '.join(refined_sentences)
        
        # Ensure proper paragraph structure
        refined = re.sub(r'\n\n+', '\n\n', refined)
        
        return RefinementResult(
            original_text=text,
            refined_text=refined,
            changes_made=changes,
            tone_improved=len(changes) > 0,
            formatting_improved=True
        )
    
    def refine_highlights(self, highlights: List[Dict]) -> List[Dict]:
        """
        Refine highlights for professional presentation
        
        Args:
            highlights: List of highlight dictionaries
        
        Returns:
            Refined highlights list
        """
        refined_highlights = []
        
        for highlight in highlights:
            refined = {
                'title': self._refine_title(highlight.get('title', '')),
                'description': self._refine_description(highlight.get('description', ''))
            }
            refined_highlights.append(refined)
        
        return refined_highlights
    
    def refine_feature_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Refine feature articles for professional presentation
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Refined articles list
        """
        refined_articles = []
        
        for article in articles:
            # Handle key_ideas which might be a list
            key_ideas = article.get('key_ideas', '')
            if isinstance(key_ideas, list):
                key_ideas = ' '.join([str(item) for item in key_ideas])
            
            # Handle benefits which might be a list
            benefits = article.get('benefits', '')
            if isinstance(benefits, list):
                benefits = ' '.join([str(item) for item in benefits])
            
            # Handle best_practices which might be a list
            best_practices = article.get('best_practices', '')
            if isinstance(best_practices, list):
                best_practices = ' '.join([str(item) for item in best_practices])
            
            refined = {
                'title': self._refine_title(article.get('title', '')),
                'context': self._refine_description(article.get('context', '')),
                'key_ideas': self._refine_description(key_ideas),
                'benefits': self._refine_description(benefits),
                'best_practices': self._refine_description(best_practices),
                'call_to_action': self._refine_description(article.get('call_to_action', ''))
            }
            refined_articles.append(refined)
        
        return refined_articles
    
    def refine_action_items(self, action_items: Dict) -> Dict:
        """
        Refine action items for clarity and professionalism
        
        Args:
            action_items: Dictionary of action items by category
        
        Returns:
            Refined action items
        """
        refined = {}
        
        for category, items in action_items.items():
            if isinstance(items, list):
                refined[category] = [
                    self._refine_action_item(item) for item in items
                ]
            else:
                refined[category] = items
        
        return refined
    
    def _remove_casual_language(self, text: str) -> str:
        """Remove casual language from text"""
        for pattern, replacement in self.professional_replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _refine_title(self, title: str) -> str:
        """Refine title for proper formatting"""
        # Remove casual language
        title = self._remove_casual_language(title)
        
        # Title case (capitalize first letter of major words)
        words = title.split()
        refined_words = []
        
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']:
                refined_words.append(word.capitalize())
            else:
                refined_words.append(word.lower())
        
        return ' '.join(refined_words)
    
    def _refine_description(self, text: str) -> str:
        """Refine description for professional tone"""
        # Remove casual language
        text = self._remove_casual_language(text)
        
        # Remove filler phrases
        text = re.sub(r'\b(you\s+know|I\s+mean|basically|actually|like)\b', '', text, flags=re.IGNORECASE)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure proper ending punctuation
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    def _refine_action_item(self, item: str) -> str:
        """Refine action item for clarity"""
        # Ensure action items start with a verb
        item = self._remove_casual_language(item)
        
        # Don't add "Review and" prefix - use strong verbs directly
        if not re.match(r'^(Review|Implement|Evaluate|Plan|Schedule|Document|Analyze|Monitor|Test|Update|Develop|Establish|Define|Create|Deploy|Optimize)', item, flags=re.IGNORECASE):
            # Add appropriate verb based on content
            if 'tool' in item.lower() or 'solution' in item.lower():
                item = f"Evaluate {item[0].lower()}{item[1:]}"
            elif 'process' in item.lower():
                item = f"Establish {item[0].lower()}{item[1:]}"
            else:
                item = f"Implement {item[0].lower()}{item[1:]}"
        
        # Ensure proper ending punctuation
        if item and not item.endswith(('.', '!', '?')):
            item += '.'
        
        return item


class TechnicalAccuracyValidator:
    """Validate technical accuracy of extracted content against source"""
    
    def __init__(self):
        """Initialize validator"""
        self.client = OpenAI(api_key="api_key_placeholder") if OPENAI_AVAILABLE else None
        
        # Speculative indicators
        self.speculative_keywords = [
            'might', 'could', 'possibly', 'perhaps', 'probably',
            'likely', 'may', 'seems', 'appears', 'suggests',
            'apparently', 'supposedly', 'allegedly', 'rumor'
        ]
        
        # Technical terminology patterns
        self.technical_terms = {
            'monitoring': ['metrics', 'latency', 'throughput', 'uptime', 'availability'],
            'architecture': ['microservices', 'monolith', 'distributed', 'scalability', 'resilience'],
            'cloud': ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 'container'],
            'database': ['sql', 'nosql', 'relational', 'document', 'time-series'],
        }
    
    def validate_technical_accuracy(self, content: str, source_content: str) -> TechnicalAccuracyReview:
        """
        Validate technical accuracy of extracted content
        
        Args:
            content: Extracted content to validate
            source_content: Original source content
        
        Returns:
            TechnicalAccuracyReview with findings
        """
        review = TechnicalAccuracyReview()
        
        # Check for speculative content
        speculative = self._find_speculative_content(content)
        if speculative:
            review.speculative_content = speculative
            review.is_accurate = False
            review.issues_found.append({
                'type': 'speculative_content',
                'count': len(speculative),
                'severity': 'medium',
                'description': 'Content contains speculative or uncertain language'
            })
        
        # Check for terminology consistency
        terminology_issues = self._check_terminology_consistency(content, source_content)
        if terminology_issues:
            review.terminology_issues = terminology_issues
            review.is_accurate = False
            review.issues_found.append({
                'type': 'terminology_inconsistency',
                'count': len(terminology_issues),
                'severity': 'low',
                'description': 'Some technical terms may not match source exactly'
            })
        
        # Check for factual claims
        if self.client:
            factual_issues = self._validate_factual_claims(content, source_content)
            if factual_issues:
                review.is_accurate = False
                review.issues_found.extend(factual_issues)
        
        # Calculate confidence score
        review.confidence_score = max(0.5, 1.0 - (len(review.issues_found) * 0.1))
        
        # Generate recommendations
        review.recommendations = self._generate_recommendations(review)
        
        return review
    
    def _find_speculative_content(self, content: str) -> List[str]:
        """Find speculative language in content"""
        speculative = []
        
        for keyword in self.speculative_keywords:
            pattern = rf'\b{keyword}\b'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()
                
                speculative.append(context)
        
        return speculative[:10]  # Limit to 10 examples
    
    def _check_terminology_consistency(self, content: str, source_content: str) -> List[Dict]:
        """Check if technical terminology is used consistently"""
        issues = []
        
        # Extract technical terms from both
        content_terms = self._extract_technical_terms(content)
        source_terms = self._extract_technical_terms(source_content)
        
        # Check for terms in content that aren't in source
        for term in content_terms:
            if term.lower() not in [t.lower() for t in source_terms]:
                issues.append({
                    'term': term,
                    'type': 'not_in_source',
                    'severity': 'medium'
                })
        
        return issues[:5]  # Limit to 5 issues
    
    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from content"""
        terms = []
        
        for category, keywords in self.technical_terms.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    terms.append(keyword)
        
        return terms
    
    def _validate_factual_claims(self, content: str, source_content: str) -> List[Dict]:
        """Validate factual claims using LLM"""
        if not self.client:
            return []
        
        try:
            prompt = f"""Review the following extracted content and verify it matches the source material.
            
Extracted Content:
{content[:1000]}

Source Material:
{source_content[:1000]}

Identify any claims in the extracted content that:
1. Are not present in the source material
2. Contradict the source material
3. Are misrepresented or taken out of context

List each issue with:
- The claim
- Why it's problematic
- Severity (low/medium/high)

Be strict - only flag actual issues, not minor rewording."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical accuracy reviewer. Verify that extracted content matches source material exactly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                timeout=30
            )
            
            # Parse response for issues
            response_text = response.choices[0].message.content.strip()
            
            if 'no issues' in response_text.lower() or 'accurate' in response_text.lower():
                return []
            
            # Extract issues from response
            issues = []
            if response_text:
                issues.append({
                    'type': 'factual_validation',
                    'severity': 'medium',
                    'description': response_text[:200]
                })
            
            return issues
            
        except Exception as e:
            print(f"  ⚠ Factual validation failed: {e}")
            return []
    
    def _generate_recommendations(self, review: TechnicalAccuracyReview) -> List[str]:
        """Generate recommendations based on review findings"""
        recommendations = []
        
        if review.speculative_content:
            recommendations.append(
                "Remove or replace speculative language with definitive statements from source material"
            )
        
        if review.terminology_issues:
            recommendations.append(
                "Verify technical terminology matches source material exactly"
            )
        
        if review.confidence_score < 0.8:
            recommendations.append(
                "Conduct manual review of extracted content against source"
            )
        
        if not review.is_accurate:
            recommendations.append(
                "Flag content for editorial review before publication"
            )
        
        return recommendations


class StrategicContentEnhancer:
    """Enhance content with executive framing and impact-focus"""
    
    def enhance_executive_summary(self, summary: str, strategic_insights: Dict) -> str:
        """Add strategic framing to executive summary"""
        
        # Extract "So What?" insight
        business_impact = strategic_insights.get('business_impact', '') if strategic_insights else ''
        
        # Reframe opening if weak
        if summary.startswith("The content covers") or summary.startswith("This newsletter"):
            # Replace weak opening with strong impact statement
            summary = self._extract_core_value(summary)
        
        # Add "So What?" callout
        if business_impact:
            so_what_html = f'<div class="so-what">{business_impact}</div>'
            summary = summary + '\n\n' + so_what_html
        
        return summary
    
    def _extract_core_value(self, summary: str) -> str:
        """Extract core value from generic opening"""
        # Simple implementation - remove generic openings
        summary = re.sub(r'^(The content covers|This newsletter discusses|This document presents)\s+', '', summary, flags=re.IGNORECASE)
        # Capitalize first letter
        if summary:
            summary = summary[0].upper() + summary[1:]
        return summary
    
    def enhance_headline(self, title: str, description: str) -> str:
        """Convert generic headlines to impact-focused"""
        
        # Patterns to fix
        weak_patterns = {
            r'^Introduction [Oo]f (.+)': r'\1 Drives Performance Optimization',
            r'^Use [Oo]f (.+)': r'\1 Enables Strategic Decision-Making',
            r'^(.+) Implementation$': r'How \1 Transforms Operations'
        }
        
        for pattern, replacement in weak_patterns.items():
            title = re.sub(pattern, replacement, title)
        
        return title
    
    def remove_action_item_prefix(self, action_item: str) -> str:
        """Remove repetitive 'Review and' prefix"""
        
        # Remove "Review and" if it's added by refinement
        action_item = re.sub(r'^Review and ', '', action_item, flags=re.IGNORECASE)
        
        # Ensure starts with strong verb
        if not re.match(r'^(Implement|Develop|Establish|Define|Create|Deploy|Monitor|Analyze|Optimize|Evaluate)', action_item, flags=re.IGNORECASE):
            # Add appropriate verb based on content
            if 'tool' in action_item.lower() or 'solution' in action_item.lower():
                action_item = f"Evaluate and deploy {action_item[0].lower()}{action_item[1:]}"
            elif 'process' in action_item.lower():
                action_item = f"Establish {action_item[0].lower()}{action_item[1:]}"
            else:
                action_item = f"Implement {action_item[0].lower()}{action_item[1:]}"
        
        return action_item


class NarrativeQualityValidator:
    """
    Validate and improve the narrative quality of newsletter content.

    Checks for:
    - Weak or generic opening statements
    - Missing "why it matters" framing
    - Passive voice prevalence
    - Speculative language
    - Narrative arc completeness in feature articles
    - Section intro engagement
    """

    # Weak opener patterns
    _WEAK_OPENERS = [
        r'^(this\s+(document|content|newsletter|meeting|presentation|session))\s+(covers|discusses|presents|reviews|explores)',
        r'^(the\s+(following|content|document))\s+(covers|discusses|presents)',
        r'^(we\s+(discussed|talked|went\s+over|covered|looked\s+at))',
        r'^(there\s+(are|were|is|was)\s+several)',
        r'^(in\s+this\s+(section|newsletter|article|edition))',
    ]

    # Passive voice markers
    _PASSIVE_MARKERS = [
        r'\b(is|are|was|were)\s+\w+ed\b',
        r'\b(has|have|had)\s+been\s+\w+ed\b',
        r'\bwill\s+be\s+\w+ed\b',
    ]

    # Speculative terms
    _SPECULATIVE_TERMS = [
        'might', 'could', 'possibly', 'perhaps', 'probably', 'maybe',
        'likely', 'seems', 'appears', 'suggests', 'apparently', 'somewhat',
    ]

    # Required narrative arc fields for feature articles
    _NARRATIVE_ARC_FIELDS = ['hook', 'context', 'key_ideas', 'benefits', 'what_this_means']

    def validate_executive_summary(self, summary: str) -> Dict:
        """
        Validate the executive summary for narrative quality.

        Returns:
            Dict with 'score' (0-100), 'issues', and 'recommendations'
        """
        issues = []
        recommendations = []
        score = 100

        if not summary or len(summary) < 100:
            return {
                'score': 0,
                'issues': ['Executive summary is missing or too short'],
                'recommendations': ['Generate a 3-5 paragraph executive summary with business impact framing'],
            }

        # Check for weak opener
        for pattern in self._WEAK_OPENERS:
            if re.match(pattern, summary.strip(), re.IGNORECASE):
                issues.append("Opens with a weak, generic statement")
                recommendations.append(
                    "Replace opening sentence with a bold strategic assertion that leads with business impact"
                )
                score -= 20
                break

        # Check paragraph count
        paragraphs = [p.strip() for p in summary.split('\n\n') if len(p.strip()) > 30]
        if len(paragraphs) < 3:
            issues.append(f"Executive summary has only {len(paragraphs)} paragraph(s); aim for 3-5")
            recommendations.append("Expand to 3-5 paragraphs covering: business signal, problem, solution, impact, recommendation")
            score -= 15

        # Passive voice check
        passive_count = sum(len(re.findall(p, summary, re.IGNORECASE)) for p in self._PASSIVE_MARKERS)
        sentence_count = max(len(re.findall(r'[.!?]', summary)), 1)
        passive_ratio = passive_count / sentence_count
        if passive_ratio > 0.25:
            issues.append(f"High passive voice usage ({passive_ratio:.0%} of sentences)")
            recommendations.append("Rewrite passive constructions with active, assertive verbs")
            score -= 15

        # Speculative language check
        spec_count = sum(1 for w in self._SPECULATIVE_TERMS if re.search(rf'\b{w}\b', summary, re.IGNORECASE))
        if spec_count > 3:
            found_terms = [w for w in self._SPECULATIVE_TERMS if re.search(rf'\b{w}\b', summary, re.IGNORECASE)]
            issues.append(f"Contains {spec_count} speculative terms ({', '.join(found_terms[:3])}...)")
            recommendations.append("Replace speculative language with confident, factual assertions")
            score -= 10

        # Check for "why it matters" framing
        impact_signals = [r'\b(impact|revenue|cost|efficiency|competitive|risk|opportunity|savings|growth)\b']
        has_impact = any(re.search(p, summary, re.IGNORECASE) for p in impact_signals)
        if not has_impact:
            issues.append("Missing business impact framing")
            recommendations.append("Add explicit business impact language (revenue, cost, efficiency, risk, competitive advantage)")
            score -= 15

        return {
            'score': max(0, score),
            'issues': issues,
            'recommendations': recommendations,
            'paragraph_count': len(paragraphs),
            'passive_ratio': round(passive_ratio, 2),
            'speculative_count': spec_count,
        }

    def validate_feature_articles(self, articles: List[Dict]) -> Dict:
        """
        Validate feature articles for narrative arc completeness.

        Returns:
            Dict with per-article scores and overall recommendations
        """
        if not articles:
            return {'overall_score': 0, 'articles': [], 'issues': ['No feature articles found']}

        article_results = []
        total_score = 0

        for i, article in enumerate(articles):
            result = self._validate_single_article(article, index=i + 1)
            article_results.append(result)
            total_score += result['score']

        return {
            'overall_score': round(total_score / len(articles)),
            'articles': article_results,
            'issues': [r['issues'] for r in article_results if r['issues']],
        }

    def validate_highlights(self, highlights: List[Dict]) -> Dict:
        """
        Validate key highlights for depth and specificity.

        Returns:
            Dict with 'score', 'issues', 'recommendations'
        """
        if not highlights:
            return {'score': 0, 'issues': ['No highlights found'], 'recommendations': []}

        issues = []
        recommendations = []
        score = 100

        # Check for generic titles
        generic_titles = 0
        for h in highlights:
            title = h.get('title', '') if isinstance(h, dict) else str(h)
            # Titles shorter than 4 words or without action words are likely generic
            if len(title.split()) < 4:
                generic_titles += 1

        if generic_titles > len(highlights) * 0.5:
            issues.append(f"{generic_titles}/{len(highlights)} highlight titles are too short or generic")
            recommendations.append(
                "Rewrite titles as impact statements that include the specific outcome "
                "(e.g. 'AI Review Cuts Defect Escape Rate by 30%' not 'AI Review')"
            )
            score -= 25

        # Check for 'why_it_matters' field
        has_why = sum(1 for h in highlights if isinstance(h, dict) and h.get('why_it_matters'))
        if has_why == 0:
            issues.append("Highlights are missing 'why it matters' context")
            recommendations.append("Add a 'why_it_matters' sentence to each highlight")
            score -= 15

        return {
            'score': max(0, score),
            'count': len(highlights),
            'issues': issues,
            'recommendations': recommendations,
        }

    def generate_section_intros(self, knowledge) -> Dict[str, str]:
        """
        Generate compelling introductory sentences for each newsletter section.

        Args:
            knowledge: ExtractedKnowledge object

        Returns:
            Dict mapping section name to intro text
        """
        intros = {}

        # Highlights intro
        if knowledge.key_highlights:
            count = len(knowledge.key_highlights)
            categories = set()
            for h in knowledge.key_highlights:
                if isinstance(h, dict):
                    categories.add(h.get('category', ''))
            cat_text = f" spanning {', '.join(c for c in categories if c)}" if categories else ""
            intros['highlights'] = (
                f"{count} strategic developments{cat_text} demand immediate attention "
                f"from engineering, architecture, and leadership teams."
            )

        # Feature articles intro
        if knowledge.feature_articles:
            titles = [a.get('title', '') for a in knowledge.feature_articles if isinstance(a, dict)][:2]
            if titles:
                intros['features'] = (
                    f"The following deep-dive analyses — including '{titles[0]}' "
                    f"— translate technical complexity into clear business impact and actionable guidance."
                )
            else:
                intros['features'] = (
                    "These deep-dive analyses examine the most consequential technical developments, "
                    "providing the strategic context and recommended actions decision-makers need."
                )

        # Quick bites intro
        if knowledge.quick_bites:
            intros['quick_bites'] = (
                "Beyond the headline stories, these rapid intelligence updates flag "
                "emerging signals that deserve a place on your strategic radar."
            )

        # Action items intro
        if knowledge.action_items:
            total_items = sum(
                len(v) for v in knowledge.action_items.values() if isinstance(v, list)
            )
            intros['action_items'] = (
                f"Strategy without execution is noise. "
                f"The following {total_items} prioritized actions are segmented by role "
                f"for immediate implementation."
            )

        return intros

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_single_article(self, article: Dict, index: int) -> Dict:
        """Validate a single feature article"""
        issues = []
        score = 100
        title = article.get('title', f'Article {index}')

        # Check for narrative arc completeness
        missing_fields = [f for f in self._NARRATIVE_ARC_FIELDS if not article.get(f)]
        if missing_fields:
            issues.append(f"Missing narrative arc fields: {', '.join(missing_fields)}")
            score -= len(missing_fields) * 10

        # Check hook quality
        hook = article.get('hook', '')
        if hook:
            for pattern in self._WEAK_OPENERS:
                if re.match(pattern, hook.strip(), re.IGNORECASE):
                    issues.append("Hook opens with a weak generic statement")
                    score -= 15
                    break

        # Check 'what_this_means' exists
        if not article.get('what_this_means'):
            issues.append("Missing 'What This Means' business-to-technical bridge")
            score -= 15

        # Check call to action
        cta = article.get('call_to_action', '')
        if not cta or len(cta) < 20:
            issues.append("Call to action is missing or too vague")
            score -= 10

        return {
            'title': title,
            'score': max(0, score),
            'issues': issues,
        }


class NewsletterContentProcessor:
    """Process newsletter content through refinement, accuracy review, and narrative validation"""

    def __init__(self):
        """Initialize processor"""
        self.refiner = ContentRefiner()
        self.validator = TechnicalAccuracyValidator()
        self.enhancer = StrategicContentEnhancer()
        self.narrative_validator = NarrativeQualityValidator()

    def process_content(self, knowledge, source_content: str, verbose: bool = True) -> Dict:
        """
        Process extracted knowledge through refinement, accuracy review, and narrative validation.

        Args:
            knowledge: ExtractedKnowledge object
            source_content: Original source content for validation
            verbose: Whether to print processing details

        Returns:
            Dictionary with processed content and review results
        """
        results = {
            'refinement_results': {},
            'accuracy_review': None,
            'narrative_validation': {},
            'section_intros': {},
            'processed_knowledge': knowledge,
            'issues': [],
            'warnings': []
        }

        if verbose:
            print("\n📝 Step 3: Refinement & Polish")
            print("-" * 70)

        # Refine executive summary
        if knowledge.executive_summary:
            summary_result = self.refiner.refine_executive_summary(knowledge.executive_summary)
            knowledge.executive_summary = summary_result.refined_text
            results['refinement_results']['executive_summary'] = summary_result

            if verbose and summary_result.changes_made:
                print(f"  ✓ Executive Summary: {len(summary_result.changes_made)} refinements")

        # Refine highlights
        if knowledge.key_highlights:
            knowledge.key_highlights = self.refiner.refine_highlights(knowledge.key_highlights)
            if verbose:
                print(f"  ✓ Key Highlights: Refined {len(knowledge.key_highlights)} items")

        # Refine feature articles
        if knowledge.feature_articles:
            knowledge.feature_articles = self.refiner.refine_feature_articles(knowledge.feature_articles)
            if verbose:
                print(f"  ✓ Feature Articles: Refined {len(knowledge.feature_articles)} articles")

        # Refine action items
        if knowledge.action_items:
            knowledge.action_items = self.refiner.refine_action_items(knowledge.action_items)
            if verbose:
                print(f"  ✓ Action Items: Refined {len(knowledge.action_items)} categories")

        if verbose:
            print("\n🔍 Step 4: Technical Accuracy Review")
            print("-" * 70)

        # Validate technical accuracy
        combined_content = f"{knowledge.executive_summary}\n\n"
        combined_content += "\n".join([
            h.get('description', '') if isinstance(h, dict) else str(h)
            for h in knowledge.key_highlights
        ])

        accuracy_review = self.validator.validate_technical_accuracy(combined_content, source_content)
        results['accuracy_review'] = accuracy_review

        if verbose:
            print(f"  Confidence Score: {accuracy_review.confidence_score:.1%}")
            print(f"  Is Accurate: {'✓ Yes' if accuracy_review.is_accurate else '✗ No'}")

            if accuracy_review.issues_found:
                print(f"\n  ⚠ Issues Found: {len(accuracy_review.issues_found)}")
                for issue in accuracy_review.issues_found:
                    print(f"    - {issue['type']}: {issue['description']}")
                results['issues'] = accuracy_review.issues_found

            if accuracy_review.recommendations:
                print(f"\n  💡 Recommendations:")
                for rec in accuracy_review.recommendations:
                    print(f"    - {rec}")
                results['warnings'] = accuracy_review.recommendations

        # ----------------------------------------------------------------
        # Step 5 (NEW): Narrative Quality Validation
        # ----------------------------------------------------------------
        if verbose:
            print("\n✍️  Step 5: Narrative Quality Validation")
            print("-" * 70)

        summary_narrative = self.narrative_validator.validate_executive_summary(knowledge.executive_summary)
        articles_narrative = self.narrative_validator.validate_feature_articles(knowledge.feature_articles)
        highlights_narrative = self.narrative_validator.validate_highlights(knowledge.key_highlights)

        results['narrative_validation'] = {
            'executive_summary': summary_narrative,
            'feature_articles': articles_narrative,
            'highlights': highlights_narrative,
        }

        if verbose:
            print(f"  Executive Summary Score: {summary_narrative['score']}/100")
            print(f"  Feature Articles Score:  {articles_narrative.get('overall_score', 0)}/100")
            print(f"  Highlights Score:        {highlights_narrative['score']}/100")
            if summary_narrative.get('issues'):
                for issue in summary_narrative['issues']:
                    print(f"    ⚠ Summary: {issue}")
            if articles_narrative.get('issues'):
                print(f"    ⚠ Articles: {len(articles_narrative['issues'])} articles have narrative issues")

        # Generate section introductions
        section_intros = self.narrative_validator.generate_section_intros(knowledge)
        results['section_intros'] = section_intros
        # Attach to knowledge for use in template rendering
        knowledge.section_intros = section_intros  # type: ignore[attr-defined]

        if verbose and section_intros:
            print(f"  ✓ Section Intros: Generated for {len(section_intros)} section(s)")

        return results


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CONTENT REFINEMENT & TECHNICAL ACCURACY REVIEW MODULE")
    print("=" * 70)
    print("\n✓ Module initialized successfully!")
    print("  - ContentRefiner: Professional tone and formatting")
    print("  - TechnicalAccuracyValidator: Accuracy verification")
    print("  - NarrativeQualityValidator: Narrative quality and tone analysis")
    print("  - NewsletterContentProcessor: Full pipeline processing")
