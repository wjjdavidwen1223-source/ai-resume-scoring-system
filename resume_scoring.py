import pandas as pd

INTERVIEW_THRESHOLD = 10
HOLD_THRESHOLD = 6

REQUIRED_SKILLS = [
    "sales",
    "communication",
    "customer service",
    "banking",
    "financial",
    "relationship management"
]

def score_sales_experience(years):
    years = float(years)
    if years >= 2:
        return 3
    elif years >= 1:
        return 2
    return 0

def score_customer_service_experience(years):
    years = float(years)
    if years >= 2:
        return 2
    return 0

def score_banking_experience(banking_exp):
    if pd.isna(banking_exp):
        return 0
    banking_exp = str(banking_exp).strip().lower()
    if banking_exp in ["yes", "y", "true", "1"]:
        return 3
    return 0

def score_education(education):
    if pd.isna(education):
        return -999

    education = str(education).lower()

    if "master" in education:
        return 3
    elif "bachelor" in education:
        return 2
    elif "high school" in education or "diploma" in education:
        return 0
    else:
        return -999

def score_skills(skills_text):
    if pd.isna(skills_text):
        return 0, []

    skills_text = str(skills_text).lower()
    matched = []

    for skill in REQUIRED_SKILLS:
        if skill in skills_text:
            matched.append(skill)

    score = 0
    if "sales" in matched:
        score += 2
    if "communication" in matched:
        score += 2
    if "customer service" in matched:
        score += 2
    if "banking" in matched or "financial" in matched:
        score += 2
    if "relationship management" in matched:
        score += 1

    return score, matched

def decision_from_score(score, education_score, matched_skills, banking_exp_score):
    if education_score == -999:
        return "Reject"

    must_have = {"sales", "communication", "customer service"}
    if not must_have.intersection(set(matched_skills)):
        return "Reject"

    # banking / financial exposure is strongly preferred for this version
    if banking_exp_score == 0 and score < INTERVIEW_THRESHOLD:
        return "Hold" if score >= HOLD_THRESHOLD else "Reject"

    if score >= INTERVIEW_THRESHOLD:
        return "Interview"
    elif score >= HOLD_THRESHOLD:
        return "Hold"
    else:
        return "Reject"

def run_screening(df):
    result = df.copy()

    if "Name" not in result.columns:
        result["Name"] = ""
    if "Sales_Years" not in result.columns:
        result["Sales_Years"] = 0
    if "Customer_Service_Years" not in result.columns:
        result["Customer_Service_Years"] = 0
    if "Banking_Experience" not in result.columns:
        result["Banking_Experience"] = "No"
    if "Education" not in result.columns:
        result["Education"] = ""
    if "Skills" not in result.columns:
        result["Skills"] = ""

    result["Sales_Score"] = result["Sales_Years"].apply(score_sales_experience)
    result["Customer_Service_Score"] = result["Customer_Service_Years"].apply(score_customer_service_experience)
    result["Banking_Score"] = result["Banking_Experience"].apply(score_banking_experience)
    result["Education_Score"] = result["Education"].apply(score_education)

    skills_output = result["Skills"].apply(score_skills)
    result["Skills_Score"] = skills_output.apply(lambda x: x[0])
    result["Matched_Skills"] = skills_output.apply(lambda x: ", ".join(x[1]))

    result["Score"] = (
        result["Sales_Score"] +
        result["Customer_Service_Score"] +
        result["Banking_Score"] +
        result["Education_Score"] +
        result["Skills_Score"]
    )

    result["Decision"] = result.apply(
        lambda row: decision_from_score(
            row["Score"],
            row["Education_Score"],
            row["Matched_Skills"].split(", ") if row["Matched_Skills"] else [],
            row["Banking_Score"]
        ),
        axis=1
    )

    return result
