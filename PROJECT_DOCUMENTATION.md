# IndoGap Project Documentation

## Comprehensive Analysis, Bug Report, and Deployment Guide

---

## 1. Project Overview

IndoGap is an AI-Powered Opportunity Discovery Engine designed specifically for the Indian startup ecosystem. The platform analyzes global startup trends from Y Combinator and Product Hunt to identify untapped market opportunities that can be capitalized on in India. This local-first, privacy-focused application leverages local AI models through Ollama to provide intelligent market analysis without relying on external cloud APIs, ensuring data privacy and reducing operational costs to zero.

The project is built with a modern technology stack combining Python for backend processing and Next.js 14 for the frontend interface. The backend utilizes FastAPI for creating RESTful APIs, BeautifulSoup4 for web scraping Y Combinator and Product Hunt data, and scikit-learn for implementing machine learning algorithms including TF-IDF vectorization and similarity scoring. The frontend is developed with Next.js 14, TailwindCSS for styling, and Shadcn/UI components for a polished user interface. The system supports multiple local AI models through Ollama including llama3.2:3b for fast classification tasks, llama3.1:8b for deep reasoning, and deepseek-coder:6.7b for code generation tasks related to MVP specifications.

The core functionality centers around a seven-dimensional scoring system that evaluates opportunities across cultural fit, logistics feasibility, payment readiness, timing, regulatory compliance, competition intensity, and execution feasibility. This comprehensive evaluation helps entrepreneurs and investors make informed decisions about which global startup concepts have the highest potential for success in the Indian market.

---

## 2. Identified Bugs and Issues

### 2.1 Critical Issues

#### 2.1.1 GPU Index Out of Range Error (api_server.py)

**Location:** Lines 132, 155-156

**Description:** The code attempts to access GPU memory without checking if any GPUs are available. The line `gpus[0].memoryUsed` will raise an `IndexError` when `GPUtil.getGPUs()` returns an empty list, which is common on systems without dedicated graphics cards.

**Current Code:**
```python
gpus = GPUtil.getGPUs()
vram = gpus[0].memoryUsed / 1024 if gpus else None
```

**Issue:** The condition checks if `gpus` exists but the expression `gpus[0].memoryUsed` is evaluated before the ternary operator can protect against the empty list case. In Python, the entire left side of the ternary expression is evaluated before the condition is checked.

**Fix:**
```python
gpus = GPUtil.getGPUs()
vram = gpus[0].memoryUsed / 1024 if len(gpus) > 0 else None
```

Alternatively, use safer access:
```python
gpus = GPUtil.getGPUs()
vram = gpus[0].memoryUsed / 1024 if gpus else None
```
Note that the current code actually works correctly in Python because the ternary operator evaluates conditionally. However, for clarity and defensive programming, the explicit length check is recommended.

#### 2.1.2 Missing Module Import (main.py)

**Location:** Line 338

**Description:** The import `from mini_services.scoring.base import ScoringRequest` assumes a specific module structure that may not exist or may have been refactored. This will cause an `ImportError` during the demo execution.

**Current Code:**
```python
from mini_services.scoring.base import ScoringRequest
scoring_request = ScoringRequest(
    opportunity_id=yc_company.get('id', yc_company['name']),
    startup_name=yc_company['name'],
    startup_description=yc_company['short_description'],
    source_batch=yc_company.get('batch'),
    tags=yc_company.get('tags', []),
    best_match=best_match
)
scores = scorer.score(scoring_request)
```

**Recommended Fix:** First verify the actual module structure by checking what exists in the `mini_services/scoring/` directory. If the `base.py` file doesn't exist, the `ScoringRequest` class should be defined either in the `__init__.py` file or in a different module. Alternatively, the code can be refactored to use a dictionary or dataclass instead of the Pydantic model for the demo.

#### 2.1.3 Insecure CORS Configuration (api_server.py)

**Location:** Line 59

