
import io
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)

from database import (
    initialize_database,
    save_investigation,
    get_investigations,
    delete_investigation,
    delete_all_investigations,
)
from agents.orchestrator import run_investigation


st.set_page_config(
    page_title="SENTINEL X | Cyber Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263449;
        padding: 16px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def make_pdf(record):
    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    def add_paragraph(text, style="BodyText"):
        story.append(Paragraph(escape(str(text)), styles[style]))
        story.append(Spacer(1, 8))

    story.append(
        Paragraph("SENTINEL X", styles["Title"])
    )
    story.append(
        Paragraph("Security Investigation Report", styles["Heading2"])
    )
    story.append(Spacer(1, 12))

    add_paragraph(f"Investigation ID: {record.get('id', 'New')}")
    add_paragraph(f"URL: {record.get('url', '')}")
    add_paragraph(f"Hostname: {record.get('hostname', 'See URL')}")
    add_paragraph(f"Risk score: {record.get('risk_score', 0)}/100")
    add_paragraph(f"Risk level: {record.get('risk_level', 'Unknown')}")
    add_paragraph(f"Created at: {record.get('created_at', 'Just now')}")

    story.append(
        Paragraph("Findings", styles["Heading2"])
    )
    story.append(Spacer(1, 8))

    for finding in record.get("findings", []):
        add_paragraph(f"- {finding}")

    report = record.get("ai_report")
    if report:
        story.append(
            Paragraph("AI Report", styles["Heading2"])
        )
        add_paragraph(report)

    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "Limitations: This report reflects the checks performed "
            "by SENTINEL X. A heuristic score is not a probability "
            "of compromise or proof that a website is malicious. "
            "Verify findings before taking action.",
            styles["Italic"],
        )
    )

    document.build(story)
    return buffer.getvalue()


def load_history():
    return get_investigations()


# Initialize the existing database table.
try:
    initialize_database()
    database_ready = True
    database_error = ""
except Exception as error:
    database_ready = False
    database_error = str(error)


with st.sidebar:
    st.title("🛡️ SENTINEL X")
    st.caption("AGENTIC CYBER DEFENSE")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        ["Overview", "Investigate URL", "History", "System"],
    )

    st.divider()
    st.caption(
        "MySQL: Connected" if database_ready
        else "MySQL: Connection error"
    )


if not database_ready:
    st.error("Could not initialize the MySQL database.")
    st.code(database_error)
    st.stop()


try:
    history = load_history()
except Exception as error:
    st.error("Could not load investigation history from MySQL.")
    st.code(str(error))
    st.stop()


