from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd

from resume_scoring import run_screening
from workflow_engine import (
    apply_workflow_to_dataframe,
    stage_summary,
    action_queue,
)
from jd_profiles import BANK_ROLE_PROFILES


app = FastAPI(
    title="AI Resume Screening & Workflow API",
    description="Backend API for candidate screening, scoring, decision automation, and hiring workflow progression.",
    version="1.0.0",
)


# =========================
# Pydantic Models
# =========================

class CandidateRequest(BaseModel):
    Name: str = Field(default="", description="Candidate full name")
    Role: str = Field(default="Retail Banker", description="Display role name")
    Sales_Years: float = Field(default=0, description="Years of sales experience")
    Customer_Service_Years: float = Field(default=0, description="Years of customer service experience")
    Cash_Handling_Years: float = Field(default=0, description="Years of cash handling experience")
    Banking_Experience: str = Field(default="No", description="Yes or No")
    Education: str = Field(default="", description="Education level, e.g. Bachelor, Master")
    Skills: str = Field(default="", description="Comma-separated or free-text skills")
    Days_In_Pipeline: float = Field(default=0, description="How many days candidate has been in the pipeline")

    Candidate_Response_Status: str = Field(default="No Response")
    Customer_Facing_Evidence: str = Field(default="")
    Sales_Evidence: str = Field(default="")
    Cash_Evidence: str = Field(default="")
    Banking_Evidence: str = Field(default="")
    Digital_Banking_Flag: str = Field(default="No")
    Digital_Banking_Evidence: str = Field(default="")
    Relationship_Flag: str = Field(default="No")
    Relationship_Evidence: str = Field(default="")
    Operations_Flag: str = Field(default="No")
    Operations_Evidence: str = Field(default="")
    Problem_Solving_Flag: str = Field(default="No")
    Problem_Solving_Evidence: str = Field(default="")
    Adaptability_Flag: str = Field(default="No")
    Adaptability_Evidence: str = Field(default="")
    Experience_Summaries: str = Field(default="")

    # Workflow fields
    Current_Stage: str = Field(default="Applied")
    Assessment_Status: str = Field(default="Not Sent")
    Assessment_Result: str = Field(default="Pending")
    Cognitive_Test_Status: str = Field(default="Not Sent")
    Personality_Test_Status: str = Field(default="Not Sent")
    Cognitive_Score: str = Field(default="")
    Personality_Match: str = Field(default="")
    Recruiter_Call_Status: str = Field(default="Not Scheduled")
    Recruiter_Call_Outcome: str = Field(default="Pending")
    Recruiter_Notes: str = Field(default="")
    Manager_Interview_Status: str = Field(default="Not Scheduled")
    Manager_Interview_Outcome: str = Field(default="Pending")
    Manager_Feedback: str = Field(default="")
    Interview_Debrief_Status: str = Field(default="Pending")
    Final_HR_Status: str = Field(default="Not Started")
    Final_HR_Outcome: str = Field(default="Pending")
    Offer_Status: str = Field(default="None")
    Offer_Decision: str = Field(default="Pending")
    Workflow_Next_Action: str = Field(default="")
    Workflow_Blocker: str = Field(default="")
    Last_Workflow_Event: str = Field(default="")


class BatchCandidateRequest(BaseModel):
    candidates: List[CandidateRequest]
    profile_key: str = Field(default="generic_retail_banker")


class SingleCandidateEnvelope(BaseModel):
    candidate: CandidateRequest
    profile_key: str = Field(default="generic_retail_banker")


# =========================
# Helper Functions
# =========================

def validate_profile_key(profile_key: str) -> None:
    if profile_key not in BANK_ROLE_PROFILES:
        valid_keys = list(BANK_ROLE_PROFILES.keys())
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid profile_key: {profile_key}",
                "valid_profile_keys": valid_keys,
            },
        )


def candidate_to_dataframe(candidate: CandidateRequest) -> pd.DataFrame:
    return pd.DataFrame([candidate.model_dump()])


