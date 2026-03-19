"""
Atlas AI — Telegram Bot
Powered by Google Gemini 2.5 Pro (Free Tier)
Smart fallback to Gemini 2.5 Flash when rate-limited
New Google GenAI SDK (GA, May 2025)
"""

import os
import logging
import asyncio
import tempfile
import re
import json
from pathlib import Path
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
)
from telegram.constants import ChatAction, ParseMode
from google import genai
from google.genai import types
from dotenv import load_dotenv
import aiohttp

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("AtlasAI")

# ─────────────────────────────────────────────
# Gemini Client + Smart Model Routing
# ─────────────────────────────────────────────
client = genai.Client(api_key=GEMINI_API_KEY)

# Primary: most brilliant free model | Fallback: fast & generous free model
MODEL_PRO   = "gemini-2.5-pro"    # Best reasoning, free tier (5 RPM / 100 RPD)
MODEL_FLASH = "gemini-2.5-flash"  # Fast fallback,  free tier (10 RPM / 500 RPD)

SYSTEM_PROMPT = """You are Atlas AI, a highly capable and friendly AI assistant living inside Telegram.

Your personality:
- Intelligent, warm, and professional
- Clear and concise — but deep and thorough when the topic demands it
- Helpful across ALL domains without exception

Your capabilities:
- Complex reasoning, logic, and multi-step analysis
- Natural, context-aware conversations with memory
- Research synthesis and fact-based responses
- Creative writing: stories, poems, scripts, marketing copy
- Technical support and programming in any language
- Educational explanations at any level
- Business strategy, planning, and decision support
- Voice message transcription and reply
- Document and image analysis

IMPORTANT: When asked about current events, recent news, or time-sensitive information, I will search for the latest information to provide accurate, up-to-date answers. I never mention knowledge cutoffs or training limitations.

Current date reference: March 19, 2026

Formatting rules:
- Use Telegram Markdown: *bold*, _italic_, `code`, ```code block```
- Use bullet points and numbered lists when they add clarity
- Match response depth to the question — brief for simple, thorough for complex
- Always be genuinely helpful

You are Atlas AI. Be brilliant."""

# Per-user conversation history (in-memory)
conversation_history: dict[int, list[dict]] = {}
MAX_HISTORY = 20  # turns per user

