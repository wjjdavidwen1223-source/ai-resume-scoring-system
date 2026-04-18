import re
import pandas as pd

SKILL_KEYWORDS = [
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

CUSTOMER_DIRECT_TERMS = [
    "customer service",
    "client service",
    "customer support",
    "guest services",
    "member services",
    "front desk",
    "help desk",
    "reception",
]

CUSTOMER_PEOPLE_TERMS = [
    "customer",
    "customers",
    "client",
    "clients",
    "guest",
    "guests",
    "patient",
    "patients",
    "visitor",
    "visitors",
    "member",
    "members",
    "user",
    "users",
    "family",
    "families",
    "students",
]

CUSTOMER_ACTION_TERMS = [
    "assisted",
    "helped",
    "supported",
    "served",
    "advised",
    "guided",
    "responded",
    "communicated",
    "interacted",
    "handled",
    "resolved",
    "addressed",
    "explained",
    "coordinated",
    "scheduled",
    "hosted",
    "welcomed",
    "greeted",
]

CUSTOMER_CONTEXT_TERMS = [
    "inquiries",
    "questions",
    "issues",
    "concerns",
    "requests",
    "appointments",
    "accounts",
    "service",
    "support",
    "onboarding",
    "check-in",
    "scheduling",
    "communications",
    "intake",
]

SALES_DIRECT_TERMS = [
    "sales",
    "selling",
    "upselling",
    "cross-selling",
    "quota",
    "revenue",
    "business development",
]

SALES_ACTION_TERMS = [
    "sold",
    "generated",
    "increased",
    "converted",
    "closed",
    "promoted",
    "recommended",
    "pitched",
    "marketed",
    "achieved",
    "exceeded",
]

SALES_CONTEXT_TERMS = [
    "target",
    "quota",
    "goal",
    "revenue",
    "conversion",
    "clients",
    "accounts",
    "products",
    "services",
]

BANKING_TERMS = [
    "bank",
    "banking",
    "teller",
    "relationship banker",
    "branch banker",
    "financial services",
    "credit union",
    "loan",
    "deposit",
    "branch",
    "account opening",
    "consumer banking",
    "retail banking",
]

COMMUNICATION_TERMS = [
    "communication",
    "communicated",
    "presented",
    "explained",
    "coordinated",
    "liaised",
    "interfaced",
    "stakeholders",
    "clients",
    "candidates",
]


def clean_lines(text: str) -> list[str]:
    raw_lines = text.splitlines()
    lines = []
    for line in raw_lines:
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def extract_name(text: str) -> str:
    lines = clean_lines(text)
    if not lines:
        return "Unknown"

    for line in lines[:5]:
        if "@" in line or re.search(r"\d{3}[-\s]?\d{3}[-\s]?\d{4}", line):
            continue
        if len(line) <= 80:
            return line

    return lines[0][:80]


def extract_education(text: str) -> str:
    lower = text.lower()

    if "master" in lower:
        return "Master"
    if "bachelor" in lower:
        return "Bachelor"
    if "high school" in lower or "diploma" in lower:
        return "High School"

    return ""


def detect_banking_experience(text: str):
    lower = text.lower()
    matched = [term for term in BANKING_TERMS if term in lower]

    if matched:
        return "Yes", ", ".join(sorted(set(matched))[:8])

    return "No", ""


def extract_skills(text: str) -> str:
    lower = text.lower()
    matched = []

    for skill in SKILL_KEYWORDS:
        if skill in lower:
            matched.append(skill)

    # inferred skills from evidence
    if infer_customer_facing_years(text)[0] >= 1 and "customer service" not in matched:
        matched.append("customer service")

    if infer_sales_years(text)[0] >= 1 and "sales" not in matched:
        matched.append("sales")

    if any(term in lower for term in COMMUNICATION_TERMS) and "communication" not in matched:
        matched.append("communication")

    if any(term in lower for term in BANKING_TERMS):
        if "banking" not in matched:
            matched.append("banking")
        if "financial" not in matched:
            matched.append("financial")

    return ", ".join(sorted(set(matched)))


def count_term_hits(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term in text)


def infer_customer_facing_years(text: str):
    lines = [normalize_text(line) for line in clean_lines(text)]
    evidence_lines = []

    for line in lines:
        direct_hit = any(term in line for term in CUSTOMER_DIRECT_TERMS)
        people_hit = any(term in line for term in CUSTOMER_PEOPLE_TERMS)
        action_hit = any(term in line for term in CUSTOMER_ACTION_TERMS)
        context_hit = any(term in line for term in CUSTOMER_CONTEXT_TERMS)

        if direct_hit or ((people_hit and action_hit) or (action_hit and context_hit)):
            evidence_lines.append(line)

    evidence_lines = list(dict.fromkeys(evidence_lines))
    evidence_count = len(evidence_lines)

    if evidence_count >= 4:
        years = 3
    elif evidence_count >= 2:
        years = 2
    elif evidence_count >= 1:
        years = 1
    else:
        years = 0

    evidence_preview = " | ".join(evidence_lines[:4])
    return years, evidence_preview


def infer_sales_years(text: str):
    lines = [normalize_text(line) for line in clean_lines(text)]
    evidence_lines = []

    for line in lines:
        direct_hit = any(term in line for term in SALES_DIRECT_TERMS)
        action_hit = any(term in line for term in SALES_ACTION_TERMS)
        context_hit = any(term in line for term in SALES_CONTEXT_TERMS)

        metric_hit = bool(re.search(r"\b\d+%|\$\d+|\bquota\b|\btarget\b|\brevenue\b", line))

        if direct_hit or (action_hit and context_hit) or (direct_hit and metric_hit):
            evidence_lines.append(line)

    evidence_lines = list(dict.fromkeys(evidence_lines))
    evidence_count = len(evidence_lines)

    if evidence_count >= 4:
        years = 3
    elif evidence_count >= 2:
        years = 2
    elif evidence_count >= 1:
        years = 1
    else:
        years = 0

    evidence_preview = " | ".join(evidence_lines[:4])
    return years, evidence_preview


def parse_resume_to_dataframe(text: str, role: str = "Relationship Banker") -> pd.DataFrame:
    customer_years, customer_evidence = infer_customer_facing_years(text)
    sales_years, sales_evidence = infer_sales_years(text)
    banking_experience, banking_evidence = detect_banking_experience(text)

    row = {
        "Name": extract_name(text),
        "Role": role,
        "Sales_Years": sales_years,
        "Customer_Service_Years": customer_years,
        "Banking_Experience": banking_experience,
        "Education": extract_education(text),
        "Skills": extract_skills(text),
        "Days_In_Pipeline": 0,
        "Candidate_Response_Status": "New Applicant",
        "Customer_Facing_Evidence": customer_evidence,
        "Sales_Evidence": sales_evidence,
        "Banking_Evidence": banking_evidence,
    }

    return pd.DataFrame([row])
