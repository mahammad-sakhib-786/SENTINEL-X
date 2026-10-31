
import io
import json
import hashlib
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
from legal_ai.document_loader import load_document
from legal_ai.clause_splitter import split_documents
from legal_ai.vector_store import create_vector_store
from legal_ai.compliance_checker import (
    check_contract_compliance,
    calculate_contract_risk_score,
)
from legal_ai.rag_pipeline import answer_contract_question
from legal_ai.agent import ask_contract_agent

import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from database import (
    initialize_database,
    save_investigation,
    get_investigations,
    delete_investigation,
    delete_all_investigations,
    save_contract_document,
    get_contract_document_path,
)

from agents.orchestrator import run_investigation


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="SENTINEL X | Cyber Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def safe_json(value):
    """Convert dictionaries/lists into readable JSON text."""
    if value is None:
        return "No data available."

    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def get_hostname(url):
    """Extract hostname without visiting the submitted website."""
    try:
        return urlsplit(url).hostname or "Unknown"
    except (ValueError, TypeError):
        return "Unknown"


def display_list(title, items):
    """Display a heading and a list of findings."""
    st.markdown(f"**{title}**")

    if not items:
        st.caption("No items available.")
        return

    for item in items:
        st.write(f"• {item}")


def add_pdf_section(story, title, content, styles):
    """Add a safely escaped section to a PDF."""
    story.append(Paragraph(escape(str(title)), styles["Heading2"]))
    story.append(Spacer(1, 6))

    if isinstance(content, (dict, list)):
        content = safe_json(content)

    if content is None:
        content = "No data available."

    lines = str(content).splitlines()

    for line in lines:
        if line.strip():
            story.append(
                Paragraph(
                    escape(line),
                    styles["BodyText"],
                )
            )
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))


# ---------------------------------------------------------
# PDF REPORT GENERATION
# ---------------------------------------------------------

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

    styles.add(
        ParagraphStyle(
            name="SmallReportText",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#374151"),
        )
    )

    story = []

    story.append(
        Paragraph("SENTINEL X", styles["Title"])
    )

    story.append(
        Paragraph(
            "Security Investigation Report",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 15))

    # Investigation details
    details = [
        ["Investigation ID", str(record.get("id", "New"))],
        ["URL", str(record.get("url", "Unknown"))],
        ["Hostname", get_hostname(record.get("url", ""))],
        ["Risk score", f"{record.get('risk_score', 0)}/100"],
        ["Risk level", str(record.get("risk_level", "Unknown"))],
        ["Created at", str(record.get("created_at", "Just now"))],
    ]

    details_table = Table(
        details,
        colWidths=[45 * mm, 125 * mm],
    )

    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(details_table)
    story.append(Spacer(1, 18))

    # Local findings
    add_pdf_section(
        story,
        "Local URL Analysis Findings",
        record.get("findings", []),
        styles,
    )

    # URLhaus threat intelligence
    threat = record.get("threat_intelligence")

    if isinstance(threat, dict):
        threat_text = (
            f"Source: {threat.get('source', 'Unknown')}\n"
            f"Status: {threat.get('status', 'Unknown')}\n"
            f"Message: {threat.get('message', 'No message')}\n"
            f"Details: {safe_json(threat.get('details'))}"
        )
    else:
        threat_text = "Threat-intelligence information is unavailable."

    add_pdf_section(
        story,
        "Threat Intelligence",
        threat_text,
        styles,
    )

    # AI evidence review
    add_pdf_section(
        story,
        "AI Evidence Verification",
        record.get("agent_review"),
        styles,
    )

    # AI risk assessment
    add_pdf_section(
        story,
        "AI Risk Assessment",
        record.get("ai_assessment"),
        styles,
    )

    # Recommendations
    add_pdf_section(
        story,
        "AI Recommendations",
        record.get("ai_recommendations", []),
        styles,
    )

    # Executive summary
    add_pdf_section(
        story,
        "Executive Summary",
        record.get("ai_report", "No AI report available."),
        styles,
    )

    # Limitations
    add_pdf_section(
        story,
        "Report Limitations",
        record.get("report_limitations", []),
        styles,
    )

    # Next steps
    add_pdf_section(
        story,
        "Recommended Next Steps",
        record.get("report_next_steps", []),
        styles,
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            escape(
                "Disclaimer: SENTINEL X provides preliminary security "
                "analysis. A heuristic score is not a probability of "
                "compromise or proof that a website is malicious. "
                "A URL not listed by URLhaus is not guaranteed safe. "
                "Verify findings before taking defensive action."
            ),
            styles["Italic"],
        )
    )

    document.build(story)

    return buffer.getvalue()


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

try:
    initialize_database()
    database_ready = True
    database_error = ""

