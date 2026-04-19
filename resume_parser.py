import re
import pandas as pd


SKILL_KEYWORDS = [
    "sales",
    "communication",
    "customer service",
    "banking",
    "financial",
    "relationship management",
    "relationship building",
    "crm",
    "client service",
    "cross-selling",
    "upselling",
    "cash handling",
    "atm",
    "mobile banking",
    "online banking",
    "problem solving",
    "operations",
    "referrals",
    "compliance",
    "risk awareness",
    "client engagement",
    "business development",
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
    "customer", "customers", "client", "clients", "guest", "guests",
    "patient", "patients", "visitor", "visitors", "member", "members",
    "user", "users", "family", "families", "students",
]

CUSTOMER_ACTION_TERMS = [
    "assisted", "helped", "supported", "served", "advised", "guided",
    "responded", "communicated", "interacted", "handled", "resolved",
    "addressed", "explained", "coordinated", "scheduled", "hosted",
    "welcomed", "greeted",
]

CUSTOMER_CONTEXT_TERMS = [
    "inquiries", "questions", "issues", "concerns", "requests",
    "appointments", "accounts", "service", "support", "onboarding",
    "check-in", "scheduling", "communications", "intake", "queue", "traffic",
]

SALES_DIRECT_TERMS = [
    "sales", "selling", "upselling", "cross-selling", "quota",
    "revenue", "business development", "referral", "referrals",
    "prospecting", "pipeline",
]

SALES_ACTION_TERMS = [
    "sold", "generated", "increased", "converted", "closed", "promoted",
    "recommended", "pitched", "marketed", "achieved", "exceeded",
    "referred", "advised",
]

SALES_CONTEXT_TERMS = [
    "target", "quota", "goal", "revenue", "conversion", "clients",
    "accounts", "products", "services", "solutions",
]

BANKING_TERMS = [
    "bank", "banking", "teller", "relationship banker", "associate banker",
    "branch banker", "financial services", "credit union", "loan", "deposit",
    "deposits", "withdrawal", "withdrawals", "branch", "account opening",
    "consumer banking", "retail banking", "checking", "savings", "financial center",
]

COMMUNICATION_TERMS = [
    "communication", "communicated", "presented", "explained", "coordinated",
    "liaised", "interfaced", "stakeholders", "clients", "customers",
]

CASH_TERMS = [
    "cash handling", "cash", "cash drawer", "cash vault", "payments",
    "deposits", "withdrawals", "money handling", "till", "register",
    "cashier", "cash transactions", "drawer reconciliation",
]

DIGITAL_BANKING_TERMS = [
    "mobile banking", "online banking", "self-service", "atm",
    "digital banking", "mobile app", "banking app", "technology solutions",
    "self service", "digital tools", "digital platform",
]

RELATIONSHIP_TERMS = [
    "relationship", "relationships", "trusted relationship", "client needs",
    "financial goals", "advisory", "recommendations", "consultative",
    "rapport", "retention", "relationship building",
]

OPERATIONS_TERMS = [
    "appointments", "scheduling", "queue", "lobby", "traffic",
    "branch operations", "compliance", "procedures", "policies",
    "regulatory", "accuracy", "process", "guidelines", "workflow",
    "documentation", "risk awareness",
]

PROBLEM_SOLVING_TERMS = [
    "resolved", "resolution", "problem solving", "troubleshoot",
    "investigated", "handled issues", "addressed concerns",
    "critical thinking", "issue resolution",
]

ADAPTABILITY_TERMS = [
    "adapted", "adaptability", "learned quickly", "new systems",
    "new technology", "fast-paced", "cross-trained", "flexible",
]

NAME_STOP_TERMS = [
    "summary", "education", "skills", "experience", "relevant experience",
    "professional experience", "language", "languages",
]


def clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def unique_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def extract_name(text: str) -> str:
    lines = clean_lines(text)

    for line in lines[:6]:
        original = line.strip()
        norm = normalize_text(original)

        if any(stop in norm for stop in NAME_STOP_TERMS):
            continue

        # 如果一行里带了邮箱/电话/地址，只取最左侧名字部分
        if "|" in original:
            original = original.split("|")[0].strip()
            norm = normalize_text(original)

        if "@" in original:
            continue

        if re.search(r"\d{3}[-\s]?\d{3}[-\s]?\d{4}", original):
            continue

        # 去掉括号内容后再判断
        cleaned = re.sub(r"\([^)]*\)", " ", original)
        cleaned = re.sub(r"[^A-Za-z\u4e00-\u9fff\s\-]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        words = cleaned.split()
        if 1 < len(words) <= 5:
            return cleaned

    return "Unknown"


def extract_education(text: str) -> str:
    lower = text.lower()
    if "master" in lower:
        return "Master"
    if "bachelor" in lower:
        return "Bachelor"
    if "associate" in lower:
        return "Associate"
    if "high school" in lower or "ged" in lower or "diploma" in lower:
        return "High School"
    return ""


def detect_banking_experience(text: str):
    lower = text.lower()
    matched = [term for term in BANKING_TERMS if term in lower]
    matched = unique_preserve_order(matched)

    if matched:
        return "Yes", " | ".join(matched[:8])
    return "No", ""


def detect_signal(text: str, terms: list[str]):
    lines = [normalize_text(line) for line in clean_lines(text)]
    evidence_lines = [line for line in lines if any(term in line for term in terms)]
    evidence_lines = unique_preserve_order(evidence_lines)
    return ("Yes" if evidence_lines else "No"), " | ".join(evidence_lines[:4])


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

    evidence_lines = unique_preserve_order(evidence_lines)
    count = len(evidence_lines)

    if count >= 5:
        years = 3
    elif count >= 3:
        years = 2
    elif count >= 1:
        years = 1
    else:
        years = 0

    return years, " | ".join(evidence_lines[:4])


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

    evidence_lines = unique_preserve_order(evidence_lines)
    count = len(evidence_lines)

    if count >= 5:
        years = 3
    elif count >= 3:
        years = 2
    elif count >= 1:
        years = 1
    else:
        years = 0

    return years, " | ".join(evidence_lines[:4])


def infer_cash_handling_years(text: str):
    lines = [normalize_text(line) for line in clean_lines(text)]
    evidence_lines = [line for line in lines if any(term in line for term in CASH_TERMS)]
    evidence_lines = unique_preserve_order(evidence_lines)
    count = len(evidence_lines)

    if count >= 4:
        years = 3
    elif count >= 2:
        years = 2
    elif count >= 1:
        years = 1
    else:
        years = 0

    return years, " | ".join(evidence_lines[:4])


def extract_skills(text: str) -> str:
    lower = text.lower()
    matched = []

    for skill in SKILL_KEYWORDS:
        if skill in lower:
            matched.append(skill)

    if infer_customer_facing_years(text)[0] >= 1 and "customer service" not in matched:
        matched.append("customer service")

    if infer_sales_years(text)[0] >= 1 and "sales" not in matched:
        matched.append("sales")

    if infer_cash_handling_years(text)[0] >= 1 and "cash handling" not in matched:
        matched.append("cash handling")

    if any(term in lower for term in COMMUNICATION_TERMS) and "communication" not in matched:
        matched.append("communication")

    if any(term in lower for term in BANKING_TERMS):
        if "banking" not in matched:
            matched.append("banking")
        if "financial" not in matched:
            matched.append("financial")

    if any(term in lower for term in DIGITAL_BANKING_TERMS) and "mobile banking" not in matched:
        matched.append("mobile banking")

    if any(term in lower for term in RELATIONSHIP_TERMS) and "relationship building" not in matched:
        matched.append("relationship building")

    if any(term in lower for term in OPERATIONS_TERMS) and "operations" not in matched:
        matched.append("operations")

    if any(term in lower for term in PROBLEM_SOLVING_TERMS) and "problem solving" not in matched:
        matched.append("problem solving")

    return ", ".join(sorted(set(matched)))


def split_experience_blocks(text: str) -> list[str]:
    lines = clean_lines(text)
    blocks = []
    current = []

    for line in lines:
        heading_like = (
            len(line) < 110 and (
                re.search(r"\b(20\d{2}|19\d{2})\b", line) or
                re.search(
                    r"\b(bank|corp|company|inc|llc|branch|store|university|college|school|restaurant|advisor|cashier|tesla|uber)\b",
                    line.lower(),
                )
            )
        )

        if heading_like and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append("\n".join(current))

    cleaned = [b for b in blocks if len(b.split()) >= 12]
    return cleaned[:6]


def summarize_experience_block(block: str) -> str:
    lower = normalize_text(block)
    tags = []

    if any(t in lower for t in CUSTOMER_DIRECT_TERMS + CUSTOMER_PEOPLE_TERMS):
        tags.append("client-facing service")
    if any(t in lower for t in SALES_DIRECT_TERMS + SALES_ACTION_TERMS):
        tags.append("sales or referral activity")
    if any(t in lower for t in CASH_TERMS):
        tags.append("cash handling")
    if any(t in lower for t in DIGITAL_BANKING_TERMS):
        tags.append("digital/self-service banking education")
    if any(t in lower for t in BANKING_TERMS):
        tags.append("banking or financial services exposure")
    if any(t in lower for t in RELATIONSHIP_TERMS):
        tags.append("relationship building")
    if any(t in lower for t in OPERATIONS_TERMS):
        tags.append("branch operations/compliance support")
    if any(t in lower for t in PROBLEM_SOLVING_TERMS):
        tags.append("problem solving")
    if any(t in lower for t in ADAPTABILITY_TERMS):
        tags.append("adaptability")

    tags = unique_preserve_order(tags)

    if not tags:
        return "General operational or support experience with limited direct banking evidence."

    return f"Demonstrated {', '.join(tags[:3])}."


def build_experience_summaries(text: str):
    blocks = split_experience_blocks(text)
    summaries = [summarize_experience_block(block) for block in blocks]
    return blocks, summaries


def parse_resume_to_dataframe(text: str, role: str = "Generic Retail Banker") -> pd.DataFrame:
    customer_years, customer_evidence = infer_customer_facing_years(text)
    sales_years, sales_evidence = infer_sales_years(text)
    cash_years, cash_evidence = infer_cash_handling_years(text)
    banking_experience, banking_evidence = detect_banking_experience(text)

    digital_flag, digital_evidence = detect_signal(text, DIGITAL_BANKING_TERMS)
    relationship_flag, relationship_evidence = detect_signal(text, RELATIONSHIP_TERMS)
    operations_flag, operations_evidence = detect_signal(text, OPERATIONS_TERMS)
    problem_flag, problem_evidence = detect_signal(text, PROBLEM_SOLVING_TERMS)
    adaptability_flag, adaptability_evidence = detect_signal(text, ADAPTABILITY_TERMS)

    _, experience_summaries = build_experience_summaries(text)
    summary_text = " || ".join(experience_summaries[:5])

    row = {
        "Name": extract_name(text),
        "Role": role,
        "Sales_Years": sales_years,
        "Customer_Service_Years": customer_years,
        "Cash_Handling_Years": cash_years,
        "Banking_Experience": banking_experience,
        "Education": extract_education(text),
        "Skills": extract_skills(text),
        "Days_In_Pipeline": 0,
        "Candidate_Response_Status": "New Applicant",
        "Customer_Facing_Evidence": customer_evidence,
        "Sales_Evidence": sales_evidence,
        "Cash_Evidence": cash_evidence,
        "Banking_Evidence": banking_evidence,
        "Digital_Banking_Flag": digital_flag,
        "Digital_Banking_Evidence": digital_evidence,
        "Relationship_Flag": relationship_flag,
        "Relationship_Evidence": relationship_evidence,
        "Operations_Flag": operations_flag,
        "Operations_Evidence": operations_evidence,
        "Problem_Solving_Flag": problem_flag,
        "Problem_Solving_Evidence": problem_evidence,
        "Adaptability_Flag": adaptability_flag,
        "Adaptability_Evidence": adaptability_evidence,
        "Experience_Summaries": summary_text,
    }

    return pd.DataFrame([row])
