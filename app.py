import streamlit as st
import pandas as pd

from jd_profiles import BANK_ROLE_PROFILES
from resume_parser import parse_resume_to_dataframe
from resume_scoring import run_screening
from file_parsers import extract_text_from_uploaded_file
from workflow_engine import apply_workflow_to_dataframe, stage_summary, action_queue
from communications import attach_messages


st.set_page_config(page_title="AI Banking Recruiter Copilot", layout="wide")

st.title("AI Banking Recruiter Copilot")

st.markdown("""
**Built by JiaJun (David) Wen (文家俊)**  
End-to-end recruiting decision system for retail banking roles
""")

st.caption(
    "AI-driven resume screening, JD matching, workflow progression, and recruiter decision support for banking roles"
)

st.markdown("""
Supports:
- BoA Relationship Banker  
- Chase Associate Banker  
- Generic Retail Banker / Universal Banker  
""")

profile_key = st.selectbox(
    "Select target job profile",
    options=list(BANK_ROLE_PROFILES.keys()),
    format_func=lambda x: BANK_ROLE_PROFILES[x]["label"],
)

selected_profile = BANK_ROLE_PROFILES[profile_key]

with st.expander("Selected JD profile details"):
    st.write("**Role:**", selected_profile["label"])
    st.write("**Company:**", selected_profile["company"])
    st.write("**Job family:**", selected_profile["job_family"])
    st.write("**Must-have signals:**", ", ".join(selected_profile["must_have_signals"]))
    st.write("**Preferred signals:**", ", ".join(selected_profile["preferred_signals"]))
    st.write("**Interview threshold:**", selected_profile["interview_threshold"])
    st.write("**Hold threshold:**", selected_profile["hold_threshold"])
    st.write("**Target outcomes:**", ", ".join(selected_profile["target_outcomes"]))

tab1, tab2, tab3 = st.tabs([
    "Batch CSV Screening",
    "Single Resume Screening",
    "Pipeline Management",
])

if "batch_results" not in st.session_state:
    st.session_state["batch_results"] = None

if "single_results" not in st.session_state:
    st.session_state["single_results"] = None


def refresh_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    df = apply_workflow_to_dataframe(df)
    df = attach_messages(df)
    return df


def update_candidate_field(df: pd.DataFrame, candidate_name: str, field: str, value):
    updated = df.copy()
    match_idx = updated.index[updated["Name"] == candidate_name]

    if len(match_idx) == 0:
        return updated

    updated.loc[match_idx[0], field] = value
    updated = refresh_pipeline(updated)
    return updated


def update_multiple_fields(df: pd.DataFrame, candidate_name: str, updates: dict):
    updated = df.copy()
    match_idx = updated.index[updated["Name"] == candidate_name]

    if len(match_idx) == 0:
        return updated

    row_idx = match_idx[0]
    for field, value in updates.items():
        updated.loc[row_idx, field] = value

    updated = refresh_pipeline(updated)
    return updated


