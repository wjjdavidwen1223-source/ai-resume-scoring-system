import streamlit as st
import pandas as pd

from jd_profiles import HEALTHCARE_ROLE_PROFILES
from resume_parser import parse_resume_to_dataframe
from resume_scoring import run_screening
from file_parsers import extract_text_from_uploaded_file
from workflow_engine import apply_workflow_to_dataframe, stage_summary, action_queue
from communications import attach_messages


st.set_page_config(page_title="AI Healthcare Recruiter Copilot", layout="wide")

st.title("AI Healthcare Recruiter Copilot")

st.markdown("""
**Built by JiaJun (David) Wen (文家俊)**  
End-to-end recruiting decision system for healthcare and clinical roles
""")

st.caption(
    "AI-driven resume screening, JD matching, workflow progression, and recruiter decision support for healthcare roles"
)

st.markdown("""
Supports:
- Registered Nurse (RN)  
- Medical Assistant  
- Clinical Research Coordinator  
""")

profile_key = st.selectbox(
    "Select target healthcare job profile",
    options=list(HEALTHCARE_ROLE_PROFILES.keys()),
    format_func=lambda x: HEALTHCARE_ROLE_PROFILES[x]["label"],
)

selected_profile = HEALTHCARE_ROLE_PROFILES[profile_key]

with st.expander("Selected JD profile details"):
    st.write("**Role:**", selected_profile["label"])
    st.write("**Company:**", selected_profile["company"])
    st.write("**Job family:**", selected_profile["job_family"])
    st.write("**Minimum education:**", selected_profile["min_education"])
    st.write("**Must-have signals:**", ", ".join(selected_profile["must_have_signals"]))
    st.write("**Preferred signals:**", ", ".join(selected_profile["preferred_signals"]))
    st.write("**Interview threshold:**", selected_profile["interview_threshold"])
    st.write("**Hold threshold:**", selected_profile["hold_threshold"])
    st.write("**Assessment required:**", selected_profile["assessment_required"])
    st.write("**Assessment types:**", ", ".join(selected_profile["assessment_types"]))
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


def update_candidate_field_by_index(df: pd.DataFrame, row_idx: int, field: str, value):
    updated = df.copy()
    if row_idx not in updated.index:
        return updated

    updated.loc[row_idx, field] = value
    updated = refresh_pipeline(updated)
    return updated


def update_multiple_fields_by_index(df: pd.DataFrame, row_idx: int, updates: dict):
    updated = df.copy()
    if row_idx not in updated.index:
        return updated

    for field, value in updates.items():
        updated.loc[row_idx, field] = value

    updated = refresh_pipeline(updated)
    return updated


def reset_candidate_workflow_by_index(df: pd.DataFrame, row_idx: int):
    updated = df.copy()
    if row_idx not in updated.index:
        return updated

    reset_fields = {
        "Assessment_Status": "Not Sent",
        "Assessment_Result": "Pending",
        "Cognitive_Test_Status": "Not Sent",
        "Personality_Test_Status": "Not Sent",
        "Clinical_Judgment_Status": "Not Sent",
        "Patient_Care_Scenario_Status": "Not Sent",
        "Compliance_Check_Status": "Not Sent",
        "Cognitive_Score": "",
        "Personality_Match": "",
        "Clinical_Judgment_Score": "",
        "Compliance_Check_Result": "",
        "Recruiter_Call_Status": "Not Scheduled",
        "Recruiter_Call_Outcome": "Pending",
        "Recruiter_Notes": "",
        "Manager_Interview_Status": "Not Scheduled",
        "Manager_Interview_Outcome": "Pending",
        "Manager_Feedback": "",
        "Clinical_Interview_Status": "Not Scheduled",
        "Clinical_Interview_Outcome": "Pending",
        "Clinical_Feedback": "",
        "Interview_Debrief_Status": "Pending",
        "Final_HR_Status": "Not Started",
        "Final_HR_Outcome": "Pending",
        "Offer_Status": "None",
        "Offer_Decision": "Pending",
        "Workflow_Next_Action": "",
        "Workflow_Blocker": "",
        "Last_Workflow_Event": "",
        "Current_Stage": "Applied",
    }

    for field, value in reset_fields.items():
        if field in updated.columns:
            updated.loc[row_idx, field] = value

    updated = refresh_pipeline(updated)
    return updated


