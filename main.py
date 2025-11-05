
"""
Main Gradio Web Interface for Vedic Astrology AI
RAG Engine + Optional Google Search Grounding
Niche-Based Specialized Astrology System
Optimized for local and Cloud Run deployment
"""

import os
import gradio as gr
from rich.console import Console

from config import PORT
from typing import Optional
from niche_instructions import NICHE_INSTRUCTIONS, NICHE_CHOICES

console = Console()

# Allow disabling RAG for local smoke tests
DISABLE_RAG = os.getenv("DISABLE_RAG", "false").lower() == "true"

# Lazy initialization for the RAG system
rag_system: Optional[object] = None

# Conversation history
conversation_history = []
current_chart_data = None


def analyze_chart(chart_data: str, question: str, selected_niche: str, use_google_search: bool = True) -> str:
    """
    Analyze birth chart using RAG Engine + optional Google Search + specialized niche instructions
    
    Args:
        chart_data: Birth chart information (D1, D9, D10)
        question: User's astrology question
        selected_niche: Specialized niche (Love, Career, Wealth, Health, Spiritual)
        use_google_search: If True, includes Google Search grounding
    
    Returns:
        Analysis result or error message
    """
    
    global current_chart_data, conversation_history, rag_system
    
    if not question.strip():
        return "⚠️ Please enter a question about your chart."
    
    if not chart_data.strip():
        return "⚠️ Please provide your birth chart data."
    
    current_chart_data = chart_data
    
    # Build COMPREHENSIVE prompt that guides RAG retrieval with niche-specific research areas
    # This multi-faceted approach helps RAG retrieve MORE relevant passages from classical texts
    
    # Niche-specific research guidance for better RAG retrieval
    niche_research_areas = {
        "Love & Relationships": """
**Primary Research Areas for LOVE/RELATIONSHIP Analysis:**
- 7th house, 7th lord placement, planets in 7th house
- Venus (natural marriage significator) - placement, strength, aspects
- Darakaraka planet characteristics and influence
- D9 Navamsa chart for marriage destiny and spouse nature
- Upapada Lagna for partner characteristics
- Relevant sign influences on physical appearance and personality
- Nakshatra influences on spouse appearance and temperament
- 8th house for intimacy and marital challenges
- Current/upcoming marriage dashas and timing
- Transit influences on relationships
- Planetary combinations affecting spouse (Saturn appearance, Venus beauty, etc.)
- Sign-based physical traits (Capricorn demeanor, Taurus stability, etc.)""",
        
        "Career & Professional": """
**Primary Research Areas for CAREER/PROFESSIONAL Analysis:**
- 10th house, 10th lord placement, planets in 10th
- D10 Dasamsa chart for professional destiny (MOST IMPORTANT)
- Sun placement (authority, government jobs)
- Mercury placement (communication, business, intellect)
- Saturn placement (discipline, service, routine work)
- Mars placement (technical fields, military, surgery)
- Professional significators and their strengths
- Career yogas (Rajayoga, Mahapurusha yogas)
- Current/upcoming career dashas
- Sign influences on career type and work style
- Entrepreneurship indicators (10th lord in 7th/11th, Mars+Mercury)
- Job stability vs frequent changes""",
        
        "Wealth & Finance": """
**Primary Research Areas for WEALTH/FINANCE Analysis:**
- 2nd house (accumulated wealth), 11th house (gains, income)
- Wealth yogas (Dhana yoga, Lakshmi yoga, Gajakesari yoga)
- Jupiter placement (natural wealth significator, fortune)
- Venus placement (luxury, comfort, material prosperity)
- 5th house (investments, speculation, stock market)
- 9th house (fortune, luck, windfall gains)
- Current/upcoming wealth-giving dashas
- Property and real estate indicators
- Business vs service income potential
- Inheritance possibilities (4th house, 8th house)
- Financial challenges and debt (6th house, 12th house)
- Best income sources for this chart""",
        
        "Health & Wellness": """
**Primary Research Areas for HEALTH/WELLNESS Analysis:**
- Ascendant and Ascendant lord (overall vitality and constitution)
- Sun (life force, vitality, energy levels)
- Moon (mental health, emotional well-being, mind)
- 6th house (diseases, immunity, acute illnesses)
- 8th house (chronic conditions, surgery, accidents)
- 12th house (hospitalization, hidden ailments, sleep)
- Planet-health correlations (Mars-inflammation, Saturn-chronic, Mercury-nervous)
- Current/upcoming health-affecting dashas
- Vulnerable body parts based on ascendant and afflicted houses
- Mental health indicators (Moon, Mercury, 4th house)
- Prevention and wellness practices
- Timing of health issues and recovery periods""",
        
        "Spiritual Purpose": """
**Primary Research Areas for SPIRITUAL/PURPOSE Analysis:**
- 9th house (dharma, higher knowledge, spiritual path)
- 12th house (moksha, liberation, meditation, isolation)
- Atmakaraka (soul significator planet - highest degree)
- Rahu-Ketu axis (karmic lessons, north/south node)
- Jupiter (spiritual wisdom, guru, higher learning)
- Ketu (past life wisdom, detachment, spirituality)
- Current incarnation purpose (Ascendant analysis)
- Spiritual yogas (Pravrajya yoga, Moksha combinations)
- Meditation and spiritual practice suitability
- Guru and teacher connections (9th lord)
- Life lessons and karmic patterns
- Spiritual awakening timing and indicators"""
    }
    
    research_area = niche_research_areas.get(selected_niche, "")
    
    full_prompt = f"""===== BIRTH CHART DATA =====
{chart_data}

===== USER QUESTION =====
{question}

===== COMPREHENSIVE ANALYSIS FRAMEWORK =====

This is a **{selected_niche}** astrology question.
Provide COMPREHENSIVE analysis by researching multiple aspects:

{research_area}

**Classical Text Research Instructions:**
Search for SPECIFIC descriptions of:
1. Planetary appearance and characteristics (e.g., "Saturn appearance", "Venus beauty traits")
2. Sign-based physical and personality traits (e.g., "Capricorn demeanor", "Cancer sensitivity")
3. House-specific results and interpretations
4. Yoga effects and planetary combinations
5. Dasha timing principles and period results
6. Nakshatra influences on nature and appearance
7. Divisional chart integration techniques (D9, D10 as relevant)

**Response Requirements:**
- Be SPECIFIC not generic (avoid "good" or "favorable" - give details!)
- Integrate D1 Rashi chart + relevant divisional charts
- Include real-world manifestations and practical examples
- Cite classical principles when strengthening your analysis
- Address the user's exact question directly
- Keep conversational and natural tone (not robotic)
- Stay within word limit while being comprehensive

Research widely across classical texts to gather rich context, then synthesize into focused insights."""
    
    try:
        # Local smoke test mode: skip GenAI
        if DISABLE_RAG:
            return (
                "CHART OVERVIEW\n"
                "Local smoke test mode is ON (DISABLE_RAG=true). The UI is running and inputs are captured.\n\n"
                "MAIN ANALYSIS\n"
                "RAG calls are disabled for this test. Set DISABLE_RAG=false and provide a valid API key to run full analysis.\n\n"
                "PRACTICAL GUIDANCE\n- Enter your chart and question, then re-run with RAG enabled."
            )

        # Create RAG system on first use (lazy import to avoid startup side-effects)
        if rag_system is None:
            console.print("[cyan]Initializing RAG system (lazy)...[/cyan]")
            from astrology_rag import VedicAstrologyRAG  # local import
            globals()['rag_system'] = VedicAstrologyRAG()
            console.print("[green]✓ RAG system ready![/green]")

        # Apply niche-specific system instruction temporarily
        original_instruction = rag_system.system_instruction
        niche_instruction = NICHE_INSTRUCTIONS.get(selected_niche, original_instruction)
        rag_system.system_instruction = niche_instruction
        
        # Set word limit based on niche (Health has 350, others 300 for conciseness)
        max_words = 350 if selected_niche == "Health & Wellness" else 300
        
        # Query RAG system with optional Google Search and word limit
        result = rag_system.query(full_prompt, use_google_search=use_google_search, max_words=max_words)
        
        # Restore original instruction
        rag_system.system_instruction = original_instruction
        
        if result['success']:
            # Save to conversation history
            conversation_history.append({
                'question': question,
                'answer': result['text'][:500]  # Save summary
            })
            
            # Add source attribution
            if result.get('used_google_search', False):
                source_text = "\n\n📚 **Sources:** Classical Vedic Texts (RAG Corpus) + Modern Astrological Knowledge (AI)"
            else:
                source_text = "\n\n📚 **Sources:** Classical Vedic Texts (RAG Corpus Only)"
            
            return result['text'] + source_text
        else:
            return f"❌ Error: {result['error']}"
            
    except Exception as e:
        return f"❌ Error analyzing chart: {str(e)}\n\nPlease try again in a moment."


