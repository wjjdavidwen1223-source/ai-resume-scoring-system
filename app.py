import streamlit as st
import pandas as pd

from jd_profiles import BANK_ROLE_PROFILES
from resume_scoring import run_screening
from resume_parser import parse_resume_to_dataframe
from file_parsers import extract_text_from_uploaded_file

st.set_page_config(page_title="AI Banking Recruiter Copilot", layout="wide")

st.title("AI Banking Recruiter Copilot")

st.markdown("""
**Built by JiaJun (David) Wen (文家俊)**  
End-to-end recruiting decision system for retail banking roles
""")
st.caption(
    "Built for retail banking hiring workflows | Resume screening, JD matching, experience summarization, and recruiter actions"
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
    st.write("**Must-have signals:**", ", ".join(selected_profile["must_have_signals"]))
    st.write("**Preferred signals:**", ", ".join(selected_profile["preferred_signals"]))
    st.write("**Interview threshold:**", selected_profile["interview_threshold"])
    st.write("**Hold threshold:**", selected_profile["hold_threshold"])

tab1, tab2 = st.tabs(["Batch CSV Screening", "Single Resume Screening"])

with tab1:
    uploaded_csv = st.file_uploader(
        "Upload candidate CSV",
        type=["csv"],
        key="csv_uploader",
    )

    if uploaded_csv is not None:
        df = pd.read_csv(uploaded_csv)

        st.subheader("Input Data")
        st.dataframe(df, use_container_width=True)

        if st.button("Run Banking Screening Workflow", key="run_csv_workflow"):
            results = run_screening(df, profile_key=profile_key)

            st.subheader("Recruiting Dashboard")
            total_candidates = len(results)
            interview_count = (results["Decision"] == "Interview").sum()
            hold_count = (results["Decision"] == "Hold").sum()
            reject_count = (results["Decision"] == "Reject").sum()
            follow_up_due_count = (results["Follow_Up_Due"] == "Yes").sum()
            avg_score = round(results["Score"].mean(), 1) if total_candidates > 0 else 0

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

            st.subheader("Decision Distribution")
            decision_counts = results["Decision"].value_counts()
            st.bar_chart(decision_counts)

            st.subheader("Recruiter Queue")
            recruiter_queue_cols = [
                "Name",
                "Role",
                "Score",
                "Max_Score",
                "Match_Score_%",
                "Decision",
                "Priority",
                "Next_Action",
                "Recruiter_Signal",
                "Matched_Signals",
                "Missing_Signals",
            ]
            st.dataframe(results[recruiter_queue_cols], use_container_width=True)

            st.subheader("Top Candidates")
            top_candidate_cols = [
                "Name",
                "Role",
                "Match_Score_%",
                "Decision",
                "Matched_Signals",
                "Reason",
                "Experience_Summaries",
            ]
            st.dataframe(results[top_candidate_cols].head(10), use_container_width=True)

            st.subheader("Full Candidate Output")
            st.dataframe(results, use_container_width=True)

            csv_output = results.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Results as CSV",
                data=csv_output,
                file_name="banking_screening_results.csv",
                mime="text/csv",
            )

with tab2:
    uploaded_resume = st.file_uploader(
        "Upload one candidate resume (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        key="resume_uploader",
    )

    if uploaded_resume is not None:
        try:
            extracted_text = extract_text_from_uploaded_file(uploaded_resume)

            st.subheader("Extracted Resume Text")
            st.text_area("Resume Preview", extracted_text[:6000], height=260)

            if st.button("Analyze This Resume", key="score_resume"):
                parsed_df = parse_resume_to_dataframe(
                    extracted_text,
                    role=selected_profile["label"],
                )
                results = run_screening(parsed_df, profile_key=profile_key)
                row = results.iloc[0]

                st.subheader("Screening Result")
                c1, c2, c3 = st.columns(3)
                c1.metric("Score", f"{row['Score']} / {row['Max_Score']}")
                c2.metric("Match Score", f"{row['Match_Score_%']}%")
                c3.metric("Decision", row["Decision"])

                st.write("**Role:**", row["Role"])
                st.write("**Pipeline Stage:**", row["Pipeline_Stage"])
                st.write("**Priority:**", row["Priority"])
                st.write("**Recruiter Signal:**", row["Recruiter_Signal"])
                st.write("**Next Action:**", row["Next_Action"])
                st.write("**Reason:**", row["Reason"])
                st.write("**Improvement:**", row["Improvement"])
                st.write("**Matched Signals:**", row["Matched_Signals"])
                st.write("**Missing Signals:**", row["Missing_Signals"])

                st.subheader("Experience Summaries")
                for i, summary in enumerate(str(row.get("Experience_Summaries", "")).split("||"), start=1):
                    summary = summary.strip()
                    if summary:
                        st.write(f"**Experience {i}:** {summary}")

                st.subheader("Evidence Detected")
                st.write("**Customer-Facing Evidence:**", row.get("Customer_Facing_Evidence", ""))
                st.write("**Sales Evidence:**", row.get("Sales_Evidence", ""))
                st.write("**Cash Handling Evidence:**", row.get("Cash_Evidence", ""))
                st.write("**Banking Evidence:**", row.get("Banking_Evidence", ""))
                st.write("**Digital Banking Evidence:**", row.get("Digital_Banking_Evidence", ""))
                st.write("**Relationship Evidence:**", row.get("Relationship_Evidence", ""))
                st.write("**Operations Evidence:**", row.get("Operations_Evidence", ""))
                st.write("**Problem Solving Evidence:**", row.get("Problem_Solving_Evidence", ""))

                st.subheader("Generated Recruiter Message")
                st.write(row["Generated_Message"])

                st.subheader("Parsed Candidate Data")
                st.dataframe(parsed_df, use_container_width=True)

        except Exception as e:
            st.error(f"Could not process file: {e}")