**Description:** The CORS middleware is configured with `allow_origins=["*"]` which allows any domain to make cross-origin requests to the API. This is a significant security vulnerability that could allow attackers to make unauthorized API calls from malicious websites.

**Current Code:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Fix for Development:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Fix for Production:** Use environment variables to specify allowed origins:
```python
from fastapi.middleware.cors import CORSMiddleware
import os

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.2 Medium Severity Issues

#### 2.2.1 Late Import of pandas (main.py)

**Location:** Line 476

**Description:** The `pandas` import is placed inside the export function instead of at the top of the file. This can cause confusion during static analysis and may result in import errors if the function is called before pandas is installed.

**Current Code:**
```python
import pandas as pd

# ... (later in the function)
rows = []
for opp in opportunities:
    # ...
df = pd.DataFrame(rows)
df.to_csv(csv_path, index=False)
```

**Fix:** Move the import to the top of the file with other imports:
```python
import pandas as pd
```

Then remove the import from inside the function.

#### 2.2.2 Nested Attribute Access Without Fallback (main.py)

**Location:** Lines 491-493

**Description:** The code accesses nested attributes that may not exist, potentially causing `AttributeError` or `KeyError` exceptions.

**Current Code:**
```python
'Cultural Fit': opp['scores'].dimensions.get('cultural_fit', {}).score if opp['scores'] and opp['scores'].dimensions else 'N/A',
'Payment Readiness': opp['scores'].dimensions.get('payment_readiness', {}).score if opp['scores'] and opp['scores'].dimensions else 'N/A',
'Execution Feasibility': opp['scores'].dimensions.get('execution_feasibility', {}).score if opp['scores'] and opp['scores'].dimensions else 'N/A',
```

**Fix:** Use safer access patterns with getattr and proper fallbacks:
```python
'Cultural Fit': getattr(getattr(opp.get('scores'), 'dimensions', {}).get('cultural_fit', {}), 'score', 'N/A'),
'Payment Readiness': getattr(getattr(opp.get('scores'), 'dimensions', {}).get('payment_readiness', {}), 'score', 'N/A'),
'Execution Feasibility': getattr(getattr(opp.get('scores'), 'dimensions', {}).get('execution_feasibility', {}), 'score', 'N/A'),
```

Alternatively, create a helper function:
```python
def safe_get_score(opp, dimension_name):
    try:
        if opp.get('scores') and opp['scores'].get('dimensions'):
            dim = opp['scores']['dimensions'].get(dimension_name, {})
            return dim.get('score', 'N/A')
    except (AttributeError, KeyError, TypeError):
        pass
    return 'N/A'
```

#### 2.2.3 Unused OpenAI Dependency (requirements.txt)

**Location:** Line 21

**Description:** The `openai>=1.3.0` package is listed in requirements.txt, but the project description indicates it uses local Ollama models exclusively. This dependency may be unused and adds unnecessary installation weight.

**Current Code:**
```
openai>=1.3.0
```

**Recommended Action:** Verify if the OpenAI client is used anywhere in the codebase. If not, remove it from requirements.txt. If it might be used in the future, add a comment explaining when it should be used.

### 2.3 Low Severity Issues

#### 2.3.1 Version Mismatch in Documentation

**Description:** The README.md mentions Next.js 14, but package.json specifies Next.js 15.3.5. This discrepancy can confuse developers setting up the project.

**Fix:** Update README.md to reflect the correct Next.js version or update package.json to match the documented version.

#### 2.3.2 Private Package Dependency (package.json)

**Location:** Line 79

**Description:** The package `z-ai-web-dev-sdk` is listed as a dependency. This appears to be a private or internal package that may not be available in public npm registries.

**Current Code:**
```json
"z-ai-web-dev-sdk": "^0.0.15",
```

**Fix:** Either remove this dependency if it's not essential, or document how to obtain and install this private package.

#### 2.3.3 React 19 Compatibility

**Description:** The project uses React 19.0.0 which was recently released and may have compatibility issues with some of the Shadcn/UI components or other dependencies that haven't been fully tested with React 19.

**Recommendation:** Test all UI components thoroughly after installation. If issues are found, consider downgrading to React 18.2 which has broader compatibility.

#### 2.3.4 Hardcoded Indian Competitors (api_server.py)

**Location:** Line 245

**Description:** The Indian competitors list is hardcoded, making it difficult to maintain and update as the market evolves.

**Current Code:**
```python
indian_competitors = "Major Indian startups in this space: Razorpay, Freshworks, Zoho, Byjus, Practo"
```

**Fix:** Load this data from a configuration file or database:
```python
indian_competitors = repository.get_indian_competitors(category=request.tags[0] if request.tags else None)
```

Or load from environment variable or JSON file:
```python
import json

