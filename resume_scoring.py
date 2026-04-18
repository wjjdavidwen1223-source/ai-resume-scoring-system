import pandas as pd

INTERVIEW_THRESHOLD = 14
HOLD_THRESHOLD = 10
MAX_SCORE = 18  # used for Match Score %

REQUIRED_SKILLS = [
    "sales",
    "communication",
    "customer service",
    "banking",
    "financial",
    "relationship management",
]

CORE_SKILLS = {"sales", "communication", "customer service"}


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

    # cap to avoid keyword stuffing
    return min(score, 5), matched


def recruiter_signal(score, decision):
    if decision == "Interview":
        return "✅ Strong Interview Candidate"
    elif decision == "Hold":
        return "⚠️ Borderline / Hold for Review"
    return "❌ Likely Rejected"


def build_reason_and_improvement(
    decision,
    education_score,
    banking_exp_score,
    sales_years,
    customer_service_years,
    matched_skills,
):
    matched_set = set(matched_skills)

    reasons = []
    improvements = []

    if education_score == -999:
        reasons.append("Does not meet minimum education requirement.")
        improvements.append("Meet the minimum education requirement listed in the job posting.")

    if banking_exp_score == 0:
        reasons.append("No clear banking or financial-related experience.")
        improvements.append("Highlight any banking, financial, teller, branch, or client account exposure.")

    if sales_years < 1:
        reasons.append("Limited direct sales experience.")
        improvements.append("Add measurable sales achievements or customer acquisition results.")
    elif sales_years < 2:
        reasons.append("Sales experience is below strong-interview level.")
        improvements.append("Strengthen sales impact with numbers such as quotas, targets, or conversion rates.")

    if customer_service_years < 2:
        reasons.append("Customer service experience is below preferred level.")
        improvements.append("Emphasize customer-facing responsibilities, conflict resolution, and service metrics.")

    if "sales" not in matched_set:
        reasons.append("Resume does not clearly show sales-related skills.")
        improvements.append("Use stronger sales-related wording such as cross-selling, upselling, or target achievement.")

    if "communication" not in matched_set:
        reasons.append("Communication strengths are not clearly reflected.")
        improvements.append("Add examples of client communication, relationship building, or stakeholder interaction.")

    if "customer service" not in matched_set:
        reasons.append("Customer service signal is weak in the resume wording.")
        improvements.append("Include customer-facing tasks, service outcomes, and support responsibilities.")

    if decision == "Interview":
        reasons = ["Strong fit across experience, education, and role-specific signals."]
        improvements = ["Continue tailoring the resume with quantified achievements and relevant banking language."]

    if decision == "Hold" and not reasons:
        reasons = ["Candidate shows potential but is missing one or more strong-match signals."]
        improvements = ["Refine the resume to better align with the role’s required experience and skills."]

    if decision == "Reject" and not reasons:
        reasons = ["Candidate does not currently meet enough core role requirements."]
        improvements = ["Add clearer role-relevant experience, stronger keywords, and quantified impact."]

    return " ".join(reasons), " ".join(improvements)


def decision_from_score(score, education_score, matched_skills, banking_exp_score, sales_years, customer_service_years):
    matched_set = set(matched_skills)

    # hard reject: no minimum education
    if education_score == -999:
        return "Reject"

    # hard reject: no meaningful customer-facing / sales signal
    if not CORE_SKILLS.intersection(matched_set) and sales_years < 1 and customer_service_years < 1:
        return "Reject"

    # strict interview rule
    if (
        education_score >= 2
        and banking_exp_score == 3
        and sales_years >= 2
        and customer_service_years >= 2
        and "sales" in matched_set
        and "communication" in matched_set
        and score >= INTERVIEW_THRESHOLD
    ):
        return "Interview"

    # hold rule
    if score >= HOLD_THRESHOLD:
        return "Hold"

    return "Reject"


def run_screening(df):
    result = df.copy()

    # required columns
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

    # scores
    result["Sales_Score"] = result["Sales_Years"].apply(score_sales_experience)
    result["Customer_Service_Score"] = result["Customer_Service_Years"].apply(score_customer_service_experience)
    result["Banking_Score"] = result["Banking_Experience"].apply(score_banking_experience)
    result["Education_Score"] = result["Education"].apply(score_education)

    skills_output = result["Skills"].apply(score_skills)
    result["Skills_Score"] = skills_output.apply(lambda x: x[0])
    result["Matched_Skills"] = skills_output.apply(lambda x: ", ".join(x[1]))
    result["Matched_Skills_List"] = skills_output.apply(lambda x: x[1])

    result["Score"] = (
        result["Sales_Score"]
        + result["Customer_Service_Score"]
        + result["Banking_Score"]
        + result["Education_Score"]
        + result["Skills_Score"]
    )

    result["Decision"] = result.apply(
        lambda row: decision_from_score(
            row["Score"],
            row["Education_Score"],
            row["Matched_Skills_List"],
            row["Banking_Score"],
            float(row["Sales_Years"]),
            float(row["Customer_Service_Years"]),
        ),
        axis=1,
    )

    result["Match_Score_%"] = ((result["Score"] / MAX_SCORE) * 100).round(1)
    result["Recruiter_Signal"] = result.apply(
        lambda row: recruiter_signal(row["Score"], row["Decision"]),
        axis=1,
    )

    explanations = result.apply(
        lambda row: build_reason_and_improvement(
            row["Decision"],
            row["Education_Score"],
            row["Banking_Score"],
            float(row["Sales_Years"]),
            float(row["Customer_Service_Years"]),
            row["Matched_Skills_List"],
        ),
        axis=1,
    )

    result["Reason"] = explanations.apply(lambda x: x[0])
    result["Improvement"] = explanations.apply(lambda x: x[1])

    # drop helper column
    result = result.drop(columns=["Matched_Skills_List"])

    # sort highest score first
    result = result.sort_values(by="Score", ascending=False).reset_index(drop=True)

    return result
