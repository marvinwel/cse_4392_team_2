# Team Project 1 – Domain-Specific Phrase Identification & Classification

## CSE 4392 – Software Engineering with Generative AI

**The University of Texas at Arlington**  
**Fall 2026**  
**Team 2**

---

## 👥 Team Members

- Marvin Wellington
- Joseph Fitchett
- Emily Ford
- Sarthak Wadhawan
- Ryan Patterson

---

## 📌 Project Overview

Team Project 1 focuses on using a **Large Language Model (LLM)** to identify and classify domain-specific phrases from software system descriptions.

The project applies an **evolutionary prompt optimization process** to iteratively improve the prompts and methodology used by the LLM.

The goal is to achieve an **F1 score of at least 97%** by improving the prompt across multiple domains.

---

## 🎯 Project Objective

The objective is to develop and optimize a prompt that allows an LLM to accurately identify domain-specific phrases and classify them into the following categories:

- **Classes**
- **Attributes of Classes**
- **Relationships between Classes**

The prompt is improved through multiple experiments by comparing the LLM-generated results against the provided ground truth.

---

## 🔄 Optimization Process

The project follows an iterative prompt optimization process.

```text id="f3gr8q"
Initial Prompt
      │
      ▼
Run LLM
      │
      ▼
Extract & Classify Phrases
      │
      ▼
Compare Against Ground Truth
      │
      ▼
Calculate Evaluation Metrics
      │
      ▼
Analyze Errors
      │
      ▼
Improve Prompt
      │
      ▼
Run Again
```

This process is repeated until the prompt produces sufficiently accurate results.

---

## 📚 Domains

Prompt optimization is performed using the following domains in order:

### 1. Library

The **Library** domain is used as the first stage of prompt development and optimization.

Results from each run are evaluated against the Library ground truth, and errors are analyzed to improve the prompt.

---

### 2. Car Rental

After improving the prompt using the Library domain, the optimized methodology is applied to the **Car Rental** domain.

The results are again compared against the provided ground truth to identify:

- Missing phrases
- Incorrect phrases
- Incorrect classifications
- Unnecessary extracted phrases

These results are used to further improve the prompt.

---

### 3. National Trade Show Service (NTSS)

The final optimized prompt is evaluated using the **National Trade Show Service (NTSS)** domain.

This domain is used to determine how well the optimized prompt and methodology generalize to another software system description.

---

## 🧠 Phrase Classification

Identified domain-specific phrases are classified according to their role within the software domain.

### Classes

Classes represent major domain entities or concepts.

Examples may include:

```text id="p3p7x4"
Customer
Vehicle
Reservation
Rental Location
```

### Attributes

Attributes describe properties associated with classes.

Examples may include:

```text id="s20sqc"
Customer Name
Vehicle Model
Rental Price
Reservation Date
```

### Relationships

Relationships describe associations between domain concepts.

Examples may include relationships such as:

```text id="kt04sz"
Customer makes Reservation

Reservation is associated with Vehicle

Rental Location contains Vehicles
```

---

## 📊 Evaluation

The quality of the LLM-generated results is evaluated using:

- **Precision**
- **Recall**
- **F1 Score**

### Precision

Precision measures how many phrases identified by the LLM are actually correct.

```text id="tvhh7c"
Precision = TP / (TP + FP)
```

### Recall

Recall measures how many of the expected phrases were successfully identified.

```text id="22fr2q"
Recall = TP / (TP + FN)
```

### F1 Score

The F1 score balances precision and recall.

```text id="3w4rgv"
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

Where:

```text id="6wxgnc"
TP = True Positives
FP = False Positives
FN = False Negatives
```

### Target

The optimization goal for the project is:

```text id="p8v57v"
F1 Score ≥ 97%
```

---

## 🧪 Experiment Process

Each experiment generally follows these steps:

1. Provide the domain description to the LLM.
2. Provide the current prompt and classification rules.
3. Ask the LLM to identify and classify domain-specific phrases.
4. Record the generated results.
5. Compare the results against the ground truth.
6. Calculate Precision, Recall, and F1 Score.
7. Identify false positives and false negatives.
8. Analyze classification errors.
9. Modify the prompt or methodology.
10. Run the experiment again.

The process continues until the prompt reaches the desired performance or no further meaningful improvements are identified.

---

## 📁 Project Structure

```text id="79b4t8"
project1/
│
├── README.md
│
├── library/
│   ├── prompts/
│   ├── runs/
│   └── results/
│
├── car-rental/
│   ├── prompts/
│   ├── runs/
│   └── results/
│
├── ntss/
│   ├── prompts/
│   ├── runs/
│   └── results/
│
└── final/
    ├── final-prompt/
    └── final-results/
```

The directory structure may be adjusted as experiments and project deliverables are completed.

---

## 📈 Experiment Tracking

Each experiment should record information such as:

| Run | Domain | Prompt Version | Precision | Recall | F1 Score |
|---|---|---|---:|---:|---:|
| 1 | Library | V1 | TBD | TBD | TBD |
| 2 | Library | V2 | TBD | TBD | TBD |
| 3 | Car Rental | V2 | TBD | TBD | TBD |
| 4 | Car Rental | V3 | TBD | TBD | TBD |
| 5 | NTSS | Final | TBD | TBD | TBD |

Results will be updated as experiments are completed.

---

## 🏁 Final Goal

The final goal is to produce an optimized prompt and methodology capable of accurately identifying and classifying domain-specific phrases from software system descriptions.

The final solution should demonstrate how **prompt engineering, iterative experimentation, and quantitative evaluation** can improve the performance of Large Language Models when applied to software engineering activities.