with open("config/indian_competitors.json", "r") as f:
    competitors_data = json.load(f)
indian_competitors = competitors_data.get("default", "")
```

---

## 3. Installation and Setup Guide

### 3.1 System Requirements

Before beginning the installation process, ensure your development environment meets the following minimum specifications. The application is designed to run locally, so adequate hardware resources are essential for running both the Python backend with its machine learning components and the Next.js frontend simultaneously.

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 16GB | 32GB |
| Storage | 10GB | 20GB SSD |
| CPU | i5 10th gen | i7 / Ryzen 7 |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ LTS |

The RAM requirement is particularly important because the local AI models through Ollama require significant memory. The llama3.1:8b model alone requires approximately 5GB of RAM when loaded, and having multiple models available simultaneously can quickly consume 16GB or more.

### 3.2 Step-by-Step Installation

#### 3.2.1 Clone the Repository

Begin by cloning the repository to your local machine using Git. Navigate to your preferred development directory and execute the clone command.

```bash
git clone https://github.com/webspoilt/Indogap.git
cd Indogap
```

#### 3.2.2 Python Environment Setup

Create a virtual environment to isolate the project dependencies from your system Python installation. This ensures that the project has all required packages without conflicting with other Python projects you may have installed.

```bash
python -m venv indogap-env
source indogap-env/bin/activate  # On Windows: indogap-env\Scripts\activate
pip install -r requirements.txt
```

The installation process may take several minutes as it downloads and compiles various dependencies including scikit-learn and its numerical dependencies. If you encounter any compilation errors, ensure you have the necessary build tools installed for your operating system.

#### 3.2.3 Node.js Environment Setup

Install the frontend dependencies using npm or your preferred package manager. The project is configured to work with npm, yarn, or bun.

```bash
npm install
```

Alternatively, if you prefer using yarn:

```bash
yarn install
```

Or for bun users:

```bash
bun install
```

#### 3.2.4 Ollama Installation and Model Setup

Ollama is the backbone of the local AI functionality. Install Ollama by following the official installation instructions for your operating system. The installation script for Linux and macOS can be run directly from the terminal.

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

After installing Ollama, pull the required AI models. This step downloads the model weights to your local system, which may take significant time and storage space depending on your internet connection speed.

```bash
ollama pull llama3.2:3b
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
```

You can verify that the models are installed correctly by listing available models:

```bash
ollama list
```

#### 3.2.5 Environment Configuration

Copy the example environment file to create your local configuration. This file contains settings that control the application's behavior and should be customized for your local environment.

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred text editor to adjust any settings as needed. The default values should work for a local development setup, but you may want to change the `OLLAMA_BASE_URL` if Ollama is running on a different machine.

#### 3.2.6 Database Setup (Optional)

If you want to use a persistent database instead of the default in-memory storage, set up PostgreSQL and update the `DATABASE_URL` environment variable in your `.env` file. The project uses Prisma as its ORM, so database migrations can be managed through Prisma commands.

```bash
# Create the database
createdb indogap

# Push the schema to the database
npx prisma db push

