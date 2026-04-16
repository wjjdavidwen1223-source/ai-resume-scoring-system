# AI Resume Scoring System

## Overview
This project is a Python-based system that analyzes candidate resumes and evaluates their fit for a given job using structured scoring logic.

It simulates a simplified recruiting evaluation workflow by transforming candidate information into a standardized, data-driven scoring framework to support consistent decision-making.

---

## Features
- Processes and structures candidate data using pandas  
- Matches candidate skills against defined job requirements  
- Calculates a score based on skill alignment and experience  
- Ranks candidates from strongest to weakest fit  
- Produces a clear and comparable evaluation output across multiple candidates  

---

## Tech Stack
- Python  
- pandas  

---

## How It Works
The system assigns:
- +2 points for each matching required skill  
- +1 point per year of relevant experience  

Candidates are then ranked based on their total score to identify the best fit for a given role.

---

## Example Use Case
Given a dataset of candidates and a job with required skills (e.g., Relationship Banker roles in banking institutions), the system evaluates each candidate and generates a ranked output.

This output can be used to support:
- Resume screening  
- Candidate comparison  
- Early-stage hiring decisions  

---

## Realistic Example (Relationship Banker Role)

### Job Requirements
- Skills: Customer Service, Sales, Relationship Management, Financial Products  
- Experience: 2+ years preferred  

### Candidate Example

| Name     | Skills                                             | Experience |
|----------|--------------------------------------------------|------------|
| Alex     | Customer Service, Sales, Relationship Management | 3 years    |
| Brian    | Retail Sales, Communication, Problem Solving     | 2 years    |
| Cathy    | Banking, Financial Products, Client Advisory     | 5 years    |

### Scoring Logic Applied
- +2 points per matching required skill  
- +1 point per year of experience  

### Output

| Name     | Score | Decision            |
|----------|------|---------------------|
| Cathy    | 11   | Strong Fit          |
| Alex     | 9    | Good Fit            |
| Brian    | 6    | Needs Improvement   |

This example demonstrates how the system standardizes candidate evaluation for a Relationship Banker role.

---

## Impact
- Standardizes candidate evaluation using consistent scoring logic  
- Reduces subjective bias in early-stage screening  
- Improves efficiency in comparing multiple candidates  

---

## Purpose
This project demonstrates:
- Applied AI workflow thinking in recruiting contexts  
- Structured and scalable decision-making logic  
- Data-driven candidate evaluation using Python  
- Translation of real-world recruiting tasks into automated systems  

---

## Demo
See `resume_scoring.py` for a sample implementation and output.
