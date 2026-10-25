# UTA AI Advisor — Chat UI

## Overview

The UTA AI Advisor is a chatbot that helps students ask questions about courses, prerequisites, and degree planning.

The Chat UI is built with **Python and Streamlit** and connects to a **LangChain backend** that uses Amazon Bedrock to generate AI responses.

The Chat UI is deployed to **AWS EC2** automatically using GitHub Actions and Docker.


## Run the Chat UI Locally

### Step 1 — Open the Chat UI directory

```bash
cd team-projects/project2/chat-ui
```

### Step 2 — Activate the Python virtual environment

```bash
source .venv/bin/activate
```

If the virtual environment doesn't exist, create it and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3 — Connect to the LangChain Backend

The local Chat UI is connected to the **deployed LangChain backend on AWS**, so you don't need to run the backend locally.


### Step 4 — Start Streamlit

```bash
streamlit run app.py
```

Open your browser:

**http://localhost:8501**

### Important Notes

- Local Streamlit runs on your computer.
- The LangChain backend runs separately on AWS.
- Questions sent from the local Chat UI are processed by the backend using Amazon Bedrock.
- **Amazon Bedrock usage is billed based on model usage.** Testing locally can still consume input and output tokens.
- Keep test questions and responses short to reduce token costs.
- Confirm the backend URL is still correct before running the app.




## How to Push Changes to GitHub

### Step 1 — Open the project

Open your terminal and navigate to the repository:

```bash
cd team-projects
```

### Step 2 — Make your changes

Update the code inside:

```text
project2/chat-ui/
```

### Step 3 — Add your changes

```bash
git add project2/chat-ui/
```

This stages the Chat UI files you changed.

### Step 4 — Commit your changes

```bash
git commit -m "Update Chat UI"
```

This saves your changes in Git.

### Step 5 — Push to GitHub

```bash
git push origin main
```

This uploads your changes to GitHub and triggers the deployment pipeline.

## Automatic Deployment Pipeline

```text
Developer
   |
   | git add
   | git commit
   | git push
   v
GitHub Repository (main)
   |
   v
GitHub Actions
   |
   v
Build Docker Image
   |
   v
Push Image to Amazon ECR
   |
   v
Deploy Image to AWS EC2
   |
   v
Start Streamlit Docker Container
   |
   v
Chat UI Updated
```
|

## How the Chat UI Works

```text
Student
   |
   v
Streamlit Chat UI (EC2)
   |
   v
LangChain Backend API
   |
   v
Amazon Bedrock (LLM)
   |
   v
LangChain Backend
   |
   v
Streamlit Displays Answer
```

## Important Notes

- Push changes to the `main` branch to trigger deployment.
- The pipeline runs when the configured Chat UI files or workflow are updated.
- GitHub Actions automatically builds and deploys the Docker container.
- Do not commit `.venv/`, Python dependencies, or `.env` files.
- The LangChain backend is deployed separately from the Chat UI.

## Quick Reference

Run these commands from the repository root whenever you update the Chat UI:

```bash
git add project2/chat-ui/
git commit -m "Update Chat UI"
git push origin main
```

**That's it!** GitHub Actions handles the deployment automatically.