import streamlit as st
import pandas as pd
from resume_scoring import run_screening

st.title("AI Recruiting Decision System (JiaJun Wen)")
st.caption("Bank Frontline Resume Screening | Rule-based Decision Engine")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Original Data")
    st.dataframe(df)

    if st.button("Run Screening"):
    results = run_screening(df)

    st.subheader("Results")
    st.dataframe(results)

    st.write("### Summary")
    st.write(results["Decision"].value_counts())
