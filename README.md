🤖 Atlas AI — Advanced Telegram Bot (Version 2)
A next-generation AI assistant for Telegram powered by Google Gemini 2.5 Pro with comprehensive real-time multi-database access.

## ✨ Features

### 🧠 AI Capabilities
- **Complex Reasoning** - Multi-step analysis, logic, math, strategy
- **Natural Conversations** - Context-aware, remembers your chat history
- **Research & Synthesis** - Deep research, summaries, fact-based answers
- **Creative Writing** - Stories, copy, poetry, scripts, brainstorming
- **Programming Help** - Debug, explain, write code in any language
- **Education** - Learn anything, explained at your level
- **Business & Strategy** - Planning, analysis, decisions

### 🎙️ Media Processing
- **Voice Messages** - Send a voice note → Atlas transcribes & replies
- **Document Analysis** - PDF, TXT, CSV, JSON, code file support
- **Image Analysis** - Describe, analyze, extract text from images

### 🌐 REAL-TIME MULTI-DATABASE ACCESS ⭐ *NEW*
Access to 14+ major databases for current, accurate information:

#### 📚 Academic & Research
- **Wikipedia** - General encyclopedia knowledge
- **Wikidata** - Structured factual data
- **arXiv** - Scientific research papers
- **PubMed** - Medical and health research

#### � Technology & Development
- **GitHub** - Code repositories and projects
- **Stack Overflow** - Programming Q&A
- **Reddit** - Community discussions

#### 📊 Financial & Economic
- **Stock Market** - Real-time financial data
- **Cryptocurrency** - Live crypto prices (Bitcoin, Ethereum)
- **World Bank** - Economic development data

#### 🌍 Government & Space
- **NASA** - Space and astronomy data
- **Google News** - Current events and breaking news

#### 🌤️ Weather & Environment
- **Weather APIs** - Real-time weather data

### 🔄 Smart Features
- **Conversation Memory** - Context across your session (20 turns)
- **Smart Model Routing** - Gemini 2.5 Pro → 2.5 Flash fallback
- **Auto-detection** - Automatically identifies when real-time data is needed
- **Parallel Search** - All databases searched simultaneously for fast results

## 🚀 Quick Setup

### 1. Clone / Download
```bash
git clone <repository-url>
cd atlas-ai-telegram
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Get API Keys

#### Telegram Bot Token:
1. Open Telegram → search @BotFather
2. Send `/newbot`
3. Follow prompts → get token like `123456:ABC-DEF...`

#### Gemini API Key:
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 4. Configure Environment
Create `.env` file:
```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEFxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 5. Run the Bot
```bash
python bot.py
```

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & feature overview |
| `/help` | Show all commands |
| `/new` | Clear conversation history, fresh start |
| `/model` | Show current AI model info |
| `/about` | About Atlas AI |

## 🎯 How It Works

### Text Messages
- **Regular Questions** → Processed by Gemini 2.5 Pro with conversation history
- **Current Event Questions** → Automatically searches 14+ databases in real-time
- **Smart Detection** → Identifies when live data is needed

### Media Processing
- **Voice** → Uploaded to Gemini Files API for transcription + response
- **Documents** → Uploaded to Gemini Files API for analysis
- **Images** → Uploaded to Gemini Files API for visual understanding

### Real-time Search Examples
Try these commands to see multi-database search in action:

```
"who is the president of usa"        → Direct current answer
"latest news about technology"       → News from multiple sources
"bitcoin price"                      → Live crypto prices
"Vivo T3 Ultra specifications"       → Current device info
"research on artificial intelligence" → Latest scientific papers
"github machine learning projects"   → Top repositories
"weather in new york"                → Weather data
"stock market today"                 → Financial data
"nasa mars mission"                  → Space data
"stackoverflow python help"          → Programming solutions
```

## 🔧 Technical Details

### Model Architecture
- **Primary**: Google Gemini 2.5 Pro (5 RPM / 100 RPD)
- **Fallback**: Google Gemini 2.5 Flash (10 RPM / 500 RPD)
- **Smart Routing**: Auto-fallback on rate limits

### Database Integration
- **Parallel Processing**: All databases searched simultaneously
- **Error Handling**: Graceful fallbacks if any database is unavailable
- **Response Combining**: Merges information from multiple sources
- **Smart Filtering**: Only relevant databases activated based on keywords

