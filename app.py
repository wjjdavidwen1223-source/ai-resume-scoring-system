import streamlit as st
import pandas as pd
from resume_scoring import run_screening
from resume_parser import parse_resume_to_dataframe
from file_parsers import extract_text_from_uploaded_file

st.set_page_config(page_title="AI Recruiting Operations System", layout="wide")

st.title("AI Recruiting Operations System (David Wen)")
st.caption("Built for high-speed recruiting workflows | Evaluation, communication, dashboards, and follow-ups")

st.markdown(
    """
This system is designed to automate key recruiting operations, including:

- candidate evaluation
- decision routing
- recruiter action prioritization
- follow-up messaging
- pipeline visibility and dashboard metrics

It now supports:
- batch CSV screening
- single-resume PDF/DOCX screening
- evidence-based inference for customer-facing and sales experience
"""
)

with st.expander("Expected CSV columns"):
    st.write(
        [
            "Name",
            "Role",
            "Sales_Years",
            "Customer_Service_Years",
            "Banking_Experience",
            "Education",
            "Skills",
            "Days_In_Pipeline",
            "Candidate_Response_Status",
        ]
    )

tab1, tab2 = st.tabs(["Batch CSV Screening", "Single Resume Screening"])

with tab1:
    uploaded_csv = st.file_uploader(
        "Upload recruiting CSV for batch screening",
        type=["csv"],
        key="csv_uploader",
    )

    if uploaded_csv is not None:
        df = pd.read_csv(uploaded_csv)

        st.subheader("Input Data")
        st.dataframe(df, use_container_width=True)

        if st.button("Run Recruiting Workflow", key="run_csv_workflow"):
            results = run_screening(df)

            st.subheader("Recruiting Dashboard")

            total_candidates = len(results)
            interview_count = (results["Decision"] == "Interview").sum()
            hold_count = (results["Decision"] == "Hold").sum()
            reject_count = (results["Decision"] == "Reject").sum()
            follow_up_due_count = (results["Follow_Up_Due"] == "Yes").sum()
            avg_score = round(results["Score"].mean(), 1) if total_candidates > 0 else 0

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Candidates", total_candidates)
            col2.metric("Interview", interview_count)
            col3.metric("Hold", hold_count)
            col4.metric("Reject", reject_count)
            col5.metric("Follow-Ups Due", follow_up_due_count)

            col6, col7 = st.columns(2)
            col6.metric(
                "Interview Rate",
                f"{round((interview_count / total_candidates) * 100, 1) if total_candidates else 0}%"
            )
            col7.metric("Average Score", avg_score)

            st.subheader("Decision Distribution")
            decision_counts = results["Decision"].value_counts()
            st.write(decision_counts)
            st.bar_chart(decision_counts)

            st.subheader("Pipeline Stage Distribution")
            stage_counts = results["Pipeline_Stage"].value_counts()
            st.write(stage_counts)
            st.bar_chart(stage_counts)

            st.subheader("Recruiter Action Queue")
            recruiter_queue_cols = [
                "Name",
                "Role",
                "Score",
                "Match_Score_%",
                "Decision",
                "Priority",
                "Follow_Up_Due",
                "Next_Action",
                "Recruiter_Signal",
            ]
            st.dataframe(results[recruiter_queue_cols], use_container_width=True)

            st.subheader("Top Candidates")
            top_candidate_cols = [
                "Name",
                "Role",
                "Score",
                "Match_Score_%",
                "Decision",
                "Matched_Skills",
                "Reason",
            ]
            st.dataframe(results[top_candidate_cols].head(10), use_container_width=True)

            st.subheader("Full Candidate Output")
            st.dataframe(results, use_container_width=True)

            csv_output = results.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Workflow Results as CSV",
                data=csv_output,
                file_name="recruiting_workflow_results.csv",
                mime="text/csv",
            )

with tab2:
    role = st.text_input("Target role", value="Relationship Banker")
    uploaded_resume = st.file_uploader(
        "Upload one candidate resume (.pdf or .docx)",
        type=["pdf", "docx"],
        key="resume_uploader",
    )

    if uploaded_resume is not None:
        try:
            extracted_text = extract_text_from_uploaded_file(uploaded_resume)

            st.subheader("Extracted Resume Text")
            st.text_area("Resume Preview", extracted_text[:5000], height=260)

            if st.button("Score This Resume", key="score_resume"):
                parsed_df = parse_resume_to_dataframe(extracted_text, role=role)

                st.subheader("Parsed Candidate Data")
                st.dataframe(parsed_df, use_container_width=True)

                results = run_screening(parsed_df)
                row = results.iloc[0]

                st.subheader("Screening Result")
                col1, col2, col3 = st.columns(3)
                col1.metric("Score", f"{row['Score']} / 22")
                col2.metric("Match Score", f"{row['Match_Score_%']}%")
                col3.metric("Decision", row["Decision"])

                st.write("**Pipeline Stage:**", row["Pipeline_Stage"])
                st.write("**Priority:**", row["Priority"])
                st.write("**Recruiter Signal:**", row["Recruiter_Signal"])
                st.write("**Next Action:**", row["Next_Action"])
                st.write("**Reason:**", row["Reason"])
                st.write("**Improvement:**", row["Improvement"])
                st.write("**Generated Message:**", row["Generated_Message"])

                st.subheader("Evidence Detected")
                st.write("**Customer-Facing Evidence:**", row.get("Customer_Facing_Evidence", ""))
                st.write("**Sales Evidence:**", row.get("Sales_Evidence", ""))
                st.write("**Banking Evidence:**", row.get("Banking_Evidence", ""))

        except Exception as e:
            st.error(f"Could not process file: {e}")
