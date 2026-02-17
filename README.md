# Enterprise Newsletter Generator (Executive-Grade v2.0)

AI-powered system that transforms documents into executive-grade technology newsletters using advanced RAG techniques.

## Quick Start

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate.bat
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY="your-key-here"

# Generate newsletter
python src/main.py input/Tech-Office-AllHandsMeeting_Nov.vtt --output output/test
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide and usage examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture with Mermaid diagrams
- **[requirements.txt](requirements.txt)** - Python dependencies

## Key Features (v2.0)

✨ **Executive-Grade Quality**
- Business impact framing with strategic insights
- Assertive, analytical language (no passive voice)
- Concrete examples and data points

🎯 **Advanced RAG Engine**
- Recursive semantic chunking (1500 chars, 200 overlap)
- Business-impact re-ranking (business 2x technical)
- 5-pass extraction strategy (8K-10K context)

📊 **Enhanced Processing**
- Noise reduction for transcripts
- Speaker contribution analytics
- Multi-format support (VTT, DOCX, PPTX, PDF, TXT, MD)

📈 **Quality Improvements**
- Depth: 3K → 10K context
- Repetition: High → Eliminated
- Framing: Generic → Business/Risk/Opportunity
- Language: Passive → Assertive

## Output Formats

- **Markdown** (`.md`) - Plain text with formatting
- **HTML** (`.html`) - Microsoft-style template
- **JSON** (`.json`) - Structured data

## Example

```bash
python src/main.py input/Tech-Office-AllHandsMeeting_Nov.vtt input/Monitoring_Systems_Overview_and_Comparison_Nov.pptx --title "Nov Newsletter for Monitoring systems"
```

## Version

**Current**: 2.0 (Executive-Grade)  
**Model**: GPT-4o-mini  
**Release**: February 2026