def render_stage_timeline(current_stage: str):
    pipeline_flow = [
        "Applied",
        "Assessment Sent",
        "Assessment Completed",
        "Assessment Passed",
        "Recruiter Phone Screen",
        "Clinical / Hiring Manager Interview",
        "Final HR Call",
        "Offer",
        "Hired",
    ]

    st.write("### Candidate Pipeline Flow")

    if current_stage == "Rejected":
        st.error("🔴 Candidate Rejected")
        return

    try:
        stage_index = pipeline_flow.index(current_stage)
    except ValueError:
        if current_stage == "Hiring Manager Interview":
            stage_index = pipeline_flow.index("Clinical / Hiring Manager Interview")
        else:
            stage_index = 0

    cols = st.columns(len(pipeline_flow))

    for i, stage in enumerate(pipeline_flow):
        if i < stage_index:
            cols[i].markdown(f"🟢<br><b>{stage}</b>", unsafe_allow_html=True)
        elif i == stage_index:
            cols[i].markdown(f"🟡<br><b>{stage}</b>", unsafe_allow_html=True)
        else:
            cols[i].markdown(f"⚪<br>{stage}", unsafe_allow_html=True)


def render_dynamic_stage_controls(df: pd.DataFrame, row_idx: int, state_key: str, scope: str):
    row = df.loc[row_idx]
    stage = str(row.get("Current_Stage", "")).strip()

    st.write("### Recruiter Workflow Controls")
    st.write(f"**Current Stage Logic:** {stage}")

    util1, util2 = st.columns(2)

    with util1:
        if st.button("Refresh Candidate Workflow", key=f"{scope}_{state_key}_refresh_{row_idx}"):
            st.session_state[state_key] = refresh_pipeline(df)
            st.rerun()

    with util2:
        if st.button("Reset Candidate Workflow", key=f"{scope}_{state_key}_reset_{row_idx}"):
            st.session_state[state_key] = reset_candidate_workflow_by_index(df, row_idx)
            st.rerun()

    if stage in {"Rejected", "Hired"}:
        st.info("This candidate is in a terminal stage.")
        return

    if stage == "Assessment Sent":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Mark Assessment Completed", key=f"{scope}_{state_key}_assessment_completed_{row_idx}"):
                updated = update_multiple_fields_by_index(
                    df,
                    row_idx,
                    {
                        "Cognitive_Test_Status": "Completed",
                        "Personality_Test_Status": "Completed",
                        "Clinical_Judgment_Status": "Completed",
                        "Patient_Care_Scenario_Status": "Completed",
                        "Compliance_Check_Status": "Completed",
                    },
                )
                st.session_state[state_key] = updated
                st.rerun()

        with c2:
            if st.button("Mark Assessment Failed", key=f"{scope}_{state_key}_assessment_failed_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Assessment_Result", "Fail")
                st.session_state[state_key] = updated
                st.rerun()
        return

    if stage == "Assessment Completed":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Mark Assessment Passed", key=f"{scope}_{state_key}_assessment_passed_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Assessment_Result", "Pass")
                st.session_state[state_key] = updated
                st.rerun()

        with c2:
            if st.button("Mark Assessment Failed", key=f"{scope}_{state_key}_assessment_failed2_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Assessment_Result", "Fail")
                st.session_state[state_key] = updated
                st.rerun()
        return

    if stage in {"Assessment Passed", "Recruiter Phone Screen"}:
        recruiter_status = str(row.get("Recruiter_Call_Status", "")).strip()

        if recruiter_status in {"Not Scheduled", "To Schedule"}:
            if st.button("Schedule Recruiter Phone Screen", key=f"{scope}_{state_key}_recruiter_schedule_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Recruiter_Call_Status", "Scheduled")
                st.session_state[state_key] = updated
                st.rerun()
            return

        if recruiter_status == "Scheduled":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Mark Recruiter Screen Passed", key=f"{scope}_{state_key}_recruiter_pass_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Recruiter_Call_Status": "Completed",
                            "Recruiter_Call_Outcome": "Pass",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()

            with c2:
                if st.button("Mark Recruiter Screen Hold", key=f"{scope}_{state_key}_recruiter_hold_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Recruiter_Call_Status": "Completed",
                            "Recruiter_Call_Outcome": "Hold",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()

            with c3:
                if st.button("Mark Recruiter Screen Failed", key=f"{scope}_{state_key}_recruiter_fail_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Recruiter_Call_Status": "Completed",
                            "Recruiter_Call_Outcome": "Fail",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()
            return

    if stage in {"Hiring Manager Interview", "Clinical / Hiring Manager Interview"}:
        manager_status = str(row.get("Manager_Interview_Status", "")).strip()

        if manager_status in {"Not Scheduled", "To Schedule"}:
            if st.button("Schedule Clinical / Hiring Manager Interview", key=f"{scope}_{state_key}_manager_schedule_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Manager_Interview_Status", "Scheduled")
                st.session_state[state_key] = updated
                st.rerun()
            return

        if manager_status == "Scheduled":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Mark Clinical Interview Passed", key=f"{scope}_{state_key}_manager_pass_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Manager_Interview_Status": "Completed",
                            "Manager_Interview_Outcome": "Pass",
                            "Clinical_Interview_Status": "Completed",
                            "Clinical_Interview_Outcome": "Pass",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()

            with c2:
                if st.button("Mark Clinical Interview Hold", key=f"{scope}_{state_key}_manager_hold_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Manager_Interview_Status": "Completed",
                            "Manager_Interview_Outcome": "Hold",
                            "Clinical_Interview_Status": "Completed",
                            "Clinical_Interview_Outcome": "Hold",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()

            with c3:
                if st.button("Mark Clinical Interview Failed", key=f"{scope}_{state_key}_manager_fail_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Manager_Interview_Status": "Completed",
                            "Manager_Interview_Outcome": "Fail",
                            "Clinical_Interview_Status": "Completed",
                            "Clinical_Interview_Outcome": "Fail",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()
            return

    if stage == "Interview Debrief":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Move to Final HR", key=f"{scope}_{state_key}_debrief_to_hr_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Final_HR_Status", "To Schedule")
                st.session_state[state_key] = updated
                st.rerun()

        with c2:
            if st.button("Reject After Debrief", key=f"{scope}_{state_key}_debrief_reject_{row_idx}"):
                updated = update_multiple_fields_by_index(
                    df,
                    row_idx,
                    {
                        "Final_HR_Outcome": "Fail",
                        "Final_HR_Status": "Completed",
                    },
                )
                st.session_state[state_key] = updated
                st.rerun()
        return

    if stage == "Final HR Call":
        final_hr_status = str(row.get("Final_HR_Status", "")).strip()

        if final_hr_status in {"Not Started", "To Schedule"}:
            if st.button("Schedule Final HR", key=f"{scope}_{state_key}_finalhr_schedule_{row_idx}"):
                updated = update_candidate_field_by_index(df, row_idx, "Final_HR_Status", "Scheduled")
                st.session_state[state_key] = updated
                st.rerun()
            return

        if final_hr_status == "Scheduled":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mark Final HR Passed", key=f"{scope}_{state_key}_finalhr_pass_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Final_HR_Status": "Completed",
                            "Final_HR_Outcome": "Pass",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()

            with c2:
                if st.button("Mark Final HR Failed", key=f"{scope}_{state_key}_finalhr_fail_{row_idx}"):
                    updated = update_multiple_fields_by_index(
                        df,
                        row_idx,
                        {
                            "Final_HR_Status": "Completed",
                            "Final_HR_Outcome": "Fail",
                        },
                    )
                    st.session_state[state_key] = updated
                    st.rerun()
            return

    if stage == "Offer":
        offer_status = str(row.get("Offer_Status", "")).strip()

        if offer_status in {"None", "Draft"}:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Draft Offer", key=f"{scope}_{state_key}_offer_draft_{row_idx}"):
                    updated = update_candidate_field_by_index(df, row_idx, "Offer_Status", "Draft")
                    st.session_state[state_key] = updated
                    st.rerun()

            with c2:
                if st.button("Send Offer", key=f"{scope}_{state_key}_offer_send_{row_idx}"):
                    updated = update_candidate_field_by_index(df, row_idx, "Offer_Status", "Sent")
                    st.session_state[state_key] = updated
                    st.rerun()
            return

        if offer_status == "Sent":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Offer Accepted", key=f"{scope}_{state_key}_offer_accept_{row_idx}"):
                    updated = update_candidate_field_by_index(df, row_idx, "Offer_Decision", "Accepted")
                    st.session_state[state_key] = updated
                    st.rerun()

            with c2:
                if st.button("Offer Declined", key=f"{scope}_{state_key}_offer_decline_{row_idx}"):
                    updated = update_candidate_field_by_index(df, row_idx, "Offer_Decision", "Declined")
                    st.session_state[state_key] = updated
                    st.rerun()
            return

    st.info("No stage-specific actions available for this candidate at the moment.")


with tab1:
    st.subheader("Batch Candidate Screening")

    uploaded_csv = st.file_uploader(
        "Upload healthcare candidate CSV",
        type=["csv"],
        key="csv_uploader",
    )

    if uploaded_csv is not None:
        df = pd.read_csv(uploaded_csv)
        st.write("### Input Data")
        st.dataframe(df, use_container_width=True)

        if st.button("Run Healthcare Screening Workflow", key="run_csv_workflow"):
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
        st.bar_chart(batch_results["Decision"].value_counts())

        st.write("### Workflow Stage Distribution")
        st.bar_chart(batch_results["Current_Stage"].value_counts())

        top_candidate_cols = [
            "Name", "Role", "Score", "Max_Score", "Match_Score_%",
            "Decision", "Current_Stage", "Stage_Badge",
            "Matched_Signals", "Risk_Flags", "Reason", "Experience_Summaries",
        ]
        existing_top_cols = [c for c in top_candidate_cols if c in batch_results.columns]
        st.write("### Top Candidates")
        st.dataframe(batch_results[existing_top_cols].head(10), use_container_width=True)

        recruiter_queue_cols = [
            "Name", "Role", "Score", "Match_Score_%",
            "Decision", "Priority", "Current_Stage",
            "Workflow_Next_Action", "Workflow_Blocker", "Recruiter_Signal",
            "Risk_Flags",
        ]
        existing_queue_cols = [c for c in recruiter_queue_cols if c in batch_results.columns]
        st.write("### Recruiter Queue")
        st.dataframe(batch_results[existing_queue_cols], use_container_width=True)

        st.write("### Full Candidate Output")
        st.dataframe(batch_results, use_container_width=True)

        csv_output = batch_results.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Results as CSV",
            data=csv_output,
            file_name="healthcare_screening_results.csv",
            mime="text/csv",
        )


with tab2:
    st.subheader("Single Resume Screening")

    uploaded_resume = st.file_uploader(
        "Upload one healthcare candidate resume (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        key="resume_uploader",
    )

    if uploaded_resume is not None:
        try:
            extracted_text = extract_text_from_uploaded_file(uploaded_resume)
            st.write("### Extracted Resume Text")
            st.text_area("Resume Preview", extracted_text[:6000], height=260)

            if st.button("Analyze This Healthcare Resume", key="analyze_resume"):
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
        row_idx = single_results.index[0]
        row = single_results.loc[row_idx]

        st.write("### Screening Result")
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{row['Score']} / {row['Max_Score']}")
        c2.metric("Match Score", f"{row['Match_Score_%']}%")
        c3.metric("Decision", row["Decision"])

        st.write("**Name:**", row["Name"])
        st.write("**Role:**", row["Role"])
        st.write("**Current Stage:**", row["Current_Stage"])
        render_stage_timeline(row["Current_Stage"])
        st.write("**Stage Badge:**", row.get("Stage_Badge", ""))
        st.write("**Priority:**", row["Priority"])
        st.write("**Recruiter Signal:**", row["Recruiter_Signal"])
        st.write("**Next Action:**", row["Workflow_Next_Action"])
        st.write("**Workflow Blocker:**", row.get("Workflow_Blocker", ""))
        st.write("**Reason:**", row["Reason"])
        st.write("**Improvement:**", row["Improvement"])
        st.write("**Risk Flags:**", row.get("Risk_Flags", ""))
        st.write("**Matched Signals:**", row["Matched_Signals"])
        st.write("**Missing Signals:**", row["Missing_Signals"])
        st.write("**Score Breakdown:**", row.get("Score_Breakdown", ""))

        st.write("### Experience Summaries")
        for i, summary in enumerate(str(row.get("Experience_Summaries", "")).split("||"), start=1):
            summary = summary.strip()
            if summary:
                st.write(f"**Experience {i}:** {summary}")

        st.write("### Evidence Detected")
        st.write("**RN License Evidence:**", row.get("RN_License_Evidence", ""))
        st.write("**BLS / ACLS Evidence:**", row.get("BLS_ACLS_Evidence", ""))
        st.write("**Patient Care Evidence:**", row.get("Patient_Care_Evidence", ""))
        st.write("**Hospital Experience Evidence:**", row.get("Hospital_Experience_Evidence", ""))
        st.write("**EMR / EHR Evidence:**", row.get("EMR_Evidence", ""))
        st.write("**HIPAA / Compliance Evidence:**", row.get("HIPAA_Evidence", ""))
        st.write("**Communication Evidence:**", row.get("Communication_Evidence", ""))
        st.write("**Teamwork Evidence:**", row.get("Teamwork_Evidence", ""))

        st.write("### Candidate Message")
        st.write(row.get("Stage_Message", ""))

        st.write("### Recruiter Note")
        st.code(row.get("Recruiter_Note", ""), language="text")

        render_dynamic_stage_controls(
            st.session_state["single_results"],
            row_idx,
            "single_results",
            "single_tab",
        )

        st.write("### Parsed Candidate Data")
        st.dataframe(st.session_state["single_results"], use_container_width=True)


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

        display_options = [
            f"{idx} | {pipeline_df.loc[idx, 'Name']}"
            for idx in pipeline_df.index
        ]

        selected_option = st.selectbox(
            "Select candidate to manage",
            options=display_options,
            key=f"{state_key}_pipeline_candidate_selector",
        )

        selected_idx = int(selected_option.split("|")[0].strip())
        selected_row = pipeline_df.loc[selected_idx]

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Stage", selected_row.get("Current_Stage", ""))
        c2.metric("Decision", selected_row.get("Decision", ""))
        c3.metric("Priority", selected_row.get("Priority", ""))

        st.write("**Name:**", selected_row.get("Name", ""))
        render_stage_timeline(selected_row.get("Current_Stage", ""))
        st.write("**Stage Badge:**", selected_row.get("Stage_Badge", ""))
        st.write("**Next Action:**", selected_row.get("Workflow_Next_Action", ""))
        st.write("**Blocker:**", selected_row.get("Workflow_Blocker", ""))
        st.write("**Last Workflow Event:**", selected_row.get("Last_Workflow_Event", ""))

        render_dynamic_stage_controls(
            st.session_state[state_key],
            selected_idx,
            state_key,
            "pipeline_tab",
        )

        refreshed_row = st.session_state[state_key].loc[selected_idx]

        st.write("### Selected Candidate Message")
        st.write(refreshed_row.get("Stage_Message", ""))

        st.write("### Selected Candidate Recruiter Note")
        st.code(refreshed_row.get("Recruiter_Note", ""), language="text")

        st.write("### Stage-Based Messages")
        message_cols = [
            "Name", "Current_Stage", "Stage_Badge",
            "Workflow_Next_Action", "Stage_Message", "Recruiter_Note",
        ]
        existing_message_cols = [c for c in message_cols if c in pipeline_df.columns]
        st.dataframe(st.session_state[state_key][existing_message_cols], use_container_width=True)

        st.write("### Pipeline Detail")
        detail_cols = [
            "Name", "Role", "Decision", "Current_Stage",
            "Assessment_Status", "Assessment_Result",
            "Cognitive_Test_Status", "Personality_Test_Status",
            "Clinical_Judgment_Status", "Patient_Care_Scenario_Status",
            "Compliance_Check_Status",
            "Recruiter_Call_Status", "Recruiter_Call_Outcome",
            "Manager_Interview_Status", "Manager_Interview_Outcome",
            "Clinical_Interview_Status", "Clinical_Interview_Outcome",
            "Final_HR_Status", "Final_HR_Outcome",
            "Offer_Status", "Offer_Decision",
            "Workflow_Next_Action", "Workflow_Blocker",
            "Last_Workflow_Event",
        ]
        existing_detail_cols = [c for c in detail_cols if c in pipeline_df.columns]
        st.dataframe(st.session_state[state_key][existing_detail_cols], use_container_width=True)
