# Project 2 — UTA AI Advisor

## Overview

UTA AI Advisor is an AI-powered academic advising application for University of Texas at Arlington (UTA) students.

Students can ask questions about courses, prerequisites, schedules, and degree requirements.

The application uses **Streamlit, LangChain, RAG, and Amazon Bedrock** to provide AI-generated answers.

## Project Features

- Ask questions about UTA courses
- Check course prerequisites
- Check schedule conflicts
- Generate degree plans
- Retrieve academic information using RAG
- Student login using Amazon Cognito (planned)

## Technology Stack

| Component | Technology |
|---|---|
| Chat UI | Python, Streamlit |
| Backend | Python, LangChain |
| Generative AI | Amazon Bedrock |
| Embedding Model | Amazon Titan Embeddings V2 |
| Vector Database | ChromaDB |
| Academic Data | Amazon S3 |
| Structured Data | Database / SQL Tools |
| Hosting | Amazon EC2 |
| Containerization | Docker |
| CI/CD | GitHub Actions, Amazon ECR |

## Project Structure

```text
project2/
│
├── chat-ui/             # Streamlit frontend
│
├── langchain/           # LangChain backend
│
├── rag/                 # RAG pipeline and embeddings
│
└── README.md            # Main project documentation
```

## Application Architecture

```text
Student
   |
   v
Streamlit Chat UI (EC2)
   |
   v
LangChain Backend (EC2)
   |
   v
Question Router
   |
   +---------------------+
   |                     |
   v                     v
RAG Pipeline          SQL Tools
   |                     |
   v                     v
Embedding Model       Student Data
   |                     |
   v                     |
ChromaDB                  |
   |                     |
   +----------+----------+
              |
              v
     LangChain Backend
              |
              v
      Amazon Bedrock
              |
              v
       AI Response
              |
              v
      Streamlit Chat UI
```

## RAG Pipeline

Academic documents are stored in Amazon S3 and processed into vector embeddings for retrieval.

```text
Academic Documents (S3)
          |
          v
       AWS Lambda
          |
          v
   Embedding Model
          |
          v
       ChromaDB
```

When a student asks a question, LangChain retrieves relevant information from ChromaDB and sends the context to Amazon Bedrock to generate an answer.

## GitHub Deployment Pipeline

The Chat UI is automatically deployed to AWS when changes are pushed to GitHub.

```text
Developer
   |
   | git add
   | git commit
   | git push
   v
GitHub (main branch)
   |
   v
GitHub Actions
   |
   v
Build Docker Image
   |
   v
Amazon ECR
   |
   v
AWS EC2
   |
   v
Updated Application
```

## How to Push Changes

From the repository root:

```bash
git add project2/
git commit -m "Update Project 2"
git push origin main
```

Only stage files you intend to commit. Do not include `.venv/`, `.env`, or installed dependencies.

## Run Chat UI Locally

Navigate to the Chat UI directory:

```bash
cd project2/chat-ui
```

Activate your virtual environment:

```bash
source .venv/bin/activate
```

Connect to the deployed LangChain backend.

Start Streamlit:

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

**Important:** The local Chat UI connects to the AWS backend. Questions may trigger Amazon Bedrock API calls and consume billable tokens.

## Project Components

### Chat UI

Provides the student-facing interface for asking questions and viewing AI responses.

See [Chat UI README](chat-ui/README.md).

### LangChain Backend

Handles student requests, routes questions, retrieves relevant data, and communicates with Amazon Bedrock.

### RAG Pipeline

Processes academic documents, creates vector embeddings, and stores them in ChromaDB for retrieval.

### Amazon Bedrock

Hosts the generative LLM used to produce final answers from the student's question and retrieved information.

## Important Notes

- The Chat UI and LangChain backend run as separate applications.
- ChromaDB is designed to run separately from the application servers.
- GitHub Actions automates the Chat UI deployment.
- Never commit virtual environments, credentials, or secrets.
- Amazon Bedrock usage can generate token-based charges.
- Degree planning and other academic checks require the appropriate backend data and logic.

## Team

**UTA CSE — Team 2**

University of Texas at Arlington