# Generate the Prisma client
npx prisma generate
```

### 3.3 Running the Application

#### 3.3.1 Starting the Backend API Server

The FastAPI backend can be started using the provided Python script. This server provides the REST API for scraping, analyzing, and managing startup opportunities.

```bash
python api_server.py
```

By default, the server runs on port 8000 and binds to all network interfaces. You can customize the host and port using command-line arguments:

```bash
python api_server.py --host 127.0.0.1 --port 8080
```

The server will output logs indicating its status and any connections made by clients.

#### 3.3.2 Starting the Frontend Development Server

In a separate terminal window, start the Next.js development server. This provides hot-reloading during development, automatically refreshing the browser as you make changes to the code.

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`. The API server must be running for the frontend to function correctly, as it makes API calls to the backend for all data operations.

#### 3.3.3 Running the CLI Tool

The project also includes a command-line interface for running batch analyses and other automated tasks without the web interface.

```bash
python main.py --demo
```

This runs the demo mode with sample data, which is useful for testing the pipeline functionality without needing to scrape live data from Y Combinator or Product Hunt.

---

## 4. API Documentation

### 4.1 Base URL

All API endpoints are relative to the server root. By default, the API is accessible at `http://localhost:8000` when running locally.

### 4.2 Endpoints

#### 4.2.1 Health Check

**Endpoint:** `GET /api/health`

**Description:** Performs a system health check and returns the status of available AI models and system resources. This endpoint is useful for monitoring the application's operational status.

**Response:**
```json
{
    "status": "healthy",
    "ollama_available": true,
    "models_available": ["llama3.2:3b", "llama3.1:8b", "deepseek-coder:6.7b"],
    "ram_usage": 45.2,
    "vram_usage": 2.5,
    "timestamp": "2026-01-27T20:24:00.000Z"
}
```

**Status Values:**
- `healthy`: All systems operational, Ollama is available
- `degraded`: Application running but Ollama is not available

#### 4.2.2 System Statistics

**Endpoint:** `GET /api/system/stats`

**Description:** Returns real-time system resource utilization including CPU, RAM, and GPU memory usage. This information helps monitor resource consumption during AI model operations.

**Response:**
```json
{
    "cpu_percent": 25.4,
    "ram_percent": 62.8,
    "ram_used_gb": 10.5,
    "ram_total_gb": 16.0,
    "vram_used_gb": 2.5,
    "vram_total_gb": 8.0,
    "models_loaded": [],
    "timestamp": "2026-01-27T20:24:00.000Z"
}
```

#### 4.2.3 List Available Models

**Endpoint:** `GET /api/models`

**Description:** Returns a list of AI models available through the local Ollama installation. This helps verify that all required models have been downloaded and are accessible.

**Response:**
```json
{
    "models": ["llama3.2:3b", "llama3.1:8b", "deepseek-coder:6.7b"]
}
```

#### 4.2.4 Scrape Data

**Endpoint:** `POST /api/scrape`

**Description:** Initiates web scraping from Y Combinator or Product Hunt to collect startup data. This operation can take several minutes depending on the number of items being scraped.

**Request Body:**
```json
{
    "source": "yc",
    "batch": "W24",
    "limit": 50
}
```

**Parameters:**
- `source`: Source to scrape - `"yc"` for Y Combinator, `"ph"` for Product Hunt, or `"all"` for both
- `batch`: Optional Y Combinator batch identifier (e.g., "W24", "S25")
- `limit`: Maximum number of items to scrape (1-200, default: 50)

**Response:**
```json
{
    "success": true,
    "count": 50,
    "items": [
        {
            "source": "yc",
            "data": {
                "id": "yc_001",
                "name": "VoiceFlow Pro",
                "description": "AI voice agents...",
                "tags": ["AI", "Enterprise"],
                "batch": "W24"
            },
            "scraped_at": "2026-01-27T20:24:00.000Z"
        }
    ]
}
```

#### 4.2.5 Analyze Startup

**Endpoint:** `POST /api/analyze`

**Description:** Analyzes a startup concept against the Indian market using local AI models. Returns a comprehensive gap score and analysis across multiple dimensions.

