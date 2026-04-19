def _first_name(name: str) -> str:
    cleaned = str(name).strip()
    if not cleaned:
        return "there"

    parts = cleaned.split()
    if not parts:
        return "there"

    return parts[0]


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def generate_stage_message(row):
    first_name = _first_name(row.get("Name", ""))
    role = _safe_text(row.get("Role", "the role"))
    stage = _safe_text(row.get("Current_Stage", ""))
    next_action = _safe_text(row.get("Workflow_Next_Action", ""))
    blocker = _safe_text(row.get("Workflow_Blocker", ""))

    if stage == "Assessment Sent":
        return (
            f"Hi {first_name}, thank you for your interest in the {role} position. "
            f"As the next step in the process, we’d like to invite you to complete a cognitive and personality assessment. "
            f"Please complete the assessments at your earliest convenience."
        )

    if stage == "Assessment Completed":
        return (
            f"Hi {first_name}, thank you for completing the assessments for the {role} position. "
            f"Our team is currently reviewing your results, and we’ll follow up soon with the next steps."
        )

    if stage == "Assessment Passed":
        return (
            f"Hi {first_name}, thank you for completing the assessments for the {role} position. "
            f"We’re pleased to move you forward to the next step, which is a recruiter phone screen."
        )

    if stage == "Recruiter Phone Screen":
        return (
            f"Hi {first_name}, thank you for your continued interest in the {role} position. "
            f"The next step in the process is a recruiter phone screen, and our team will be in touch regarding scheduling."
        )

    if stage == "Hiring Manager Interview":
        return (
            f"Hi {first_name}, we’re excited to move you forward in the process for the {role} position. "
            f"The next step is a hiring manager interview."
        )

    if stage == "Interview Debrief":
        return (
            f"Hi {first_name}, thank you again for speaking with our team regarding the {role} position. "
            f"We are currently reviewing interview feedback and will follow up with next steps as soon as possible."
        )

    if stage == "Final HR Call":
        return (
            f"Hi {first_name}, thank you for progressing through the interview process for the {role} position. "
            f"We’d like to schedule a final HR conversation as the next step."
        )

    if stage == "Offer":
        return (
            f"Hi {first_name}, thank you for your time throughout the process for the {role} position. "
            f"We are currently preparing the next stage of your candidacy and will follow up shortly regarding the offer process."
        )

    if stage == "Hired":
        return (
            f"Hi {first_name}, congratulations! We’re excited to move forward with you for the {role} position. "
            f"Our team will follow up shortly with onboarding details."
        )

    if stage == "Rejected":
        return (
            f"Hi {first_name}, thank you for your interest in the {role} position and for your time throughout the process. "
            f"After careful review, we will not be moving forward at this time. "
            f"We appreciate your interest and encourage you to apply again in the future if relevant opportunities arise."
        )

    if next_action:
        return (
            f"Hi {first_name}, thank you for your interest in the {role} position. "
            f"Our team is currently reviewing your application. Next step: {next_action}."
        )

    if blocker:
        return (
            f"Hi {first_name}, thank you for your continued interest in the {role} position. "
            f"Our team is still reviewing your application and will follow up once the next step is available."
        )

    return (
        f"Hi {first_name}, thank you for your interest in the {role} position. "
        f"We’ll follow up soon with the next steps in the process."
    )


def generate_internal_recruiter_note(row):
    name = _safe_text(row.get("Name", "Unknown Candidate"))
    role = _safe_text(row.get("Role", "Unknown Role"))
    stage = _safe_text(row.get("Current_Stage", ""))
    decision = _safe_text(row.get("Decision", ""))
    score = _safe_text(row.get("Score", ""))
    match_pct = _safe_text(row.get("Match_Score_%", ""))
    priority = _safe_text(row.get("Priority", ""))
    matched_signals = _safe_text(row.get("Matched_Signals", ""))
    missing_signals = _safe_text(row.get("Missing_Signals", ""))
    reason = _safe_text(row.get("Reason", ""))
    blocker = _safe_text(row.get("Workflow_Blocker", ""))
    next_action = _safe_text(row.get("Workflow_Next_Action", ""))
    last_event = _safe_text(row.get("Last_Workflow_Event", ""))

    return (
        f"Candidate: {name} | "
        f"Role: {role} | "
        f"Stage: {stage} | "
        f"Screening Decision: {decision} | "
        f"Priority: {priority} | "
        f"Score: {score} | "
        f"Match: {match_pct}% | "
        f"Matched Signals: {matched_signals or 'N/A'} | "
        f"Missing Signals: {missing_signals or 'N/A'} | "
        f"Reason: {reason or 'N/A'} | "
        f"Last Event: {last_event or 'N/A'} | "
        f"Blocker: {blocker or 'None'} | "
        f"Next Action: {next_action or 'None'}"
    )


def generate_stage_badge(row):
    stage = _safe_text(row.get("Current_Stage", "")).lower()

    if stage in {"offer", "hired"}:
        return "🟢 Late Stage"

    if stage in {"final hr call", "hiring manager interview", "recruiter phone screen"}:
        return "🟡 Interviewing"

    if stage in {"assessment sent", "assessment completed", "assessment passed"}:
        return "🔵 Assessment"

    if stage in {"rejected"}:
        return "🔴 Closed"

    return "⚪ Early Stage"


def generate_candidate_status_summary(row):
    decision = _safe_text(row.get("Decision", ""))
    stage = _safe_text(row.get("Current_Stage", ""))
    next_action = _safe_text(row.get("Workflow_Next_Action", ""))
    blocker = _safe_text(row.get("Workflow_Blocker", ""))

    parts = []

    if decision:
        parts.append(f"Decision: {decision}")
    if stage:
        parts.append(f"Stage: {stage}")
    if next_action:
        parts.append(f"Next: {next_action}")
    if blocker:
        parts.append(f"Blocker: {blocker}")

    return " | ".join(parts)


def attach_messages(df):
    result = df.copy()
    result["Stage_Message"] = result.apply(generate_stage_message, axis=1)
    result["Recruiter_Note"] = result.apply(generate_internal_recruiter_note, axis=1)
    result["Stage_Badge"] = result.apply(generate_stage_badge, axis=1)
    result["Candidate_Status_Summary"] = result.apply(generate_candidate_status_summary, axis=1)
    return result