if page == "Overview":
    st.title("Security Command Center")
    st.write(
        "Investigate URLs, review indicators, and manage "
        "saved security reports."
    )

    high_risk = sum(
        (record["risk_score"] or 0) >= 45
        for record in history
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Saved reports", len(history))
    col2.metric("High / critical scores", high_risk)
    col3.metric("Retention limit", "30 reports")

    st.divider()
    st.subheader("Recent Investigations")

    if not history:
        st.info("No saved reports yet. Start an investigation.")
    else:
        for record in history[:5]:
            with st.container(border=True):
                st.write(f"**Report #{record['id']}**")
                st.write(record["url"])
                st.write(
                    f"Risk: {record['risk_level']} "
                    f"({record['risk_score']}/100)"
                )


elif page == "Investigate URL":
    st.title("URL Investigation")
    st.write(
        "Analyze URL characteristics without visiting "
        "the submitted website."
    )

    with st.container(border=True):
        url = st.text_input(
            "Target URL",
            placeholder="https://example.com",
        )

        run_analysis = st.button(
            "Analyze and Save Report",
            type="primary",
            width="stretch",
        )

    
    if run_analysis:
        with st.spinner(
            "Running URL analysis and three AI agents..."
        ):
            try:
                result = run_investigation(url)

                if not result["valid"]:
                    st.error(result["error"])
                else:
                    report_id = save_investigation(result)
                    result["id"] = report_id
                    st.session_state.last_result = result

                    st.success(
                        f"Investigation #{report_id} saved to MySQL."
                    )
                    st.rerun()

            except Exception as error:
                st.error(
                    "The investigation failed. Check your Gemini "
                    "configuration, API availability, and terminal logs."
                )
                st.code(str(error))
                

    result = st.session_state.get("last_result")

    if result:
        st.divider()
        st.subheader("Latest Investigation")
        
        st.divider()
        st.subheader("AI Agent Findings")

        assessment = result.get("ai_assessment", {})

        if assessment:
            st.write("**Agent risk assessment:**", assessment["risk_level"])
            st.write("**Assessment rationale:**", assessment["rationale"])

            st.write("**Recommended defensive actions**")
            for recommendation in result.get("ai_recommendations", []):
                st.write(f"• {recommendation}")

        review = result.get("agent_review", {})

        if review:
            st.write("**Evidence verification**")
            st.write("Confidence:", review["confidence"])

            st.write("Supported claims")
            for claim in review["supported_claims"]:
                st.write(f"• {claim}")

            st.write("Claims not established by evidence")
            for claim in review["unsupported_claims"]:
                st.write(f"• {claim}")

        if result.get("ai_report"):
            st.write("**Executive summary**")
            st.write(result["ai_report"])

        for limitation in result.get("report_limitations", []):
            st.caption(f"Limitation: {limitation}")


        col1, col2 = st.columns(2)
        col1.metric(
            "Risk score",
            f"{result['risk_score']}/100",
        )
        col2.metric("Risk level", result["risk_level"])

        st.write("**URL**")
        st.code(result["url"])

        st.write("**Indicators**")
        for finding in result["findings"]:
            st.write(f"• {finding}")

        pdf = make_pdf(result)

        st.download_button(
            "📄 Download PDF Report",
            data=pdf,
            file_name=f"sentinel_x_report_{result['id']}.pdf",
            mime="application/pdf",
            width="stretch",
        )

        st.warning(
            "This is a preliminary heuristic assessment, "
            "not proof of malicious activity."
        )


elif page == "History":
    st.title("Investigation History")
    st.caption(
        "These reports are loaded from MySQL and persist "
        "across application restarts."
    )

    top_left, top_right = st.columns([3, 1])
    top_left.metric("Saved reports", len(history))

    if top_right.button(
        "🗑️ Delete All",
        disabled=not history,
        width="stretch",
    ):
        st.session_state.confirm_delete_all = True

    if st.session_state.get("confirm_delete_all", False):
        st.error(
            "This permanently deletes all investigation records "
            "from the sentinel_x investigations table."
        )

        confirm_col, cancel_col = st.columns(2)

        if confirm_col.button(
            "Confirm Permanent Deletion",
            type="primary",
        ):
            try:
                count = delete_all_investigations()
                st.session_state.confirm_delete_all = False
                st.session_state.last_result = None
                st.success(f"Deleted {count} investigation records.")
                st.rerun()
            except Exception as error:
                st.error("Deletion failed.")
                st.code(str(error))

        if cancel_col.button("Cancel"):
            st.session_state.confirm_delete_all = False
            st.rerun()

    st.divider()

    if not history:
        st.info("No saved reports.")
    else:
        for record in history:
            with st.expander(
                f"#{record['id']} — {record['risk_level']} — "
                f"{record['url']}"
            ):
                st.write(
                    f"**Risk score:** {record['risk_score']}/100"
                )
                st.write(
                    f"**Created:** {record['created_at']}"
                )

                st.write("**Findings**")
                for finding in record["findings"]:
                    st.write(f"• {finding}")

                pdf_record = dict(record)
                pdf_record["hostname"] = "See URL"

                pdf = make_pdf(pdf_record)

                col_download, col_delete = st.columns(2)

                col_download.download_button(
                    "📄 Download PDF",
                    data=pdf,
                    file_name=(
                        f"sentinel_x_report_{record['id']}.pdf"
                    ),
                    mime="application/pdf",
                    key=f"download_{record['id']}",
                    width="stretch",
                )

                if col_delete.button(
                    "🗑️ Delete Report",
                    key=f"delete_{record['id']}",
                    width="stretch",
                ):
                    st.session_state[
                        f"confirm_delete_{record['id']}"
                    ] = True

                if st.session_state.get(
                    f"confirm_delete_{record['id']}", False
                ):
                    st.warning(
                        f"Confirm deletion of report #{record['id']}?"
                    )

                    yes, no = st.columns(2)

                    if yes.button(
                        "Confirm",
                        key=f"yes_{record['id']}",
                    ):
                        try:
                            delete_investigation(record["id"])
                            st.session_state[
                                f"confirm_delete_{record['id']}"
                            ] = False
                            st.rerun()
                        except Exception as error:
                            st.error("Deletion failed.")
                            st.code(str(error))

                    if no.button(
                        "Cancel",
                        key=f"no_{record['id']}",
                    ):
                        st.session_state[
                            f"confirm_delete_{record['id']}"
                        ] = False
                        st.rerun()


elif page == "System":
    st.title("System Status")

    st.success("MySQL persistence enabled")
    st.success("30-report retention enabled")
    st.success("PDF report export enabled")
    st.success("Individual and bulk deletion enabled")

    st.info(
        "Gemini report generation and specialist agents "
        "will be integrated in the next development stage."
    )

    st.write(f"Current saved reports: {len(history)}")
    st.write("Storage: MySQL database `sentinel_x`")
