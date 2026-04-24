import re
import pandas as pd


# =========================
# HEALTHCARE KEYWORDS
# =========================
CERT_KEYWORDS = ["rn", "registered nurse", "bls", "acls", "cpr"]
CLINICAL_TERMS = ["hospital", "icu", "er", "clinic", "ward", "patient care", "triage"]
EMR_TERMS = ["epic", "cerner", "emr", "ehr"]
COMPLIANCE_TERMS = ["hipaa", "compliance", "regulation"]
COMMUNICATION_TERMS = ["communication", "coordinated", "collaborated", "explained"]
TEAMWORK_TERMS = ["team", "collaboration", "cross-functional"]


# =========================
# BASIC UTILS
# =========================
def clean_lines(text: str):
    return [line.strip() for line in text.splitlines() if line.strip()]


def normalize(text: str):
    return re.sub(r"\s+", " ", text).lower().strip()


# =========================
# NAME
# =========================
def extract_name(text: str):
    lines = clean_lines(text)
    for line in lines[:5]:
        if "@" not in line and not re.search(r"\d", line):
            words = line.split()
            if 1 < len(words) <= 4:
                return line.strip()
    return "Unknown"


# =========================
# EDUCATION
# =========================
def extract_education(text: str):
    t = text.lower()
    if "master" in t or "msn" in t:
        return "Master"
    if "bachelor" in t or "bsn" in t:
        return "Bachelor"
    if "associate" in t or "adn" in t:
        return "Associate"
    return ""


# =========================
# SIGNAL DETECTORS
# =========================
def detect_flag(text, keywords):
    lower = text.lower()
    return any(k in lower for k in keywords)


def extract_evidence(text, keywords):
    lines = clean_lines(text)
    hits = [l for l in lines if any(k in l.lower() for k in keywords)]
    return " | ".join(hits[:3])


def infer_clinical_years(text):
    lines = clean_lines(text)
    hits = [l for l in lines if any(k in l.lower() for k in CLINICAL_TERMS)]
    count = len(hits)

    if count >= 5:
        return 3
    if count >= 3:
        return 2
    if count >= 1:
        return 1
    return 0


# =========================
# SKILLS
# =========================
def extract_skills(text):
    lower = text.lower()
    skills = []

    if detect_flag(text, CERT_KEYWORDS):
        skills.append("certifications")

    if detect_flag(text, CLINICAL_TERMS):
        skills.append("clinical")

    if detect_flag(text, EMR_TERMS):
        skills.append("emr")

    if detect_flag(text, COMPLIANCE_TERMS):
        skills.append("hipaa")

    if detect_flag(text, COMMUNICATION_TERMS):
        skills.append("communication")

    if detect_flag(text, TEAMWORK_TERMS):
        skills.append("teamwork")

    return ", ".join(sorted(set(skills)))


# =========================
# EXPERIENCE SUMMARY
# =========================
def summarize_experience(text):
    lower = text.lower()
    tags = []

    if detect_flag(text, CLINICAL_TERMS):
        tags.append("clinical experience")

    if detect_flag(text, CERT_KEYWORDS):
        tags.append("certifications")

    if detect_flag(text, EMR_TERMS):
        tags.append("EMR systems")

    if detect_flag(text, COMPLIANCE_TERMS):
        tags.append("HIPAA compliance")

    if not tags:
        return "General healthcare or support experience."

    return f"Demonstrated {', '.join(tags[:3])}."


# =========================
# MAIN PARSER
# =========================
def parse_resume_to_dataframe(text: str, role: str = "Registered Nurse"):
    clinical_years = infer_clinical_years(text)

    row = {
        "Name": extract_name(text),
        "Role": role,
        "Certifications": extract_evidence(text, CERT_KEYWORDS),
        "Clinical_Years": clinical_years,
        "Education": extract_education(text),
        "Skills": extract_skills(text),
        "Experience_Summaries": summarize_experience(text),

        # Flags for scoring
        "RN_License_Flag": "Yes" if detect_flag(text, ["rn", "registered nurse"]) else "No",
        "BLS_ACLS_Flag": "Yes" if detect_flag(text, ["bls", "acls"]) else "No",
        "Hospital_Experience_Flag": "Yes" if detect_flag(text, ["hospital", "icu", "er"]) else "No",
        "Patient_Care_Flag": "Yes" if detect_flag(text, ["patient care", "triage"]) else "No",
        "EMR_Flag": "Yes" if detect_flag(text, EMR_TERMS) else "No",
        "HIPAA_Flag": "Yes" if detect_flag(text, COMPLIANCE_TERMS) else "No",
        "Communication_Flag": "Yes" if detect_flag(text, COMMUNICATION_TERMS) else "No",
        "Teamwork_Flag": "Yes" if detect_flag(text, TEAMWORK_TERMS) else "No",
    }

    return pd.DataFrame([row])