except Exception as error:
    database_ready = False
    database_error = f"{type(error).__name__}: {error}"


# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------

with st.sidebar:
    st.title("🛡️ SENTINEL X")
    st.caption("AGENTIC CYBER DEFENSE")

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Investigate URL",
            "Legal Compliance",
            "History",
            "System",
        ],
    )

    st.divider()

    if database_ready:
        st.success("MySQL: Connected")
    else:
        st.error("MySQL: Connection error")


if not database_ready:
    st.error("Could not initialize the MySQL database.")
    st.code(database_error)
    st.stop()


# ---------------------------------------------------------
# LOAD INVESTIGATION HISTORY
# ---------------------------------------------------------

try:
    history = get_investigations()

except Exception as error:
    st.error("Could not load investigation history from MySQL.")
    st.code(f"{type(error).__name__}: {error}")
    st.stop()


# ---------------------------------------------------------
# OVERVIEW PAGE
# ---------------------------------------------------------

if page == "Overview":

    st.title("Security Command Center")

    st.write(
        "Investigate URLs, review threat intelligence, "
        "and manage saved security reports."
    )

    high_risk = sum(
        (record.get("risk_score") or 0) >= 45
        for record in history
    )

    critical_risk = sum(
        (record.get("risk_score") or 0) >= 70
        for record in history
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Saved reports", len(history))
    col2.metric("High / critical scores", high_risk)
    col3.metric("Critical scores", critical_risk)
    col4.metric("Retention limit", "30")

    st.divider()

    st.subheader("Recent Investigations")

    if not history:
        st.info("No saved reports yet. Start an investigation.")

    else:
        for record in history[:5]:

            with st.container(border=True):

                st.write(f"**Report #{record['id']}**")
                st.write(record["url"])

                score = record.get("risk_score")
                level = record.get("risk_level", "Unknown")

                st.write(f"Risk: {level} ({score}/100)")

                threat = record.get("threat_intelligence") or {}

                if isinstance(threat, dict):
                    st.write(
                        "URLhaus:",
                        threat.get("status", "Unavailable"),
                    )


# ---------------------------------------------------------
# URL INVESTIGATION PAGE
# ---------------------------------------------------------

elif page == "Investigate URL":

    st.title("URL Investigation")

    st.write(
        "Analyze URL characteristics and available threat intelligence "
        "without visiting the submitted website."
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

        if not url.strip():
            st.error("Please enter a URL.")
            st.stop()

        with st.spinner(
            "Running URL analysis, threat intelligence, and AI agents..."
        ):

            try:
                result = run_investigation(url.strip())

                if not result.get("valid"):
                    st.error(result.get("error", "Invalid URL."))

                else:
                    report_id = save_investigation(result)

                    result["id"] = report_id
                    st.session_state.last_result = result

                    st.success(
                        f"Investigation #{report_id} saved to MySQL."
                    )

                    st.rerun()

            except Exception as error:

                st.error("The investigation could not be completed.")

                st.code(
                    f"{type(error).__name__}: {error}"
                )

    result = st.session_state.get("last_result")

    if result:

        st.divider()
        st.subheader("Latest Investigation")

        # Risk metrics
        col1, col2 = st.columns(2)

        col1.metric(
            "Risk score",
            f"{result.get('risk_score', 0)}/100",
        )

        col2.metric(
            "Risk level",
            result.get("risk_level", "Unknown"),
        )

        st.write("**Investigation URL**")
        st.code(result.get("url", ""))

        st.write("**Hostname**")
        st.write(get_hostname(result.get("url", "")))

        # Local findings
        st.divider()

        st.subheader("Local Security Findings")

        display_list(
            "Detected indicators",
            result.get("findings", []),
        )

        # Threat intelligence
        st.divider()

        st.subheader("Threat Intelligence")

        threat = result.get("threat_intelligence") or {}

        if isinstance(threat, dict):

            threat_status = threat.get("status", "unavailable")

            st.write("**Source:**", threat.get("source", "Unknown"))

            if threat_status == "listed":
                st.error("URL is listed in URLhaus.")

            elif threat_status == "not_listed":
                st.success("URL was not found in URLhaus.")

            else:
                st.warning("URLhaus check was unavailable.")

            st.write(threat.get("message", "No message available."))

            details = threat.get("details")

            if details:
                with st.expander("URLhaus technical details"):
                    st.json(details)

        else:
            st.warning("Threat-intelligence data is unavailable.")

        # AI assessment
        st.divider()

        st.subheader("AI Agent Findings")

        assessment = result.get("ai_assessment") or {}

        if assessment:

            st.write(
                "**Agent risk assessment:**",
                assessment.get("risk_level", "Unknown"),
            )

            st.write(
                "**Assessment score:**",
                assessment.get("risk_score", "Not provided"),
            )

            st.write(
                "**Assessment rationale:**",
                assessment.get("rationale", "Not available."),
            )

        else:
            st.info("AI risk assessment is not available.")

        # Recommendations
        display_list(
            "Recommended defensive actions",
            result.get("ai_recommendations", []),
        )

        # Evidence review
        st.divider()

        st.subheader("Evidence Verification")

        review = result.get("agent_review") or {}

        if review:

            st.write(
                "**Confidence:**",
                review.get("confidence", "Unknown"),
            )

            display_list(
                "Supported claims",
                review.get("supported_claims", []),
            )

            display_list(
                "Claims not established by evidence",
                review.get("unsupported_claims", []),
            )

        else:
            st.info("Evidence verification is not available.")

        # Executive report
        st.divider()

        st.subheader("Executive Summary")

        st.write(
            result.get("ai_report", "No AI summary available.")
        )

        display_list(
            "Report limitations",
            result.get("report_limitations", []),
        )

        display_list(
            "Recommended next steps",
            result.get("report_next_steps", []),
        )

        # PDF download
        st.divider()

        st.subheader("Download Investigation Report")

        pdf = make_pdf(result)

        st.download_button(
            "📄 Download Complete PDF Report",
            data=pdf,
            file_name=f"sentinel_x_report_{result['id']}.pdf",
            mime="application/pdf",
            width="stretch",
        )

        st.warning(
            "A low risk score or a URLhaus not-listed result does not "
            "guarantee that a website is safe."
        )


# ---------------------------------------------------------
# INVESTIGATION HISTORY PAGE
# ---------------------------------------------------------

elif page == "Legal Compliance":
    st.title("LEGAL COMPLIANCE AGENT")

    st.write(
        "Upload a contract PDF to review its clauses "
        "and identify potential compliance issues."
    )

    uploaded_contract = st.file_uploader(
        "Upload Contract PDF",
        type=["pdf"],
        key="legal_contract_uploader"
    )

    if uploaded_contract is not None:
        st.success(
            f"Uploaded successfully: {uploaded_contract.name}"
        )

        if st.button("Save Contract", key="save_legal_contract"):
            contract_bytes = uploaded_contract.getvalue()

            document_id = hashlib.sha256(
                contract_bytes
            ).hexdigest()

            upload_dir = (
                Path(__file__).resolve().parent
                / "data"
                / "legal_documents"
                / "uploads"
            )

            upload_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            contract_path = upload_dir / f"{document_id}.pdf"
            contract_path.write_bytes(contract_bytes)
            save_contract_document(
                document_id,
                uploaded_contract.name,
                str(contract_path.resolve()),
            )

            st.session_state.legal_document_id = document_id
            st.session_state.legal_contract_path = str(contract_path)
            st.session_state.legal_contract_name = uploaded_contract.name

            try:
                with st.spinner("Analyzing contract..."):
                    documents = load_document(str(contract_path))
                    chunks = split_documents(documents)

                    if not chunks:
                        raise ValueError(
                            "No readable text was found in the PDF."
                        )

                    create_vector_store(chunks, document_id)

                    compliance_results = check_contract_compliance(chunks)
                    risk_summary = calculate_contract_risk_score(compliance_results)
                    st.session_state.legal_risk_summary = risk_summary


                    st.session_state.legal_compliance_results = (
                        compliance_results
                    )

                    st.session_state.legal_contract_processed = True
                    st.session_state.legal_ai_answer = None

                st.success("Contract saved and processed successfully!")
                st.write(f"Pages loaded: {len(documents)}")
                st.write(f"Clause-aware chunks created: {len(chunks)}")

            except Exception as error:
                st.session_state.legal_contract_processed = False
                st.error(f"Contract processing failed: {error}")

    # Display results independently of the Save Contract button.
    if st.session_state.get("legal_contract_processed", False):

        st.subheader("COMPLIANCE REVIEW RESULTS")

        results = st.session_state.get(
            "legal_compliance_results",
            {}
        )

        for check_id, result in results.items():
            with st.expander(result["description"]):
                if result["status"] == "REVIEW_INDICATED":
                    st.warning(
                        "Evidence detected — manual review required."
                    )
                else:
                    st.info(
                        "No matching keyword evidence found "
                        "in the reviewed text."
                    )

                
                if result["evidence"]:
                    for evidence in result["evidence"]:

                        evidence_type = evidence.get(
                            "evidence_type",
                            "SUPPORTING_KEYWORD_MENTION"
                        )

                        if evidence_type == "MATCHING_CLAUSE_HEADING":
                            st.success("PRIMARY EVIDENCE — Matching clause heading")
                        else:
                            st.info("SUPPORTING EVIDENCE — Keyword mention")

                        st.write(
                            f"**Page:** {evidence['page']} | "
                            f"**Clause:** {evidence['clause']}"
                        )

                        st.write(
                            "**Matched keywords:** "
                            + ", ".join(evidence["matched_keywords"])
                        )

                        st.write(evidence["text"])
                        st.divider()

                else:
                    st.write("No matching evidence was detected.")

        st.caption(
            "Disclaimer: This is a preliminary, keyword-based "
            "contract review, not a legal opinion. A qualified "
            "professional should review the findings."
        )

        st.divider()
        st.subheader("ASK SENTINEL X")

        question = st.text_area(
            "Ask a question about your uploaded contract:",
            placeholder="Example: What is the termination notice period?",
            key="legal_contract_question"
        )

        if st.button("Ask AI", key="ask_legal_contract"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    with st.spinner(
                        "Searching contract and generating answer..."
                    ):
                        
                        answer = ask_contract_agent(
                            question,
                            st.session_state.legal_document_id
                        )


                    st.session_state.legal_ai_answer = answer

                except Exception as error:
                    st.error(f"Question answering failed: {error}")

        if st.session_state.get("legal_ai_answer"):
            st.markdown("### AI Analysis")
            st.write(st.session_state.legal_ai_answer)

elif page == "History":

    st.title("Investigation History")

    st.caption(
        "Investigation records are stored in MySQL and persist "
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
            "from the investigations table."
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
                st.code(f"{type(error).__name__}: {error}")

        if cancel_col.button("Cancel"):

            st.session_state.confirm_delete_all = False
            st.rerun()

    st.divider()

    if not history:

        st.info("No saved reports.")

    else:

        for record in history:

            with st.expander(
                f"#{record['id']} — {record.get('risk_level')} — "
                f"{record.get('url')}"
            ):

                st.write("**Risk score:**", record.get("risk_score"), "/100")

                st.write("**Created:**", record.get("created_at"))

                st.write("**URL:**", record.get("url"))

                st.write("**Findings**")

                for finding in record.get("findings") or []:
                    st.write(f"• {finding}")

                threat = record.get("threat_intelligence") or {}

                st.write("**Threat Intelligence**")

                if isinstance(threat, dict):

                    st.write("Source:", threat.get("source", "Unknown"))
                    st.write("Status:", threat.get("status", "Unknown"))
                    st.write("Message:", threat.get("message", "Unknown"))

                    if threat.get("details"):
                        st.json(threat["details"])

                else:
                    st.info("No threat-intelligence data saved.")

                st.write("**AI Evidence Review**")

                review = record.get("agent_review")

                if review:
                    st.json(review)
                else:
                    st.caption("No evidence review saved.")

                st.write("**AI Risk Assessment**")

                assessment = record.get("ai_assessment")

                if assessment:
                    st.json(assessment)
                else:
                    st.caption("No AI assessment saved.")

                st.write("**AI Recommendations**")

                display_list(
                    "Defensive recommendations",
                    record.get("ai_recommendations") or [],
                )

                st.write("**Executive Summary**")

                st.write(
                    record.get("ai_report") or "No AI report saved."
                )

                pdf = make_pdf(record)

                col_download, col_delete = st.columns(2)

                col_download.download_button(
                    "📄 Download PDF",
                    data=pdf,
                    file_name=f"sentinel_x_report_{record['id']}.pdf",
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
                    f"confirm_delete_{record['id']}",
                    False,
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

                            st.code(
                                f"{type(error).__name__}: {error}"
                            )

                    if no.button(
                        "Cancel",
                        key=f"no_{record['id']}",
                    ):

                        st.session_state[
                            f"confirm_delete_{record['id']}"
                        ] = False

                        st.rerun()


# ---------------------------------------------------------
# SYSTEM STATUS PAGE
# ---------------------------------------------------------

elif page == "System":

    st.title("System Status")

    st.success("MySQL persistence enabled")
    st.success("30-report retention enabled")
    st.success("PDF report export enabled")
    st.success("Individual and bulk deletion enabled")
    st.success("URLhaus integration enabled in investigation pipeline")
    st.success("Three-stage AI investigation pipeline configured")

    st.divider()

    st.subheader("Storage Information")

    st.write("Database:", "sentinel_x")
    st.write("Table:", "investigations")
    st.write("Current saved reports:", len(history))
    st.write("Maximum retained reports:", 30)

    st.divider()

    st.subheader("AI and Threat Intelligence")

    st.write("AI provider selection: Groq with Gemini fallback configured")
    st.write("Threat intelligence: URLhaus")
    st.write("Local URL analysis: Enabled")

    st.info(
        "Gemini fallback and local Ollama fallback should be "
        "tested independently before being marked fully verified."
    )