with tab1:
    st.subheader("Batch Candidate Screening")

    uploaded_csv = st.file_uploader(
        "Upload candidate CSV",
        type=["csv"],
        key="csv_uploader",
    )

    if uploaded_csv is not None:
        df = pd.read_csv(uploaded_csv)

        st.write("### Input Data")
        st.dataframe(df, use_container_width=True)

        if st.button("Run Banking Screening Workflow", key="run_csv_workflow"):
            screened = run_screening(df, profile_key=profile_key)
            screened = refresh_pipeline(screened)
            st.session_state["batch_results"] = screened

    batch_results = st.session_state["batch_results"]

    if batch_results is not None:
        st.write("### Recruiting Dashboard")

        total_candidates = len(batch_results)
        interview_count = (batch_results["Decision"] == "Interview").sum()
        hold_count = (batch_results["Decision"] == "Hold").sum()
        reject_count = (batch_results["Decision"] == "Reject").sum()
        avg_score = round(batch_results["Score"].mean(), 1) if total_candidates else 0
        follow_up_due_count = (batch_results["Follow_Up_Due"] == "Yes").sum()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Candidates", total_candidates)
        c2.metric("Interview", interview_count)
        c3.metric("Hold", hold_count)
        c4.metric("Reject", reject_count)
        c5.metric("Follow-Ups Due", follow_up_due_count)

        c6, c7 = st.columns(2)
        c6.metric(
            "Interview Rate",
            f"{round((interview_count / total_candidates) * 100, 1) if total_candidates else 0}%"
        )
        c7.metric("Average Score", avg_score)

        st.write("### Decision Distribution")
        decision_counts = batch_results["Decision"].value_counts()
        st.bar_chart(decision_counts)

        st.write("### Workflow Stage Distribution")
        workflow_counts = batch_results["Current_Stage"].value_counts()
        st.bar_chart(workflow_counts)

        st.write("### Top Candidates")
        top_candidate_cols = [
            "Name",
            "Role",
            "Score",
            "Max_Score",
            "Match_Score_%",
            "Decision",
            "Current_Stage",
            "Stage_Badge",
            "Matched_Signals",
            "Reason",
            "Experience_Summaries",
        ]
        existing_top_cols = [c for c in top_candidate_cols if c in batch_results.columns]
        st.dataframe(batch_results[existing_top_cols].head(10), use_container_width=True)

        st.write("### Recruiter Queue")
        recruiter_queue_cols = [
            "Name",
            "Role",
            "Score",
            "Match_Score_%",
            "Decision",
            "Priority",
            "Current_Stage",
            "Workflow_Next_Action",
            "Workflow_Blocker",
            "Recruiter_Signal",
        ]
        existing_queue_cols = [c for c in recruiter_queue_cols if c in batch_results.columns]
        st.dataframe(batch_results[existing_queue_cols], use_container_width=True)

        st.write("### Full Candidate Output")
        st.dataframe(batch_results, use_container_width=True)

        csv_output = batch_results.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Results as CSV",
            data=csv_output,
            file_name="banking_screening_results.csv",
            mime="text/csv",
        )


with tab2:
    st.subheader("Single Resume Screening")

    uploaded_resume = st.file_uploader(
        "Upload one candidate resume (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        key="resume_uploader",
    )

    if uploaded_resume is not None:
        try:
            extracted_text = extract_text_from_uploaded_file(uploaded_resume)

            st.write("### Extracted Resume Text")
            st.text_area("Resume Preview", extracted_text[:6000], height=260)

            if st.button("Analyze This Resume", key="analyze_resume"):
                parsed_df = parse_resume_to_dataframe(
                    extracted_text,
                    role=selected_profile["label"],
                )

                screened = run_screening(parsed_df, profile_key=profile_key)
                screened = refresh_pipeline(screened)

                st.session_state["single_results"] = screened

        except Exception as e:
            st.error(f"Could not process file: {e}")

    single_results = st.session_state["single_results"]

    if single_results is not None:
        row = single_results.iloc[0]

        st.write("### Screening Result")
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{row['Score']} / {row['Max_Score']}")
        c2.metric("Match Score", f"{row['Match_Score_%']}%")
        c3.metric("Decision", row["Decision"])

        st.write("**Role:**", row["Role"])
        st.write("**Current Stage:**", row["Current_Stage"])
        st.write("**Stage Badge:**", row.get("Stage_Badge", ""))
        st.write("**Priority:**", row["Priority"])
        st.write("**Recruiter Signal:**", row["Recruiter_Signal"])
        st.write("**Next Action:**", row["Workflow_Next_Action"])
        st.write("**Workflow Blocker:**", row.get("Workflow_Blocker", ""))
        st.write("**Reason:**", row["Reason"])
        st.write("**Improvement:**", row["Improvement"])
        st.write("**Matched Signals:**", row["Matched_Signals"])
        st.write("**Missing Signals:**", row["Missing_Signals"])
        st.write("**Score Breakdown:**", row.get("Score_Breakdown", ""))

        st.write("### Experience Summaries")
        for i, summary in enumerate(str(row.get("Experience_Summaries", "")).split("||"), start=1):
            summary = summary.strip()
            if summary:
                st.write(f"**Experience {i}:** {summary}")

        st.write("### Evidence Detected")
        st.write("**Customer-Facing Evidence:**", row.get("Customer_Facing_Evidence", ""))
        st.write("**Sales Evidence:**", row.get("Sales_Evidence", ""))
        st.write("**Cash Handling Evidence:**", row.get("Cash_Evidence", ""))
        st.write("**Banking Evidence:**", row.get("Banking_Evidence", ""))
        st.write("**Digital Banking Evidence:**", row.get("Digital_Banking_Evidence", ""))
        st.write("**Relationship Evidence:**", row.get("Relationship_Evidence", ""))
        st.write("**Operations Evidence:**", row.get("Operations_Evidence", ""))
        st.write("**Problem Solving Evidence:**", row.get("Problem_Solving_Evidence", ""))
        st.write("**Adaptability Evidence:**", row.get("Adaptability_Evidence", ""))

        st.write("### Candidate Message")
        st.write(row.get("Stage_Message", ""))

        st.write("### Recruiter Note")
        st.code(row.get("Recruiter_Note", ""), language="text")

        st.write("### Parsed Candidate Data")
        st.dataframe(single_results, use_container_width=True)


