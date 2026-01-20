IndoGap - AI-Powered Opportunity Discovery Engine

IndoGap-AI%20Opportunity%20Discovery-blue?style=for-the-badge


Python-3.11+-green?style=flat-square&logo=python


Next.js-14-black?style=flat-square&logo=next.js


License-MIT-yellow?style=flat-square


Discover business opportunities by analyzing global startups and identifying gaps in the Indian market


✨ Features
Feature	Description
🔍 Automated Scraping	Collects data from Y Combinator and Product Hunt
🧠 AI-Powered Analysis	Uses local LLMs for intelligent opportunity scoring
📊 7-Dimension Scoring	Evaluates cultural fit, logistics, timing, and more
🗺️ India-Specific	Tailored recommendations for the Indian market
📈 MVP Generation	Creates detailed MVP roadmaps automatically
🔒 Privacy-First	All AI runs locally - no data leaves your machine
💰 100% Free	No OpenAI, Anthropic, or paid API costs
🎯 How It Works
SCRAPE (YC + Product Hunt) → ANALYZE (Local AI) → IDENTIFY (Market Gaps)
                                                          │
                                                          ▼
                                                  BUILD (MVP)
Phase 1: Data Collection
Scrapes startup data from Y Combinator and Product Hunt.

Phase 2: Gap Detection
Uses TF-IDF similarity to compare against Indian startups.

Phase 3: AI Scoring
Evaluates 7 dimensions using local AI models.

Phase 4: MVP Generation
Generates complete MVP specifications.

🛠️ Tech Stack
Backend
Python 3.11+ - Core language
FastAPI - Web framework
BeautifulSoup4 - Web scraping
scikit-learn - ML algorithms
AI & ML
Ollama - Local LLM inference
Llama 3.2 3B - Fast classification
Llama 3.1 8B - Reasoning
DeepSeek Coder 6.7B - Code generation
Frontend
Next.js 14 - React framework
Tailwind CSS - Styling
TypeScript - Type safety
📦 Installation
Prerequisites
Requirement	Minimum	Recommended
RAM	16GB	32GB
Storage	10GB	20GB SSD
CPU	i5 10th gen	i7/Ryzen 7
Clone and Install
bash
# Clone the repository
git clone https://github.com/webspoilt/Indogap.git
cd Indogap

# Install Python dependencies
pip install -r requirements.txt

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull AI models
ollama pull llama3.2:3b
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
🚀 Quick Start
Run with Dashboard (Recommended)
bash
python api_server.py
Open http://localhost:8000 in your browser.

Run CLI Demo
bash
python main.py --demo
📖 Usage
API Endpoints
Method	Endpoint	Description
GET	/api/health	System health check
GET	/api/system/stats	Resource usage
POST	/api/scrape	Scrape YC/PH data
POST	/api/analyze	Analyze startup
GET	/api/opportunities	List opportunities
Example
bash
# Scrape Y Combinator
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"source": "yc", "limit": 20}'

# Analyze a startup
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"startup_name": "FarmOS", "description": "IoT for farming", "tags": ["AgriTech"]}'
🧠 AI Models
Model	Size	Use Case
llama3.2:3b	2GB	Fast classification
llama3.1:8b	5GB	Reasoning & analysis
deepseek-coder:6.7b	4GB	Code generation
🌐 Hosting
Free Deployment Options
Platform	Backend	Frontend
Render.com	✅ Free	❌
Vercel	❌	✅ Free
Railway	✅ Free	❌
Deploy to Render (Backend)
1.
Push to GitHub
2.
Go to render.com
3.
Create Web Service, connect repo
4.
Build: pip install -r requirements.txt
5.
Start: gunicorn api_server:app -k uvicorn.workers.UvicornWorker
Deploy to Vercel (Frontend)
1.
Go to vercel.com
2.
Import GitHub repo (select src/ folder)
3.
Add env: NEXT_PUBLIC_API_URL=https://your-render-app.onrender.com
4.
Deploy
📁 Project Structure
Indogap/
├── api_server.py              # FastAPI server + dashboard
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── mini_services/             # Core modules
│   ├── llm/                   # AI integration
│   ├── scrapers/              # Web scrapers
│   ├── processors/            # NLP & ML
│   ├── scoring/               # 7-dimension scoring
│   ├── mvp_generator/         # MVP generation
│   └── models/                # Data models
└── src/                       # Next.js frontend
🤝 Contributing
Contributions welcome! Open issues or submit PRs.

📄 License
MIT License - See LICENSE file.


Built with ❤️ for the Indian startup ecosystem


⭐ Star us if you found this useful!
