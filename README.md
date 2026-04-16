# 🚀 Machine Learning-Based Resume Ranking System

## 📌 Overview
This project is a Python-based system that evaluates candidate-job fit by transforming unstructured resume data into a structured scoring framework.

It models candidate evaluation as a **ranking and classification problem**, enabling consistent, data-driven comparison across multiple candidates.

---

## 🧠 Key Concepts
- Feature engineering from unstructured data  
- Rule-based scoring as a baseline model  
- Candidate ranking and classification  
- Handling real-world data variability  

---

🗄️ Data Extraction (SQL Integration)

Candidate data is first queried using SQL to simulate extraction from a structured database, then processed using Pandas.

SELECT 
  candidate_id,
  skills,
  years_experience,
  job_required_skills
FROM candidates
WHERE years_experience IS NOT NULL;

This step reflects how real-world systems retrieve and filter structured data before downstream processing.

---

## ⚙️ Features
- Processes and structures candidate data using **Pandas**  
- Matches candidate skills against job requirements  
- Computes scores based on **skill alignment and experience**  
- Ranks candidates from strongest to weakest fit  
- Produces standardized outputs for consistent evaluation  

---

## 🧮 Scoring Model
- **+2 points** per matching required skill  
- **+1 point** per year of relevant experience  

---

## 📊 Example Output

| Name  | Score | Decision          |
|------|------|------------------|
| Cathy | 11   | Strong Fit        |
| Alex  | 9    | Good Fit          |
| Brian | 6    | Needs Improvement |

---

## 🧪 Real-World Validation
- Evaluated system using **20+ real candidate profiles**  
- Tested across **50+ simulated scenarios**  
- Identified edge cases such as:
  - Strong candidates under-ranked due to missing keywords  
  - Inconsistent resume formatting affecting evaluation  
- Refined scoring logic to improve **consistency and robustness**  

---

## 🛠️ Tech Stack
- Python  
- Pandas  
- scikit-learn  

---

## 📁 Project Structure

resume-ranking-system/
│── resume_scoring.py
│── data/
│ └── sample_candidates.csv
│── README.md


---

## ▶️ How to Run

pip install pandas scikit-learn
python resume_scoring.py


---

## 💡 Example Use Case
Given a dataset of candidates and job requirements, the system:
1. Extracts structured features  
2. Computes candidate scores  
3. Ranks candidates  
4. Outputs standardized decisions  

---

## 🤖 ML Extension
This project includes a baseline supervised machine learning model using Logistic Regression.

The workflow includes:
- preprocessing structured candidate features  
- one-hot encoding categorical variables  
- splitting data into training and test sets  
- training a classification model to predict candidate fit  
- evaluating performance using **accuracy, precision, and recall**  

**Model Performance:**
- Accuracy: ~0.80  

This extension demonstrates the transition from **rule-based scoring → data-driven ML approach**.

---

## 📈 Impact
- Standardizes candidate evaluation  
- Reduces subjective bias in screening  
- Improves efficiency in comparing candidates  
- Simulates real-world decision workflows  

---

## 🔄 Future Improvements
- Improve feature engineering for better predictive performance  
- Integrate NLP for resume text parsing  
- Expand dataset for more robust evaluation  
- Explore advanced models (e.g., Random Forest, Gradient Boosting)  

---

## 🎯 Purpose
This project demonstrates:
- Translating real-world workflows into data-driven systems  
- Structured decision-making using Python  
- Foundations for machine learning-based ranking systems  

---

## 📌 Demo
See `resume_scoring.py` for a sample implementation and output.