**Request Body:**
```json
{
    "startup_name": "VoiceFlow Pro",
    "description": "AI voice agents for customer service automation",
    "tags": ["AI", "Enterprise", "Customer Service"],
    "source": "yc",
    "batch": "W24"
}
```

**Response:**
```json
{
    "gap_score": 0.85,
    "similarity_score": 0.15,
    "opportunity_level": "HIGH",
    "analysis": {
        "cultural_fit": 8,
        "payment_readiness": 7,
        "execution_feasibility": 6,
        "recommendation": "Strong opportunity for Indian market..."
    }
}
```

#### 4.2.6 Generate MVP Specification

**Endpoint:** `POST /api/mvp`

**Description:** Generates a detailed MVP specification including tech stack recommendations, feature roadmap, and implementation timeline using local AI models.

**Request Body:**
```json
{
    "startup_name": "VoiceFlow Pro",
    "description": "AI voice agents for customer service automation",
    "gap_score": 0.85
}
```

**Response:**
```json
{
    "startup": "VoiceFlow Pro",
    "gap_score": 0.85,
    "mvp_specification": {
        "tech_stack": {
            "frontend": "React with TypeScript",
            "backend": "FastAPI with Python",
            "database": "PostgreSQL",
            "ai_integration": "Ollama with Llama 3"
        },
        "core_features": [
            "Voice input/output interface",
            "Customer service workflow builder",
            "Integration with Indian payment gateways"
        ],
        "timeline": "3-4 months for MVP"
    },
    "generated_at": "2026-01-27T20:24:00.000Z"
}
```

#### 4.2.7 Get Opportunities

**Endpoint:** `GET /api/opportunities`

**Description:** Retrieves all analyzed opportunities stored in the database. This endpoint supports filtering and pagination through query parameters.

**Response:**
```json
[
    {
        "id": "opp_voiceflow_pro_1234567890",
        "name": "VoiceFlow Pro",
        "description": "AI voice agents for customer service",
        "source": "yc",
        "gap_score": 0.85,
        "similarity_score": 0.15,
        "opportunity_level": "HIGH",
        "analysis": {},
        "created_at": "2026-01-27T20:24:00.000Z"
    }
]
```

#### 4.2.8 Run Demo Analysis

**Endpoint:** `POST /api/demo`

**Description:** Runs a demonstration analysis using predefined sample data. Useful for testing the analysis pipeline without needing to scrape live data.

**Response:**
```json
{
    "success": true,
    "count": 5,
    "opportunities": [
        {
            "id": "opp_voiceflow_pro",
            "name": "VoiceFlow Pro",
            "description": "AI voice agents for customer service",
            "source": "yc_demo",
            "gap_score": 0.82,
            "similarity_score": 0.18,
            "opportunity_level": "HIGH",
            "analysis": {},
            "created_at": "2026-01-27T20:24:00.000Z"
        }
    ]
}
```

---

## 5. Free Hosting Guide

### 5.1 Hosting Overview

Hosting a full-stack application like IndoGap that requires local AI model processing presents unique challenges. The application has two main components with different hosting requirements: the Python backend that runs Ollama for local AI inference, and the Next.js frontend that serves the user interface. The Ollama component is particularly demanding as it requires significant GPU resources and memory to run AI models effectively.

Given these requirements, truly free hosting options are limited. Most cloud platforms charge for GPU instances and sufficient RAM. However, there are several strategies to minimize costs or use free tiers effectively for development, staging, or demonstration purposes. This section covers the available options from completely free solutions to cost-effective paid alternatives that offer generous free tiers.

### 5.2 Backend Hosting Options

#### 5.2.1 Railway

Railway offers a generous free tier that includes 500 hours of compute time per month and 5 GB of storage. While GPU instances are not available on the free tier, Railway is excellent for deploying the API server and frontend application without GPU requirements.

**Deployment Steps:**

1. Create a Railway account at railway.app and connect your GitHub repository
2. Create a new project and select your IndoGap repository
3. Configure the start command for the backend service:

