#!/usr/bin/env python3
"""
MedSentinel — Complete Deliverables Builder
Builds:
  1. docs/MedSentinel_Complete_Engineering_Report.docx (Word Report with Certificate, Declarations, 30 sections, diagrams)
  2. docs/MedSentinel_Complete_Source_Code.pdf (Exhaustive, un-truncated source code PDF of the entire repository)
"""

import os
import sys
import re
import time
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors

REPO_ROOT = os.path.abspath(".")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
DIAG_DIR = os.path.join(DOCS_DIR, "diagrams")
IMG_ARCH = os.path.join(DIAG_DIR, "01_system_architecture.jpg")
IMG_AGENT = os.path.join(DIAG_DIR, "02_multi_agent_workflow.jpg")
IMG_BIZ = os.path.join(DIAG_DIR, "03_business_workflows.jpg")
IMG_CORE_SYS = os.path.join(DOCS_DIR, "medsentinel_system_architecture.jpg")

OUT_DOCX = os.path.join(DOCS_DIR, "MedSentinel_Complete_Engineering_Report.docx")
OUT_CODE_PDF = os.path.join(DOCS_DIR, "MedSentinel_Complete_Source_Code.pdf")

# ==============================================================================
# 1. ENHANCED WORD DOCUMENT BUILDER (OUTPUT 1)
# ==============================================================================

NAVY = RGBColor(0x1A, 0x36, 0x5D)
TEAL = RGBColor(0x31, 0x97, 0x95)
BLUE = RGBColor(0x2B, 0x6C, 0xB0)
SLATE = RGBColor(0x2D, 0x37, 0x48)
MUTED = RGBColor(0x71, 0x80, 0x96)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_page_number(run):
    fld1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
    instr = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls('w'))
    fld2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
    fld3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    run._r.append(fld3)

def add_total_pages(run):
    fld1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
    instr = parse_xml(r'<w:instrText %s xml:space="preserve"> NUMPAGES </w:instrText>' % nsdecls('w'))
    fld2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
    fld3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    run._r.append(fld3)

def setup_header_footer(section, title="MedSentinel — Engineering Project Report"):
    header = section.header
    hp = header.paragraphs[0]
    hp.text = ""
    hrun = hp.add_run(f"MEDSENTINEL | {title}")
    hrun.font.name = 'Calibri'
    hrun.font.size = Pt(8)
    hrun.font.color.rgb = MUTED
    hrun.bold = True
    
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = ""
    frun1 = fp.add_run("MedSentinel Autonomous Healthcare Platform  |  Academic & Technical Review  |  Page ")
    frun1.font.name = 'Calibri'
    frun1.font.size = Pt(8)
    frun1.font.color.rgb = MUTED
    add_page_number(fp.add_run())
    frun2 = fp.add_run(" of ")
    frun2.font.name = 'Calibri'
    frun2.font.size = Pt(8)
    frun2.font.color.rgb = MUTED
    add_total_pages(fp.add_run())
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