with tab3:
    st.subheader("Pipeline Management Dashboard")

    source_option = st.radio(
        "Choose data source",
        options=["Batch Results", "Single Resume Result"],
        horizontal=True,
    )

    if source_option == "Batch Results":
        pipeline_df = st.session_state["batch_results"]
        state_key = "batch_results"
    else:
        pipeline_df = st.session_state["single_results"]
        state_key = "single_results"

    if pipeline_df is None:
        st.info("Run batch screening or single resume screening first to populate the pipeline.")
    else:
        st.write("### Funnel Overview")
        summary_df = stage_summary(pipeline_df)
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)
            st.bar_chart(summary_df.set_index("Current_Stage"))

        st.write("### Workflow Action Queue")
        queue_df = action_queue(pipeline_df)
        if not queue_df.empty:
            st.dataframe(queue_df, use_container_width=True)

        st.write("### Candidate Workflow Controls")

        candidate_names = pipeline_df["Name"].tolist()
        selected_candidate = st.selectbox(
            "Select candidate to manage",
            options=candidate_names,
            key="pipeline_candidate_selector",
        )

        selected_row = pipeline_df[pipeline_df["Name"] == selected_candidate].iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Stage", selected_row.get("Current_Stage", ""))
        c2.metric("Decision", selected_row.get("Decision", ""))
        c3.metric("Priority", selected_row.get("Priority", ""))

        st.write("**Stage Badge:**", selected_row.get("Stage_Badge", ""))
        st.write("**Next Action:**", selected_row.get("Workflow_Next_Action", ""))
        st.write("**Blocker:**", selected_row.get("Workflow_Blocker", ""))
        st.write("**Last Workflow Event:**", selected_row.get("Last_Workflow_Event", ""))

        st.write("### Recruiter Action Buttons")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("Assessment Completed", key="assessment_completed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Cognitive_Test_Status": "Completed",
                        "Personality_Test_Status": "Completed",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Assessment marked as completed.")
                st.rerun()

            if st.button("Assessment Passed", key="assessment_passed"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Assessment_Result",
                    "Pass",
                )
                st.session_state[state_key] = updated
                st.success("Assessment marked as passed.")
                st.rerun()

            if st.button("Assessment Failed", key="assessment_failed"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Assessment_Result",
                    "Fail",
                )
                st.session_state[state_key] = updated
                st.success("Assessment marked as failed.")
                st.rerun()

        with col_b:
            if st.button("Recruiter Call Scheduled", key="recruiter_call_scheduled"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Recruiter_Call_Status",
                    "Scheduled",
                )
                st.session_state[state_key] = updated
                st.success("Recruiter call marked as scheduled.")
                st.rerun()

            if st.button("Recruiter Call Passed", key="recruiter_call_passed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Recruiter_Call_Status": "Completed",
                        "Recruiter_Call_Outcome": "Pass",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Recruiter call marked as passed.")
                st.rerun()

            if st.button("Recruiter Call Failed", key="recruiter_call_failed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Recruiter_Call_Status": "Completed",
                        "Recruiter_Call_Outcome": "Fail",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Recruiter call marked as failed.")
                st.rerun()

        with col_c:
            if st.button("Manager Interview Scheduled", key="manager_interview_scheduled"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Manager_Interview_Status",
                    "Scheduled",
                )
                st.session_state[state_key] = updated
                st.success("Manager interview marked as scheduled.")
                st.rerun()

            if st.button("Manager Interview Passed", key="manager_interview_passed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Manager_Interview_Status": "Completed",
                        "Manager_Interview_Outcome": "Pass",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Manager interview marked as passed.")
                st.rerun()

            if st.button("Manager Interview Failed", key="manager_interview_failed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Manager_Interview_Status": "Completed",
                        "Manager_Interview_Outcome": "Fail",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Manager interview marked as failed.")
                st.rerun()

        st.write("### Final Stage Controls")

        col_d, col_e, col_f = st.columns(3)

        with col_d:
            if st.button("Final HR Scheduled", key="final_hr_scheduled"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Final_HR_Status",
                    "Scheduled",
                )
                st.session_state[state_key] = updated
                st.success("Final HR marked as scheduled.")
                st.rerun()

            if st.button("Final HR Passed", key="final_hr_passed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Final_HR_Status": "Completed",
                        "Final_HR_Outcome": "Pass",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Final HR marked as passed.")
                st.rerun()

            if st.button("Final HR Failed", key="final_hr_failed"):
                updated = update_multiple_fields(
                    pipeline_df,
                    selected_candidate,
                    {
                        "Final_HR_Status": "Completed",
                        "Final_HR_Outcome": "Fail",
                    },
                )
                st.session_state[state_key] = updated
                st.success("Final HR marked as failed.")
                st.rerun()

        with col_e:
            if st.button("Offer Drafted", key="offer_drafted"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Offer_Status",
                    "Draft",
                )
                st.session_state[state_key] = updated
                st.success("Offer marked as drafted.")
                st.rerun()

            if st.button("Offer Sent", key="offer_sent"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Offer_Status",
                    "Sent",
                )
                st.session_state[state_key] = updated
                st.success("Offer marked as sent.")
                st.rerun()

        with col_f:
            if st.button("Offer Accepted", key="offer_accepted"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Offer_Decision",
                    "Accepted",
                )
                st.session_state[state_key] = updated
                st.success("Offer marked as accepted.")
                st.rerun()

            if st.button("Offer Declined", key="offer_declined"):
                updated = update_candidate_field(
                    pipeline_df,
                    selected_candidate,
                    "Offer_Decision",
                    "Declined",
                )
                st.session_state[state_key] = updated
                st.success("Offer marked as declined.")
                st.rerun()

        st.write("### Selected Candidate Message")
        refreshed_row = st.session_state[state_key][st.session_state[state_key]["Name"] == selected_candidate].iloc[0]
        st.write(refreshed_row.get("Stage_Message", ""))

        st.write("### Selected Candidate Recruiter Note")
        st.code(refreshed_row.get("Recruiter_Note", ""), language="text")

        st.write("### Stage-Based Messages")
        message_cols = [
            "Name",
            "Current_Stage",
            "Stage_Badge",
            "Workflow_Next_Action",
            "Stage_Message",
            "Recruiter_Note",
        ]
        existing_message_cols = [c for c in message_cols if c in pipeline_df.columns]
        st.dataframe(pipeline_df[existing_message_cols], use_container_width=True)

        st.write("### Pipeline Detail")
        detail_cols = [
            "Name",
            "Role",
            "Decision",
            "Current_Stage",
            "Assessment_Status",
            "Assessment_Result",
            "Cognitive_Test_Status",
            "Personality_Test_Status",
            "Recruiter_Call_Status",
            "Recruiter_Call_Outcome",
            "Manager_Interview_Status",
            "Manager_Interview_Outcome",
            "Final_HR_Status",
            "Final_HR_Outcome",
            "Offer_Status",
            "Offer_Decision",
            "Workflow_Next_Action",
            "Workflow_Blocker",
            "Last_Workflow_Event",
        ]
        existing_detail_cols = [c for c in detail_cols if c in pipeline_df.columns]
        st.dataframe(pipeline_df[existing_detail_cols], use_container_width=True)
