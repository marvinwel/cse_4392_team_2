# Project 2 — UTA AI Advisor

## Overview

UTA AI Advisor is an AI-powered academic advising application that helps students get course information, check prerequisites, and generate degree plans.

The Chat UI is built with Streamlit and automatically deployed to AWS EC2 using GitHub Actions and Docker.

## How to Push Changes

### Step 1 — Open the project

Open your terminal and navigate to the GitHub repository.

```bash
cd team-projects
```

### Step 2 — Make your changes

Update the files inside:

```text
project2/chat-ui/
```

### Step 3 — Push your changes

Run these commands:

```bash
git add project2/chat-ui/
git commit -m "Update Chat UI"
git push origin main
```

That's it! GitHub Actions will automatically build and deploy the updated Chat UI to AWS EC2.


## How Automatic Deployment Works

```text
Push Code to GitHub
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
Deploy to AWS EC2
        |
        v
Start Streamlit Container
        |
        v
Chat UI Updated
```


```
## Important Notes

- Always push Chat UI changes to the `main` branch to trigger deployment.
- Only changes inside `project2/chat-ui/` or the Chat UI workflow file automatically trigger this pipeline.
- GitHub Actions handles Docker builds, ECR uploads, and EC2 deployment automatically.