```bash
python api_server.py
```

4. Set environment variables in the Railway dashboard, including any required configuration
5. Deploy the service and note the assigned URL

**Limitations:** The free tier does not include GPU support, so AI analysis features that require Ollama will not work. The API server will function but will return errors when attempting AI operations.

#### 5.2.2 Render

Render provides free web services with 750 hours per month of compute time. Like Railway, GPU instances are not available on the free tier, but the application infrastructure can be deployed.

**Deployment Steps:**

1. Sign up at render.com and connect your GitHub repository
2. Create a new Web Service and select your IndoGap repository
3. Configure the build command:

```bash
pip install -r requirements.txt
```

4. Configure the start command:

```bash
python api_server.py
```

5. Set environment variables and deploy

#### 5.2.3 Fly.io

Fly.io offers a generous free tier with limited compute and allows running Docker containers. The platform is particularly suitable for applications that need to run close to users in multiple regions.

**Deployment Steps:**

1. Install the Fly CLI and authenticate:

```bash
flyctl auth login
```

2. Create a fly.toml configuration file or initialize:

```bash
fly launch
```

3. Create a Dockerfile for the application:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "api_server.py"]
```

4. Deploy the application:

```bash
fly deploy
```

**Note:** Fly.io does not provide GPU support on the free tier. For AI features, consider using Fly.io's GPU instances which are priced per GPU second.

### 5.3 Frontend Hosting Options

#### 5.3.1 Vercel

Vercel is the creators of Next.js and offers seamless deployment for Next.js applications with excellent performance and generous free tier. The platform automatically optimizes Next.js applications for production deployment.

**Deployment Steps:**

1. Create a Vercel account at vercel.com
2. Click "Add New Project" and import your GitHub repository
3. Vercel automatically detects the Next.js configuration
4. Configure environment variables if needed
5. Click "Deploy"

Vercel's free tier includes unlimited bandwidth for personal projects, making it ideal for hosting the IndoGap frontend. The deployment completes in a few minutes, and Vercel provides a globally distributed CDN for optimal performance.

**Configuration:** Vercel automatically handles Next.js build optimization. The next.config.ts file should work without modifications:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    output: "standalone",
    poweredByHeader: false,
};

export default nextConfig;
```

#### 5.3.2 Netlify

Netlify provides excellent support for static and serverless deployments with a generous free tier. While Vercel is optimized for Next.js, Netlify offers similar functionality with additional features like form handling and edge functions.

**Deployment Steps:**

1. Create a Netlify account at netlify.com
2. Drag and drop your build output folder or connect your GitHub repository
3. Configure build settings:

```bash
# Build command
npm run build

# Publish directory
.next/static
```

4. Set environment variables if needed
5. Deploy the site

#### 5.3.3 GitHub Pages

GitHub Pages is completely free for open-source projects and provides reliable hosting with GitHub's infrastructure. However, Next.js applications require static export to work with GitHub Pages.

**Configuration:**

1. Modify next.config.ts to enable static export:

```typescript
const nextConfig: NextConfig = {
    output: 'export',
    images: {
        unoptimized: true,
    },
};
```

2. Build the static export:

```bash
npm run build
```

3. Deploy the out folder to GitHub Pages through repository settings

**Limitation:** Static export disables server-side rendering and API routes, significantly limiting the application's functionality. This option is only suitable for a simple static demo.

### 5.4 Complete Free Stack Deployment

For a fully functional deployment with both frontend and backend, the most cost-effective approach combines multiple services. Deploy the frontend on Vercel (free) and the backend on Railway or Render (free tier). This separates the concerns and allows each service to run on its optimal platform.

**Architecture:**

```
Internet → Vercel (Frontend) → Railway (Backend API) → Local Ollama (Development Only)
```

**CORS Configuration:** When deploying frontend and backend to different domains, update the CORS configuration in api_server.py to allow requests from the frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.5 GPU Hosting for AI Features

