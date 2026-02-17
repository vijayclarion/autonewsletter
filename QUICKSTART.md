# Quick Start Guide - Executive-Grade Newsletter System

## Prerequisites

1. **Python 3.8+** installed
2. **OpenAI API Key** with access to GPT-4o-mini

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"

# Windows (Command Prompt)
set OPENAI_API_KEY=your-api-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

Generate a newsletter from a single VTT transcript:

```bash
python src/main.py input/Tech-Office-AllHandsMeeting_Nov.vtt --output output/test
```

### Multiple Input Files

Combine multiple sources into one newsletter:

```bash
python src/main.py \
  input/meeting.vtt \
  input/presentation.pptx \
  input/document.docx \
  --title "Q1 Technology Newsletter" \
  --subtitle "Enterprise IT Update" \
  --output output/q1-newsletter
```

### Supported Input Formats

- **VTT** (`.vtt`): Video transcripts with speaker attribution
- **DOCX** (`.docx`): Word documents
- **PPTX** (`.pptx`): PowerPoint presentations
- **PDF** (`.pdf`): PDF documents
- **TXT** (`.txt`): Plain text files
- **MD** (`.md`): Markdown files

## What's New in Executive-Grade Version

### Enhanced RAG Engine

- **Recursive Chunking**: Preserves semantic boundaries (1500 chars, 200 overlap)
- **Smart Re-ranking**: Prioritizes business-impact content (business keywords 2x technical)
- **Multi-Pass Extraction**: 5 specialized passes for different content types
- **Strategic Insights**: Extracts business impact, risks, and opportunities

### Advanced Document Processing

- **Noise Reduction**: Filters `[MUSIC]`, `[APPLAUSE]`, filler words
- **Speaker Analytics**: Tracks contribution percentage per speaker
- **Enhanced Sections**: Maintains speaker attribution with timestamps

### Executive-Grade Content

- **Business Impact Framing**: Leads with "why it matters"
- **Assertive Language**: No passive or speculative terms
- **Strategic Categories**: Business Impact | Risk Factor | Strategic Opportunity
- **Concrete Examples**: Specific data points, not vague generalities

## Output Files

The system generates three output formats:

1. **Markdown** (`newsletter_*.md`): Plain text with formatting
2. **HTML** (`newsletter_*.html`): Styled with Microsoft template
3. **JSON** (`newsletter_*.json`): Structured data for integration

Plus optional:
- **Diagrams** (`diagrams/*.png`): Auto-generated technical diagrams
- **Documentation** (`diagrams_guide.md`): Diagram usage guide

## Example Output Structure

```markdown
# Technology Newsletter

**Enterprise IT Update**
*Generated: February 17, 2026*

## Executive Summary
[Business impact framing, risks, opportunities]

## Key Highlights / What's New
1. **Business Impact**: [Specific example with data]
2. **Risk Factor**: [Identified challenge]
3. **Strategic Opportunity**: [Growth potential]

## Feature Articles / Deep Dives
### [Article Title]
**Context**: [Problem with concrete example]
**Key Ideas**: [Detailed technical concepts]
**Benefits**: [Quantified benefits]
**Best Practices**: [Actionable recommendations]
**Call to Action**: [Specific next step with timeline]

## Quick Bites / Short Updates
- [Update 1]
- [Update 2]

## Action Items / Next Steps
### For Engineering Teams
- [Action item 1]

### For Architecture Teams
- [Action item 2]

### For Leadership
- [Action item 3]

## Technologies Mentioned
AWS, Kubernetes, Docker, PostgreSQL, Redis...

## Best Practices & Recommendations
- [Practice 1]
- [Practice 2]
```

## Quality Targets

The system aims for:

✅ **Depth**: Deep analysis (10K context) with specific examples  
✅ **No Repetition**: Multi-pass extraction eliminates duplicates  
✅ **Strategic Framing**: Business/Risk/Opportunity categorization  
✅ **Assertive Language**: Active voice, no speculation  
✅ **Executive-Grade**: Professional tone, actionable insights  

## Troubleshooting

### API Key Issues

If you see "OpenAI not available" warnings:

```bash
# Verify API key is set
echo $OPENAI_API_KEY  # Linux/Mac
echo %OPENAI_API_KEY%  # Windows CMD
```

### Import Errors

If modules are not found:

```bash
# Ensure you're in the project root
cd /path/to/autonewsletter

# Reinstall dependencies
pip install -r requirements.txt
```

### Speaker Stats Missing

For VTT files, ensure the format includes speaker tags:

```vtt
WEBVTT

00:00:01.000 --> 00:00:05.000
<v Speaker Name>This is the content</v>
```

## Advanced Usage

### Custom Templates

Edit `templates/microsoft_newsletter_template.html` to customize the HTML output styling.

### Adjusting Parameters

Edit `src/rag_engine.py` to tune:
- `chunk_size`: Default 1500 characters
- `chunk_overlap`: Default 200 characters
- `max_tokens`: Per extraction type (800-2500)
- `temperature`: 0.3-0.5 for different styles

### Re-ranking Weights

Modify business/technical keyword lists in `RAGEngine.__init__()`:
```python
self.business_keywords = ['impact', 'cost', 'revenue', ...]
self.technical_keywords = ['architecture', 'scalability', ...]
```

## Performance Tips

1. **Content Size**: Optimal input is 500-5000 words
2. **Multiple Files**: Combine related sources for better context
3. **VTT Quality**: Clean transcripts produce better results
4. **API Quota**: Monitor OpenAI usage for large batches

## Support

For detailed architecture and implementation details, see:
- `ARCHITECTURE.md`: System architecture with diagrams
- `README.md`: Project overview and setup

## Version

**Current Version**: 2.0 (Executive-Grade)  
**Release Date**: February 2026  
**Model**: GPT-4o-mini