### Memory Management
- **In-memory Storage**: Conversation history per user
- **Auto-cleanup**: Files deleted after processing
- **Session Reset**: Use `/new` or restart bot to clear history

## ☁️ Deployment

### 🚀 Render Deployment (Recommended) ⭐

#### Step 1: Prepare Your Project
1. **Create a GitHub repository** with your bot code
2. **Ensure `.env` is in `.gitignore`** (don't commit secrets)
3. **Add `render.yaml`** to your repository:

```yaml
# render.yaml
services:
  - type: web
    name: atlas-ai-bot
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python bot.py"
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: GEMINI_API_KEY
        sync: false
```

#### Step 2: Deploy to Render
1. **Go to [render.com](https://render.com)** and sign up
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure deployment:**
   - **Name**: `atlas-ai-bot`
   - **Environment**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

#### Step 3: Add Environment Variables
In Render Dashboard → Your Service → Environment:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

#### Step 4: Deploy!
- **Render will automatically build and deploy**
- **Your bot will be live 24/7** with webhook URL
- **Free tier includes** 750 hours/month

### 🐳 Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t atlas-ai .
docker run -d --name atlas-ai --env-file .env atlas-ai
```

### 🖥️ Traditional Server (VPS/Dedicated)

#### Using Screen
```bash
# Install screen
sudo apt update && sudo apt install screen -y

# Run bot in screen
screen -S atlas
python bot.py

# Detach (Ctrl+A then D)
# Reattach: screen -r atlas
```

#### Using Systemd (Recommended for 24/7)
Create service file:
```bash
sudo nano /etc/systemd/system/atlas-ai.service
```

```ini
[Unit]
Description=Atlas AI Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/atlas-ai-telegram
Environment=TELEGRAM_BOT_TOKEN=your_token
Environment=GEMINI_API_KEY=your_key
ExecStart=/usr/bin/python3 /path/to/atlas-ai-telegram/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable atlas-ai
sudo systemctl start atlas-ai

# Check status
sudo systemctl status atlas-ai
```

### 📱 Platform Comparison

| Platform | Cost | Uptime | Setup | Best For |
|----------|------|--------|-------|----------|
| **Render** | Free tier available | 99.9% | ⭐⭐⭐⭐⭐ | Beginners, quick deployment |
| **DigitalOcean** | $5-20/month | 99.99% | ⭐⭐⭐ | Full control, custom setup |
| **Heroku** | $7+/month | 99.95% | ⭐⭐⭐⭐ | Easy deployment, dynos |
| **AWS EC2** | $3-50/month | 99.99% | ⭐⭐ | Enterprise, scalability |
| **VPS (Self)** | $2-10/month | Varies | ⭐ | Maximum control, learning |

## 📦 Requirements

```
google-genai==1.58.0
python-dotenv==1.2.1
python-telegram-bot==22.6
google-auth
aiohttp
```

## 🔒 Privacy & Security

- ✅ **No permanent storage** - All history is in-memory
- ✅ **File cleanup** - Uploaded files deleted after processing
- ✅ **Secure APIs** - All connections use HTTPS
- ✅ **Rate limiting** - Built-in protection against API abuse

## 🆕 Version 2 Updates

### Major Enhancements:
- ✅ **Multi-database search** (14+ data sources)
- ✅ **Real-time information access**
- ✅ **Smart query detection**
- ✅ **Parallel database processing**
- ✅ **Enhanced error handling**
- ✅ **Live crypto prices**
- ✅ **Current event awareness**

### Bug Fixes:
- ✅ Fixed knowledge cutoff issues
- ✅ Improved current event detection
- ✅ Enhanced search reliability
- ✅ Better fallback mechanisms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

If you encounter issues:
1. Check your API keys in `.env`
2. Ensure all dependencies are installed
3. Check internet connection for database access
4. Review logs for error messages

## 🎉 Conclusion

Atlas AI Version 2 represents a significant leap forward in AI assistance, combining the power of Google Gemini 2.5 Pro with comprehensive real-time data access from the world's most important databases.

**Atlas AI — Intelligence, always available with real-time knowledge.**