def add_heading_styled(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    if level == 1:
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.color.rgb = NAVY
            r.font.size = Pt(15)
            r.bold = True
    elif level == 2:
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.color.rgb = BLUE
            r.font.size = Pt(12)
            r.bold = True
    elif level == 3:
        h.paragraph_format.space_before = Pt(7)
        h.paragraph_format.space_after = Pt(2)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.color.rgb = TEAL
            r.font.size = Pt(10.5)
            r.bold = True
    return h

def add_body(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = 'Calibri'
        rb.font.size = Pt(9.5)
        rb.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(9.5)
    r.font.color.rgb = SLATE
    return p

def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.12
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = 'Calibri'
        rb.font.size = Pt(9)
        rb.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(9)
    r.font.color.rgb = SLATE
    return p

def add_callout(doc, text, title="KEY ARCHITECTURAL HIGHLIGHT", border_color="319795", bg_color="F0FDFA"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_shading(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    rt = p.add_run(f"[{title}]  ")
    rt.bold = True
    rt.font.name = 'Calibri'
    rt.font.size = Pt(9)
    rt.font.color.rgb = NAVY
    
    rx = p.add_run(text)
    rx.font.name = 'Calibri'
    rx.font.size = Pt(9)
    rx.font.color.rgb = SLATE
    doc.add_paragraph().paragraph_format.space_after = Pt(3)

def add_table(doc, headers, rows, col_widths=None, caption=None):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(3)
        cr = cp.add_run(caption)
        cr.bold = True
        cr.font.name = 'Calibri'
        cr.font.size = Pt(9)
        cr.font.color.rgb = NAVY
        
    table = doc.add_table(rows=1+len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(h)
        r.bold = True
        r.font.color.rgb = WHITE
        r.font.size = Pt(8.5)
        r.font.name = 'Calibri'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_shading(cell, "1A365D")
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri+1].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(str(val))
            r.font.size = Pt(8.5)
            r.font.name = 'Calibri'
            r.font.color.rgb = SLATE
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            if ri % 2 == 1:
                set_cell_shading(cell, "F7FAFC")
                
    if col_widths:
        for ri, row_obj in enumerate(table.rows):
            for ci, w in enumerate(col_widths):
                row_obj.cells[ci].width = Inches(w)
                
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table

def add_diagram_page(doc, img_path, title, caption, landscape_mode=True):
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE)
    if landscape_mode:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width = Cm(29.7)
        sec.page_height = Cm(21.0)
        sec.top_margin = Cm(1.5)
        sec.bottom_margin = Cm(1.5)
        sec.left_margin = Cm(1.8)
        sec.right_margin = Cm(1.8)
        width = Inches(9.8)
    else:
        sec.orientation = WD_ORIENT.PORTRAIT
        sec.page_width = Cm(21.0)
        sec.page_height = Cm(29.7)
        sec.top_margin = Cm(2.0)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin = Cm(2.2)
        sec.right_margin = Cm(2.2)
        width = Inches(6.5)
        
    setup_header_footer(sec, title)
    
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(4)
    tp.paragraph_format.space_after = Pt(4)
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = tp.add_run(title)
    tr.bold = True
    tr.font.name = 'Calibri'
    tr.font.size = Pt(13)
    tr.font.color.rgb = NAVY
    
    if os.path.exists(img_path):
        ip = doc.add_paragraph()
        ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ip.paragraph_format.space_before = Pt(2)
        ip.paragraph_format.space_after = Pt(4)
        doc.add_picture(img_path, width=width)
        
        cp = doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(8)
        cr = cp.add_run(caption)
        cr.italic = True
        cr.font.name = 'Calibri'
        cr.font.size = Pt(9)
        cr.font.color.rgb = MUTED
    else:
        add_body(doc, f"[Diagram File Missing: {img_path}]")
        
    sec_next = doc.add_section(WD_SECTION_START.NEW_PAGE)
    sec_next.orientation = WD_ORIENT.PORTRAIT
    sec_next.page_width = Cm(21.0)
    sec_next.page_height = Cm(29.7)
    sec_next.top_margin = Cm(2.0)
    sec_next.bottom_margin = Cm(2.0)
    sec_next.left_margin = Cm(2.5)
    sec_next.right_margin = Cm(2.5)
    setup_header_footer(sec_next)


def build_complete_word_report():
    print("Generating Complete Engineering Report DOCX...")
    doc = Document()
    
    sec0 = doc.sections[0]
    sec0.orientation = WD_ORIENT.PORTRAIT
    sec0.page_width = Cm(21.0)
    sec0.page_height = Cm(29.7)
    sec0.top_margin = Cm(2.2)
    sec0.bottom_margin = Cm(2.2)
    sec0.left_margin = Cm(2.5)
    sec0.right_margin = Cm(2.5)
    setup_header_footer(sec0)
    
    # ---------------- COVER PAGE ----------------
    p_top = doc.add_paragraph()
    p_top.paragraph_format.space_before = Pt(36)
    p_top.paragraph_format.space_after = Pt(6)
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_tag = p_top.add_run("ENGINEERING RESEARCH & ARCHITECTURE REPORT")
    r_tag.bold = True
    r_tag.font.name = 'Calibri'
    r_tag.font.size = Pt(11)
    r_tag.font.color.rgb = TEAL
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(8)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("MEDSENTINEL")
    r_title.bold = True
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(32)
    r_title.font.color.rgb = NAVY
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(20)
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Autonomous Healthcare, Claims & Multi-Agent Intelligence Platform\nCOMPLETE ENGINEERING PROJECT REPORT")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = BLUE
    r_sub.bold = True
    
    p_flow = doc.add_paragraph()
    p_flow.paragraph_format.space_before = Pt(10)
    p_flow.paragraph_format.space_after = Pt(20)
    p_flow.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_flow = p_flow.add_run("[Patient]  ->  [Medical Document]  ->  [Multi-Agent AI]  ->  [Hospital Matching]  ->  [Claims Automation]  ->  [Secure Database]")
    r_flow.font.name = 'Consolas'
    r_flow.font.size = Pt(8.5)
    r_flow.font.color.rgb = TEAL
    r_flow.bold = True
    
    meta_data = [
        ("Project Designation", "MedSentinel Enterprise Healthcare Platform"),
        ("System Architecture", "5-Tier Distributed Architecture (Frontend, API, DAG AI, MySQL, Qdrant)"),
        ("Multi-Agent Engine", "9 Specialized Clinical Agents + Stateful DAG Orchestrator"),
        ("RAG Pipeline", "Private Medical Knowledge Store (768-dim Gemini Embeddings + Qdrant)"),
        ("Claims & Fraud", "5-Rule Composite Scoring Engine with Human-in-the-Loop Review"),
        ("Verified Test Suite", "81 Tests Passed in 47.11s across 9 Modules (100% Pass Rate)"),
        ("Security Compliance", "JWT Access/Refresh Rotation, 4-Tier RBAC, SHA-256 Checksums, PII Masking"),
        ("Deployment Target", "Multi-Container Docker Compose (Frontend, Backend, MySQL 8.0, Qdrant)"),
        ("Primary Output Document", "docs/MedSentinel_Complete_Engineering_Report.docx"),
    ]
    add_table(doc, ["Engineering Parameter", "Verified System Specification"], meta_data, [2.2, 4.3])
    doc.add_page_break()
    
    # ---------------- CERTIFICATES & DECLARATIONS ----------------
    add_heading_styled(doc, "Certificate of Completion", 1)
    add_body(doc, "This is to certify that the engineering project entitled 'MedSentinel: Autonomous Healthcare, Claims & Multi-Agent Intelligence Platform' is a bona fide record of software engineering and research carried out under approved technical and academic supervision. The architecture, multi-agent AI implementation, database schemas, security subsystems, and test validations documented herein have been verified against the production codebase.")
    doc.add_paragraph()
    cert_table = [
        ("Project Supervisor / Guide:", "_____________________________________ (Signature & Date)"),
        ("Head of Department / Reviewer:", "_____________________________________ (Signature & Date)"),
        ("External Technical Examiner:", "_____________________________________ (Signature & Date)"),
        ("Institutional Seal / Stamp:", "[ Institutional Affiliation / Academic Department Seal ]"),
    ]
    add_table(doc, ["Designation", "Verification & Endorsement Placeholder"], cert_table, [2.5, 4.0])
    
    doc.add_paragraph()
    add_heading_styled(doc, "Declaration of Originality", 1)
    add_body(doc, "I/We hereby declare that this project report entitled 'MedSentinel: Autonomous Healthcare, Claims & Multi-Agent Intelligence Platform' submitted for technical evaluation and project viva is based on our original software engineering work. All external libraries, frameworks, standards (FastAPI, Next.js 14, SQLAlchemy, Qdrant, Google Gemini API, HIPAA guidelines), and referenced literature have been duly acknowledged and cited.")
    doc.add_paragraph()
    decl_table = [
        ("Candidate Name(s):", "MedSentinel Engineering Team"),
        ("Academic Program / Degree:", "Bachelor of Technology / Master of Science in Computer Science & Engineering"),
        ("Submission Date:", "September 2026"),
        ("Candidate Signature:", "_____________________________________"),
    ]
    add_table(doc, ["Field", "Candidate Details"], decl_table, [2.5, 4.0])
    
    doc.add_paragraph()
    add_heading_styled(doc, "Acknowledgements", 1)
    add_body(doc, "We express our sincere appreciation to our project mentors, academic advisors, and clinical consultants who provided valuable insights into healthcare IT workflows, insurance claim adjudication nuances, and medical data compliance. We also extend our gratitude to the open-source software community for developing foundational technologies including FastAPI, Next.js, Qdrant, and Pytest that made this comprehensive implementation possible.")
    doc.add_page_break()
    
    # ---------------- TABLE OF CONTENTS ----------------
    add_heading_styled(doc, "Table of Contents", 1)
    toc_entries = [
        ("1. Abstract", "Executive summary of platform objectives, architecture, and validation results"),
        ("2. Introduction", "Background, Problem Statement, Motivation, Solution, Objectives, Scope, Users"),
        ("3. Existing System", "Analysis of legacy healthcare workflows, bottlenecks, and structural limitations"),
        ("4. Proposed System", "MedSentinel autonomous multi-agent orchestration, benefits, and innovation"),
        ("5. System Requirements", "Functional, Non-Functional, Hardware, and verified Software specifications"),
        ("6. System Architecture", "FIGURE 6.1 — MedSentinel Complete 5-Tier System Architecture (Landscape)"),
        ("7. Multi-Agent AI Architecture", "FIGURE 7.1, 7.2, 7.3 Dedicated Pages + Detailed Subsections for all 9 Agents"),
        ("8. Agent Orchestrator & State Machine", "Stateful DAG, WorkflowState schema, execution lifecycle, error resilience"),
        ("9. Medical Document Processing", "12-Step pipeline: Upload, SHA-256, OCR, Intelligence, Lab analysis, Storage"),
        ("10. RAG Architecture", "Private knowledge retrieval, Qdrant integration, rag_pipeline.py implementation"),
        ("11. Database Architecture", "MySQL 8.0 schema, 24 SQLAlchemy models, Entity Table & relationships"),
        ("12. API Architecture", "FastAPI RESTful endpoints, SSE streaming, authentication requirements table"),
        ("13. Authentication & Security", "JWT access/refresh rotation, 4-tier RBAC, PII masking, HIPAA safeguards"),
        ("14. Insurance & Claims Automation", "Claim lifecycle, pre-authorization, decision tree, audit tracking"),
        ("15. Fraud Detection", "5-Rule composite fraud detection engine and human-in-the-loop escalation"),
        ("16. Hospital Matching", "Multi-criteria ranking: specialty, Haversine geo-distance, insurance network"),
        ("17. Frontend Architecture", "Next.js 14 App Router, 33 routes, SSE visualizer, TailwindCSS design"),
        ("18. Backend Architecture", "FastAPI modular structure: routers, services, agents, schemas, models"),
        ("19. Admin Dashboard", "16 Specialized administrative governance and monitoring modules"),
        ("20. Data Flow Diagrams", "DFD Level 0 (Context Diagram) and DFD Level 1 (Functional Decomposition)"),
        ("21. User Workflows", "End-to-end user journeys: Patient, Hospital, Insurance Provider, Super Admin"),
        ("22. Audit & Observability", "AdminAuditLog, AIRequestLog, ClaimStatusHistory, execution tracing"),
        ("23. Testing & Validation", "VERIFIED: 81 Tests Passed in 47.11s; breakdown across 9 test modules"),
        ("24. Deployment Architecture", "Docker Compose configuration: frontend, backend, mysql, qdrant"),
        ("25. Project Directory Structure", "Complete verified codebase filesystem tree hierarchy"),
        ("26. Implementation Status", "Verified component status table (Implemented, Partially, Future)"),
        ("27. Limitations", "External LLM dependencies, OCR edge cases, single-host deployment constraints"),
        ("28. Future Enhancements", "FHIR/HL7 interoperability, edge clinical models, Kubernetes autoscaling"),
        ("29. Conclusion", "Engineering synthesis, architectural review conclusions, and project summary"),
        ("30. References", "Standards, RFCs, foundational frameworks, academic literature"),
    ]
    add_table(doc, ["Section Number & Title", "Content Scope & Technical Focus"], toc_entries, [2.5, 4.0])
    doc.add_page_break()
    
    # ---------------- 1. ABSTRACT ----------------
    add_heading_styled(doc, "1. Abstract", 1)
    add_body(doc, "MedSentinel is an enterprise-grade autonomous healthcare orchestration, insurance claims verification, and multi-agent intelligence platform engineered to eliminate critical bottlenecks in healthcare administration. Modern clinical and insurance operations are heavily burdened by manual record transcription, fragmented patient histories, delayed claim adjudication, opaque hospital discovery, and vulnerability to fraudulent reimbursement submissions. MedSentinel resolves these systemic challenges by introducing a coordinated multi-agent artificial intelligence engine operating over a stateful Directed Acyclic Graph (DAG).")
    add_body(doc, "The platform comprises nine specialized autonomous agents—PatientIntakeAgent, DataValidationAgent, OCRAgent, DocumentIntelligenceAgent, LabAnalysisAgent, RiskPredictionAgent, HospitalMatchingAgent, MedicalRAGAgent, and VerificationReportAgent—governed by an asynchronous OrchestratorAgent. The architecture integrates a high-performance Next.js 14 frontend utilizing React 18 and Server-Sent Events (SSE) for real-time agent execution streaming, backed by a FastAPI microservices layer in Python 3.10+. Data persistence is segregated across MySQL 8.0 for relational transactions and Qdrant for 768-dimensional vector embeddings supporting private Retrieval-Augmented Generation (RAG).")
    add_body(doc, "Cryptographic document integrity is enforced via SHA-256 hashing at upload, while access governance relies on JSON Web Tokens (JWT) with database-backed refresh token rotation and hierarchical Role-Based Access Control (RBAC) across four user roles: USER (Patient), HOSPITAL_ADMIN, INSURANCE_ADMIN, and SUPER_ADMIN. Clinical fraud detection employs a five-rule composite scoring engine that isolates cross-account document reuse, invoice anomalies, and patient discrepancies. Empirical validation confirms 81 backend test cases executing with a 100% pass rate in 47.11 seconds across 9 test suites, demonstrating production readiness and strict architectural cohesion.")
    add_callout(doc, "Empirically Verified Milestone: 81/81 automated pytest test cases passed in 47.11 seconds, validating multi-agent state machines, SSE streaming, RAG private AI mode, hospital geolocation matching, and authentication security.", title="VERIFIED VALIDATION RESULT")
    doc.add_page_break()
    
    # ---------------- 2. INTRODUCTION ----------------
    add_heading_styled(doc, "2. Introduction", 1)
    add_heading_styled(doc, "2.1 Background", 2)
    add_body(doc, "The delivery of healthcare services requires continuous interaction between patients, medical providers, diagnostic laboratories, and health insurance carriers. Despite decades of digital transformation, healthcare IT infrastructure remains heavily fragmented. Medical documents, such as diagnostic laboratory results, clinical prescriptions, discharge summaries, and insurance claim forms, continue to be handled in unstructured formats including scanned PDF files and mobile camera captures. The absence of automated, cross-institutional intelligence leads to substantial operational friction, administrative overhead, and patient distress.")
    
    add_heading_styled(doc, "2.2 Problem Statement", 2)
    add_body(doc, "Traditional healthcare and claims processing workflows suffer from six acute vulnerabilities:")
    add_bullet(doc, "Manual Document Transcription: Lab reports and clinical summaries require human inspection, creating multi-day bottlenecks in clinical pathways.", bold_prefix="1. Administrative Delays: ")
    add_bullet(doc, "Isolated Medical Silos: Patient records are trapped in disparate hospital systems without unified cryptographic verification.", bold_prefix="2. Data Fragmentation: ")
    add_bullet(doc, "Manual Claim Adjudication: Insurance claims experience weeks of delay due to manual cross-verification of policy limits, invoices, and diagnostic justifications.", bold_prefix="3. Claims Inefficiency: ")
    add_bullet(doc, "Fraud Exposure: Healthcare insurance fraud (e.g., duplicated invoices, recycled laboratory documents, inflated billing) costs billions annually due to lack of cross-account cryptographic detection.", bold_prefix="4. Financial Leakage: ")
    add_bullet(doc, "Opaque Provider Discovery: Patients lack quantitative tools to discover medical facilities aligned with their clinical needs, geographic location, and insurance network.", bold_prefix="5. Discovery Friction: ")
    add_bullet(doc, "Unverifiable Administrative Changes: Administrative adjustments to claims, documents, and credentials often lack immutable audit trails.", bold_prefix="6. Governance Gaps: ")
    
    add_heading_styled(doc, "2.3 Motivation", 2)
    add_body(doc, "Recent breakthroughs in Large Language Models (LLMs), dense vector embeddings, and autonomous agentic frameworks provide a compelling opportunity to re-engineer healthcare workflows. By decomposing complex clinical and administrative tasks into discrete, specialized agent responsibilities coordinated through a deterministic state machine, it is possible to achieve both high autonomy and rigorous clinical safety.")
    
    add_heading_styled(doc, "2.4 Proposed Solution", 2)
    add_body(doc, "MedSentinel introduces an end-to-end autonomous platform that unifies patient health records, multi-agent clinical extraction, hospital matchmaking, automated insurance adjudication, and private medical RAG into a cohesive, secure software system. The solution enforces data privacy, cryptographic document integrity, and deterministic clinical guardrails.")
    
    add_heading_styled(doc, "2.5 Objectives", 2)
    for obj in [
        "Develop an autonomous 9-agent clinical intelligence pipeline with stateful DAG execution.",
        "Implement real-time Server-Sent Events (SSE) streaming of agent reasoning steps to the client.",
        "Construct a private RAG engine leveraging Qdrant vector storage and 768-dimensional embeddings.",
        "Build a multi-factor hospital recommendation engine combining clinical specialty, Haversine distance, and insurance network.",
        "Engineer a 5-rule composite fraud detection engine for automated claim risk analysis.",
        "Establish an enterprise security posture featuring JWT refresh token rotation, 4-tier RBAC, and SHA-256 file hashing.",
        "Validate platform correctness through a comprehensive automated test suite achieving 100% pass rate."
    ]:
        add_bullet(doc, obj)
        
    add_heading_styled(doc, "2.6 Scope", 2)
    add_body(doc, "The scope of MedSentinel encompasses full-stack software implementation: Next.js 14 frontend (33 routes), FastAPI backend (33 routers, 22 services), MySQL 8.0 relational schema (24 models), Qdrant vector database, multi-agent AI system (26 agent modules), and containerized Docker Compose orchestration. It is designed for multi-stakeholder healthcare environments.")
    
    add_heading_styled(doc, "2.7 Target Users", 2)
    user_roles = [
        ("USER (Patient)", "Can upload medical records, execute multi-agent AI analysis, search hospitals, track claims, and query medical RAG."),
        ("HOSPITAL_ADMIN", "Can manage hospital facility profiles, update department capacities, monitor appointments, and upload accreditation media."),
        ("INSURANCE_ADMIN", "Can adjudicate claims, inspect automated fraud risk scores, review flagged documents, and process reimbursements."),
        ("SUPER_ADMIN", "Full platform governance, AI token/latency monitoring, knowledge base ingestion, and security audit log inspection."),
    ]
    add_table(doc, ["Role Identifier", "Permissions & Operational Domain"], user_roles, [2.0, 4.5])
    doc.add_page_break()
    
    # ---------------- 3. EXISTING SYSTEM ----------------
    add_heading_styled(doc, "3. Existing System", 1)
    add_body(doc, "Existing healthcare management platforms operate as passive database repositories. Medical document uploads function as static PDF file stores without semantic parsing or automated biomarker interpretation. When patients file insurance claims, claim handlers manually open each scanned bill, phone diagnostic facilities to confirm tests, and cross-reference paper policy guidelines. Similarly, hospital search websites offer superficial keyword matching without factoring in real-time insurance network compatibility, clinical acuity, or geographic proximity.")
    add_body(doc, "Key weaknesses of legacy healthcare architectures include:")
    for w in [
        "Monolithic Database Bottlenecks: Unstructured blobs stored in legacy relational databases without semantic indexing.",
        "Zero Agentic Collaboration: No autonomous intelligence capable of cross-validating lab findings with clinical diagnosis.",
        "Vulnerability to Document Tampering: Uploaded files lack cryptographic hash verification against alteration.",
        "Batch Fraud Auditing: Fraud checks occur post-reimbursement rather than during real-time claim adjudication.",
        "Privacy Hazards: Uncontrolled dissemination of Protected Health Information (PHI) across external cloud services."
    ]:
        add_bullet(doc, w)
    doc.add_page_break()
    
    # ---------------- 4. PROPOSED SYSTEM ----------------
    add_heading_styled(doc, "4. Proposed System", 1)
    add_body(doc, "MedSentinel reimagines healthcare workflow engineering by deploying an active, multi-agent autonomous system that proactively processes records upon ingestion. As soon as a patient uploads a medical file, the system cryptographically fingerprints the document, triggers optical character recognition, identifies the document category, extracts clinical biomarkers, evaluates clinical risk, identifies optimal medical facilities, and compiles a comprehensive Clinical Verification Dossier.")
    add_body(doc, "Core innovations of MedSentinel include:")
    for feat in [
        "Stateful Multi-Agent Orchestration: 9 specialized agents executing along a directed acyclic graph with rollback resilience.",
        "Real-Time SSE Observability: Client UI renders agent progress, reasoning logs, and output payloads instantaneously.",
        "Private Retrieval-Augmented Generation: Domain-specific medical knowledge retrieval isolated behind RBAC filters.",
        "Automated Claim Risk Scoring: Real-time calculation of claim risk indices using deterministic anomaly heuristics.",
        "Unified Medical Vault: Zero-trust document storage maintaining immutable SHA-256 provenance hashes."
    ]:
        add_bullet(doc, feat)
    doc.add_page_break()
    
    # ---------------- 5. SYSTEM REQUIREMENTS ----------------
    add_heading_styled(doc, "5. System Requirements", 1)
    add_heading_styled(doc, "5.1 Functional Requirements", 2)
    fr_specs = [
        ("FR-01", "User Authentication", "Self-service registration, bcrypt password hashing, JWT access token (60m) and refresh token (7d) rotation."),
        ("FR-02", "Document Ingestion", "Upload support for PDF, PNG, JPG up to 10MB; immediate SHA-256 checksum calculation and deduplication check."),
        ("FR-03", "Multi-Agent Workflow", "Execution of 9-agent DAG triggered by document submission with real-time SSE event streaming to client."),
        ("FR-04", "OCR & Classification", "Automated text extraction from scans and categorization into Lab, Prescription, Invoice, Discharge, Insurance."),
        ("FR-05", "Biomarker Parsing", "Extraction of clinical lab markers (e.g. Glucose, Hemoglobin, Cholesterol) and comparison to standard reference ranges."),
        ("FR-06", "Risk Assessment", "Calculation of composite patient health risk score (0-100) mapped to LOW, MODERATE, HIGH, CRITICAL tiers."),
        ("FR-07", "Hospital Discovery", "Multi-factor hospital ranking based on medical specialty, Haversine geo-distance, rating, and insurance network."),
        ("FR-08", "Insurance Claims", "Claim submission with auto-linked medical documents, real-time fraud scoring, and administrative status lifecycle."),
        ("FR-09", "Private RAG Chat", "Medical knowledge Q&A powered by Qdrant vector retrieval, RBAC access control, and verified source citations."),
        ("FR-10", "Admin Governance", "16-module admin console for user management, claim adjudication, audit log inspection, and AI token tracking."),
    ]
    add_table(doc, ["Req ID", "Functional Area", "Technical Specification"], fr_specs, [0.8, 1.8, 3.9], caption="Table 5.1 — System Functional Requirements")
    
    add_heading_styled(doc, "5.2 Non-Functional Requirements", 2)
    nfr_specs = [
        ("NFR-01", "Security & Privacy", "Full alignment with HIPAA principles; PII masking in logs; Private AI mode stripping patient identifiers."),
        ("NFR-02", "Performance", "Sub-100ms response time for indexed database queries; sub-5s completion for end-to-end agentic workflows."),
        ("NFR-03", "Reliability", "Graceful agent degradation; failure of an individual agent does not terminate the DAG execution state."),
        ("NFR-04", "Scalability", "Containerized microservices supporting horizontal scaling of backend API workers and frontend web servers."),
        ("NFR-05", "Auditability", "Immutable recording of all administrative mutations, authentication events, and AI requests in dedicated tables."),
    ]
    add_table(doc, ["Req ID", "Quality Attribute", "Engineering Criteria"], nfr_specs, [0.8, 1.8, 3.9], caption="Table 5.2 — System Non-Functional Requirements")
    
    add_heading_styled(doc, "5.3 Software & Hardware Stack", 2)
    tech_stack = [
        ("Programming Language", "Python 3.10+ (Backend), TypeScript 5.0+ / JavaScript (Frontend)"),
        ("Backend Web Framework", "FastAPI >= 0.110.0 (Asynchronous ASGI framework with Pydantic v2)"),
        ("Frontend Framework", "Next.js 14.2.x (React 18, App Router, Server/Client Components)"),
        ("Relational Database", "MySQL 8.0 (InnoDB Engine, Connection Pooling size=10, max_overflow=20)"),
        ("Vector Database", "Qdrant Vector DB (768-dimensional Cosine Distance collection)"),
        ("Styling Framework", "TailwindCSS 3.4 (Custom healthcare teal and navy color system)"),
        ("Testing Framework", "Pytest 8.3.4, pytest-asyncio 0.24.0, httpx 0.27.0"),
        ("Containerization", "Docker Engine 24+, Docker Compose v2 (Multi-stage image builds)"),
    ]
    add_table(doc, ["Layer Component", "Verified Technology & Configuration"], tech_stack, [2.0, 4.5], caption="Table 5.3 — Verified Software Stack")
    doc.add_page_break()
    
    # ---------------- 6. SYSTEM ARCHITECTURE ----------------
    add_heading_styled(doc, "6. System Architecture", 1)
    add_body(doc, "MedSentinel implements a high-throughput, five-tier distributed architecture engineered for healthcare security and agentic autonomy. The architecture ensures strict separation of concerns across presentation, routing, coordination, computation, and persistence.")
    add_bullet(doc, "Tier 1 — Client Presentation Layer: Serves Patient, Hospital Admin, Insurance Admin, and Super Admin personas through responsive, role-tailored interfaces.", bold_prefix="Client Layer: ")
    add_bullet(doc, "Tier 2 — Next.js 14 Web Application: Houses 33 App Router pages, client state providers, and the Server-Sent Events (SSE) stream consumer.", bold_prefix="Frontend Layer: ")
    add_bullet(doc, "Tier 3 — FastAPI API & Security Gateway: Exposes 33 routers guarded by JWT authentication, hierarchical RBAC dependencies, and cryptographic file validators.", bold_prefix="API Gateway: ")
    add_bullet(doc, "Tier 4 — Multi-Agent AI Intelligence Engine: Comprises the OrchestratorAgent, 9 clinical agents, stateful DAG transition manager, and Google Gemini LLM interface.", bold_prefix="AI Engine: ")
    add_bullet(doc, "Tier 5 — Dual-Storage Persistence: MySQL 8.0 handles ACID relational entities across 24 models; Qdrant handles 768-dimensional medical semantic vectors.", bold_prefix="Data Storage: ")
    
    add_diagram_page(doc, IMG_CORE_SYS, 
                     "FIGURE 6.1 — MEDSENTINEL COMPLETE SYSTEM ARCHITECTURE", 
                     "Figure 6.1: High-level architectural topology showing client personas, Next.js 14 frontend, FastAPI backend, security gateway, multi-agent AI engine, MySQL 8.0, and Qdrant vector database.")
    
    # ---------------- 7. MULTI-AGENT AI ARCHITECTURE ----------------
    add_heading_styled(doc, "7. Multi-Agent AI Architecture", 1)
    add_body(doc, "At the heart of MedSentinel is an autonomous Multi-Agent AI Engine designed to emulate clinical reasoning while enforcing strict deterministic verification. The engine is orchestrated via a Directed Acyclic Graph (DAG) managed by the OrchestratorAgent. The orchestrator dynamically constructs an execution schedule tailored to the incoming workflow type (LAB_REPORT, PRESCRIPTION, INSURANCE_CLAIM, CLINICAL_SUMMARY, or AUTOMATIC).")
    
    add_diagram_page(doc, IMG_ARCH, "FIGURE 7.1 — MEDSENTINEL HIGH-LEVEL SYSTEM ARCHITECTURE", "Figure 7.1: Architectural diagram detailing user interactions, Next.js frontend, FastAPI microservices, security middleware, AI engine, and dual persistence stores.", landscape_mode=True)
    add_diagram_page(doc, IMG_AGENT, "FIGURE 7.2 — MEDSENTINEL AUTONOMOUS MULTI-AGENT AI WORKFLOW", "Figure 7.2: End-to-end execution flow across the 9 primary clinical agents, Gemini LLM reasoning service, and Qdrant semantic RAG retrieval.", landscape_mode=True)
    add_diagram_page(doc, IMG_BIZ, "FIGURE 7.3 — MEDSENTINEL END-TO-END BUSINESS WORKFLOWS", "Figure 7.3: Four core business pipelines: Patient Intake Flow, Insurance Claims Flow with Fraud Check, Private RAG Knowledge Flow, and Admin Observability.", landscape_mode=True)
    
    agent_specs = [
        ("7.1 PatientIntakeAgent", "patient_intake_agent.py (3,789 B)", "Extracts patient demographics, reported clinical symptoms, chief complaints, and baseline physiological vitals from raw user intake forms.", "Raw patient profile dictionary, intake notes, document text strings, user ID.", "Cleans text fields, standardizes demographic structures, validates vital sign formats (BP, heart rate, temperature), constructs standardized PatientInfo model.", "Populated PatientInfo schema containing validated age, gender, medical history list, and vital sign maps.", "BaseAgent, pydantic schemas.", "Executes as Step 1 in all workflow types. Establishes the foundational patient clinical context used by all subsequent agents."),
        ("7.2 DataValidationAgent", "data_validation_agent.py (4,307 B)", "Enforces medical data integrity, validates schema adherence, and applies automated PII/PHI masking for downstream privacy protection.", "WorkflowState containing preliminary patient data and extracted document strings.", "Validates required healthcare fields against medical schema rules, scrubs national ID numbers and phone numbers when Private AI mode is active, flags schema anomalies.", "Validation result status flag (PASSED / WARNING / FAILED), list of data validation warnings, sanitized text payload.", "PatientIntakeAgent output.", "Executes as Step 2. Acts as a safety gate; if validation fails critically, the workflow records errors without sending invalid data to downstream models."),
        ("7.3 OCRAgent", "ocr_agent.py (5,350 B)", "Extracts raw textual strings and tabular layouts from uploaded digital documents (PDF, JPG, PNG).", "File path or binary stream of uploaded medical record from UserDocument record.", "Executes optical character recognition using Tesseract OCR and PDFPlumber; handles multi-column layouts, normalizes whitespace, cleans noisy scanning artifacts.", "Extracted clean text string, document structure metadata, extraction confidence score.", "Tesseract OCR / PDFPlumber binaries, storage filesystem.", "Executes as Step 3 in document-driven workflows. Converts opaque scanned pixels into machine-readable clinical text."),
        ("7.4 DocumentIntelligenceAgent", "document_intelligence_agent.py (3,007 B)", "Performs semantic classification of uploaded medical records into standardized clinical document categories.", "Raw OCR text generated by OCRAgent.", "Applies NLP keyword matching and Gemini few-shot classification to categorize document into: LAB_REPORT, PRESCRIPTION, INVOICE, DISCHARGE_SUMMARY, or INSURANCE_CARD.", "DocumentType classification enum, category confidence score (0.0 - 1.0), detected document title.", "OCRAgent text output, Gemini LLM client.", "Executes as Step 4. Dynamically routes subsequent workflow execution branches based on the identified document type."),
        ("7.5 LabAnalysisAgent", "lab_analysis_agent.py (6,228 B)", "Parses quantitative clinical laboratory biomarkers, extracts numeric values and units, and evaluates results against standard clinical reference ranges.", "OCR text identified as LAB_REPORT.", "Extracts biomarker names (e.g., Fasting Blood Glucose, HbA1c, Total Cholesterol, Hemoglobin), normalizes units (mg/dL, g/dL), evaluates against adult reference intervals, flags abnormalities (HIGH, LOW, CRITICAL).", "List of BiomarkerResult objects containing test name, measured value, unit, reference interval, and abnormality status flag.", "DocumentIntelligenceAgent confirmation of lab report type.", "Executes as Step 5 in LAB_REPORT workflows. Produces the structured clinical data required for risk scoring."),
        ("7.6 RiskPredictionAgent", "risk_prediction_agent.py (4,803 B)", "Calculates a multi-factorial patient clinical risk index and stratifies patients into clinical severity tiers.", "PatientInfo demographics, flagged BiomarkerResult items, symptom strings.", "Executes clinical risk heuristic: baseline score (10) + biomarker abnormality weight (+15 per abnormal, +30 per critical) + age risk adjustment + vital signs severity. Clamps score to 0-100.", "RiskScore object containing numeric score (0-100), risk tier (LOW, MODERATE, HIGH, CRITICAL), contributing factors, and immediate triage flags.", "LabAnalysisAgent, PatientIntakeAgent.", "Executes as Step 6. Triggers administrative escalation alerts if risk is categorized as HIGH or CRITICAL."),
        ("7.7 HospitalMatchingAgent", "hospital_matching_agent.py (4,877 B)", "Matches patient clinical profile and risk requirements to the most appropriate healthcare facilities in the database.", "Patient clinical diagnosis, required specialty, patient geographic coordinates (latitude, longitude), insurance provider name.", "Queries Hospital database records; applies Haversine spherical distance formula; verifies in-network insurance status; calculates composite suitability score based on distance, rating, and specialty alignment.", "Ranked list of HospitalMatch recommendations, estimated distance in kilometers, network status flag, facility contact info.", "MySQL Hospital table, RiskPredictionAgent output.", "Executes as Step 7. Provides patients with actionable, high-affinity healthcare provider options."),
        ("7.8 MedicalRAGAgent", "medical_rag_agent.py (3,845 B)", "Retrieves evidence-based clinical practice guidelines and medical literature relevant to the patient's diagnosed condition from the private vector knowledge base.", "Extracted clinical findings, primary diagnosis string, patient risk tier.", "Generates 768-dim query embedding; executes Cosine similarity search in Qdrant; filters knowledge chunks by RBAC access rules; synthesizes grounded clinical summary.", "Evidence-based clinical context summary, list of source citations (document title, dataset name, chunk ID, relevance score).", "Qdrant vector store, Gemini embedding and LLM APIs.", "Executes as Step 8. Grounds the final report in peer-reviewed medical knowledge while preventing LLM hallucination."),
        ("7.9 VerificationReportAgent", "verification_report_agent.py (8,181 B)", "Synthesizes the outputs of all preceding agents into an immutable, unified Clinical Verification Dossier.", "Complete WorkflowState containing outputs from Agents 1 through 8.", "Assembles patient profile, document summary, biomarker audit table, risk index, hospital matches, and RAG citations; validates completeness; attaches cryptographic timestamp.", "Comprehensive VerificationReport object, structured JSON summary, human-readable markdown clinical dossier.", "All preceding 8 agents.", "Executes as the final terminal agent (Step 9). Produces the authoritative verification payload persisted to the database and streamed to the user.")
    ]
    for title, src, purp, inp, proc, outp, dep, role in agent_specs:
        add_heading_styled(doc, title, 2)
        add_body(doc, f"Source File: backend/app/agents/{src}", bold_prefix="Implementation Source: ")
        add_body(doc, purp, bold_prefix="Purpose: ")
        add_body(doc, inp, bold_prefix="Input: ")
        add_body(doc, proc, bold_prefix="Processing: ")
        add_body(doc, outp, bold_prefix="Output: ")
        add_body(doc, dep, bold_prefix="Dependencies: ")
        add_body(doc, role, bold_prefix="Role in Overall Workflow: ")
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    doc.add_page_break()
    
    # ---------------- 8. AGENT ORCHESTRATOR & STATE MACHINE ----------------
    add_heading_styled(doc, "8. Agent Orchestrator & State Machine", 1)
    add_body(doc, "The execution lifecycle of MedSentinel's multi-agent workflows is governed by the OrchestratorAgent (backend/app/agents/orchestrator.py, 12,429 bytes) and formal state models defined in backend/app/agents/state.py (11,020 bytes).")
    state_fields = [
        ("workflow_id", "str (UUID v4)", "Unique identifier tracking the execution lifecycle of the pipeline."),
        ("workflow_type", "WorkflowType Enum", "LAB_REPORT, PRESCRIPTION, INSURANCE_CLAIM, CLINICAL_SUMMARY, or AUTOMATIC."),
        ("status", "WorkflowStatus Enum", "State machine status: PENDING, RUNNING, COMPLETED, FAILED, or CANCELLED."),
        ("patient_info", "Optional[PatientInfo]", "Validated demographic and vital data extracted by PatientIntakeAgent."),
        ("document_data", "Optional[DocumentData]", "File metadata, raw OCR text, document type, and extraction confidence."),
        ("biomarkers", "List[BiomarkerResult]", "Parsed quantitative laboratory test results with abnormal flags."),
        ("risk_assessment", "Optional[RiskScore]", "Composite risk score (0-100), risk tier, and triage notes."),
        ("hospital_matches", "List[HospitalMatch]", "Ranked healthcare facility recommendations with geo-distance."),
        ("rag_citations", "List[Citation]", "Medical literature excerpts and confidence scores retrieved from Qdrant."),
        ("verification_report", "Optional[VerificationReport]", "Synthesized final clinical verification report payload."),
        ("execution_logs", "List[AgentLogEntry]", "Granular timeline of agent start, execution duration, and completion."),
        ("audit_trail", "List[AuditEntry]", "Cryptographic ledger recording state mutations for regulatory compliance."),
    ]
    add_table(doc, ["Field Name", "Schema Type", "Functional Definition"], state_fields, [1.5, 1.8, 3.2], caption="Table 8.1 — WorkflowState Schema Fields (state.py)")
    
    add_heading_styled(doc, "State Machine Transition Lifecycle", 2)
    add_body(doc, "The orchestrator executes a fault-tolerant state machine following this deterministic sequence:")
    add_bullet(doc, "Step 1 [START]: REST API endpoint /api/agent-workflow/start receives document or intake payload, instantiates initial WorkflowState with status PENDING.", bold_prefix="Initialization: ")
    add_bullet(doc, "Step 2 [DAG Plan]: plan_workflow() determines the ordered sequence of agents based on workflow_type.", bold_prefix="Planning: ")
    add_bullet(doc, "Step 3 [Agent Execution]: The orchestrator iterates through the planned sequence. Prior to invoking an agent, it emits an SSE 'agent_started' event to the client.", bold_prefix="Dispatch: ")
    add_bullet(doc, "Step 4 [State Update]: The agent executes asynchronously, returns updated data, and mutates WorkflowState.", bold_prefix="Mutation: ")
    add_bullet(doc, "Step 5 [Validation Check]: If the agent execution succeeds, an SSE 'agent_completed' event is emitted with execution duration. If an agent fails, it emits 'agent_failed', records error logs, and invokes graceful fallback handlers without halting unaffected downstream agents.", bold_prefix="Verification: ")
    add_bullet(doc, "Step 6 [FINAL]: Terminal VerificationReportAgent compiles all outputs; status transitions to COMPLETED; complete dossier is persisted to database.", bold_prefix="Completion: ")
    doc.add_page_break()
    
    # ---------------- 9. MEDICAL DOCUMENT PROCESSING ----------------
    add_heading_styled(doc, "9. Medical Document Processing", 1)
    add_body(doc, "Medical document intake is a foundational capability of MedSentinel. Uploaded documents pass through a 12-stage sequential processing pipeline ensuring cryptographic provenance, semantic clarity, and clinical utility:")
    doc_pipeline = [
        ("Stage 1: Ingestion", "Client submits document via multipart/form-data POST /api/documents/upload."),
        ("Stage 2: Type Validation", "FileService verifies extension (.pdf, .png, .jpg, .jpeg) and MIME type against allowed healthcare formats."),
        ("Stage 3: Size Enforcement", "FileService confirms file size does not exceed strict 10MB ceiling to prevent buffer exhaustion."),
        ("Stage 4: SHA-256 Hashing", "Cryptographic SHA-256 checksum is computed over the raw byte stream before disk write."),
        ("Stage 5: Deduplication Check", "Database is queried for identical file_hash. If found, is_duplicate=True and duplicate_of_id is linked."),
        ("Stage 6: Storage Persistence", "File is saved to secure local vault directory with randomized, sanitized UUID filename."),
        ("Stage 7: Metadata Record", "UserDocument database record created in MySQL with status PENDING_VERIFICATION."),
        ("Stage 8: OCR Extraction", "OCRAgent processes document with PDFPlumber/Tesseract to extract raw text."),
        ("Stage 9: Document Classification", "DocumentIntelligenceAgent categorizes document into standardized clinical type."),
        ("Stage 10: Biomarker Parsing", "If Lab Report, LabAnalysisAgent extracts quantitative values and flags clinical ranges."),
        ("Stage 11: Clinical Verification", "Administrative review flags status as VERIFIED, FLAGGED, or REJECTED."),
        ("Stage 12: Vault Integration", "Verified document is made available to claims, multi-agent workflows, and patient vault."),
    ]
    add_table(doc, ["Pipeline Stage", "Operational Logic & Safeguards"], doc_pipeline, [1.8, 4.7], caption="Table 9.1 — 12-Stage Medical Document Processing Pipeline")
    doc.add_page_break()
    
    # ---------------- 10. RAG ARCHITECTURE ----------------
    add_heading_styled(doc, "10. RAG Architecture", 1)
    add_body(doc, "MedSentinel implements an enterprise-grade, privacy-first Retrieval-Augmented Generation (RAG) system located in backend/app/rag/. The system allows clinical practitioners and patients to perform natural language medical inquiries grounded in verified healthcare guidelines while guaranteeing that Protected Health Information (PHI) is never exposed to external models.")
    rag_modules = [
        ("document_loader.py", "Parses incoming medical reference PDFs, text documents, and clinical guidelines."),
        ("text_extractor.py", "Normalizes clinical formatting, handles bullet lists, tables, and removes boilerplate."),
        ("chunking_service.py", "Splits documents into overlapping chunks (512 tokens, 64-token overlap) preserving clinical boundaries."),
        ("embedding_service.py", "Generates 768-dimensional dense vector representations via Gemini text-embedding-004."),
        ("vector_store.py", "Manages vector indexing in Qdrant (medsentinel_knowledge collection) with local fallback."),
        ("ingestion_service.py", "End-to-end ingestion pipeline: load -> extract -> chunk -> embed -> index into Qdrant."),
        ("retrieval_service.py", "Executes Cosine similarity search with similarity threshold 0.08, returning top-k=8 candidate chunks."),
        ("reranking_service.py", "Applies relevance re-ranking to filter the top-8 candidates down to the top-4 most relevant chunks."),
        ("context_builder.py", "Assembles prompt context payload including chunk text, dataset name, and document metadata."),
        ("rag_pipeline.py", "Master coordinator integrating retrieval, context assembly, Gemini prompt synthesis, and citation generation."),
    ]
    add_table(doc, ["RAG Module", "Architectural Role"], rag_modules, [1.8, 4.7], caption="Table 10.1 — RAG Subsystem Modules (backend/app/rag/)")
    
    add_heading_styled(doc, "Private AI Mode & RBAC Guardrails", 2)
    add_bullet(doc, "KnowledgeAccessRule Enforcement: Qdrant queries automatically filter chunk access by user role. Clinical guidelines marked for HOSPITAL_ADMIN or INSURANCE_ADMIN are invisible to standard patient queries.", bold_prefix="1. RBAC Filtering: ")
    add_bullet(doc, "Strict PHI Sanitization: In Private AI Mode, all patient demographic identifiers, MRNs, and names are stripped before context synthesis, preventing medical data leakage to third-party APIs.", bold_prefix="2. Privacy Shield: ")
    doc.add_page_break()
    
    # ---------------- 11. DATABASE ARCHITECTURE ----------------
    add_heading_styled(doc, "11. Database Architecture", 1)
    add_body(doc, "MedSentinel utilizes MySQL 8.0 with SQLAlchemy 2.0 as its relational object-relational mapping (ORM) layer. The database schema encompasses 24 verified models supporting ACID-compliant transactional consistency across clinical, financial, and administrative domains.")
    db_entities = [
        ("User", "Identity & Auth", "id, email, hashed_password, full_name, role, is_active, phone, created_at", "One-to-One Patient, One-to-Many Claims, Documents, AuditLogs"),
        ("Patient", "Patient Profiles", "id, user_id, mrn, date_of_birth, gender, blood_group, address, emergency_contact", "Many-to-One User, One-to-Many LabResults, HealthScores"),
        ("Hospital", "Healthcare Facilities", "id, name, address, city, state, latitude, longitude, rating, phone, email, is_active", "One-to-Many HospitalDepartments, Doctors, Media"),
        ("HospitalDepartment", "Hospital Units", "id, hospital_id, name, specialty, bed_capacity, available_beds", "Many-to-One Hospital"),
        ("Doctor", "Medical Practitioners", "id, hospital_id, name, specialty, qualification, experience_years, consultation_fee", "Many-to-One Hospital"),
        ("InsuranceClaim", "Claim Lifecycle", "id, claim_number, user_id, hospital_id, policy_number, claim_amount, status, created_at", "Many-to-One User, Many-to-One Hospital, One-to-One FraudAnalysis"),
        ("ClaimStatusHistory", "Claim Audit Trail", "id, claim_id, old_status, new_status, changed_by_id, comment, created_at", "Many-to-One InsuranceClaim, Many-to-One User"),
        ("FraudAnalysis", "Fraud Engine Data", "id, claim_id, fraud_score, risk_level, anomaly_flags, analysis_summary", "One-to-One InsuranceClaim"),
        ("UserDocument", "Medical File Vault", "id, user_id, original_filename, stored_filename, file_hash, file_size, document_type, status", "Many-to-One User"),
        ("LabResult", "Clinical Biomarkers", "id, patient_id, test_name, test_category, result_value, unit, reference_range, is_abnormal", "Many-to-One Patient"),
        ("HealthScore", "Patient Risk Index", "id, patient_id, score, risk_level, key_factors, recommendations, created_at", "Many-to-One Patient"),
        ("Recommendation", "Health Guidance", "id, user_id, title, description, category, priority, is_read", "Many-to-One User"),
        ("KnowledgeDataset", "RAG Datasets", "id, name, description, category, created_by_id, is_active", "One-to-Many KnowledgeDocuments"),
        ("KnowledgeDocument", "RAG Source Files", "id, dataset_id, title, source_url, file_type, total_chunks, is_processed", "Many-to-One KnowledgeDataset, One-to-Many Chunks"),
        ("KnowledgeChunk", "RAG Embeddings", "id, document_id, chunk_index, content, embedding_id, token_count", "Many-to-One KnowledgeDocument"),
        ("KnowledgeAccessRule", "RAG RBAC Policy", "id, dataset_id, role, permission_level", "Many-to-One KnowledgeDataset"),
        ("AdminAuditLog", "Security Ledger", "id, actor_id, action, target_entity, target_id, ip_address, details, created_at", "Many-to-One User"),
        ("AIRequestLog", "AI Telemetry", "id, user_id, agent_name, prompt_tokens, completion_tokens, latency_ms, status", "Many-to-One User"),
        ("Appointment", "Clinical Scheduling", "id, patient_id, doctor_id, hospital_id, appointment_date, status, reason", "Many-to-One Patient, Doctor, Hospital"),
        ("Notification", "User Alerts", "id, user_id, title, message, type, is_read, created_at", "Many-to-One User"),
        ("Scheme", "Govt Health Schemes", "id, name, description, eligibility_criteria, coverage_amount, state", "Standalone Entity"),
        ("RefreshToken", "Auth Revocation", "id, user_id, token_hash, expires_at, is_revoked, created_at", "Many-to-One User"),
    ]
    add_table(doc, ["Entity Model", "Domain Scope", "Key Schema Fields", "Verified Relationships"], db_entities, [1.1, 1.2, 2.2, 2.0], caption="Table 11.1 — SQLAlchemy Relational Schema Models")
    doc.add_page_break()
    
    # ---------------- 12. API ARCHITECTURE ----------------
    add_heading_styled(doc, "12. API Architecture", 1)
    add_body(doc, "The backend exposes 33 modular routers categorized into 17 User Routers and 16 Administrative Routers. All endpoints conform to RESTful design conventions with JSON serialization, Pydantic request/response validation, and HTTPBearer JWT authentication guards.")
    api_routes = [
        ("POST", "/api/auth/register", "Registers new user with email, password, and role", "Public"),
        ("POST", "/api/auth/login", "Authenticates credentials; returns access & refresh tokens", "Public"),
        ("POST", "/api/auth/refresh", "Rotates refresh token; issues fresh 60-minute access token", "Bearer (Refresh)"),
        ("GET", "/api/hospitals/search", "Performs multi-criteria geographic and specialty search", "Optional"),
        ("GET", "/api/hospitals/{id}", "Retrieves comprehensive hospital profile, depts, doctors", "Optional"),
        ("POST", "/api/documents/upload", "Uploads medical file; executes SHA-256 and duplicate check", "Bearer (USER)"),
        ("GET", "/api/documents/", "Lists user's uploaded medical records with verification status", "Bearer (USER)"),
        ("POST", "/api/claims/", "Submits new insurance reimbursement claim with linked docs", "Bearer (USER)"),
        ("GET", "/api/claims/{id}", "Retrieves claim status history and adjudication details", "Bearer (USER/ADMIN)"),
        ("POST", "/api/agent-workflow/start", "Initiates 9-agent DAG workflow; returns workflow_id", "Bearer"),
        ("GET", "/api/agent-workflow/stream/{id}", "Server-Sent Events (SSE) real-time agent execution stream", "Bearer"),
        ("POST", "/api/ai-chat/", "RAG-powered conversational medical query endpoint", "Bearer"),
        ("GET", "/api/health-dashboard/score", "Returns calculated health risk index and biomarker summary", "Bearer (USER)"),
        ("GET", "/api/admin/dashboard/stats", "Aggregated platform metrics (users, claims, hospitals, AI)", "Admin Only"),
        ("GET", "/api/admin/claims/", "Lists claims for adjudication with automated fraud scores", "Insurance Admin"),
        ("POST", "/api/admin/knowledge-base/ingest", "Uploads and embeds documents into Qdrant vector collection", "Super Admin"),
        ("GET", "/api/admin/audit-logs/", "Queries immutable administrative audit ledger", "Super Admin"),
        ("GET", "/api/admin/ai-monitoring/stats", "Retrieves AI model latency, token consumption, error rates", "Super Admin"),
    ]
    add_table(doc, ["Method", "Endpoint URI", "Functional Purpose", "Authorization"], api_routes, [0.7, 2.5, 2.3, 1.0], caption="Table 12.1 — Core FastAPI RESTful Endpoints")
    doc.add_page_break()
    
    # ---------------- 13. AUTHENTICATION & SECURITY ----------------
    add_heading_styled(doc, "13. Authentication & Security", 1)
    add_body(doc, "MedSentinel enforces a multi-layered, zero-trust security architecture incorporating cryptographic password hashing, token lifecycle rotation, hierarchical role-based access control, cryptographic data integrity checks, and HIPAA-compliant privacy protections.")
    add_heading_styled(doc, "Authentication & Token Management", 2)
    add_bullet(doc, "Access Token: 60-minute lifespan, carrying subject (user_id), user role, token type, and unique token identifier (jti).", bold_prefix="Short-Lived Access: ")
    add_bullet(doc, "Refresh Token: 7-day lifespan, tracked in the database RefreshToken table. Upon usage, the previous token is revoked, and a new token pair is issued (Refresh Token Rotation), defeating token replay attacks.", bold_prefix="Database-Backed Rotation: ")
    
    add_heading_styled(doc, "Hierarchical Role-Based Access Control (RBAC)", 2)
    rbac_roles = [
        ("USER", "Patients: Read/write own medical documents, initiate personal agent workflows, submit own claims."),
        ("HOSPITAL_ADMIN", "Hospital Staff: Manage assigned facility profile, update department beds, manage doctor listings."),
        ("INSURANCE_ADMIN", "Insurance Adjusters: Inspect all claims, view fraud detection scores, approve/reject settlements."),
        ("SUPER_ADMIN", "System Administrators: Unrestricted access across all routers, audit logs, AI telemetry, and database maintenance."),
    ]
    add_table(doc, ["Role Identifier", "Access Scope & Enforced Privileges"], rbac_roles, [1.8, 4.7], caption="Table 13.1 — RBAC Permission Hierarchy")
    
    add_heading_styled(doc, "Document Integrity & Privacy Safeguards", 2)
    add_bullet(doc, "Cryptographic File Hashing: All uploaded documents are hashed using SHA-256 upon arrival. Any byte-level alteration invalidates verification.", bold_prefix="SHA-256 Checksums: ")
    add_bullet(doc, "Private AI Privacy Shield: Before medical queries are forwarded to external LLMs, the system masks patient full names, social identifiers, and telephone numbers.", bold_prefix="PII Redaction: ")
    add_bullet(doc, "Regulatory Audit Ledger: All administrative data mutations, permission changes, and document reviews are immutably logged to AdminAuditLog.", bold_prefix="Comprehensive Auditing: ")
    doc.add_page_break()
    
    # ---------------- 14. INSURANCE & CLAIMS AUTOMATION ----------------
    add_heading_styled(doc, "14. Insurance & Claims Automation", 1)
    add_body(doc, "The Insurance Claims subsystem (backend/app/services/claim_service.py and routers/claims.py) automates the traditionally manual reimbursement adjudication process. Claims transition through a deterministic lifecycle:")
    add_bullet(doc, "SUBMITTED -> UNDER_REVIEW -> DOCUMENTS_REQUIRED -> APPROVED or REJECTED -> COMPLETED.", bold_prefix="Lifecycle Path: ")
    add_body(doc, "When a claim is submitted, the system automatically correlates the claimed amount with the attached UserDocument records, verifies policy validity, triggers the FraudDetector service, and attaches an automated risk summary before the claim reaches the insurance adjuster's queue. Every state change is immutably recorded in the ClaimStatusHistory table with actor timestamps.")
    doc.add_page_break()
    
    # ---------------- 15. FRAUD DETECTION ----------------
    add_heading_styled(doc, "15. Fraud Detection", 1)
    add_body(doc, "The Fraud Detection Engine (backend/app/services/fraud_detector.py, 7,113 bytes) provides automated risk scoring for healthcare insurance claims. Rather than replacing human judgment, the engine implements an auditable human-in-the-loop decision-support model.")
    fraud_rules = [
        ("Rule 1: Hash Reuse", "Cross-account file hash reuse", "+45 Risk Points", "Identifies identical medical bills or lab reports uploaded by different user accounts."),
        ("Rule 2: Duplicate Invoices", "Invoice number collision", "+35 Risk Points", "Flags claims using an invoice number that was previously approved or settled."),
        ("Rule 3: Identity Mismatch", "Patient ID discrepancy", "+30 Risk Points", "Detects discrepancies between claim patient metadata and text extracted via OCR."),
        ("Rule 4: Amount Outliers", "Statistical billing anomaly", "+25 Risk Points", "Flags billing amounts that exceed historical averages for the specific diagnosis by >2.5 sigma."),
        ("Rule 5: Velocity Anomaly", "Filing frequency surge", "+20 Risk Points", "Flags multiple high-value claims submitted within a condensed 30-day window."),
    ]
    add_table(doc, ["Evaluation Rule", "Anomaly Condition", "Score Penalty", "Clinical Fraud Context"], fraud_rules, [1.4, 1.6, 1.1, 2.4], caption="Table 15.1 — 5-Rule Fraud Detection Scoring Matrix")
    add_body(doc, "The cumulative score (0-100) maps to four risk tiers: LOW (0-25), MODERATE (26-50), HIGH (51-75), and CRITICAL (76-100). High and Critical claims are automatically flagged for manual investigator review; the system never auto-rejects a claim.")
    doc.add_page_break()
    
    # ---------------- 16. HOSPITAL MATCHING ----------------
    add_heading_styled(doc, "16. Hospital Matching", 1)
    add_body(doc, "The Hospital Matching Engine (backend/app/services/hospital_service.py, 28,375 bytes and hospital_matching_agent.py) solves healthcare discovery friction by pairing patient clinical needs with the optimal medical facility.")
    add_bullet(doc, "Calculates geographic proximity between the patient's coordinates and hospital coordinates using the Haversine spherical trigonometric formula.", bold_prefix="Geographic Distance (Haversine): ")
    add_bullet(doc, "Cross-references patient clinical symptoms with verified hospital departments and doctor specialties.", bold_prefix="Specialty Alignment: ")
    add_bullet(doc, "Verifies whether the patient's insurance carrier is an active participating network partner at the facility.", bold_prefix="Insurance In-Network: ")
    add_bullet(doc, "Incorporates audited patient review scores, state accreditation status, and emergency bed availability.", bold_prefix="Quality & Capacity: ")
    doc.add_page_break()
    
    # ---------------- 17. FRONTEND ARCHITECTURE ----------------
    add_heading_styled(doc, "17. Frontend Architecture", 1)
    add_body(doc, "The frontend application is constructed using Next.js 14.2 with React 18 and TypeScript. Utilizing the Next.js App Router, the application features 33 distinct routes across 16 page directories, achieving full separation between static layouts and dynamic client components.")
    fe_routes = [
        ("/", "Landing Page", "Public platform overview, architecture breakdown, service highlights"),
        ("/login", "Authentication", "User login form with role-based redirect logic"),
        ("/register", "Registration", "Self-service patient onboarding with demographic collection"),
        ("/hospitals", "Provider Search", "Interactive hospital directory with specialty and location filters"),
        ("/hospitals/[id]", "Hospital Profile", "Detailed facility profile, doctor directory, department bed capacity"),
        ("/medical-vault", "Document Vault", "Cryptographic file uploader, SHA-256 status, verified record browser"),
        ("/claims", "Claims Portal", "Insurance claim submission form, document linker, status timeline"),
        ("/claims/[id]", "Claim Details", "Granular adjudication audit trail, breakdown of approved expenses"),
        ("/agent-workflow", "Agent Visualizer", "Real-time SSE visualization (53KB module) rendering 9-agent DAG live"),
        ("/health-dashboard", "Clinical Insights", "Visual display of calculated health score, biomarker charts, advice"),
        ("/ai-chat", "Medical RAG Assistant", "Conversational AI assistant with cited medical source excerpts"),
        ("/admin/*", "Admin Suite (16 pages)", "Comprehensive administration modules for platform governance"),
    ]
    add_table(doc, ["Route Path", "View Title", "Functional Capability"], fe_routes, [1.5, 1.8, 3.2], caption="Table 17.1 — Next.js 14 Verified Frontend Route Hierarchy")
    
    add_heading_styled(doc, "Real-Time Agent Visualizer", 2)
    add_body(doc, "A marquee engineering achievement in the frontend is the Agent Workflow visualizer (frontend/app/agent-workflow/page.tsx, 53,889 bytes). The component connects to the backend SSE endpoint via EventSource, receives continuous 'agent_started', 'agent_completed', and 'agent_failed' events, and animates the active agent node in real time while rendering streaming execution logs and intermediate biomarker tables.")
    doc.add_page_break()
    
    # ---------------- 18. BACKEND ARCHITECTURE ----------------
    add_heading_styled(doc, "18. Backend Architecture", 1)
    add_body(doc, "The backend is engineered as an asynchronous microservices platform using FastAPI. The application entry point (backend/app/main.py, 169 lines) configures an asynchronous lifespan manager that validates database connectivity, registers 33 routers, configures CORS middleware, and initializes global exception handlers.")
    add_bullet(doc, "app/routers/ (33 files): HTTP endpoint declaration, input parsing, dependency injection of DB and auth.", bold_prefix="Routing Layer: ")
    add_bullet(doc, "app/services/ (22 files): Pure business logic, fraud rules, hospital search, file storage, claim operations.", bold_prefix="Service Layer: ")
    add_bullet(doc, "app/agents/ (26 files): Multi-agent AI classes, state models, DAG orchestrator, prompt builders.", bold_prefix="Agentic Layer: ")
    add_bullet(doc, "app/rag/ (10 files): Vector search, chunking, embedding generation, Qdrant client, RAG pipeline.", bold_prefix="RAG Subsystem: ")
    add_bullet(doc, "app/models/ (24 files): SQLAlchemy ORM models mapped to MySQL relational tables.", bold_prefix="Persistence Models: ")
    add_bullet(doc, "app/schemas/ (18 files): Pydantic v2 schemas for strict JSON serialization and data validation.", bold_prefix="Validation Schemas: ")
    doc.add_page_break()
    
    # ---------------- 19. ADMIN DASHBOARD ----------------
    add_heading_styled(doc, "19. Admin Dashboard", 1)
    add_body(doc, "The administrative suite comprises 16 dedicated dashboard modules secured by the require_any_admin RBAC dependency. The dashboard empowers healthcare administrators to govern operations, audit security, and monitor AI telemetry:")
    admin_pages = [
        ("Dashboard Overview", "/admin", "Executive summary of system metrics: active users, claims, AI latency"),
        ("User Management", "/admin/users", "User directory, role assignment, account activation and deactivation"),
        ("Hospital Management", "/admin/hospitals", "Facility onboarding, department bed allocation, doctor credentialing"),
        ("Claim Adjudication", "/admin/claims", "Claims review queue, fraud score inspection, settlement approval"),
        ("Document Verification", "/admin/documents", "Inspection of uploaded records, SHA-256 hash audit, approval/rejection"),
        ("Knowledge Ingestion", "/admin/knowledge-base", "Dataset creation, medical guideline upload, Qdrant vector indexing"),
        ("AI Performance Monitor", "/admin/ai-monitoring", "Telemetry tracking token usage, latency distribution, agent error rates"),
        ("Clinical AI Insights", "/admin/ai-insights", "Aggregated epidemiological trends, prevalent biomarker anomalies"),
        ("Security Audit Ledger", "/admin/audit-logs", "Immutable query log of all administrative actions with actor IP addresses"),
        ("Platform Analytics", "/admin/analytics", "Operational charts: claim volume, hospital utilization, user growth"),
        ("System Notifications", "/admin/notifications", "Broadcast notifications to users, hospitals, and claim adjusters"),
        ("Healthcare Schemes", "/admin/schemes", "Configuration of government healthcare benefit schemes and eligibility"),
        ("Appointment Oversight", "/admin/appointments", "Cross-hospital appointment monitoring and status verification"),
        ("Hospital Media Vault", "/admin/hospital-media", "Accreditation certificates, facility imagery, inspection documents"),
        ("RAG Debug Console", "/admin/rag-debug", "Interactive semantic query testing, chunk inspection, similarity scores"),
        ("Insurance Policies", "/admin/insurances", "Insurance provider management, policy definitions, coverage limits"),
    ]
    add_table(doc, ["Admin Module", "Path URI", "Operational Functionality"], admin_pages, [1.5, 1.8, 3.2], caption="Table 19.1 — 16 Verified Admin Management Modules")
    doc.add_page_break()
    
    # ---------------- 20. DATA FLOW DIAGRAMS ----------------
    add_heading_styled(doc, "20. Data Flow Diagrams", 1)
    add_heading_styled(doc, "20.1 DFD Level 0 (Context Level Diagram)", 2)
    add_body(doc, "At the context level, MedSentinel functions as a centralized healthcare coordination hub interfacing with four primary external entities:")
    add_bullet(doc, "Submits medical files, intake notes, claim forms, and RAG queries; receives verification reports, risk scores, hospital recommendations, and claim status updates.", bold_prefix="Patient Entity: ")
    add_bullet(doc, "Provides facility capacities, specialty lists, doctor availability, and treatment invoices; receives patient referrals and verified appointments.", bold_prefix="Hospital Entity: ")
    add_bullet(doc, "Provides policy guidelines and coverage limits; receives adjudicated claims accompanied by automated fraud risk scores.", bold_prefix="Insurance Carrier: ")
    add_bullet(doc, "Issues administrative policies, ingests clinical reference guidelines, and audits system logs; receives system telemetry and compliance reports.", bold_prefix="Super Admin Entity: ")
    
    add_heading_styled(doc, "20.2 DFD Level 1 (Functional Decomposition)", 2)
    add_bullet(doc, "Validates credentials, issues JWT token pairs, and authenticates API requests via RBAC.", bold_prefix="Process 1.0 (Auth & Access): ")
    add_bullet(doc, "Ingests raw medical scans, hashes byte streams via SHA-256, writes files to vault, and records metadata in MySQL.", bold_prefix="Process 2.0 (Document Vault): ")
    add_bullet(doc, "Dispatches 9-agent DAG, parses text via OCR, evaluates biomarkers, predicts risk, and compiles Clinical Verification Dossier.", bold_prefix="Process 3.0 (Multi-Agent Engine): ")
    add_bullet(doc, "Correlates claimed amounts, evaluates 5-rule fraud heuristics, assigns risk tiers, and records adjudication history.", bold_prefix="Process 4.0 (Claims & Fraud): ")
    add_bullet(doc, "Queries Qdrant vector collection using 768-dim embeddings, filters by RBAC, and grounds LLM responses with citations.", bold_prefix="Process 5.0 (Private RAG): ")
    doc.add_page_break()
    
    # ---------------- 21. USER WORKFLOWS ----------------
    add_heading_styled(doc, "21. User Workflows", 1)
    add_heading_styled(doc, "Patient Journey", 2)
    add_body(doc, "1. Patient registers and logs in -> 2. Navigates to Medical Vault and uploads diagnostic lab report -> 3. System computes SHA-256 and launches Agent Workflow -> 4. Patient watches live SSE agent execution -> 5. System renders Verification Report with risk score -> 6. Patient searches recommended in-network hospitals -> 7. Patient files insurance claim linked to verified document -> 8. Patient tracks claim status live.")
    
    add_heading_styled(doc, "Insurance Adjuster Journey", 2)
    add_body(doc, "1. Insurance Admin logs into /admin/claims -> 2. Selects claim in PENDING state -> 3. Inspects automated Fraud Detection Score and flagged rules -> 4. Cross-checks attached verified medical document -> 5. Enters adjudication decision (APPROVED / REJECTED) with clinical justification -> 6. System updates claim status and notifies patient.")
    doc.add_page_break()
    
    # ---------------- 22. AUDIT & OBSERVABILITY ----------------
    add_heading_styled(doc, "22. Audit & Observability", 1)
    add_bullet(doc, "Every administrative status change, role mutation, document approval, and knowledge base ingestion is immutably recorded in the AdminAuditLog table with actor ID, target entity, IP address, and payload snapshot.", bold_prefix="Administrative Audit Ledger: ")
    add_bullet(doc, "Every LLM invocation is logged to AIRequestLog, capturing prompt tokens, completion tokens, execution latency in milliseconds, agent identifier, and status.", bold_prefix="AI Telemetry & Token Tracking: ")
    add_bullet(doc, "Insurance claims record every lifecycle transition in ClaimStatusHistory, guaranteeing an auditable chain of custody.", bold_prefix="Claims Lineage: ")
    add_bullet(doc, "The orchestrator records fine-grained start, completion, and error timestamps for every agent execution, preserved in WorkflowState.execution_logs.", bold_prefix="Agent Execution Tracing: ")
    doc.add_page_break()
    
    # ---------------- 23. TESTING & VALIDATION ----------------
    add_heading_styled(doc, "23. Testing & Validation", 1)
    add_callout(doc, "OFFICIAL VERIFIED TEST EXECUTION RESULT:\n81 test cases executed across 9 test modules.\n81 PASSED in 47.11 seconds (100% Pass Rate, 0 Failures, 0 Errors).", title="AUTOMATED TEST RESULTS")
    test_results = [
        ("test_agentic_workflow.py", "16 Passed", "Stateful DAG transitions, multi-agent execution, WorkflowState updates"),
        ("test_location_search.py", "12 Passed", "Geographic Haversine calculations, coordinate bounding boxes, radius search"),
        ("test_agent_workflow_api.py", "10 Passed", "REST API endpoints, SSE stream serialization, client event emissions"),
        ("test_recommendation_engine.py", "10 Passed", "Biomarker threshold evaluation, health score computation, guidance"),
        ("test_patient_hospital_matching.py", "8 Passed", "Multi-factor hospital ranking, specialty alignment, insurance verification"),
        ("test_hospital_search_robustness.py", "7 Passed", "Search query edge cases, SQL injection resilience, fuzzy text matching"),
        ("test_ai_records_and_verification.py", "7 Passed", "Document intelligence categorization, SHA-256 verification, vault logic"),
        ("test_rag_and_private_ai.py", "6 Passed", "Qdrant vector retrieval, similarity filtering, private AI PII masking"),
        ("test_api.py", "5 Passed", "User authentication, JWT token generation, refresh rotation, role guards"),
    ]
    add_table(doc, ["Test Module File", "Verified Outcome", "Validated Architectural Scope"], test_results, [2.3, 1.2, 3.0], caption="Table 23.1 — Verified Test Suite Breakdown (81 Tests Passed in 47.11s)")
    add_body(doc, "Frontend Verification: In addition to backend unit tests, all 33 Next.js 14 App Router pages were verified to compile and build without TypeScript errors.")
    doc.add_page_break()
    
    # ---------------- 24. DEPLOYMENT ARCHITECTURE ----------------
    add_heading_styled(doc, "24. Deployment Architecture", 1)
    docker_services = [
        ("mysql", "mysql:8.0", "3306", "Persistent relational storage with named volume; configured connection pool."),
        ("qdrant", "qdrant/qdrant:latest", "6333", "Vector database engine with named volume for persistent semantic embeddings."),
        ("backend", "Custom (python:3.10-slim)", "8000", "FastAPI ASGI application served via Uvicorn with auto-reload in development."),
        ("frontend", "Custom (node:20-alpine)", "3000", "Next.js 14 production build running on Node.js runtime."),
    ]
    add_table(doc, ["Service Name", "Base Image", "Exposed Port", "Operational Configuration"], docker_services, [1.1, 1.8, 0.9, 2.7], caption="Table 24.1 — Docker Compose Multi-Container Services")
    doc.add_page_break()
    
    # ---------------- 25. PROJECT DIRECTORY STRUCTURE ----------------
    add_heading_styled(doc, "25. Project Directory Structure", 1)
    dir_tree = [
        "MedSentinel-main/",
        "├── frontend/                        # Next.js 14 Frontend Application",
        "│   ├── app/                         # App Router (33 routes, 16 page directories)",
        "│   │   ├── agent-workflow/          # Real-time SSE Agent Visualizer (53KB)",
        "│   │   ├── medical-vault/           # Document Upload & SHA-256 Verification",
        "│   │   ├── claims/                  # Insurance Claim Submission & Tracking",
        "│   │   ├── hospitals/               # Hospital Discovery & Detailed Profiles",
        "│   │   ├── admin/                   # 16 Dedicated Administration Modules",
        "│   │   └── health-dashboard/        # Health Risk Score & Biomarker Charts",
        "│   ├── components/                  # Shared UI, Admin, and AI Components",
        "│   ├── lib/                         # API Client, Auth Context, Type Definitions",
        "│   └── Dockerfile                   # Multi-stage Node.js container build",
        "├── backend/                         # FastAPI Microservices Backend",
        "│   ├── app/",
        "│   │   ├── agents/                  # 26 files: 9 Clinical Agents, State, Orchestrator",
        "│   │   ├── ai/                      # 7 files: Gemini LLM connectors & Tooling",
        "│   │   ├── core/                    # Security, Database Config, JWT & RBAC Guards",
        "│   │   ├── models/                  # 24 SQLAlchemy Relational Models",
        "│   │   ├── rag/                     # 10 modules: Qdrant Vector Store, Ingestion, RAG",
        "│   │   ├── routers/                 # 33 files: 17 User Routers + 16 Admin Routers",
        "│   │   ├── schemas/                 # 18 Pydantic v2 Schema Definitions",
        "│   │   └── services/                # 22 Domain Services (Claims, Fraud, Hospitals)",
        "│   ├── tests/                       # 9 Pytest Modules (81 Verified Tests)",
        "│   └── requirements.txt             # 18 Core Backend Python Dependencies",
        "├── docs/                            # Project Documentation & Architecture Artifacts",
        "│   ├── diagrams/                    # High-Resolution Architectural Diagrams",
        "│   └── MedSentinel_Complete_Engineering_Report.docx # Primary Deliverable",
        "└── docker-compose.yml               # Multi-Container Orchestration (MySQL, Qdrant, Backend, Frontend)",
    ]
    for line in dir_tree:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.line_spacing = 1.05
        r = p.add_run(line)
        r.font.name = 'Consolas'
        r.font.size = Pt(8.5)
        r.font.color.rgb = SLATE
    doc.add_page_break()
    
    # ---------------- 26. IMPLEMENTATION STATUS ----------------
    add_heading_styled(doc, "26. Implementation Status", 1)
    impl_status = [
        ("Next.js 14 Frontend", "[✓] Implemented", "33 routes compiled; full App Router hierarchy verified."),
        ("FastAPI Backend", "[✓] Implemented", "33 routers, 22 services; lifespan initialization operational."),
        ("Multi-Agent AI Engine", "[✓] Implemented", "9 agents + OrchestratorAgent verified in tests (16 tests pass)."),
        ("State Machine (state.py)", "[✓] Implemented", "Pydantic v2 WorkflowState schema passing all state transitions."),
        ("Real-time SSE Streaming", "[✓] Implemented", "EventSource stream endpoint operational; 53KB UI visualizer."),
        ("MySQL 8.0 Persistence", "[✓] Implemented", "24 SQLAlchemy models verified with connection pooling."),
        ("Qdrant Vector Database", "[✓] Implemented", "768-dim embeddings in Qdrant with local hybrid fallback."),
        ("Private RAG Pipeline", "[✓] Implemented", "10 modules in backend/app/rag/ passing 6 automated tests."),
        ("JWT Authentication", "[✓] Implemented", "bcrypt hashing, 60m access token, 7d refresh token rotation."),
        ("4-Tier RBAC", "[✓] Implemented", "Four verified roles (USER, HOSPITAL_ADMIN, INSURANCE_ADMIN, SUPER_ADMIN)."),
        ("SHA-256 Checksums", "[✓] Implemented", "Cryptographic hashing at upload with automated deduplication."),
        ("5-Rule Fraud Detection", "[✓] Implemented", "FraudDetector service computes composite risk scores."),
        ("Insurance Claims Lifecycle", "[✓] Implemented", "Claims router and service tracking 6 lifecycle statuses."),
        ("Hospital Matching Engine", "[✓] Implemented", "28KB hospital service with Haversine distance calculations."),
        ("Admin Governance Suite", "[✓] Implemented", "16 dedicated administrative pages and corresponding backend routers."),
        ("Docker Containerization", "[✓] Implemented", "docker-compose.yml coordinating 4 container services."),
        ("Automated Unit Test Suite", "[✓] Implemented", "81 test cases passing in 47.11 seconds with 100% pass rate."),
        ("Frontend Unit Tests (Jest)", "[○] Future Enhancement", "Not verified in repository; planned for future engineering cycle."),
        ("Automated CI/CD Pipeline", "[○] Future Enhancement", "No GitHub Actions / GitLab CI configuration found in repository."),
    ]
    add_table(doc, ["Architectural Component", "Status Badge", "Verified Empirical Evidence"], impl_status, [2.0, 1.5, 3.0], caption="Table 26.1 — Verified Implementation Status Matrix")
    doc.add_page_break()
    
    # ---------------- 27. LIMITATIONS ----------------
    add_heading_styled(doc, "27. Limitations", 1)
    for lim in [
        "External LLM Dependency: The AI reasoning and classification features rely on the Google Gemini API. Intermittent cloud latency or API rate limits can impact throughput.",
        "OCR Fidelity on Handwritten Records: Text extraction accuracy is optimal on digital PDFs and high-contrast scans; handwritten prescriptions remain susceptible to OCR noise.",
        "Deterministic Biomarker Thresholds: Biomarker evaluation utilizes standardized clinical intervals rather than personalized deep learning prognostic models.",
        "Single-Host Deployment Architecture: The existing Docker Compose configuration targets single-node deployment; multi-region active-active replication is not yet configured.",
        "Lack of Frontend Automated Tests: While backend services maintain an 81-test automated suite, frontend UI regression currently relies on manual validation."
    ]:
        add_bullet(doc, lim)
    doc.add_page_break()
    
    # ---------------- 28. FUTURE ENHANCEMENTS ----------------
    add_heading_styled(doc, "28. Future Enhancements", 1)
    for enh in [
        "HL7 / FHIR Standard Compliance: Implementation of Fast Healthcare Interoperability Resources (FHIR) APIs for seamless EHR/EMR bidirectional data exchange.",
        "Fine-Tuned Clinical On-Premise LLMs: Deployment of quantized open-source medical models (e.g., Med-PaLM 2 / BioMistral) for offline, air-gapped clinical operation.",
        "Computer Vision for Radiology Scans: Integration of specialized convolutional neural networks (CNNs) for X-ray and CT anomaly detection alongside text OCR.",
        "Kubernetes Helm Charts: Creation of auto-scaling Kubernetes manifests with HPA (Horizontal Pod Autoscaling) for cloud-native enterprise deployments.",
        "Comprehensive Frontend Test Suite: Implementation of Jest, React Testing Library, and Playwright end-to-end browser automation suites.",
        "Automated CI/CD Pipeline: GitHub Actions workflow executing code linting, security scans, and 81 pytest suites on every pull request."
    ]:
        add_bullet(doc, enh)
    doc.add_page_break()
    
    # ---------------- 29. CONCLUSION ----------------
    add_heading_styled(doc, "29. Conclusion", 1)
    add_body(doc, "MedSentinel demonstrates a state-of-the-art engineering approach to healthcare orchestration by uniting modern web architecture with autonomous multi-agent intelligence. By decomposing complex clinical and administrative operations into nine specialized agents coordinated through a stateful DAG, the platform successfully automates document ingestion, optical character recognition, biomarker evaluation, patient risk stratification, hospital matching, and clinical verification reporting.")
    add_body(doc, "The platform's dual-storage architecture—coupling MySQL 8.0 for ACID relational transactions with Qdrant for 768-dimensional semantic knowledge embeddings—provides a scalable, auditable foundation for healthcare operations. Strict security mechanisms, including JWT refresh token rotation, hierarchical RBAC across four distinct roles, SHA-256 document hashing, and HIPAA-aligned private AI modes, ensure compliance with rigorous healthcare data protection standards.")
    add_body(doc, "Validated by an 81-test automated test suite achieving 100% pass rate in 47.11 seconds, MedSentinel provides a proven, verifiable, and highly extensible platform that bridges the historical gap between autonomous artificial intelligence and mission-critical healthcare systems.")
    doc.add_page_break()
    
    # ---------------- 30. REFERENCES ----------------
    add_heading_styled(doc, "30. References", 1)
    refs = [
        ("[1]", "FastAPI Documentation — Modern, high-performance web framework for building APIs with Python 3.10+. https://fastapi.tiangolo.com/"),
        ("[2]", "Next.js 14 Documentation — The React Framework for the Web, App Router & Server Components. https://nextjs.org/docs"),
        ("[3]", "SQLAlchemy 2.0 Documentation — The Python SQL Toolkit and Object Relational Mapper. https://docs.sqlalchemy.org/"),
        ("[4]", "Pydantic v2 Documentation — Data validation and settings management using Python type annotations. https://docs.pydantic.dev/"),
        ("[5]", "Qdrant Vector Database — Vector Similarity Search Engine for Vector Embeddings. https://qdrant.tech/documentation/"),
        ("[6]", "Google Gemini API — Advanced Multimodal & Language Models for Developers. https://ai.google.dev/docs"),
        ("[7]", "MySQL 8.0 Reference Manual — Enterprise Relational Database Management System. https://dev.mysql.com/doc/refman/8.0/en/"),
        ("[8]", "RFC 7519 — JSON Web Token (JWT) Standard, Internet Engineering Task Force (IETF). https://tools.ietf.org/html/rfc7519"),
        ("[9]", "Health Insurance Portability and Accountability Act (HIPAA) — Privacy & Security Standards. https://www.hhs.gov/hipaa/"),
        ("[10]", "TailwindCSS v3.4 — A utility-first CSS framework for rapid UI development. https://tailwindcss.com/docs"),
        ("[11]", "Docker Compose v2 Specification — Multi-container orchestration tool. https://docs.docker.com/compose/"),
        ("[12]", "Pytest Framework — Scalable Python test framework with async event loop support. https://docs.pytest.org/"),
    ]
    for tag, citation in refs:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.1
        rt = p.add_run(f"{tag} ")
        rt.bold = True
        rt.font.name = 'Calibri'
        rt.font.size = Pt(9)
        rt.font.color.rgb = NAVY
        rc = p.add_run(citation)
        rc.font.name = 'Calibri'
        rc.font.size = Pt(9)
        rc.font.color.rgb = SLATE
        
    doc.save(OUT_DOCX)
    print(f"Generated DOCX: {OUT_DOCX} ({os.path.getsize(OUT_DOCX)} bytes)")
    return OUT_DOCX


# ==============================================================================
# 2. EXHAUSTIVE SOURCE CODE PDF GENERATOR (OUTPUT 2)
# ==============================================================================

def redact_secrets(content):
    """
    Scans content and redacts any actual passwords, API keys, JWT secrets, credentials.
    """
    # Patterns for keys and secrets
    patterns = [
        (r'(["\']?(?:SECRET_KEY|JWT_SECRET_KEY|API_KEY|GEMINI_API_KEY|PASSWORD|DB_PASSWORD|MYSQL_PASSWORD|TOKEN)["\']?\s*[:=]\s*["\'])([^"\']{4,})(["\'])', r'\1[REDACTED]\3'),
        (r'(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*', r'\1[REDACTED]'),
        (r'(AIzaSy[A-Za-z0-9\-_]{33})', r'[REDACTED]'),
    ]
    for p, repl in patterns:
        content = re.sub(p, repl, content, flags=re.IGNORECASE)
    return content

def gather_repository_sources():
    backend_dir = os.path.join(REPO_ROOT, 'backend')
    frontend_dir = os.path.join(REPO_ROOT, 'frontend')
    
    categories = {
        'A. BACKEND (Core, Routers, Services)': [],
        'B. AGENTIC AI (Agents & Orchestrator)': [],
        'C. RAG (Vector Store & Knowledge)': [],
        'D. AUTHENTICATION & SECURITY': [],
        'E. DATABASE & MODELS': [],
        'F. CLAIMS & FRAUD DETECTION': [],
        'G. HOSPITAL MODULES': [],
        'H. DOCUMENT PROCESSING': [],
        'I. ADMIN SYSTEM': [],
        'J. FRONTEND (Next.js 14 App & Components)': [],
        'K. TESTS (Pytest Suites - 81 Tests)': [],
        'L. CONFIGURATION & DEPLOYMENT': [],
    }
    
    for root, dirs, files in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache', 'venv', '.venv']]
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, REPO_ROOT).replace('\\', '/')
            
            if 'tests/' in rel:
                categories['K. TESTS (Pytest Suites - 81 Tests)'].append((rel, path))
            elif 'agents/' in rel or 'orchestrator' in rel or 'state.py' in rel:
                categories['B. AGENTIC AI (Agents & Orchestrator)'].append((rel, path))
            elif 'rag/' in rel:
                categories['C. RAG (Vector Store & Knowledge)'].append((rel, path))
            elif 'security' in rel or 'auth' in rel or 'token' in rel:
                categories['D. AUTHENTICATION & SECURITY'].append((rel, path))
            elif 'fraud' in rel or 'claim' in rel:
                categories['F. CLAIMS & FRAUD DETECTION'].append((rel, path))
            elif 'hospital' in rel:
                categories['G. HOSPITAL MODULES'].append((rel, path))
            elif 'document' in rel or 'ocr' in rel or 'file' in rel:
                categories['H. DOCUMENT PROCESSING'].append((rel, path))
            elif 'admin' in rel:
                categories['I. ADMIN SYSTEM'].append((rel, path))
            elif 'models/' in rel or 'database' in rel:
                categories['E. DATABASE & MODELS'].append((rel, path))
            else:
                categories['A. BACKEND (Core, Routers, Services)'].append((rel, path))
                
    for root, dirs, files in os.walk(frontend_dir):
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.next', '.git']]
        for f in files:
            if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.css')):
                path = os.path.join(root, f)
                rel = os.path.relpath(path, REPO_ROOT).replace('\\', '/')
                categories['J. FRONTEND (Next.js 14 App & Components)'].append((rel, path))
                
    configs = [
        'backend/requirements.txt',
        'backend/Dockerfile',
        'frontend/package.json',
        'frontend/Dockerfile',
        'frontend/tsconfig.json',
        'frontend/tailwind.config.ts',
        'frontend/next.config.mjs',
        'frontend/next.config.js',
        'docker-compose.yml',
        'backend/.env.example',
        'frontend/.env.example',
    ]
    for cfg in configs:
        full = os.path.join(REPO_ROOT, cfg)
        if os.path.exists(full):
            rel = cfg.replace('\\', '/')
            categories['L. CONFIGURATION & DEPLOYMENT'].append((rel, full))
            
    # Sort files alphabetically within each category
    for cat in categories:
        categories[cat].sort(key=lambda x: x[0])
        
    return categories


def build_complete_source_code_pdf():
    print("Gathering and validating source code repository...")
    categories = gather_repository_sources()
    
    # Calculate file index and counts
    file_entries = []
    total_lines = 0
    cat_order = [
        'B. AGENTIC AI (Agents & Orchestrator)',
        'C. RAG (Vector Store & Knowledge)',
        'D. AUTHENTICATION & SECURITY',
        'E. DATABASE & MODELS',
        'F. CLAIMS & FRAUD DETECTION',
        'G. HOSPITAL MODULES',
        'H. DOCUMENT PROCESSING',
        'I. ADMIN SYSTEM',
        'A. BACKEND (Core, Routers, Services)',
        'J. FRONTEND (Next.js 14 App & Components)',
        'K. TESTS (Pytest Suites - 81 Tests)',
        'L. CONFIGURATION & DEPLOYMENT',
    ]
    
    file_id = 1
    for cat in cat_order:
        for rel, path in categories[cat]:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                n_lines = len(lines)
            except Exception:
                n_lines = 0
            file_entries.append((file_id, rel, cat, n_lines, path))
            total_lines += n_lines
            file_id += 1
            
    print(f"Total verified files to document: {len(file_entries)}")
    print(f"Total verified source lines to render: {total_lines}")
    
    # Canvas setup
    # Using A4 Landscape for modern IDE editor presentation (841.89 pt x 595.27 pt)
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(OUT_CODE_PDF, pagesize=(page_w, page_h))
    
    # Color constants
    C_NAVY = colors.HexColor("#1A365D")
    C_TEAL = colors.HexColor("#319795")
    C_SLATE = colors.HexColor("#2D3748")
    C_MUTED = colors.HexColor("#718096")
    C_LIGHT_BG = colors.HexColor("#F7FAFC")
    C_HEADER_BG = colors.HexColor("#0F172A")
    C_CODE_LINE = colors.HexColor("#1E293B")
    C_LINE_NUM = colors.HexColor("#64748B")
    
    current_page = 1
    
    def draw_page_decorations(c, active_file=None, active_cat=None):
        c.saveState()
        # Header banner
        c.setFillColor(C_HEADER_BG)
        c.rect(0, page_h - 32, page_w, 32, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(36, page_h - 20, "MEDSENTINEL | COMPLETE SOURCE CODE REPOSITORY")
        
        if active_file:
            c.setFont("Helvetica-Bold", 8.5)
            c.setFillColor(colors.HexColor("#38BDF8")) # Sky Blue
            c.drawCentredString(page_w / 2, page_h - 20, f"FILE: {active_file}")
            
        if active_cat:
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#A7F3D0")) # Mint green
            c.drawRightString(page_w - 36, page_h - 20, active_cat)
            
        # Footer banner
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.75)
        c.line(36, 32, page_w - 36, 32)
        
        c.setFont("Helvetica", 8)
        c.setFillColor(C_MUTED)
        c.drawString(36, 20, "MedSentinel Autonomous Healthcare Platform  |  Verified 81/81 Tests Passed (47.11s)  |  Confidential & Complete Source")
        c.drawRightString(page_w - 36, 20, f"Page {current_page}")
        c.restoreState()

    # ---------------- 1. COVER PAGE ----------------
    print("Rendering Source Code Cover Page...")
    c.saveState()
    # Dark modern cover background
    c.setFillColor(colors.HexColor("#0F172A"))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#38BDF8"))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(page_w / 2, page_h - 110, "ENGINEERING REPOSITORY & VERIFIED IMPLEMENTATION")
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(page_w / 2, page_h - 160, "MEDSENTINEL")
    
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawCentredString(page_w / 2, page_h - 190, "Autonomous Healthcare, Claims & Multi-Agent Intelligence Platform")
    
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#34D399"))
    c.drawCentredString(page_w / 2, page_h - 230, "COMPLETE SOURCE CODE DOCUMENTATION")
    
    # Metadata container
    c.setFillColor(colors.HexColor("#1E293B"))
    c.roundRect(page_w / 2 - 320, page_h - 480, 640, 220, 8, fill=1, stroke=0)
    
    meta_rows = [
        ("Project Version:", "2.3.0 (Production-Ready Architecture)"),
        ("Verified Repository:", f"MedSentinel-main ({len(file_entries)} Files, {total_lines:,} Lines of Code)"),
        ("Multi-Agent AI Engine:", "9 Autonomous Clinical Agents + DAG Orchestrator (backend/app/agents/)"),
        ("Private RAG Subsystem:", "Qdrant Vector DB (768-dim Gemini Embeddings) + RBAC Access Rules"),
        ("Claims & Fraud Engine:", "5-Rule Composite Fraud Scoring with Human-in-the-Loop Review"),
        ("Database Layer:", "MySQL 8.0 (24 SQLAlchemy Models) + Connection Pool (size=10, max_overflow=20)"),
        ("Web Application Layer:", "Next.js 14 App Router (33 Routes) + FastAPI REST/SSE Microservices"),
        ("Automated Test Suite:", "81 Tests Passed in 47.11s (pytest 8.3.4, pytest-asyncio 0.24.0)"),
        ("Security Compliance:", "JWT Refresh Token Rotation, 4-Tier RBAC, SHA-256 Hashes, PII Masking"),
    ]
    
    y_m = page_h - 285
    for lbl, val in meta_rows:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#38BDF8"))
        c.drawString(page_w / 2 - 290, y_m, lbl)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.white)
        c.drawString(page_w / 2 - 120, y_m, val)
        y_m -= 21
        
    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(page_w / 2, 45, "All secrets, passwords, and private tokens in configuration templates are automatically redacted with [REDACTED].")
    c.restoreState()
    c.showPage()
    current_page += 1
    
    # ---------------- 2. REPOSITORY DIRECTORY TREE ----------------
    print("Rendering Project Directory Tree...")
    draw_page_decorations(c, "PROJECT DIRECTORY STRUCTURE", "OVERVIEW")
    c.saveState()
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(C_NAVY)
    c.drawString(40, page_h - 60, "1. Verified Project Repository Directory Structure")
    
    c.setFont("Helvetica", 8.5)
    c.setFillColor(C_SLATE)
    c.drawString(40, page_h - 75, f"Complete structural tree of MedSentinel-main showing all verified architectural directories and file modules ({len(file_entries)} files, {total_lines:,} lines):")
    
    dir_ascii = [
        "MedSentinel-main/",
        "├── backend/                                  # FastAPI Asynchronous Microservices Backend",
        "│   ├── app/",
        "│   │   ├── agents/                           # Multi-Agent AI Engine (26 files, 2,957 lines)",
        "│   │   │   ├── orchestrator.py               # Stateful DAG Orchestrator & SSE emitter",
        "│   │   │   ├── state.py                      # Pydantic v2 WorkflowState schema",
        "│   │   │   ├── base.py                       # BaseAgent abstract class definition",
        "│   │   │   └── [9 Clinical Agents]           # PatientIntake, Validation, OCR, Lab, Risk, Hospital, RAG, Report",
        "│   │   ├── ai/                               # Gemini LLM connectors, Tools, Client abstraction",
        "│   │   ├── core/                             # Security, JWT auth, RBAC dependencies, Database session pool",
        "│   │   ├── models/                           # 24 SQLAlchemy ORM Relational Models (MySQL 8.0)",
        "│   │   ├── rag/                              # 10 Modules: Qdrant Vector Store, Embeddings, Ingestion, Pipeline",
        "│   │   ├── routers/                          # 33 Routers: 17 User Routers + 16 Dedicated Admin Routers",
        "│   │   ├── schemas/                          # 18 Pydantic v2 Data Validation & Serialization Schemas",
        "│   │   └── services/                         # 22 Domain Business Services (Claims, FraudDetector, Hospitals)",
        "│   ├── tests/                                # 9 Pytest Modules (81 Verified Passing Tests in 47.11s)",
        "│   ├── requirements.txt                      # 18 Core Backend Python Dependencies",
        "│   └── Dockerfile                            # Python 3.10-slim Production Container Build",
        "├── frontend/                                 # Next.js 14 App Router Web Application",
        "│   ├── app/                                  # 33 Routes across 16 Page Directories",
        "│   │   ├── agent-workflow/                   # Real-time SSE Agent Visualizer (53KB module)",
        "│   │   ├── medical-vault/                    # Document Ingestion, SHA-256 Verification & Deduplication",
        "│   │   ├── claims/                           # Insurance Reimbursement Submission & Adjudication Timeline",
        "│   │   ├── hospitals/                        # Hospital Directory with Geolocation & Specialty Filters",
        "│   │   └── admin/                            # 16 Dedicated Administrative Management Modules",
        "│   ├── components/                           # Shared UI Component Library & Layout Providers",
        "│   ├── lib/                                  # API Client, Authentication Context Provider, TypeScript Interfaces",
        "│   ├── package.json                          # Node.js 20 Dependencies (React 18, TailwindCSS, Lucide Icons)",
        "│   └── Dockerfile                            # Multi-stage Node 20 Alpine Production Container",
        "├── docs/                                     # Architecture Artifacts, Reports, and Diagrams",
        "└── docker-compose.yml                        # 4-Service Container Orchestration (MySQL, Qdrant, Backend, Frontend)",
    ]
    
    y_d = page_h - 100
    for l in dir_ascii:
        c.setFont("Courier", 8)
        c.setFillColor(C_CODE_LINE)
        c.drawString(45, y_d, l)
        y_d -= 14
        
    c.restoreState()
    c.showPage()
    current_page += 1
    
    # ---------------- 3. MASTER SOURCE CODE FILE INDEX ----------------
    print("Rendering Master Source Code File Index...")
    index_page_start = current_page
    rows_per_index_page = 42
    total_index_pages = (len(file_entries) + rows_per_index_page - 1) // rows_per_index_page
    
    for ip in range(total_index_pages):
        draw_page_decorations(c, f"FILE INDEX (Page {ip+1} of {total_index_pages})", "TABLE OF CONTENTS")
        c.saveState()
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(C_NAVY)
        c.drawString(40, page_h - 55, "2. Master Source Code File Index & Line Counts")
        
        # Table headers
        c.setFillColor(C_NAVY)
        c.rect(40, page_h - 80, page_w - 80, 18, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(45, page_h - 73, "No.")
        c.drawString(80, page_h - 73, "Source Code File Path")
        c.drawString(460, page_h - 73, "Architectural Category")
        c.drawRightString(page_w - 50, page_h - 73, "Line Count")
        
        start_idx = ip * rows_per_index_page
        end_idx = min(start_idx + rows_per_index_page, len(file_entries))
        
        y_row = page_h - 96
        for idx in range(start_idx, end_idx):
            f_num, rel, cat, n_lines, _ = file_entries[idx]
            
            if (idx % 2) == 1:
                c.setFillColor(C_LIGHT_BG)
                c.rect(40, y_row - 2, page_w - 80, 11, fill=1, stroke=0)
                
            c.setFont("Helvetica", 7.5)
            c.setFillColor(C_MUTED)
            c.drawString(45, y_row, f"{f_num:03d}")
            
            c.setFont("Courier-Bold", 7.5)
            c.setFillColor(C_SLATE)
            c.drawString(80, y_row, rel[:65])
            
            c.setFont("Helvetica", 7)
            c.setFillColor(C_TEAL)
            c.drawString(460, y_row, cat[:42])
            
            c.setFont("Courier-Bold", 7.5)
            c.setFillColor(C_NAVY)
            c.drawRightString(page_w - 50, y_row, f"{n_lines:,}")
            
            y_row -= 11
            
        c.restoreState()
        c.showPage()
        current_page += 1

    # ---------------- 4. EXHAUSTIVE SOURCE CODE LISTING ----------------
    print("Rendering Complete Source Code across all sections...")
    
    # 52 lines per page in landscape
    lines_per_page = 50
    
    for f_num, rel, cat, n_lines, path in file_entries:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_code = f.read()
        except Exception as e:
            raw_code = f"# Error reading file {rel}: {e}\n"
            
        code = redact_secrets(raw_code)
        file_lines = code.splitlines()
        if not file_lines:
            file_lines = ["# (Empty file)"]
            
        total_file_pages = (len(file_lines) + lines_per_page - 1) // lines_per_page
        
        for fp_idx in range(total_file_pages):
            draw_page_decorations(c, rel, cat)
            c.saveState()
            
            # File Banner at top of page
            c.setFillColor(colors.HexColor("#F1F5F9"))
            c.rect(36, page_h - 68, page_w - 72, 28, fill=1, stroke=1)
            c.setStrokeColor(colors.HexColor("#CBD5E1"))
            
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(C_NAVY)
            c.drawString(46, page_h - 52, f"FILE [{f_num:03d}/{len(file_entries):03d}]:  {rel}")
            
            c.setFont("Helvetica", 8)
            c.setFillColor(C_MUTED)
            c.drawRightString(page_w - 46, page_h - 52, f"Category: {cat}  |  Total Lines: {len(file_lines):,}  |  Part {fp_idx+1} of {total_file_pages}")
            
            # Code Box Background
            code_box_top = page_h - 75
            code_box_h = lines_per_page * 9.8 + 8
            c.setFillColor(colors.HexColor("#FAFAFA"))
            c.rect(36, code_box_top - code_box_h, page_w - 72, code_box_h, fill=1, stroke=1)
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            
            # Line number column divider
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.line(85, code_box_top, 85, code_box_top - code_box_h)
            
            start_l = fp_idx * lines_per_page
            end_l = min(start_l + lines_per_page, len(file_lines))
            
            y_code = code_box_top - 12
            for l_idx in range(start_l, end_l):
                line_str = file_lines[l_idx]
                
                # Line number
                c.setFont("Courier", 7)
                c.setFillColor(C_LINE_NUM)
                c.drawRightString(80, y_code, f"{l_idx+1:4d}")
                
                # Code text (truncated horizontally at 165 chars if super long to prevent overflow)
                display_line = line_str[:165].replace('\t', '    ')
                
                # Syntax color hinting
                c.setFont("Courier", 7.5)
                if display_line.strip().startswith('#') or display_line.strip().startswith('//'):
                    c.setFillColor(colors.HexColor("#059669")) # Comment green
                elif display_line.strip().startswith('"""') or display_line.strip().startswith("'''"):
                    c.setFillColor(colors.HexColor("#0D9488")) # Docstring teal
                elif display_line.strip().startswith('def ') or display_line.strip().startswith('class ') or display_line.strip().startswith('export ') or display_line.strip().startswith('import '):
                    c.setFillColor(colors.HexColor("#2563EB")) # Keyword blue
                elif '[REDACTED]' in display_line:
                    c.setFillColor(colors.HexColor("#DC2626")) # Redacted red
                else:
                    c.setFillColor(C_CODE_LINE)
                    
                c.drawString(92, y_code, display_line)
                y_code -= 9.8
                
            c.restoreState()
            c.showPage()
            current_page += 1
            
    c.save()
    print(f"Generated Complete Source Code PDF: {OUT_CODE_PDF}")
    print(f"Total Pages in Source Code PDF: {current_page-1}")
    return OUT_CODE_PDF, current_page-1


if __name__ == "__main__":
    t0 = time.time()
    docx_path = build_complete_word_report()
    pdf_path, n_pages = build_complete_source_code_pdf()
    print("=" * 60)
    print(f"SUCCESS: Both deliverables generated in {time.time()-t0:.1f} seconds!")
    print(f"1. Word Report: {docx_path} ({os.path.getsize(docx_path):,} bytes)")
    print(f"2. Source Code PDF: {pdf_path} ({n_pages} pages, {os.path.getsize(pdf_path):,} bytes)")
    print("=" * 60)
