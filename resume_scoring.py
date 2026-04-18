import pandas as pd

INTERVIEW_THRESHOLD = 15
HOLD_THRESHOLD = 11
MAX_SCORE = 22

REQUIRED_SKILLS = [
    "sales",
    "communication",
    "customer service",
    "banking",
    "financial",
    "relationship management",
    "crm",
    "client service",
    "cross-selling",
    "upselling",
]

CORE_SKILLS = {"sales", "communication", "customer service"}


def safe_float(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def score_sales_experience(years):
    years = safe_float(years)
    if years >= 3:
        return 4
    elif years >= 2:
        return 3
    elif years >= 1:
        return 2
    return 0


def score_customer_service_experience(years):
    years = safe_float(years)
    if years >= 3:
        return 3
    elif years >= 2:
        return 2
    elif years >= 1:
        return 1
    return 0


def score_banking_experience(banking_exp):
    if pd.isna(banking_exp):
        return 0
    value = str(banking_exp).strip().lower()
    if value in ["yes", "y", "true", "1"]:
        return 4
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
    if "crm" in matched:
        score += 1
    if "client service" in matched:
        score += 1
    if "cross-selling" in matched or "upselling" in matched:
        score += 1

    return min(score, 6), matched


def stage_from_decision(decision):
    if decision == "Interview":
        return "Recruiter Phone Screen"
    elif decision == "Hold":
        return "Pipeline Hold"
    return "Closed / Reject"


def recruiter_signal(decision, score):
    if decision == "Interview" and score >= 17:
        return "🔥 High Priority"
    elif decision == "Interview":
        return "✅ Interview Ready"
    elif decision == "Hold":
        return "⚠️ Keep Warm"
    return "❌ Likely Rejected"


def follow_up_due(days_in_pipeline, decision):
    days = safe_float(days_in_pipeline)
    if decision == "Interview" and days >= 1:
        return "Yes"
    if decision == "Hold" and days >= 3:
        return "Yes"
    if decision == "Reject" and days >= 2:
        return "Yes"
    return "No"


def next_action(decision, follow_up_due_flag):
    if decision == "Interview":
        return "Schedule recruiter screen"
    elif decision == "Hold" and follow_up_due_flag:
        return "Send pipeline update"
    elif decision == "Hold":
        return "Review later / compare against pool"
    return "Send rejection note"


def priority_level(decision, score):
    if decision == "Interview" and score >= 17:
        return "High"
    elif decision == "Interview":
        return "Medium"
    elif decision == "Hold":
        return "Medium"
    return "Low"


def build_reason_and_improvement(
    decision,
    education_score,
    banking_score,
    sales_years,
    service_years,
    matched_skills,
):
    matched = set(matched_skills)
    reasons = []
    improvements = []

    if education_score == -999:
        reasons.append("Does not meet minimum education requirement.")
        improvements.append("Meet the minimum education requirement for the role.")

    if banking_score == 0:
        reasons.append("No clear banking or financial-related experience.")
        improvements.append("Highlight teller, branch, banking, finance, or account-related exposure.")

    if sales_years < 2:
        reasons.append("Sales experience is below preferred threshold.")
        improvements.append("Add measurable sales outcomes such as quotas, targets, or conversion metrics.")

    if service_years < 2:
        reasons.append("Customer-facing experience is below preferred threshold.")
        improvements.append("Emphasize client-facing work, issue resolution, onboarding, scheduling, or service impact.")

    if "sales" not in matched:
        reasons.append("Resume does not clearly signal sales experience.")
        improvements.append("Use stronger sales wording such as upselling, cross-selling, quotas, conversions, or target achievement.")

    if "communication" not in matched:
        reasons.append("Communication signal is not strong enough.")
        improvements.append("Add client communication, relationship management, or stakeholder interaction examples.")

    if "customer service" not in matched:
        reasons.append("Customer-facing signal is weak in the resume wording.")
        improvements.append("Include customer-facing responsibilities and service-related outcomes more explicitly.")

    if decision == "Interview":
        reasons = ["Strong fit across role-relevant experience, communication, and operational readiness."]
        improvements = ["Keep quantified achievements and finance-related language visible for recruiter review."]

    if decision == "Hold" and not reasons:
        reasons = ["Candidate shows potential but is missing one or more strong-match signals."]
        improvements = ["Strengthen role alignment with more explicit sales, service, or banking indicators."]

    if decision == "Reject" and not reasons:
        reasons = ["Candidate does not currently meet enough core role requirements."]
        improvements = ["Clarify experience, increase keyword alignment, and add measurable impact."]

    return " ".join(reasons), " ".join(improvements)


def generate_message(name, decision, next_step):
    first_name = str(name).split()[0] if str(name).strip() else "there"

    if decision == "Interview":
        return (
            f"Hi {first_name}, thank you for your application. "
            f"We were impressed with your background and would like to move you forward to the next step. "
            f"Next step: {next_step}."
        )
    elif decision == "Hold":
        return (
            f"Hi {first_name}, thank you for your application. "
            f"We appreciate your background and would like to keep your profile in consideration while we continue our review. "
            f"We will follow up with updates as the process moves forward."
        )
    else:
        return (
            f"Hi {first_name}, thank you for your interest. "
            f"After review, we will not be moving forward at this time. "
            f"We appreciate your time and encourage you to apply again in the future if relevant opportunities arise."
        )


def decision_from_score(score, education_score, matched_skills, banking_score, sales_years, service_years):
    matched = set(matched_skills)

    if education_score == -999:
        return "Reject"

    core_match_count = len(CORE_SKILLS.intersection(matched))

    if core_match_count == 0 and sales_years < 1 and service_years < 1:
        return "Reject"

    if (
        education_score >= 2
        and banking_score >= 4
        and sales_years >= 2
        and service_years >= 2
        and "sales" in matched
        and "communication" in matched
        and score >= INTERVIEW_THRESHOLD
    ):
        return "Interview"

    if score >= HOLD_THRESHOLD:
        return "Hold"

    return "Reject"


def run_screening(df):
    result = df.copy()

    defaults = {
        "Name": "",
        "Role": "Relationship Banker",
        "Sales_Years": 0,
        "Customer_Service_Years": 0,
        "Banking_Experience": "No",
        "Education": "",
        "Skills": "",
        "Days_In_Pipeline": 0,
        "Candidate_Response_Status": "No Response",
        "Customer_Facing_Evidence": "",
        "Sales_Evidence": "",
        "Banking_Evidence": "",
    }

    for col, default_val in defaults.items():
        if col not in result.columns:
            result[col] = default_val

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
            safe_float(row["Sales_Years"]),
            safe_float(row["Customer_Service_Years"]),
        ),
        axis=1,
    )

    result["Pipeline_Stage"] = result["Decision"].apply(stage_from_decision)
    result["Recruiter_Signal"] = result.apply(
        lambda row: recruiter_signal(row["Decision"], row["Score"]),
        axis=1,
    )
    result["Match_Score_%"] = ((result["Score"] / MAX_SCORE) * 100).round(1)

    explanations = result.apply(
        lambda row: build_reason_and_improvement(
            row["Decision"],
            row["Education_Score"],
            row["Banking_Score"],
            safe_float(row["Sales_Years"]),
            safe_float(row["Customer_Service_Years"]),
            row["Matched_Skills_List"],
        ),
        axis=1,
    )

    result["Reason"] = explanations.apply(lambda x: x[0])
    result["Improvement"] = explanations.apply(lambda x: x[1])

    result["Follow_Up_Due"] = result.apply(
        lambda row: follow_up_due(row["Days_In_Pipeline"], row["Decision"]),
        axis=1,
    )

    result["Next_Action"] = result.apply(
        lambda row: next_action(row["Decision"], row["Follow_Up_Due"] == "Yes"),
        axis=1,
    )

    result["Priority"] = result.apply(
        lambda row: priority_level(row["Decision"], row["Score"]),
        axis=1,
    )

    result["Generated_Message"] = result.apply(
        lambda row: generate_message(row["Name"], row["Decision"], row["Next_Action"]),
        axis=1,
    )

    result = result.drop(columns=["Matched_Skills_List"])
    result = result.sort_values(by=["Priority", "Score"], ascending=[True, False]).reset_index(drop=True)

    return result