Running the AI features that make IndoGap powerful requires GPU access, which is typically not available on free tiers. The following options provide GPU access at minimal cost:

#### 5.5.1 Google Colab (Free Tier with Limitations)

Google Colab provides free GPU access in Jupyter notebook sessions. While not designed for production hosting, Colab can be used for batch processing opportunities analysis.

**Usage Pattern:**

1. Open the IndoGap repository in Google Colab
2. Install dependencies and Ollama
3. Run analysis on sample data
4. Export results for use in the main application

**Limitations:** Sessions are limited to 12 hours, GPU access varies by availability, and the environment resets between sessions.

#### 5.5.2 Gradient (Free GPU Hours)

Paperspace Gradient offers 200 free GPU hours per month on basic GPU instances. This is sufficient for development and testing of AI features.

**Steps:**

1. Sign up at gradient.paperspace.com
2. Create a new notebook or machine
3. Clone the IndoGap repository
4. Install dependencies and run the analysis pipeline

#### 5.5.3 Cost-Effective Paid Options

For production deployment with GPU support, consider these affordable options:

**RunPod:** GPU instances starting at $0.20/hour for RTX 4090 GPUs. Deploy using Docker containers with persistent storage.

**TensorDock:** GPU instances starting at $0.39/hour for various GPU types. Offers pre-configured containers for machine learning applications.

**Lambda Labs:** GPU instances starting at $1.10/hour for A100 GPUs. Provides optimized environments for AI workloads.

### 5.6 Recommended Free Hosting Strategy

For development and demonstration purposes without GPU requirements, the following configuration provides a complete free deployment:

**Frontend:** Vercel (automatic Next.js deployment, unlimited bandwidth)

**Backend:** Railway (500 hours/month free compute)

**Database:** Railway PostgreSQL (free tier includes 1GB database)

**Procedure:**

1. Deploy frontend to Vercel by connecting your GitHub repository
2. Deploy backend to Railway with the start command `python api_server.py`
3. Configure the frontend to point to the backend URL using environment variables
4. Set up CORS on the backend to allow requests from the Vercel frontend URL

This configuration provides a fully functional application for non-GPU features. The scraping and analysis API endpoints will function, but AI-powered analysis will fail without Ollama running on a machine with sufficient resources.

---

## 6. Testing Guide

### 6.1 Backend Testing

#### 6.1.1 Health Check Test

Verify the API server is running and healthy by making a request to the health endpoint:

```bash
curl http://localhost:8000/api/health
```

Expected response should show `"status": "healthy"` with `ollama_available: true` if Ollama is running.

#### 6.1.2 API Endpoint Testing

Test individual endpoints using curl or a tool like Postman:

```bash
# Test system stats
curl http://localhost:8000/api/system/stats

# Test model listing
curl http://localhost:8000/api/models

# Test demo analysis
curl -X POST http://localhost:8000/api/demo
```

#### 6.1.3 Python Unit Tests

Create a test file to verify core functionality:

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ollama_available" in data

