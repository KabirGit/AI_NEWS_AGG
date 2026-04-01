# 🧠 AI Personalized News Aggregator

A production-ready AI-powered news aggregation system that ingests, ranks, summarizes, and delivers personalized news using a modular, containerized architecture.

---

## 🚀 Features

* 📡 **RSS Ingestion Pipeline** — Fetches and normalizes news from multiple sources
* 🧠 **Recommendation Engine** — TF-IDF + cosine similarity + recency weighting
* ✂️ **Summarization** — Extractive summarization (OpenAI optional)
* 📧 **Email Digest** — Personalized daily news via email
* 🖥️ **Interactive UI** — Streamlit-based user interface
* 🗄️ **Database Layer** — PostgreSQL with SQLAlchemy ORM
* ⚙️ **Background Scheduler** — Automated daily pipeline execution

---

## 🏗️ Architecture

* **Frontend**: Streamlit
* **Backend**: Python (modular services)
* **Database**: PostgreSQL
* **ML Layer**: Scikit-learn (TF-IDF + similarity)
* **Containerization**: Docker + Docker Compose
* **Deployment**: Render (Web Service + Background Worker)

---

## ⚙️ Local Development (Docker)

### 1. Clone repo

```bash
git clone https://github.com/<KabirGit>/<AI_NEWS_AGG>.git
cd <repo-name>
```

### 2. Setup environment

```bash
cp .env.example .env
```

Update `.env`:

```env
DATABASE_URL=postgresql://postgres:password@db:5432/news_db
RESEND_API_KEY=your_key
EMAIL_FROM=your_email
```

### 3. Run system

```bash
docker-compose up --build
```

### 4. Access UI

```
http://localhost:8501
```

---

## 🧪 Local (Without Docker)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set environment

```bash
export DATABASE_URL=postgresql://localhost:5432/news_db
```

### Run services

**UI:**

```bash
streamlit run app.py
```

**Scheduler:**

```bash
python main.py
```

---

## ☁️ Production Deployment (Render)

### Services

| Service        | Description                 |
| -------------- | --------------------------- |
| Web Service    | Streamlit UI                |
| Background Job | Scheduler pipeline          |
| Database       | Managed PostgreSQL (Render) |

---

### Deployment Steps

1. Push code to GitHub
2. Create PostgreSQL on Render
3. Deploy:

   * Web Service → `streamlit run app.py`
   * Worker → `python main.py`
4. Set environment variables:

   ```
   DATABASE_URL
   RESEND_API_KEY
   EMAIL_FROM
   ```

---

## 🔑 Environment Variables

```env
DATABASE_URL=
RESEND_API_KEY=
EMAIL_FROM=
OPENAI_API_KEY=
APP_ENV=local
LOG_LEVEL=INFO
```

---

## 📊 Key Components

* **RSS Fetcher** — Ingests and cleans feed data
* **Recommender** — Ranks articles using hybrid scoring
* **Summarizer** — Generates concise summaries
* **Email Service** — Sends daily digest
* **Scheduler** — Automates full pipeline

---

## 🧠 Design Highlights

* Environment-driven configuration
* Stateless services (cloud-ready)
* Modular architecture (scalable + testable)
* Idempotent ingestion (deduplication via DB constraints)
* Separation of concerns (UI vs worker)

---

## 📌 Future Improvements

* User interaction tracking (click-based personalization)
* Real-time streaming (Kafka / queues)
* Advanced NLP summarization (LLMs)
* Frontend upgrade (React dashboard)

---

## 📄 License

MIT License

---

## 👤 Author

<Kabir Talbhandare>

---
