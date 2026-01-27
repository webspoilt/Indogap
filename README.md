# 🇮🇳 IndoGap - AI-Powered Opportunity Discovery Engine

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange?logo=ollama&logoColor=white)](https://ollama.ai)

**The First Local-First, Privacy-Focused Market Gap Discovery Engine for the Indian Startup Ecosystem**

[🌐 Live Demo](https://webspoilt.github.io/Indogap) • [📖 Documentation](#-usage) • [🚀 Quick Start](#-quick-start)

</div>

---

## 🎯 What is IndoGap?

IndoGap analyzes **global startup trends** from Y Combinator and Product Hunt, then identifies **untapped opportunities** specifically for the Indian market. All AI processing runs **100% locally** on your machine—zero API costs, complete privacy.

```
SCRAPE (YC + PH) → ANALYZE (Local AI) → IDENTIFY (Gaps) → BUILD (MVP)
```

---

## ✨ Features

| Feature | Description |
|:--------|:------------|
| 🔍 **Smart Scraping** | Automated data collection from Y Combinator & Product Hunt |
| 🧠 **Local AI Analysis** | Runs Llama 3 & DeepSeek locally via Ollama—no cloud APIs |
| 📊 **7-Dimension Scoring** | Cultural fit, logistics, timing, payments & more |
| 🇮🇳 **India-Focused** | Tailored recommendations for Indian market nuances |
| 🚀 **MVP Generator** | Auto-generates tech specs & implementation roadmaps |
| 🔒 **Privacy-First** | Your data never leaves your machine |
| 💰 **Zero Cost** | No OpenAI/Anthropic fees—runs entirely on local hardware |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** — Core language
- **FastAPI** — High-performance API framework
- **BeautifulSoup4** — Web scraping
- **scikit-learn** — ML algorithms (TF-IDF, similarity)

### AI Models (via Ollama)
| Model | Size | Purpose |
|:------|:-----|:--------|
| `llama3.2:3b` | ~2GB | Fast classification |
| `llama3.1:8b` | ~5GB | Deep reasoning |
| `deepseek-coder:6.7b` | ~4GB | Code generation |

### Frontend
- **Next.js 15** — React framework
- **TailwindCSS** — Styling
- **Shadcn/UI** — Component library
- **TypeScript** — Type safety

---

## ⚙️ Prerequisites

| Requirement | Minimum | Recommended |
|:------------|:--------|:------------|
| RAM | 16GB | 32GB |
| Storage | 10GB | 20GB SSD |
| CPU | i5 10th gen | i7 / Ryzen 7 |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ LTS |

---

## 🚀 Quick Start

### 1️⃣ Clone & Install

```bash
git clone https://github.com/webspoilt/Indogap.git
cd Indogap

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### 2️⃣ Setup Ollama (Required for AI)

```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai

# Pull AI models
ollama pull llama3.2:3b
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
```

### 3️⃣ Run the Application

```bash
# Start the API server (includes dashboard)
python api_server.py

# Or run CLI demo
python main.py --demo
```

Open **http://localhost:8000** in your browser.

---

## 📖 Usage

### Dashboard Features
- **System Monitor** — Real-time RAM/VRAM usage
- **Scrape Control** — Trigger YC/PH scrapes
- **Opportunity Feed** — Ranked opportunities with gap scores
- **MVP Generator** — One-click tech spec generation

### API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/system/stats` | System resources |
| `POST` | `/api/scrape` | Scrape YC/PH |
| `POST` | `/api/analyze` | Analyze startup |
| `GET` | `/api/opportunities` | List opportunities |

### CLI Commands

```bash
python main.py --demo          # Demo with mock data
python main.py --batch W24     # Scrape specific YC batch
python main.py --optimize      # Optimize for performance
```

---

## 🌐 Deployment

### Backend → Render.com (Free)

1. Push to GitHub
2. Create Web Service on [render.com](https://render.com)
3. **Build**: `pip install -r requirements.txt`
4. **Start**: `gunicorn api_server:app -k uvicorn.workers.UvicornWorker`

### Frontend → Vercel (Free)

1. Import repo on [vercel.com](https://vercel.com)
2. Set root directory to `src/`
3. Add env: `NEXT_PUBLIC_API_URL=https://your-render-app.onrender.com`

---

## 📁 Project Structure

```
Indogap/
├── api_server.py          # FastAPI backend + dashboard
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
├── index.html             # Landing page (GitHub Pages)
├── mini_services/         # Core modules
│   ├── llm/               # Ollama AI clients
│   ├── scrapers/          # YC & PH scrapers
│   ├── processors/        # NLP & ML processing
│   ├── scoring/           # 7-dimension scoring
│   ├── mvp_generator/     # MVP generation
│   └── database/          # Data persistence
└── src/                   # Next.js frontend
    ├── app/               # App Router pages
    └── components/        # UI components
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the Indian Startup Ecosystem**

⭐ **Star this repo if you found it useful!**

[Report Bug](https://github.com/webspoilt/Indogap/issues) • [Request Feature](https://github.com/webspoilt/Indogap/issues)

</div>