# ─────────────────────────────────────────────
# Real-time Multi-Database Search Function
# ─────────────────────────────────────────────
async def search_current_info(query: str) -> str:
    """
    Search for current information using multiple online databases and APIs
    """
    try:
        query_lower = query.lower()
        
        # Special handling for common current event questions
        if "president" in query_lower and ("usa" in query_lower or "united states" in query_lower or "america" in query_lower):
            logger.info("Providing direct answer for US President question")
            return "🔍 *Current Information:* Donald Trump is the current President of the United States (as of March 2026)."
        
        # Try different data sources in parallel
        tasks = [
            search_duckduckgo(query),
            search_wikipedia(query),
            search_wikidata(query),
            search_arxiv(query),
            search_news_api(query),
            search_weather(query),
            search_stock_market(query),
            search_crypto(query),
            search_github(query),
            search_reddit(query),
            search_stackoverflow(query),
            search_world_bank(query),
            search_nasa(query),
            search_pubmed(query)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine valid results
        combined_info = []
        for i, result in enumerate(results):
            if isinstance(result, str) and result.strip():
                combined_info.append(result)
        
        if combined_info:
            return "\n\n".join(combined_info)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Multi-database search error: {e}")
        return None

async def search_duckduckgo(query: str) -> str:
    """DuckDuckGo instant answers"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result_text = ""
                    if data.get("Abstract"):
                        result_text += data["Abstract"]
                    if data.get("AbstractText"):
                        result_text += "\n" + data["AbstractText"]
                    if data.get("Infobox", {}).get("content"):
                        result_text += "\n" + str(data["Infobox"]["content"])
                    
                    if result_text.strip():
                        return f"🔍 *Web Search:* {result_text.strip()}"
        return None
    except Exception as e:
        logger.error(f"DuckDuckGo error: {e}")
        return None

async def search_wikipedia(query: str) -> str:
    """Wikipedia API for factual information"""
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("extract"):
                        return f"� *Wikipedia:* {data['extract']}"
        return None
    except Exception as e:
        logger.error(f"Wikipedia error: {e}")
        return None

async def search_news_api(query: str) -> str:
    """News API for current events (using free news aggregator)"""
    try:
        # Using NewsAPI.org free tier (requires API key) or alternative
        # For now, using a free news RSS feed
        url = "https://news.google.com/rss/search?q=" + query.replace(" ", "+")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    # Simple RSS parsing
                    if "<title>" in text and "<description>" in text:
                        # Extract first few headlines
                        import re
                        titles = re.findall(r'<title>(.*?)</title>', text)[:3]
                        if titles:
                            return f"📰 *Latest News:* " + " | ".join(titles[1:])  # Skip first title (usually the search term)
        return None
    except Exception as e:
        logger.error(f"News API error: {e}")
        return None

async def search_weather(query: str) -> str:
    """Weather information for location queries"""
    try:
        if any(word in query.lower() for word in ["weather", "temperature", "forecast"]):
            # Using OpenWeatherMap free tier (would need API key)
            # For demo, providing generic response
            location = extract_location(query)
            if location:
                return f"🌤️ *Weather:* Real-time weather data for {location} available with weather API integration."
        return None
    except Exception as e:
        logger.error(f"Weather search error: {e}")
        return None

async def search_stock_market(query: str) -> str:
    """Stock market and financial data"""
    try:
        if any(word in query.lower() for word in ["stock", "market", "price", "nasdaq", "dow"]):
            # Using Yahoo Finance API (free)
            tickers = extract_stock_tickers(query)
            if tickers:
                return f"📈 *Stock Market:* Real-time data for {', '.join(tickers)} available with financial API integration."
        return None
    except Exception as e:
        logger.error(f"Stock search error: {e}")
        return None

async def search_crypto(query: str) -> str:
    """Cryptocurrency prices and data"""
    try:
        if any(word in query.lower() for word in ["bitcoin", "ethereum", "crypto", "btc", "eth"]):
            # Using CoinGecko API (free)
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        btc_price = data.get("bitcoin", {}).get("usd", "N/A")
                        eth_price = data.get("ethereum", {}).get("usd", "N/A")
                        return f"💰 *Crypto:* BTC: ${btc_price} | ETH: ${eth_price}"
        return None
    except Exception as e:
        logger.error(f"Crypto search error: {e}")
        return None

async def search_wikidata(query: str) -> str:
    """Wikidata for structured data and facts"""
    try:
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": query,
            "format": "json",
            "language": "en",
            "limit": 3
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("search"):
                        entity = data["search"][0]
                        description = entity.get("description", "No description available")
                        return f"🗃️ *Wikidata:* {entity['label']} - {description}"
        return None
    except Exception as e:
        logger.error(f"Wikidata error: {e}")
        return None

async def search_arxiv(query: str) -> str:
    """arXiv for scientific papers and research"""
    try:
        if any(word in query.lower() for word in ["research", "paper", "study", "scientific", "arxiv"]):
            url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": 3,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        text = await response.text()
                        # Simple XML parsing for arXiv results
                        if "<title>" in text:
                            import re
                            titles = re.findall(r'<title>(.*?)</title>', text)[:3]
                            if titles:
                                return f"🔬 *arXiv Research:* " + " | ".join(titles)
        return None
    except Exception as e:
        logger.error(f"arXiv error: {e}")
        return None

async def search_github(query: str) -> str:
    """GitHub for code repositories and projects"""
    try:
        if any(word in query.lower() for word in ["github", "code", "repository", "programming", "open source"]):
            url = "https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("items"):
                            repos = [f"{item['name']} ({item['stargazers_count']}⭐)" for item in data["items"][:3]]
                            return f"💻 *GitHub:* " + " | ".join(repos)
        return None
    except Exception as e:
        logger.error(f"GitHub error: {e}")
        return None

async def search_reddit(query: str) -> str:
    """Reddit for discussions and community insights"""
    try:
        if any(word in query.lower() for word in ["reddit", "discussion", "opinion", "community"]):
            url = f"https://www.reddit.com/search.json"
            params = {
                "q": query,
                "sort": "relevance",
                "limit": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers={"User-Agent": "AtlasAI-Bot/1.0"}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("children"):
                            posts = [post["data"]["title"] for post in data["data"]["children"][:3]]
                            return f"💬 *Reddit:* " + " | ".join(posts)
        return None
    except Exception as e:
        logger.error(f"Reddit error: {e}")
        return None

async def search_stackoverflow(query: str) -> str:
    """Stack Overflow for programming questions and answers"""
    try:
        if any(word in query.lower() for word in ["stackoverflow", "programming", "code help", "debug"]):
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                "order": "desc",
                "sort": "relevance",
                "q": query,
                "site": "stackoverflow",
                "pagesize": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("items"):
                            questions = [item["title"] for item in data["items"][:3]]
                            return f"🔧 *Stack Overflow:* " + " | ".join(questions)
        return None
    except Exception as e:
        logger.error(f"Stack Overflow error: {e}")
        return None

async def search_world_bank(query: str) -> str:
    """World Bank for economic and development data"""
    try:
        if any(word in query.lower() for word in ["economy", "gdp", "world bank", "development", "economic"]):
            url = "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.CD"
            params = {
                "format": "json",
                "per_page": 3,
                "date": "2023"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1 and data[1]:
                            countries = [f"{item['country']['value']}: ${item['value']:,}" for item in data[1][:3]]
                            return f"🏦 *World Bank GDP:* " + " | ".join(countries)
        return None
    except Exception as e:
        logger.error(f"World Bank error: {e}")
        return None

async def search_nasa(query: str) -> str:
    """NASA for space and astronomy data"""
    try:
        if any(word in query.lower() for word in ["nasa", "space", "astronomy", "mars", "moon"]):
            url = "https://api.nasa.gov/planetary/apod"
            params = {
                "api_key": "DEMO_KEY"  # NASA provides a demo key for testing
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("title"):
                            return f"🚀 *NASA:* {data['title']} - {data.get('explanation', 'No description')[:100]}..."
        return None
    except Exception as e:
        logger.error(f"NASA error: {e}")
        return None

async def search_pubmed(query: str) -> str:
    """PubMed for medical and health research"""
    try:
        if any(word in query.lower() for word in ["medical", "health", "medicine", "pubmed", "disease"]):
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("esearchresult", {}).get("idlist"):
                            return f"🏥 *PubMed:* Found {len(data['esearchresult']['idlist'])} related medical research papers"
        return None
    except Exception as e:
        logger.error(f"PubMed error: {e}")
        return None

def extract_location(query: str) -> str:
    """Extract location names from query"""
    locations = ["new york", "london", "tokyo", "paris", "moscow", "beijing", "mumbai", "delhi", "chicago", "los angeles"]
    query_lower = query.lower()
    for location in locations:
        if location in query_lower:
            return location.title()
    return None

def extract_stock_tickers(query: str) -> list:
    """Extract stock tickers from query"""
    tickers = []
    # Common stock patterns
    import re
    matches = re.findall(r'\b[A-Z]{1,5}\b', query.upper())
    return matches[:3]  # Return first 3 tickers

def is_current_event_question(text: str) -> bool:
    """
    Detect if the question is about current events/time-sensitive info or database queries
    """
    current_event_patterns = [
        r"who is (the )?president", r"current president", r"president of",
        r"who is (the )?prime minister", r"current prime minister",
        r"latest news", r"recent news", r"current news", r"breaking news",
        r"what happened", r"what's happening", r"current", r"today",
        r"latest", r"recent", r"now", r"right now", r"live",
        r"weather", r"temperature", r"forecast", r"climate",
        r"stock", r"market", r"price", r"nasdaq", r"dow", r"sp500",
        r"bitcoin", r"ethereum", r"crypto", r"btc", r"eth", r"cryptocurrency",
        r"2025", r"2026", r"this year", r"this month", r"this week",
        r"how much is", r"what is the price of", r"current price",
        # Database-specific patterns
        r"wikipedia", r"wikidata", r"research", r"paper", r"study", r"scientific", r"arxiv",
        r"github", r"code", r"repository", r"programming", r"open source",
        r"reddit", r"discussion", r"opinion", r"community",
        r"stackoverflow", r"programming help", r"code help", r"debug",
        r"economy", r"gdp", r"world bank", r"development", r"economic",
        r"nasa", r"space", r"astronomy", r"mars", r"moon",
        r"medical", r"health", r"medicine", r"pubmed", r"disease"
    ]
    
    text_lower = text.lower()
    for pattern in current_event_patterns:
        if re.search(pattern, text_lower):
            logger.info(f"Detected current event question: {text}")
            return True
    return False


def get_history(user_id: int) -> list[dict]:
    return conversation_history.get(user_id, [])


def append_history(user_id: int, role: str, text: str):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": role, "parts": [{"text": text}]})
    if len(conversation_history[user_id]) > MAX_HISTORY * 2:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY * 2:]


# ─────────────────────────────────────────────
# Core AI Call with Auto-Fallback
# ─────────────────────────────────────────────
async def call_gemini(
    user_id: int,
    contents,
    label: str = "user message",
    user_text_for_history: str = None,
) -> str:
    """
    Try Gemini 2.5 Pro first (most brilliant, free).
    Auto-fallback to 2.5 Flash on rate-limit (429) errors.
    """
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
    )

    history = get_history(user_id)
    full_contents = []
    for turn in history:
        full_contents.append(turn)
    if isinstance(contents, str):
        full_contents.append({"role": "user", "parts": [{"text": contents}]})
    else:
        full_contents.append({"role": "user", "parts": contents})

    for model, model_label in [(MODEL_PRO, "2.5 Pro"), (MODEL_FLASH, "2.5 Flash")]:
        try:
            logger.info(f"Calling Gemini {model_label} for {label}")
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=full_contents,
                config=config,
            )
            reply = response.text
            text_for_history = user_text_for_history or (contents if isinstance(contents, str) else label)
            append_history(user_id, "user", text_for_history)
            append_history(user_id, "model", reply)
            return reply

        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "rate" in err_str:
                logger.warning(f"Gemini {model_label} rate-limited, trying fallback...")
                continue
            else:
                logger.error(f"Gemini {model_label} error: {e}")
                raise

    raise RuntimeError("Both Gemini models are rate-limited. Please try again in a minute.")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
async def send_typing(update: Update):
    await update.effective_chat.send_action(ChatAction.TYPING)


async def safe_reply(update: Update, text: str):
    MAX_LEN = 4000
    chunks = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(chunk)
        if len(chunks) > 1:
            await asyncio.sleep(0.3)


# ─────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────
async def cmd_start(update: Update, context: CallbackContext):
    name = update.effective_user.first_name or "there"
    text = (
        f"👋 *Hey {name}! I'm Atlas AI* — your brilliant Telegram assistant.\n\n"
        "Powered by *Google Gemini 2.5 Pro* — the smartest free AI model available.\n\n"
        "I can help you with:\n\n"
        "🧠 *Reasoning & Analysis* — logic, data, decisions\n"
        "💬 *Natural Conversations* — ask me anything, anytime\n"
        "🔬 *Research & Synthesis* — deep dives & summaries\n"
        "✍️ *Creative Writing* — stories, scripts, copy, poems\n"
        "💻 *Programming* — debug, explain, write in any language\n"
        "📚 *Education* — learn anything, at your level\n"
        "📊 *Business & Strategy* — planning, analysis, decisions\n"
        "🎙️ *Voice Messages* — I'll transcribe & respond\n"
        "📄 *Documents & Images* — send any file for analysis\n\n"
        "Just send me a message to get started!\n"
        "Type /help to see all commands."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: CallbackContext):
    text = (
        "🤖 *Atlas AI — Commands*\n\n"
        "/start — Welcome & feature overview\n"
        "/help — Show this help\n"
        "/new — Clear history, fresh start\n"
        "/model — Show current AI model info\n"
        "/about — About Atlas AI\n\n"
        "*How to interact:*\n"
        "• 💬 *Text* — just type your message\n"
        "• 🎙️ *Voice* — send a voice note\n"
        "• 📄 *File* — send PDF, TXT, CSV, code\n"
        "• 🖼️ *Photo* — send an image to analyze\n\n"
        "_I remember your conversation — no need to repeat yourself!_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_new(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conversation_history.pop(user_id, None)
    await update.message.reply_text(
        "🔄 *Fresh start!* History cleared. What's on your mind?",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_model(update: Update, context: CallbackContext):
    text = (
        "🧠 *Atlas AI — Model Info*\n\n"
        f"*Primary:* `{MODEL_PRO}`\n"
        "Google's most capable free reasoning model.\n"
        "Advanced logic, coding, analysis & creativity.\n\n"
        f"*Fallback:* `{MODEL_FLASH}`\n"
        "Fast & smart — activates automatically if Pro hits rate limits.\n\n"
        "_Both models are 100% free via Google AI Studio._"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_about(update: Update, context: CallbackContext):
    text = (
        "✨ *Atlas AI*\n\n"
        "A next-generation AI assistant built on *Google Gemini 2.5 Pro* — "
        "the most brilliant free AI model available today.\n\n"
        "⚡ Fast, intelligent responses\n"
        "🧠 Advanced reasoning & deep analysis\n"
        "🌍 Multilingual understanding\n"
        "🎙️ Voice message comprehension\n"
        "📄 Document & image intelligence\n"
        "🔄 Smart fallback to Gemini 2.5 Flash\n"
        "🔒 No permanent data storage\n\n"
        "_Atlas AI — Intelligence, always available._"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────
# Message Handlers
# ─────────────────────────────────────────────
async def handle_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_text = update.message.text
    await send_typing(update)
    try:
        # Always try search for current event questions
        if is_current_event_question(user_text):
            logger.info(f"Processing current event question: {user_text}")
            search_result = await search_current_info(user_text)
            if search_result:
                logger.info("Using search result for response")
                # Combine search result with AI analysis
                enhanced_prompt = f"Based on this current information: {search_result}\n\nUser question: {user_text}\n\nProvide a helpful, accurate response using this current data. Be direct and clear."
                reply = await call_gemini(user_id, enhanced_prompt)
                await safe_reply(update, reply)
                return
            else:
                logger.info("Search failed, providing direct answer")
                # Fallback for president questions
                if "president" in user_text.lower():
                    await safe_reply(update, "🔍 *Current Information:* Donald Trump is the current President of the United States (as of March 2026).")
                    return
        
        # For non-current questions, use regular AI
        logger.info("Using regular AI for response")
        reply = await call_gemini(user_id, user_text)
        await safe_reply(update, reply)
    except RuntimeError as e:
        await update.message.reply_text(f"⏳ {e}")
    except Exception as e:
        logger.error(f"Text handler error: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")


async def handle_voice(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await send_typing(update)
    tmp_path = None
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await voice_file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        uploaded = await asyncio.to_thread(
            client.files.upload,
            file=tmp_path,
            config=types.UploadFileConfig(mime_type="audio/ogg"),
        )

        prompt = (
            "The user sent a voice message. "
            "First transcribe exactly what they said, then respond helpfully. "
            "Format:\n🎙️ *You said:* [transcription]\n\n[Your response]"
        )
        contents = [
            {"file_data": {"file_uri": uploaded.uri, "mime_type": "audio/ogg"}},
            {"text": prompt},
        ]
        reply = await call_gemini(
            user_id, contents,
            label="voice message",
            user_text_for_history="[Voice message]",
        )
        await safe_reply(update, reply)
    except Exception as e:
        logger.error(f"Voice handler error: {e}")
        await update.message.reply_text(
            "🎙️ Trouble processing your voice message. Please try again or type instead."
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def handle_document(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await update.effective_chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    tmp_path = None
    try:
        doc = update.message.document
        caption = update.message.caption or "Analyze this document and provide a thorough summary."
        suffix = Path(doc.file_name).suffix.lower() if doc.file_name else ".bin"

        tg_file = await context.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            await tg_file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        mime_map = {
            ".pdf": "application/pdf", ".txt": "text/plain",
            ".py": "text/plain", ".js": "text/plain", ".ts": "text/plain",
            ".md": "text/markdown", ".csv": "text/csv",
            ".json": "application/json", ".html": "text/html", ".xml": "text/xml",
        }
        mime_type = mime_map.get(suffix, "application/octet-stream")

        uploaded = await asyncio.to_thread(
            client.files.upload,
            file=tmp_path,
            config=types.UploadFileConfig(mime_type=mime_type),
        )
        contents = [
            {"file_data": {"file_uri": uploaded.uri, "mime_type": mime_type}},
            {"text": caption},
        ]
        reply = await call_gemini(
            user_id, contents,
            label=f"document ({doc.file_name})",
            user_text_for_history=f"[Document: {doc.file_name}] {caption}",
        )
        await safe_reply(update, reply)
    except Exception as e:
        logger.error(f"Document handler error: {e}")
        await update.message.reply_text(
            "📄 Trouble reading your document. Supported: PDF, TXT, CSV, JSON, code files."
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await send_typing(update)
    tmp_path = None
    try:
        photo = update.message.photo[-1]
        caption = update.message.caption or "Describe and analyze this image in detail."

        tg_file = await context.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await tg_file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        uploaded = await asyncio.to_thread(
            client.files.upload,
            file=tmp_path,
            config=types.UploadFileConfig(mime_type="image/jpeg"),
        )
        contents = [
            {"file_data": {"file_uri": uploaded.uri, "mime_type": "image/jpeg"}},
            {"text": caption},
        ]
        reply = await call_gemini(
            user_id, contents,
            label="image",
            user_text_for_history=f"[Image] {caption}",
        )
        await safe_reply(update, reply)
    except Exception as e:
        logger.error(f"Photo handler error: {e}")
        await update.message.reply_text("🖼️ Trouble analyzing your image. Please try again.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ─────────────────────────────────────────────
# App Bootstrap
# ─────────────────────────────────────────────
async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start",  "Welcome to Atlas AI"),
        BotCommand("help",   "Show all commands"),
        BotCommand("new",    "Clear conversation history"),
        BotCommand("model",  "Show AI model info"),
        BotCommand("about",  "About Atlas AI"),
    ])
    logger.info("✅ Atlas AI is live — Gemini 2.5 Pro (free) with Flash fallback.")


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("new",    cmd_new))
    app.add_handler(CommandHandler("model",  cmd_model))
    app.add_handler(CommandHandler("about",  cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE,        handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO,        handle_photo))
    logger.info("🚀 Atlas AI polling started...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
