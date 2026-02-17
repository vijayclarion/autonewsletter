#!/usr/bin/env python3
"""
Content Refinement & Technical Accuracy Review Module
Implements Step 3 and Step 4 of the newsletter generation pipeline:
- Step 3: Refinement & Polish (professional tone, proper formatting)
- Step 4: Technical Accuracy Review (verify against source content)
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


class NewsletterContentProcessor:
    """Process newsletter content through refinement and accuracy review"""
    
    def __init__(self):
        """Initialize processor"""
        self.refiner = ContentRefiner()
        self.validator = TechnicalAccuracyValidator()
        self.enhancer = StrategicContentEnhancer()  # NEW
    
    def process_content(self, knowledge, source_content: str, verbose: bool = True) -> Dict:
        """
        Process extracted knowledge through refinement and accuracy review
        
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
        combined_content += "\n".join([h.get('description', '') for h in knowledge.key_highlights])
        
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
        
        return results


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CONTENT REFINEMENT & TECHNICAL ACCURACY REVIEW MODULE")
    print("=" * 70)
    print("\n✓ Module initialized successfully!")
    print("  - ContentRefiner: Professional tone and formatting")
    print("  - TechnicalAccuracyValidator: Accuracy verification")
    print("  - NewsletterContentProcessor: Full pipeline processing")
