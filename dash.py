
import re
from collections import Counter

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Easylogs",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Easylogs")
st.caption("Free log analysis for DevOps and application support")

uploaded_file = st.file_uploader(
    "Where is the log Bro ?",
    type=["log", "txt", "out", "csv"],
)

if uploaded_file is None:
    st.info("Hey? Why are you fooling around? Upload a log file to analyze it.")
    st.code(
        "2026-10-28 10:00:01 INFO Application started\n"
        "2026-10-28 10:00:03 WARN High memory usage\n"
        "2026-10-28 10:00:05 ERROR Database connection failed\n"
        "2026-10-28 10:00:06 ERROR Database connection failed\n"
        "2026-10-28 10:00:08 CRITICAL Service unavailable",
        language="text",
    )
    st.stop()

try:
    content = uploaded_file.getvalue().decode(
        "utf-8-sig", errors="replace"
    )
    lines = content.splitlines()

    if not lines:
        st.warning("The uploaded file is empty.")
        st.stop()

    records = []

    for line_number, line in enumerate(lines, start=1):
        match = re.search(
            r"\b(CRITICAL|FATAL|ERROR|ERR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b",
            line,
            re.IGNORECASE,
        )

        severity = match.group(1).upper() if match else "UNKNOWN"

        if severity == "WARNING":
            severity = "WARN"
        elif severity == "ERR":
            severity = "ERROR"
        elif severity == "FATAL":
            severity = "CRITICAL"

        records.append({
            "Line": line_number,
            "Severity": severity,
            "Message": line,
        })

    df = pd.DataFrame(records)

    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total lines", len(df))
    col2.metric("Errors", int((df["Severity"] == "ERROR").sum()))
    col3.metric("Warnings", int((df["Severity"] == "WARN").sum()))
    col4.metric(
        "Critical",
        int((df["Severity"] == "CRITICAL").sum()),
    )

    st.subheader("Severity distribution")
    severity_counts = (
        df["Severity"].value_counts().rename_axis("Severity")
        .reset_index(name="Count")
    )
    st.bar_chart(severity_counts.set_index("Severity"))

    st.subheader("Search logs")

    search = st.text_input("Search message")
    severities = sorted(df["Severity"].unique().tolist())

    selected = st.multiselect(
        "Filter severity",
        severities,
        default=severities,
    )

    filtered = df[df["Severity"].isin(selected)]

    if search:
        filtered = filtered[
            filtered["Message"].str.contains(
                search, case=False, regex=False
            )
        ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("Most repeated messages")

    error_logs = df[
        df["Severity"].isin(["ERROR", "CRITICAL"])
    ]

    if error_logs.empty:
        st.write("No ERROR or CRITICAL messages found.")
    else:
        repeated = (
            error_logs.groupby("Message")
            .size()
            .reset_index(name="Occurrences")
            .sort_values("Occurrences", ascending=False)
            .head(10)
        )
        st.dataframe(repeated, use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered logs as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="logpilot_analysis.csv",
        mime="text/csv",
    )

except Exception as exc:
    st.error(f"Could not analyze the file: {exc}")
