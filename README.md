# Job Recommendation System

An intelligent job recommendation system that collects job postings from online recruitment platforms, processes and stores job data, generates semantic embeddings, and provides personalized job recommendations using vector search and large language models.

## Features

* Automated job crawling pipeline using Airflow
* Data cleaning and preprocessing
* PostgreSQL data storage
* Semantic job search using embeddings and FAISS
* Personalized job recommendation engine
* Google OAuth authentication
* Search history tracking
* Career analytics and skill-gap analysis
* Local LLM integration via Ollama
* Dockerized deployment

---

## System Architecture

```text
Job Sources
      │
      ▼
Job Crawler
      │
      ▼
Data Cleaning
      │
      ▼
PostgreSQL Database
      │
      ├──────────────► Analytics Service
      │
      ▼
Embedding Generation
      │
      ▼
FAISS Vector Index
      │
      ▼
Recommendation Engine
      │
      ▼
FastAPI Backend
      │
      ▼
Frontend Application
```

---

## Technology Stack

### Backend

* FastAPI
* Python
* PostgreSQL
* Redis

### Data Pipeline

* Apache Airflow

### Machine Learning

* Sentence Transformers
* FAISS
* Ollama
* Embedding-based Retrieval

### Deployment

* Docker
* Docker Compose

---

## Project Structure

```text
.
├── dags/
├── frontend/
├── initdb/
├── src/
│   ├── api/
│   ├── crawl/
│   ├── ml/
│   ├── repositories/
│   ├── services/
│   ├── train/
│   └── core/
├── data/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Airflow Pipeline

The workflow consists of the following tasks:

1. crawl_jobs

   * Collect job postings from recruitment platforms

2. clean_jobs

   * Clean and normalize raw job data

3. load_to_database

   * Store processed jobs into PostgreSQL

4. train_model

   * Generate embeddings and build FAISS index

Pipeline Flow:

```text
crawl_jobs
      ↓
clean_jobs
      ↓
load_to_database
      ↓
train_model
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/bigbox1304/Job_Recommendation_System.git
cd Job_Recommendation_System
```

### Create Environment File

Create a `.env` file:

```env
SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
DATABASE_URL=
REDIS_HOST=
OLLAMA_HOST=
```

### Start Services

```bash
docker compose up -d
```

---

## API Modules

### Authentication

* Google OAuth Login

### Job Management

* Search Jobs
* Job Details

### Recommendation

* Skill-aware Recommendation
* Semantic Search

### Analytics

* Career Path Analysis
* Skill Gap Analysis

### History

* Search History Tracking

---

## Machine Learning Components

### Embedding Service

Generate vector representations for jobs and skills.

### FAISS Service

Fast similarity search for recommendation retrieval.

### Recommendation Model

Combines:

* Skill matching
* Semantic similarity
* User preferences

---

## Future Improvements

* Hybrid recommendation models
* User profile personalization
* Real-time recommendation updates
* Resume parsing
* Interview preparation assistant
* Multi-source job aggregation

---

## Author

Vu Nguyen

Graduation Project – Intelligent Job Recommendation System