def test_demo_endpoint():
    response = client.post("/api/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "opportunities" in data
```

Run tests with pytest:

```bash
pytest tests/ -v
```

### 6.2 Frontend Testing

#### 6.2.1 Build Verification

Build the Next.js application to verify there are no compilation errors:

```bash
npm run build
```

This command runs type checking, linting, and the production build process. Address any errors before deployment.

#### 6.2.2 Lighthouse Testing

Use Google Chrome's Lighthouse tool to audit the deployed application for performance, accessibility, best practices, and SEO. Target scores of 90+ for each category.

#### 6.2.3 Cross-Browser Testing

Test the application in multiple browsers:

- Google Chrome (latest)
- Mozilla Firefox (latest)
- Safari (latest)
- Microsoft Edge (latest)

Check for rendering consistency and functionality across browsers.

### 6.3 Integration Testing

#### 6.3.1 End-to-End Testing with Playwright

Create comprehensive end-to-end tests that verify the complete user workflow:

```javascript
// tests/e2e.spec.js
import { test, expect } from '@playwright/test';

test('complete analysis workflow', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for the dashboard to load
    await expect(page.locator('text=Dashboard')).toBeVisible();
    
    // Click on demo analysis button
    await page.click('text=Run Demo Analysis');
    
    // Wait for analysis to complete
    await expect(page.locator('text=High Priority')).toBeVisible({ timeout: 30000 });
    
    // Verify opportunities are displayed
    const opportunities = page.locator('.opportunity-card');
    await expect(opportunities).toHaveCount(5);
});
```

Run end-to-end tests:

```bash
npx playwright install
npx playwright test
```

---

## 7. Quick Reference

### 7.1 Essential Commands

| Command | Description |
|---------|-------------|
| `pip install -r requirements.txt` | Install Python dependencies |
| `npm install` | Install Node.js dependencies |
| `ollama pull llama3.2:3b` | Download AI model |
| `python api_server.py` | Start backend server |
| `npm run dev` | Start frontend dev server |
| `python main.py --demo` | Run CLI demo |
| `npm run build` | Build frontend for production |

### 7.2 File Structure Overview

```
Indogap/
├── api_server.py          # FastAPI backend entry point
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
├── setup.sh               # Automated setup script
├── mini_services/         # Core Python modules
│   ├── llm/              # AI/LLM integration
│   ├── scrapers/         # Web scraping modules
│   ├── scoring/          # Opportunity scoring
│   ├── database/         # Data persistence
│   └── mvp_generator/    # MVP specification generation
├── src/                   # Next.js frontend
│   ├── app/              # App router pages
│   ├── components/       # React components
│   └── hooks/            # Custom React hooks
└── prisma/               # Database schema
```

### 7.3 Troubleshooting Common Issues

#### 7.3.1 Ollama Not Available

**Error:** `"ollama_available": false`

**Solution:** Ensure Ollama is installed and running. Start Ollama with:

```bash
ollama serve
```

Verify models are downloaded:

```bash
ollama list
```

#### 7.3.2 Import Errors

**Error:** `ModuleNotFoundError: No module named 'mini_services...'`

**Solution:** Run Python from the project root directory:

```bash
cd /path/to/Indogap
python api_server.py
```

#### 7.3.3 Port Already in Use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:** Use a different port:

```bash
python api_server.py --port 8001
```

Or stop the process using the port:

```bash
lsof -ti:8000 | xargs kill -9
```

#### 7.3.4 Out of Memory

**Error:** AI models fail to load or system becomes unresponsive

**Solution:** Reduce the number of parallel Ollama requests by setting:

```bash
export OLLAMA_NUM_PARALLEL=1
```

Or use smaller models:

```bash
ollama pull llama3.2:3b  # Uses ~2GB RAM instead of ~5GB for llama3.1:8b
```

---

## 8. Conclusion

IndoGap represents a sophisticated AI-powered platform for identifying market opportunities in the Indian startup ecosystem. The application successfully combines web scraping, machine learning, local AI inference, and a modern web interface to deliver valuable insights for entrepreneurs and investors.

The identified bugs and issues documented in this report are primarily related to defensive programming practices, configuration management, and dependency handling. Addressing these issues will improve the application's reliability, security, and maintainability. The critical GPU index error should be addressed to prevent crashes on systems without dedicated graphics cards. The CORS configuration should be tightened before any production deployment to prevent unauthorized API access.

For hosting, the application's unique requirement for local AI processing limits truly free deployment options. The recommended approach combines Vercel for the frontend and Railway for the backend on their respective free tiers. This provides a functional application for development and demonstration purposes, while AI-powered features require either local execution or paid GPU hosting services.

Future development priorities should focus on improving error handling, adding comprehensive test coverage, documenting the configuration options more thoroughly, and potentially implementing cloud-based AI alternatives that would enable true cloud hosting without requiring local Ollama instances.

---

*Documentation generated for IndoGap project version 1.0.0*
*Last updated: January 2026*