def batch_to_dataframe(candidates: List[CandidateRequest]) -> pd.DataFrame:
    return pd.DataFrame([c.model_dump() for c in candidates])


def safe_record(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {}
    return df.to_dict(orient="records")[0]


# =========================
# Basic Endpoints
# =========================

@app.get("/")
def root():
    return {
        "message": "AI Resume Screening & Workflow API is running",
        "docs_url": "/docs",
        "available_endpoints": [
            "/health",
            "/profiles",
            "/resume/screen",
            "/resume/full_pipeline",
            "/resume/batch_screen",
            "/resume/batch_full_pipeline",
            "/workflow/stage_summary",
            "/workflow/action_queue",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Resume Screening & Workflow API",
        "version": "1.0.0",
    }


@app.get("/profiles")
def get_profiles():
    return {
        "available_profile_keys": list(BANK_ROLE_PROFILES.keys()),
        "profiles": BANK_ROLE_PROFILES,
    }


# =========================
# Screening Endpoints
# =========================

@app.post("/resume/screen")
def screen_resume(payload: SingleCandidateEnvelope):
    validate_profile_key(payload.profile_key)

    df = candidate_to_dataframe(payload.candidate)
    screened_df = run_screening(df, profile_key=payload.profile_key)
    return safe_record(screened_df)


@app.post("/resume/full_pipeline")
def full_pipeline(payload: SingleCandidateEnvelope):
    validate_profile_key(payload.profile_key)

    df = candidate_to_dataframe(payload.candidate)

    screened_df = run_screening(df, profile_key=payload.profile_key)
    final_df = apply_workflow_to_dataframe(screened_df)

    return safe_record(final_df)


# =========================
# Batch Endpoints
# =========================

@app.post("/resume/batch_screen")
def batch_screen(payload: BatchCandidateRequest):
    validate_profile_key(payload.profile_key)

    if not payload.candidates:
        raise HTTPException(status_code=400, detail="candidates list cannot be empty")

    df = batch_to_dataframe(payload.candidates)
    screened_df = run_screening(df, profile_key=payload.profile_key)

    return {
        "count": len(screened_df),
        "results": screened_df.to_dict(orient="records"),
    }


@app.post("/resume/batch_full_pipeline")
def batch_full_pipeline(payload: BatchCandidateRequest):
    validate_profile_key(payload.profile_key)

    if not payload.candidates:
        raise HTTPException(status_code=400, detail="candidates list cannot be empty")

    df = batch_to_dataframe(payload.candidates)
    screened_df = run_screening(df, profile_key=payload.profile_key)
    final_df = apply_workflow_to_dataframe(screened_df)

    return {
        "count": len(final_df),
        "results": final_df.to_dict(orient="records"),
    }


# =========================
# Workflow Analytics Endpoints
# =========================

@app.post("/workflow/stage_summary")
def workflow_stage_summary(payload: BatchCandidateRequest):
    validate_profile_key(payload.profile_key)

    if not payload.candidates:
        raise HTTPException(status_code=400, detail="candidates list cannot be empty")

    df = batch_to_dataframe(payload.candidates)
    screened_df = run_screening(df, profile_key=payload.profile_key)
    final_df = apply_workflow_to_dataframe(screened_df)
    summary_df = stage_summary(final_df)

    return {
        "count": len(summary_df),
        "stage_summary": summary_df.to_dict(orient="records"),
    }


@app.post("/workflow/action_queue")
def workflow_action_queue(payload: BatchCandidateRequest):
    validate_profile_key(payload.profile_key)

    if not payload.candidates:
        raise HTTPException(status_code=400, detail="candidates list cannot be empty")

    df = batch_to_dataframe(payload.candidates)
    screened_df = run_screening(df, profile_key=payload.profile_key)
    final_df = apply_workflow_to_dataframe(screened_df)
    queue_df = action_queue(final_df)

    return {
        "count": len(queue_df),
        "action_queue": queue_df.to_dict(orient="records"),
    }