# Create Gradio interface
with gr.Blocks(title="Vedic Astrology AI (RAG)", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("""
    # 🌟 Vedic Astrology AI (Niche-Based)
    
    Powered by RAG Engine + AI Knowledge + Specialized Expertise
    
    **Features:**
    - 📚 Classical Texts: BPHS, Phaladeepika, Brihat Jataka, Light on Life (RAG Corpus)
    - 🧠 AI Model: Gemini 2.5 Flash (Modern astrology, psychology, real-world examples)
    - 🎯 5 Specialized Niches: Love, Career, Wealth, Health, Spiritual
    - ✨ Smart Formatting: Natural language, no symbols, conversational tone
    - 📏 Word Limit: 400 words max (350 for Health) for focused insights
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Your Birth Chart")
            chart_input = gr.Textbox(
                label="Chart Data",
                placeholder="""Enter your complete birth chart:

RASHI CHART (D1):
Ascendant: Cancer
4th House: Mars
6th House: Sun, Moon (Exalted), Mercury (Exalted), Ketu
7th House: Venus in Capricorn
11th House: Jupiter (Retrograde), Saturn (Retrograde)
12th House: Rahu

NAVAMSA (D9):
[Enter D9 placements]

DASAMSA (D10):
[Enter D10 placements]""",
                lines=14
            )
            
            gr.Markdown("### ❓ Your Question")
            question_input = gr.Textbox(
                label="Question",
                placeholder="Examples:\n- When will I get married?\n- Best career for me?\n- Wealth potential?\n- Health concerns?\n- My life purpose?",
                lines=3
            )
            
            gr.Markdown("### 🎯 Choose Your Focus")
            niche_selector = gr.Radio(
                choices=NICHE_CHOICES,
                value="Love & Relationships",
                label="Astrology Niche",
                info="Select specialized area for tailored insights"
            )
            
            gr.Markdown("### 🌐 Knowledge Mode")
            use_google_search = gr.Checkbox(
                label="📖 Include Modern Context (Hybrid Mode)",
                value=True,
                info="Combines classical texts (RAG) with AI's trained knowledge of modern astrology"
            )
            
            submit_btn = gr.Button("🔮 Analyze Chart", variant="primary", size="lg")
        
        with gr.Column(scale=2):
            gr.Markdown("### 📝 AI Analysis")
            output = gr.Textbox(
                label="Detailed Analysis",
                lines=28,
                show_copy_button=True,
                interactive=False
            )
    
    # Connect button click to analysis function
    submit_btn.click(
        fn=analyze_chart,
        inputs=[chart_input, question_input, niche_selector, use_google_search],
        outputs=output
    )


if __name__ == "__main__":
    console.print("[bold cyan]🚀 Vedic Astrology AI (Niche-Based System)[/bold cyan]")
    console.print(f"[green]Configuration:[/green]")
    console.print(f"   Project: superb-analog-464304-s0")
    console.print(f"   Region: asia-south1")
    console.print(f"   Model: gemini-2.5-flash")
    console.print(f"   Port: {PORT}")
    console.print(f"[yellow]Features:[/yellow]")
    console.print(f"   ✓ RAG Engine (Classical Vedic Texts)")
    console.print(f"   ✓ Hybrid Mode (RAG + AI's Modern Knowledge)")
    console.print(f"   ✓ 5 Specialized Niches (Love, Career, Wealth, Health, Spiritual)")
    console.print(f"   ✓ Smart Formatting (No asterisks, natural language)")
    console.print(f"   ✓ Word Limit Enforcement (400 words, 350 for Health)")
    console.print(f"[yellow]Cloud Run Settings:[/yellow]")
    console.print(f"   Memory: 2 GiB")
    console.print(f"   CPU: 2 vCPU")
    console.print(f"   Timeout: 600s")
    console.print(f"   Concurrency: 10")
    console.print(f"[blue]Local URL: http://127.0.0.1:{PORT}[/blue]")
    
    # Launch with Cloud Run compatible settings
    demo.launch(
        server_name="0.0.0.0",
        server_port=PORT,
        share=False,
        show_error=True
    )
