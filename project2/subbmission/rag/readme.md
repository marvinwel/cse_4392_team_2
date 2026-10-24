# UTA AI Advisor — RAG Pipeline

This directory contains the Retrieval-Augmented Generation (RAG) document ingestion pipeline for the UTA AI Advisor project.

The pipeline uploads academic documents from GitHub to Amazon S3, where they will be processed and stored as embeddings in ChromaDB for academic advising queries.




## Directory Structure

```text
rag/
├── README.md
├── documents/
│   ├── cse_undergraduate_catalog.pdf
│   ├── degree_requirements.docx
│   ├── course_prerequisites.csv
│   └── academic_policies.txt
└── lambda/
    └── lambda_function.py
```

All academic reference documents must be placed inside `rag/documents/`.

## Supported Document Formats


| Format | Extension |
|---|---|
| PDF | `.pdf` |
| Microsoft Word | `.docx` |
| Plain Text | `.txt` |
| Markdown | `.md` |
| CSV | `.csv` |
| JSON | `.json` |



## Recommended Documents

- UTA undergraduate course catalogs
- Course descriptions and prerequisites
- Degree plans and graduation requirements
- Academic policies and regulations
- Course schedules and credit-hour requirements

Use authorized, current academic references. Do not upload confidential student information, credentials, or other sensitive data.

## How to Add and Push Documents

### 1. Pull the Latest Changes

Run these commands from the root of the Git repository:

```bash
git checkout main
git pull origin main
```

### 2. Add Documents

Copy the documents into:

```text
project2/rag/documents/
```

### 3. Stage the Documents

```bash
git add project2/rag/documents/
```

### 4. Commit Changes

```bash
git commit -m "Add academic documents for RAG"
```

### 5. Push to GitHub

```bash
git push origin main
```

If working on a feature branch, create a pull request and merge into `main` after review.



## Architecture

```text
GitHub Repository
       |
       v
GitHub Actions
       |
       v
Amazon S3
       |
       v
AWS Lambda
  - Extract text
  - Split into chunks
  - Generate embeddings
       |
       v
ChromaDB (Vector Database)
```


## Document Guidelines

- Use descriptive filenames.
- Prefer text-based PDFs rather than scanned PDFs.
- Keep academic references current and accurate.
- Avoid duplicate documents.
- Do not upload confidential information.
- Do not assume an S3 upload means a document has already been embedded.
- Document deletions are not automatically synchronized to S3 or ChromaDB.


**Project:** CSE 4392 — UTA AI Advisor

