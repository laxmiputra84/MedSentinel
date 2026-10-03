import os
import sys
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Suppress headers/footers on page 1 (cover)
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1C2541"))
            self.drawString(40, 805, "AI DATA ANALYST AGENT — MASTER ENGINEERING ROADMAP (WEEKS 1-10)")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#6C757D"))
            self.drawRightString(555, 805, "ENTERPRISE SAAS SPECIFICATION")
            
            # Header rule
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(40, 798, 555, 798)

            # Footer rule
            self.line(40, 45, 555, 45)
            # Footer
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#6C757D"))
            self.drawString(40, 32, "Confidential & Proprietary • Full-Stack AI Engineering Architecture")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(555, 32, page_text)
        self.restoreState()

def generate_roadmap_pdf(output_filename="AI_Data_Analyst_Agent_Master_Roadmap.pdf"):
    pdf = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=50,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    # Color palette
    NAVY_PRIMARY = colors.HexColor("#0B132B")
    NAVY_SECONDARY = colors.HexColor("#1C2541")
    BLUE_ACCENT = colors.HexColor("#2563EB")
    BLUE_LIGHT = colors.HexColor("#EFF6FF")
    DARK_GRAY = colors.HexColor("#1E293B")
    MID_GRAY = colors.HexColor("#475569")
    LIGHT_GRAY = colors.HexColor("#F1F5F9")
    BORDER_COLOR = colors.HexColor("#CBD5E1")
    GREEN_ACCENT = colors.HexColor("#059669")
    YELLOW_ACCENT = colors.HexColor("#D97706")
    RED_ACCENT = colors.HexColor("#DC2626")

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=NAVY_PRIMARY,
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=BLUE_ACCENT,
        alignment=0
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=MID_GRAY
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=NAVY_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=BLUE_ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'SectionH3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=NAVY_SECONDARY,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=DARK_GRAY
    )

    body_bold = ParagraphStyle(
        'BodyDarkBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=DARK_GRAY
    )

    code_style = ParagraphStyle(
        'CodeText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=NAVY_PRIMARY
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=DARK_GRAY
    )

    table_body_bold = ParagraphStyle(
        'TableBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=NAVY_PRIMARY
    )

    badge_completed = ParagraphStyle(
        'BadgeCompleted',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=GREEN_ACCENT
    )

    badge_partial = ParagraphStyle(
        'BadgePartial',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=YELLOW_ACCENT
    )

    badge_notstarted = ParagraphStyle(
        'BadgeNotStarted',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=RED_ACCENT
    )

    story = []

    # ================= COVER BANNER / HEADER =================
    story.append(Spacer(1, 10))
    story.append(Paragraph("AI DATA ANALYST AGENT", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Enterprise Multi-Agent Data Analysis, Automated Profiling, Natural-Language SQL & Statistical Insights Platform", subtitle_style))
    story.append(Spacer(1, 8))
    
    meta_text = "<b>Target Stack:</b> Next.js 14 (App Router, TypeScript, Tailwind CSS) | Python FastAPI | MySQL 8.0 | LangGraph / Multi-Agent Engine | Recharts & Plotly<br/>" \
                "<b>Theme:</b> Enterprise Dark Navy (#0B132B / #1C2541) with Minimal Electric Blue Accents (#2563EB / #38BDF8)<br/>" \
                "<b>Target Audience:</b> CSE Fresher / Junior AI Engineer building a Tier-1 Industry-Grade Portfolio & Production SaaS Product"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE_ACCENT, spaceBefore=4, spaceAfter=12))

    # ================= 1. CURRENT PROJECT AUDIT =================
    story.append(Paragraph("1. Current Project Status Audit & Gap Analysis", h1_style))
    story.append(Paragraph("This audit reflects the exact state of your existing codebase (FastAPI backend with JWT/OTP, Agent workflow architecture, Next.js dark navy dashboard, MySQL schema), outlining what is preserved, what requires pivoting to Data Analytics, and what needs to be constructed from scratch.", body_style))
    story.append(Spacer(1, 6))

    audit_data = [
        [Paragraph("Category", table_header_style), Paragraph("Current Codebase State", table_header_style), Paragraph("Action Required for AI Data Analyst Agent", table_header_style)],
        [
            Paragraph("1. What is already completed", table_body_bold),
            Paragraph("• FastAPI server with modular router structure<br/>• JWT auth + OTP + Refresh Token lifecycle<br/>• User management, audit logs, and notification schemas<br/>• Agent orchestrator, base agent state machine, and tool execution system<br/>• Next.js layout with dark navy theme, Lucide icons, responsive sidebar, protected route wrapper", table_body_style),
            Paragraph("Keep and reuse 100% as the platform foundation. The auth engine, agent state-machine, and UI shell are already production-grade.", table_body_style)
        ],
        [
            Paragraph("2. What is partially completed", table_body_bold),
            Paragraph("• Document upload router (handles files, but tuned for medical docs)<br/>• Analytics endpoint (returns static/mock KPI counts)<br/>• AI chat router (general conversational LLM without dataset context)<br/>• Agent Workflow Visualizer UI (visualizes agent DAG steps, needs dataset execution nodes)", table_body_style),
            Paragraph("Refactor upload to parse tabular datasets (CSV, XLSX, Parquet, JSON), hook chat to SQL/Pandas execution tool, and wire visualizer to data-profiling nodes.", table_body_style)
        ],
        [
            Paragraph("3. What is missing", table_body_bold),
            Paragraph("• Tabular data ingestion & in-memory DuckDB / Pandas sandbox<br/>• Automated exploratory data analysis (EDA) & summary statistics<br/>• Text-to-SQL & SQL-to-visualization code generation agent<br/>• Natural-language query interface with chart renderer<br/>• Automated PDF / Executive Summary Report generation<br/>• Export engine (CSV, Excel, Cleaned JSON, PDF Reports)", table_body_style),
            Paragraph("Implement in Phase 2 & Phase 3 as core functional agents (Data Ingestion, Cleaning, SQL Gen, Visualization, and Reporting agents).", table_body_style)
        ],
        [
            Paragraph("4. What should be improved", table_body_bold),
            Paragraph("• Database connection pooling & dataset metadata tables in MySQL<br/>• Sandboxed Python code execution safety (AST parsing, timeout guards)<br/>• Dynamic charting UI (add Recharts / Plotly.js for interactive time-series, bar, scatter, correlation heatmaps)", table_body_style),
            Paragraph("Upgrade frontend with dynamic chart engines; add rigorous safety guards on generated SQL and pandas snippets.", table_body_style)
        ],
        [
            Paragraph("5. What should be implemented next", table_body_bold),
            Paragraph("• Immediate: Dataset schema & CSV/Excel streaming ingestion API<br/>• Immediate: Auto-profiling service (missing values, types, distributions)<br/>• Next: Text-to-SQL + Text-to-Pandas LangGraph agent pipeline", table_body_style),
            Paragraph("Follow the Phase 1 & Phase 2 roadmap to transition the data pipeline immediately.", table_body_style)
        ]
    ]

    t_audit = Table(audit_data, colWidths=[110, 230, 200])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_SECONDARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_audit)
    story.append(Spacer(1, 10))

    # ================= 2. PROJECT MODULE FEATURE MATRIX =================
    story.append(Paragraph("2. Project Modules & Feature Status Matrix", h1_style))
    story.append(Paragraph("Complete breakdown of all 22 required enterprise modules mapped against current project assets.", body_style))
    story.append(Spacer(1, 4))

    feat_matrix = [
        [Paragraph("Module / Feature", table_header_style), Paragraph("Status", table_header_style), Paragraph("Current Codebase Baseline", table_header_style), Paragraph("Target Enhancement for AI Data Analyst", table_header_style)],
        [Paragraph("1. Authentication", table_body_bold), Paragraph("✅ COMPLETED", badge_completed), Paragraph("JWT, bcrypt hashing, refresh token, OTP in FastAPI & Next.js", table_body_style), Paragraph("Add project-level API keys and workspace access scoping", table_body_style)],
        [Paragraph("2. Dashboard Shell", table_body_bold), Paragraph("✅ COMPLETED", badge_completed), Paragraph("Next.js dark navy layout, sidebar, stats cards, navbar", table_body_style), Paragraph("Replace domain stats with Dataset Metrics, Query Latency, and Active Datasets", table_body_style)],
        [Paragraph("3. User / Project Mgmt", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("User tables and profile editing completed", table_body_style), Paragraph("Add multi-workspace/project entity linking datasets & chat sessions", table_body_style)],
        [Paragraph("4. File Management", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Upload router and local storage handler present", table_body_style), Paragraph("Add dataset storage registry with versioning, S3/local storage abstraction", table_body_style)],
        [Paragraph("5. CSV / Excel Upload", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("Only general file/image/PDF uploads exist", table_body_style), Paragraph("Streaming upload, chunked multipart, automatic encoding detection", table_body_style)],
        [Paragraph("6. Dataset Processing", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("No tabular data engine integrated", table_body_style), Paragraph("Polars / DuckDB / Pandas schema inference, type coercion, row counting", table_body_style)],
        [Paragraph("7. Data Cleaning Engine", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Auto-handling of missing values, duplicates, outliers, whitespace stripping", table_body_style)],
        [Paragraph("8. Data Profiling", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Automated summary stats, distribution histograms, skewness, correlation matrix", table_body_style)],
        [Paragraph("9. SQL Generation", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Text-to-SQL agent with schema injection, DML blocklist, EXPLAIN check", table_body_style)],
        [Paragraph("10. NL Data Queries", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("General chat router only", table_body_style), Paragraph("Semantic router directing queries to SQL vs Python Pandas vs Direct LLM answer", table_body_style)],
        [Paragraph("11. AI-Generated Insights", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Automated anomaly detection, trend detection, business recommendations", table_body_style)],
        [Paragraph("12. Charts & Visualizations", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Basic CSS / Tailwind indicators in dashboard", table_body_style), Paragraph("Dynamic Recharts & Plotly component rendering from LLM JSON specs", table_body_style)],
        [Paragraph("13. Statistical Analysis", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Hypothesis testing (t-test, ANOVA), correlation, linear regression, seasonality", table_body_style)],
        [Paragraph("14. Data Analyst Chat", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Basic AI Chat router exists", table_body_style), Paragraph("Full Conversational Agent with dataset memory, code execution sandbox, artifacts", table_body_style)],
        [Paragraph("15. Report Generation", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Automated Executive Data Brief PDF & HTML generation with charts", table_body_style)],
        [Paragraph("16. Export Engine", table_body_bold), Paragraph("🔴 NOT STARTED", badge_notstarted), Paragraph("None", table_body_style), Paragraph("Export cleaned datasets, SQL query results, charts (PNG/SVG), PDF reports", table_body_style)],
        [Paragraph("17. Analytics Telemetry", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Audit log model and basic metrics endpoint", table_body_style), Paragraph("Log LLM token usage, query latency, dataset query volume, error rates", table_body_style)],
        [Paragraph("18. Error Handling", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("FastAPI exception handlers & React error boundaries", table_body_style), Paragraph("Structured agent self-correction loop (auto-healing bad SQL queries)", table_body_style)],
        [Paragraph("19. Security & Sandboxing", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("JWT auth, input validation with Pydantic", table_body_style), Paragraph("Read-only SQL query sandbox, restricted AST Python execution, rate limiting", table_body_style)],
        [Paragraph("20. Logging & Tracing", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Basic Python logging configured", table_body_style), Paragraph("Structured JSON logging with request IDs, LangChain/OpenAI trace spans", table_body_style)],
        [Paragraph("21. Automated Testing", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Pytest suite with 10+ test cases in backend/tests", table_body_style), Paragraph("Add unit tests for SQL generator, data cleaning pipeline, and frontend mock queries", table_body_style)],
        [Paragraph("22. Production Deployment", table_body_bold), Paragraph("🟡 PARTIAL", badge_partial), Paragraph("Dockerfiles & docker-compose.yml exist", table_body_style), Paragraph("Multi-stage Docker build, Nginx reverse proxy, PostgreSQL/MySQL prod config, CI/CD", table_body_style)]
    ]

    t_feat = Table(feat_matrix, colWidths=[105, 75, 175, 185])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_SECONDARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_feat)
    story.append(PageBreak())

    # ================= 3. 10-WEEK MASTER ROADMAP (WEEKS 1 TO 10) =================
    story.append(Paragraph("3. Master 10-Week Engineering Roadmap", h1_style))
    story.append(Paragraph("Structured into 6 progressive phases from foundational architecture to production deployment.", body_style))
    story.append(Spacer(1, 6))

    weeks_data = [
        # PHASE 1 - WEEK 1
        {
            "phase": "PHASE 1 – Foundation",
            "week": "WEEK 1: Workspace Initialization, Data Ingestion Architecture & Schema Design",
            "status": "✅ COMPLETED: Base FastAPI & Next.js Dark Theme Shell | 🟡 PARTIAL: Database schema | 🔴 NOT STARTED: Dataset entities",
            "goal": "Establish the dataset management database schema, storage abstraction, and streaming CSV/Excel ingestion pipeline with automatic metadata inference.",
            "completed": "JWT Authentication, Next.js dashboard shell, responsive sidebar, FastAPI router architecture, base MySQL connection pool.",
            "remains": "Dataset & Column metadata MySQL tables, DuckDB/Polars integration, File Upload REST endpoints with chunking, frontend dataset upload dropzone.",
            "days": [
                ("Day 1", "Audit existing MySQL schema; design `datasets`, `dataset_columns`, `data_profiles`, and `query_history` tables with foreign keys and indexes."),
                ("Day 2", "Write Alembic migration scripts to create dataset tables; configure MySQL connection pool with PyMySQL and SQLAlchemy 2.0."),
                ("Day 3", "Build FastAPI `/api/v1/datasets/upload` endpoint supporting CSV, XLSX, and JSON with python-multipart and streaming write to storage."),
                ("Day 4", "Integrate DuckDB and Pandas for rapid in-memory schema inference (column names, inferred SQL types, row count, null count)."),
                ("Day 5", "Create Next.js Dataset Management page with enterprise Drag & Drop file dropzone, file validation (max 50MB), and progress bar."),
                ("Day 6", "Build Dataset List UI showing uploaded datasets, row/column counts, file sizes, and upload timestamps with delete/preview actions."),
                ("Day 7", "Write pytest integration test for upload endpoint; commit baseline dataset ingestion module to git branch `feature/data-ingestion`.")
            ],
            "fe_tasks": "Build `/datasets` page, Drag-and-Drop file uploader component with Tailwind CSS, file size/format validator, and upload progress bar.",
            "be_tasks": "Create `app/routers/datasets.py`, file storage service (`app/services/storage.py`), and metadata extractor using DuckDB.",
            "db_tasks": "Create `datasets` (id, user_id, name, file_path, row_count, col_count, file_size) and `dataset_columns` (id, dataset_id, col_name, data_type, is_nullable).",
            "ai_tasks": "Setup prompt templates for schema summarization and initial dataset semantic tagging.",
            "api_tasks": "`POST /api/v1/datasets/upload`, `GET /api/v1/datasets`, `GET /api/v1/datasets/{id}`, `DELETE /api/v1/datasets/{id}`.",
            "test_tasks": "Pytest for CSV/Excel upload validation, mime-type verification, and database record insertion.",
            "git_tasks": "Create milestone `M1-Data-Ingestion`, branch `feature/data-ingestion`, PR review against `main`.",
            "output": "A fully functional Dataset Upload UI and API where users can upload any CSV/Excel file, storing raw data securely with metadata registered in MySQL.",
            "checklist": ["MySQL migration applied", "FastAPI upload endpoint functional", "DuckDB schema inference working", "Next.js Dropzone UI styled with dark theme", "Pytest passing for upload"]
        },
        # PHASE 1 - WEEK 2
        {
            "phase": "PHASE 1 – Foundation",
            "week": "WEEK 2: Dataset Preview, In-Memory DuckDB Engine & Dynamic Schema Viewer",
            "status": "🟡 PARTIAL: Frontend tables exist in other views | 🔴 NOT STARTED: Paginated dataset grid & SQL sandbox",
            "goal": "Build a high-performance paginated dataset previewer, dynamic column data-type inspector, and embedded DuckDB SQL execution backend.",
            "completed": "Dataset upload and metadata registration in MySQL from Week 1.",
            "remains": "Dynamic data grid with sorting/filtering, paginated SQL/DuckDB preview API, data-type override dropdown, and column statistics summary card.",
            "days": [
                ("Day 1", "Implement `/api/v1/datasets/{id}/preview` endpoint returning paginated rows (offset/limit) and column headers via DuckDB."),
                ("Day 2", "Add column filtering, sorting, and column search query parameters to the preview endpoint."),
                ("Day 3", "Build dynamic Next.js Data Grid component with sticky headers, column resizing, virtualized scrolling, and dark navy styling."),
                ("Day 4", "Implement Column Data Type Inspector modal allowing users to override inferred types (e.g., String -> Datetime/Category)."),
                ("Day 5", "Create Quick Column Summary Drawer in frontend displaying null counts, distinct count, min/max values for clicked columns."),
                ("Day 6", "Implement dataset rename, tag assignment, and soft-delete capabilities in backend and frontend."),
                ("Day 7", "Perform end-to-end testing with 100,000-row CSV datasets to ensure sub-200ms preview response times; merge to `main`.")
            ],
            "fe_tasks": "Build `DatasetPreviewGrid.tsx`, `ColumnTypeModal.tsx`, and `ColumnStatsDrawer.tsx` with responsive layout and Lucide icons.",
            "be_tasks": "Implement DuckDB query executor in `app/services/duckdb_service.py` with parameterization and memory limits.",
            "db_tasks": "Add `tags`, `updated_at`, and `type_overrides` JSON columns to `datasets` table.",
            "ai_tasks": "Create dataset description generator using LLM to automatically generate a 2-sentence summary of the dataset contents.",
            "api_tasks": "`GET /api/v1/datasets/{id}/preview?page=1&limit=50`, `PATCH /api/v1/datasets/{id}/columns`, `POST /api/v1/datasets/{id}/auto-describe`.",
            "test_tasks": "Unit test pagination logic, type casting handlers, and large file streaming memory footprint.",
            "git_tasks": "Create branch `feature/dataset-preview`, push commits with structured conventional messages (`feat: add duckdb preview`).",
            "output": "Interactive dataset exploration portal where users can inspect raw data, filter rows, adjust data types, and view automatic dataset descriptions.",
            "checklist": ["Paginated preview API working with DuckDB", "Virtualized Next.js grid rendered", "Column type inspector functioning", "Auto-describe LLM endpoint working"]
        },
        # PHASE 2 - WEEK 3
        {
            "phase": "PHASE 2 – Core Backend & Database",
            "week": "WEEK 3: Automated Data Cleaning & Transformation Pipeline",
            "status": "🔴 NOT STARTED: Data cleaning engine and transformation history",
            "goal": "Develop an automated and user-guided data cleaning engine that handles missing values, duplicates, outliers, date standardization, and text cleaning.",
            "completed": "Dataset storage and preview engine from Weeks 1-2.",
            "remains": "Cleaning pipeline rules engine, Pandas/Polars transformation recipes, dataset versioning, and UI cleaning action panel.",
            "days": [
                ("Day 1", "Design data cleaning taxonomy: Drop Nulls, Impute (Mean/Median/Mode/KNN), Remove Duplicates, Trim Whitespace, Lowercase, Outlier Clipping (IQR)."),
                ("Day 2", "Create `app/services/data_cleaner.py` utilizing Pandas and Scikit-learn for automated strategy suggestions and deterministic cleaning runs."),
                ("Day 3", "Build `/api/v1/datasets/{id}/clean` API supporting dry-run previews (showing before vs after diffs) and permanent versioned execution."),
                ("Day 4", "Build database versioning: store clean dataset as `dataset_v2.csv` linked to parent dataset ID in MySQL."),
                ("Day 5", "Create Data Cleaning Workbench in Next.js with step-by-step cleaning wizards, one-click 'Auto-Clean' toggle, and diff metrics."),
                ("Day 6", "Add real-time transformation log showing exact operations performed (e.g., 'Removed 142 duplicates, Imputed 12 nulls in age with median 34')."),
                ("Day 7", "Write pytest unit tests for every cleaning operation; test edge cases (all-null columns, empty strings, categorical date formats).")
            ],
            "fe_tasks": "Build `DataCleaningWorkbench.tsx`, `CleaningAuditLog.tsx`, and Before/After comparison stat widgets.",
            "be_tasks": "Develop `DataCleaner` service, `DatasetVersionManager`, and transformation audit logger.",
            "db_tasks": "Create `dataset_transformations` (id, dataset_id, action_type, parameters, affected_rows, executed_at).",
            "ai_tasks": "Build 'AI Clean Advisor' prompt that analyzes column anomalies and returns a prioritized list of recommended cleaning actions in JSON.",
            "api_tasks": "`POST /api/v1/datasets/{id}/clean/suggest`, `POST /api/v1/datasets/{id}/clean/execute`, `GET /api/v1/datasets/{id}/versions`.",
            "test_tasks": "Test all imputation strategies, duplicate drop edge cases, and ensure non-destructive versioning works.",
            "git_tasks": "Milestone `M2-Data-Cleaning`, branch `feature/data-cleaner`, update PR with before/after benchmarks.",
            "output": "End-to-end Data Cleaning studio where messy CSVs can be cleaned automatically with 1-click or customized with full rollback history.",
            "checklist": ["Cleaning strategies implemented in Python", "Dry-run diff API functional", "Next.js Cleaning Workbench UI styled", "Versioned dataset saving working"]
        },
        # PHASE 2 - WEEK 4
        {
            "phase": "PHASE 2 – Core Backend & Database",
            "week": "WEEK 4: Deep Data Profiling & Statistical Analytics Engine",
            "status": "🟡 PARTIAL: Basic health score & analytics endpoints exist in backend | 🔴 NOT STARTED: Comprehensive EDA profiler",
            "goal": "Build an in-depth exploratory data analysis (EDA) profiling engine calculating skewness, kurtosis, correlations, histograms, and cardinality.",
            "completed": "Dataset preview and cleaning pipeline from Weeks 1-3.",
            "remains": "Full statistical profiler service, correlation matrix calculation, distribution bucket generator, and Next.js Profiling Overview tab.",
            "days": [
                ("Day 1", "Develop `app/services/profiler.py` using NumPy/SciPy to calculate mean, median, std, min, max, Q25, Q75, skewness, kurtosis for numeric columns."),
                ("Day 2", "Implement categorical profiling: unique count, top 10 frequencies, entropy/cardinality ratios, and missing value percentages."),
                ("Day 3", "Implement Pearson and Spearman correlation matrix calculation and save structured results in `data_profiles` table as JSON."),
                ("Day 4", "Build `/api/v1/datasets/{id}/profile` caching profile JSON in database to eliminate redundant computations."),
                ("Day 5", "Create Next.js Profiler Dashboard tab with distribution mini-charts, correlation heatmap, data health score, and quality warnings."),
                ("Day 6", "Implement statistical hypothesis test endpoints (Two-sample T-Test, Chi-Square test of independence, One-Way ANOVA) for user-selected columns."),
                ("Day 7", "Perform benchmarks with 50-column datasets; ensure profile generation completes under 2.5 seconds.")
            ],
            "fe_tasks": "Build `DataProfilerDashboard.tsx`, `CorrelationHeatmap.tsx`, `DistributionHistogram.tsx`, and `DataQualityScorecard.tsx`.",
            "be_tasks": "Build `app/services/profiler.py`, statistical hypothesis test runners, and JSON serialization helpers.",
            "db_tasks": "Create `data_profiles` (id, dataset_id, profile_json, quality_score, calculated_at) with indexed dataset_id.",
            "ai_tasks": "Build 'AI Data Doctor' prompt summarizing top 3 data quality red flags and key structural insights from the profile JSON.",
            "api_tasks": "`GET /api/v1/datasets/{id}/profile`, `POST /api/v1/datasets/{id}/hypothesis-test`, `GET /api/v1/datasets/{id}/correlations`.",
            "test_tasks": "Validate numerical accuracy of statistical metrics against Pandas/SciPy reference values.",
            "git_tasks": "Create branch `feature/data-profiler`, document statistical formulas in `docs/STATISTICS.md`.",
            "output": "A rich automated Data Profiler tab offering statistical insights, correlation heatmaps, data distribution graphs, and AI quality diagnosis.",
            "checklist": ["NumPy/SciPy profiling engine built", "Profile JSON caching in MySQL", "Correlation Heatmap rendered in Next.js", "Statistical hypothesis testing working"]
        },
        # PHASE 3 - WEEK 5
        {
            "phase": "PHASE 3 – AI Data Analyst Agent",
            "week": "WEEK 5: Multi-Agent Architecture, Text-to-SQL & In-Memory Query Execution Sandbox",
            "status": "🟡 PARTIAL: Base agent state machine & tools.py exist in backend/app/agents | 🔴 NOT STARTED: Text-to-SQL & SQL Sandbox agent",
            "goal": "Transform the existing agent architecture into a specialized Data Analyst Agent pipeline capable of converting English queries to secure SQL.",
            "completed": "Base agent state machine (`base.py`, `orchestrator.py`, `tools.py`), authentication, and dataset ingestion.",
            "remains": "Data Analyst Agent DAG, SQL Generator Tool with AST validation, DuckDB read-only query runner, and SQL self-healing retry loop.",
            "days": [
                ("Day 1", "Adapt `backend/app/agents/base.py` and `state.py` for Data Analyst state (user_query, schema_context, generated_sql, query_results, error, retry_count)."),
                ("Day 2", "Develop `SQLGenerationAgent` with few-shot prompting, dynamic table schema injection, and Dialect-specific formatting (DuckDB/MySQL)."),
                ("Day 3", "Create `SQLValidationTool` using `sqlparse` to block destructive statements (DROP, DELETE, UPDATE, INSERT, ALTER, GRANT) and enforce LIMIT <= 500."),
                ("Day 4", "Build Self-Healing Query Execution Loop: if DuckDB throws a syntax or column error, feed error back to LLM to re-generate correct SQL (max 3 retries)."),
                ("Day 5", "Integrate SQL query router `/api/v1/agent/query` returning generated SQL, execution duration, row results, and natural-language interpretation."),
                ("Day 6", "Build Next.js SQL Query Playground with Monaco/CodeMirror SQL editor, 'Ask in English' input bar, and formatted results table."),
                ("Day 7", "Test complex queries (JOINs, GROUP BY, Window Functions, Date truncations) across multi-table datasets.")
            ],
            "fe_tasks": "Build `SQLQueryPlayground.tsx`, `SQLCodeBlock.tsx` with copy-to-clipboard and syntax highlighting, and Execution Time pill.",
            "be_tasks": "Create `app/agents/sql_agent.py`, `app/agents/sql_validator.py`, and self-correction orchestrator node.",
            "db_tasks": "Create `query_history` (id, dataset_id, user_id, prompt, generated_sql, execution_time_ms, row_count, is_successful, created_at).",
            "ai_tasks": "Design robust system prompt for SQL generation with schema awareness, column type constraints, and NULL handling.",
            "api_tasks": "`POST /api/v1/agent/sql-query`, `POST /api/v1/agent/explain-sql`, `GET /api/v1/agent/history/{dataset_id}`.",
            "test_tasks": "Unit test SQL injection security guards, AST parser validation, and multi-turn self-healing loop.",
            "git_tasks": "Milestone `M3-SQL-Agent`, branch `feature/sql-analyst-agent`, add comprehensive prompt regression tests.",
            "output": "A secure Text-to-SQL engine that translates natural-language queries into optimized SQL, executes them safely, and heals its own errors automatically.",
            "checklist": ["Text-to-SQL prompt tuned with few-shots", "SQL AST safety validator active", "Self-healing retry loop working on bad syntax", "Next.js SQL Playground styled"]
        },
        # PHASE 3 - WEEK 6
        {
            "phase": "PHASE 3 – AI Data Analyst Agent",
            "week": "WEEK 6: Conversational Data Analyst Chat with Streaming & Artifacts",
            "status": "🟡 PARTIAL: Basic AI Chat router exists | 🔴 NOT STARTED: Conversational memory with dataset context & dynamic artifacts",
            "goal": "Build an enterprise conversational copilot with streaming responses, multi-turn dataset awareness, interactive chart generation, and thought-process steps.",
            "completed": "FastAPI streaming infrastructure, base chat router, and SQL agent from Week 5.",
            "remains": "Agent reasoning step streaming (Thought -> SQL -> Execution -> Visualization -> Explanation), conversation session memory, dynamic chart payload builder.",
            "days": [
                ("Day 1", "Implement SSE (Server-Sent Events) in FastAPI for streaming agent tokens and intermediate status updates (`planning`, `querying`, `visualizing`)."),
                ("Day 2", "Create `VisualizationAgent` tool that selects the optimal chart type (Bar, Line, Area, Scatter, Pie, Heatmap) and generates JSON specs for Recharts."),
                ("Day 3", "Integrate session-based conversation memory in MySQL allowing users to ask follow-up questions (e.g. 'Now filter that for 2024 only')."),
                ("Day 4", "Build Enterprise Chat Interface in Next.js with dark navy bubbles, markdown parsing, syntax highlighting, and collapsible 'Agent Thought Process' pills."),
                ("Day 5", "Implement Dynamic Artifacts Panel on the right side of the chat rendering live Recharts and interactive data tables based on agent responses."),
                ("Day 6", "Add quick prompt suggestions ('What is the revenue trend?', 'Find top 5 outliers', 'Correlate age with spend') above chat input."),
                ("Day 7", "Conduct latency optimization; ensure first token is delivered in under 800ms and chart rendering takes under 1.5s.")
            ],
            "fe_tasks": "Build `DataAnalystChat.tsx`, `AgentThoughtSteps.tsx`, `ArtifactViewer.tsx`, and `QuickPromptChips.tsx`.",
            "be_tasks": "Create `app/agents/visualization_agent.py`, SSE streaming router in `app/routers/agent_chat.py`, and session memory manager.",
            "db_tasks": "Create `chat_sessions` and `chat_messages` (id, session_id, role, content, thoughts_json, chart_spec_json, sql_query, created_at).",
            "ai_tasks": "Develop chart selection heuristic prompt ensuring accurate X-axis/Y-axis mapping and proper color palette tokens matching dark theme.",
            "api_tasks": "`POST /api/v1/agent/chat/stream` (SSE), `GET /api/v1/agent/sessions/{dataset_id}`, `DELETE /api/v1/agent/sessions/{session_id}`.",
            "test_tasks": "Test SSE stream lifecycle, reconnection handling, and multi-turn context retention across 10-message dialogues.",
            "git_tasks": "Create branch `feature/analyst-chat-streaming`, merge to main with demo recording.",
            "output": "A world-class conversational AI Data Analyst chat where users converse with their data, watch agent thoughts in real-time, and get live charts.",
            "checklist": ["SSE streaming working seamlessly", "Conversational multi-turn memory active", "Recharts dynamic renderer connected", "Dark theme artifact panel operational"]
        },
        # PHASE 4 - WEEK 7
        {
            "phase": "PHASE 4 – Advanced AI & Automation",
            "week": "WEEK 7: Advanced Statistical Modeling, Anomaly Detection & AI Insights Engine",
            "status": "🔴 NOT STARTED: Automated anomaly detection, trend forecasting, and executive insight generation",
            "goal": "Build proactive analytical agents that automatically scan datasets for anomalies, detect seasonality/trends, and generate actionable business insights.",
            "completed": "Conversational data analyst and data profiling from Weeks 4-6.",
            "remains": "Isolation Forest anomaly detector, ARIMA/Prophet or linear trend forecaster, automated insights summarizer agent.",
            "days": [
                ("Day 1", "Implement `app/services/anomaly_detector.py` using Scikit-Learn (Isolation Forest & Z-Score) to flag anomalous rows and clusters."),
                ("Day 2", "Implement time-series decomposition and simple linear/moving-average forecasting service for date-indexed metrics."),
                ("Day 3", "Create `InsightGeneratorAgent` that ingests anomalies, top correlations, and trend slopes to draft high-level executive insights."),
                ("Day 4", "Build `/api/v1/datasets/{id}/insights` returning categorized cards: '🚨 Anomalies Detected', '📈 Growth Trend', '💡 Optimization Opportunities'."),
                ("Day 5", "Create Next.js Automated Insights Tab with expandable insight cards, severity tags (High, Medium, Low), and 1-click 'Investigate in Chat' button."),
                ("Day 6", "Add Anomaly Inspector UI highlighting exact outlier rows in the dataset grid with visual explanation tooltips."),
                ("Day 7", "Perform validation on benchmark datasets (e.g., retail sales, server logs, healthcare claims) to ensure high anomaly precision.")
            ],
            "fe_tasks": "Build `AutomatedInsightsTab.tsx`, `InsightCard.tsx`, and `AnomalyHighlightTable.tsx` with electric blue and amber alert accents.",
            "be_tasks": "Develop `AnomalyDetector` service, `TrendForecaster`, and `InsightGeneratorAgent`.",
            "db_tasks": "Create `dataset_insights` (id, dataset_id, category, severity, title, description, chart_config, created_at).",
            "ai_tasks": "Tune executive summary prompt to output structured JSON insights with quantified business impact (e.g. '+$45,000 potential savings').",
            "api_tasks": "`GET /api/v1/datasets/{id}/insights`, `POST /api/v1/datasets/{id}/insights/generate`, `POST /api/v1/datasets/{id}/forecast`.",
            "test_tasks": "Unit test anomaly detection algorithms against synthetic datasets with injected outliers.",
            "git_tasks": "Milestone `M4-Advanced-AI`, branch `feature/insights-engine`.",
            "output": "An autonomous AI intelligence tab that surfaces hidden patterns, statistical anomalies, and future trend predictions without manual queries.",
            "checklist": ["Isolation Forest anomaly detection working", "Insight generation prompt producing structured JSON", "Next.js Insights UI with severity filters", "1-click 'Investigate in Chat' integrated"]
        },
        # PHASE 4 - WEEK 8
        {
            "phase": "PHASE 4 – Advanced AI & Automation",
            "week": "WEEK 8: Automated PDF Report Generation & Multi-Format Export Engine",
            "status": "🔴 NOT STARTED: Report generator and multi-format export",
            "goal": "Build an enterprise Report Builder capable of compiling executive data summaries, charts, and query logs into professional PDF, Excel, and CSV exports.",
            "completed": "Dataset profiling, chart generation, and automated insights from Weeks 1-7.",
            "remains": "ReportLab / Weasyprint PDF compiler, Excel export with formatted sheets, Chart PNG exporter, Report generation UI.",
            "days": [
                ("Day 1", "Develop `app/services/report_generator.py` using ReportLab / Jinja2-HTML to build styled multi-page PDF Executive Data Briefs."),
                ("Day 2", "Include dataset summary, data health score, top KPI cards, key anomalies, and embedded high-res charts in the generated PDF."),
                ("Day 3", "Build multi-sheet Excel export using `openpyxl` (Sheet 1: Summary KPIs, Sheet 2: Clean Data, Sheet 3: Data Profile, Sheet 4: Query History)."),
                ("Day 4", "Implement frontend canvas/SVG chart export to PNG/JPEG and CSV export for any filtered query view."),
                ("Day 5", "Create Report Customization Modal in Next.js allowing users to select which sections to include (KPIs, Charts, Anomalies, Recommendations)."),
                ("Day 6", "Build `/api/v1/reports/download/{id}` supporting direct streaming download with background task generation for heavy reports."),
                ("Day 7", "Test PDF generation across 20+ distinct report layouts to ensure pixel-perfect typography, no text clipping, and professional aesthetics.")
            ],
            "fe_tasks": "Build `ReportExportModal.tsx`, `ReportHistoryDrawer.tsx`, and 1-Click Export buttons on all data views.",
            "be_tasks": "Create `app/services/report_generator.py`, `app/services/excel_exporter.py`, and asynchronous report worker.",
            "db_tasks": "Create `reports` (id, dataset_id, user_id, title, report_type, file_path, file_size, status, created_at).",
            "ai_tasks": "Create 'Executive Brief Writer' prompt that synthesizes the entire dataset analysis into a formal 3-paragraph executive summary.",
            "api_tasks": "`POST /api/v1/reports/generate`, `GET /api/v1/reports`, `GET /api/v1/reports/{id}/download`.",
            "test_tasks": "Validate PDF compilation speed, verify Excel multi-sheet data integrity, test large export file download streaming.",
            "git_tasks": "Branch `feature/report-generator`, push documentation for PDF styling template.",
            "output": "A one-click Executive PDF Report Generator and multi-format export hub creating C-suite-ready presentations and formatted Excel workbooks.",
            "checklist": ["ReportLab PDF engine generating clean reports", "Excel multi-sheet export functional", "Next.js Report Export Modal styled", "Background task for heavy generation active"]
        },
        # PHASE 5 - WEEK 9
        {
            "phase": "PHASE 5 – Testing, Security & Optimization",
            "week": "WEEK 9: Enterprise Security, Code Sandboxing, Rate Limiting & End-to-End Testing",
            "status": "🟡 PARTIAL: Unit tests exist in backend/tests | 🔴 NOT STARTED: E2E Playwright tests & code sandbox isolation",
            "goal": "Harden the entire platform with code execution sandboxing, strict rate limiting, audit logging, and automated test coverage across frontend & backend.",
            "completed": "Full functional application stack from Weeks 1-8.",
            "remains": "Restricted AST Python code sandbox, Redis/Token-bucket rate limiter, comprehensive Pytest suite (>80% coverage), Cypress/Playwright E2E tests.",
            "days": [
                ("Day 1", "Build restricted Python sandbox for advanced analysis scripts (disable `os`, `sys`, `subprocess`, `socket`, `open`; set CPU timeout 3s)."),
                ("Day 2", "Implement FastAPI SlowAPI rate limiting (60 requests/min for general API, 10 requests/min for AI LLM endpoints)."),
                ("Day 3", "Perform security audit: SQL injection testing, CORS strict origin configuration, XSS payload filtering in chat markdown."),
                ("Day 4", "Write comprehensive Pytest suite covering all routers (`datasets`, `cleaner`, `profiler`, `sql_agent`, `reports`, `auth`)."),
                ("Day 5", "Set up Playwright / Cypress frontend tests for complete user journey: Login -> Upload CSV -> Auto-Clean -> Ask Chat -> Export PDF."),
                ("Day 6", "Optimize backend query performance: add compound indexes in MySQL on `(user_id, created_at)`, enable DuckDB memory caching."),
                ("Day 7", "Perform load testing with Locust (50 concurrent users querying datasets simultaneously); verify zero server crashes and <1% error rate.")
            ],
            "fe_tasks": "Fix all console warnings, optimize bundle size with Next.js dynamic imports, implement error boundary fallback screens.",
            "be_tasks": "Implement `app/core/sandbox.py`, add SlowAPI rate limiter middleware, configure structured JSON log format with correlation IDs.",
            "db_tasks": "Add database indexes for high-frequency queries; run EXPLAIN on all ORM queries to eliminate N+1 bottlenecks.",
            "ai_tasks": "Add LLM prompt injection defense filter and output safety check before returning markdown to frontend.",
            "api_tasks": "Add health check endpoint `GET /health` with DB connection and DuckDB engine status probes.",
            "test_tasks": "Achieve 85%+ backend code coverage with Pytest; pass all E2E user flow tests in Playwright.",
            "git_tasks": "Milestone `M5-Security-Hardening`, configure GitHub Actions CI workflow to run Pytest and ESLint on every push.",
            "output": "A hardened, secure, and thoroughly tested enterprise SaaS platform with sandbox execution protection, rate limits, and CI automation.",
            "checklist": ["Python AST sandbox active", "Rate limiting on AI endpoints working", "Pytest suite >85% coverage", "GitHub Actions CI pipeline passing"]
        },
        # PHASE 6 - WEEK 10
        {
            "phase": "PHASE 6 – Deployment & Production",
            "week": "WEEK 10: Production Dockerization, Cloud Deployment, CI/CD & Portfolio Showcase",
            "status": "🟡 PARTIAL: Basic Dockerfiles and docker-compose exist | 🔴 NOT STARTED: Production Nginx, SSL, Cloud deployment & README showcase",
            "goal": "Deploy the complete platform to production (AWS/GCP/Render/Vercel) with Docker, Nginx reverse proxy, SSL certificates, and complete portfolio assets.",
            "completed": "Hardened application code and automated tests from Weeks 1-9.",
            "remains": "Production Docker compose with Nginx SSL, cloud database setup, CI/CD automated deployment, architecture documentation, and demo video.",
            "days": [
                ("Day 1", "Create multi-stage production Dockerfiles for Next.js (`standalone` output) and FastAPI (Gunicorn + Uvicorn workers)."),
                ("Day 2", "Configure `docker-compose.prod.yml` with Nginx reverse proxy, automatic Let's Encrypt SSL renewal, and volume persistence."),
                ("Day 3", "Deploy Backend & MySQL database to Cloud VM / Render / AWS ECS; deploy Next.js frontend to Vercel or cloud container."),
                ("Day 4", "Configure production environment variables, secret managers, and domain DNS routing (`api.yourdomain.com` and `app.yourdomain.com`)."),
                ("Day 5", "Verify live production workflows: upload sample sales/healthcare datasets, test live AI chat, download production PDF reports."),
                ("Day 6", "Record a 3-minute high-impact Loom / YouTube product demo showcasing the end-to-end user experience and AI agent thought process."),
                ("Day 7", "Polish GitHub README with architectural diagrams, live demo link, API docs, installation guide, and prepare interview presentation.")
            ],
            "fe_tasks": "Configure Next.js production environment variables (`NEXT_PUBLIC_API_URL`), test production build bundle.",
            "be_tasks": "Tune Gunicorn worker concurrency (`-w 4 -k uvicorn.workers.UvicornWorker`), setup automated database backups.",
            "db_tasks": "Apply production MySQL database migration, initialize seed demo datasets.",
            "ai_tasks": "Verify production OpenAI / Anthropic / Gemini API key rotation and fallback provider logic.",
            "api_tasks": "Verify all production endpoints over HTTPS with valid SSL certificates.",
            "test_tasks": "Smoke test all critical paths on the live production URL.",
            "git_tasks": "Tag release `v1.0.0-release`, write release notes, merge all PRs into `main` branch.",
            "output": "Live production-grade AI Data Analyst SaaS accessible via public URL, with CI/CD, complete documentation, and demo video.",
            "checklist": ["Multi-stage Docker builds optimized", "Production deployment live over HTTPS", "Sample demo datasets pre-loaded", "GitHub README polished with architecture diagram", "Demo video recorded"]
        }
    ]

    for w in weeks_data:
        # Week Header box
        story.append(Paragraph(w["phase"].upper(), h3_style))
        story.append(Paragraph(w["week"], h2_style))
        story.append(Spacer(1, 2))
        
        # Meta table
        w_meta = [
            [Paragraph("Current Status", table_body_bold), Paragraph(w["status"], table_body_style)],
            [Paragraph("Weekly Goal", table_body_bold), Paragraph(w["goal"], table_body_style)],
            [Paragraph("What is Completed", table_body_bold), Paragraph(w["completed"], table_body_style)],
            [Paragraph("What Remains", table_body_bold), Paragraph(w["remains"], table_body_style)]
        ]
        t_wmeta = Table(w_meta, colWidths=[110, 430])
        t_wmeta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t_wmeta)
        story.append(Spacer(1, 4))

        # Day by Day breakdown
        story.append(Paragraph("Day-by-Day Implementation Schedule", h3_style))
        day_rows = [[Paragraph("Day", table_header_style), Paragraph("Planned Engineering Tasks", table_header_style)]]
        for day, desc in w["days"]:
            day_rows.append([Paragraph(day, table_body_bold), Paragraph(desc, table_body_style)])
        
        t_days = Table(day_rows, colWidths=[65, 475])
        t_days.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_SECONDARY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t_days)
        story.append(Spacer(1, 4))

        # Domain breakdown table
        story.append(Paragraph("Domain Task Breakdown & Expected Deliverable", h3_style))
        domain_data = [
            [Paragraph("Frontend", table_body_bold), Paragraph(w["fe_tasks"], table_body_style)],
            [Paragraph("Backend", table_body_bold), Paragraph(w["be_tasks"], table_body_style)],
            [Paragraph("Database", table_body_bold), Paragraph(w["db_tasks"], table_body_style)],
            [Paragraph("AI / LLM", table_body_bold), Paragraph(w["ai_tasks"], table_body_style)],
            [Paragraph("API Spec", table_body_bold), Paragraph(w["api_tasks"], table_body_style)],
            [Paragraph("Testing & CI", table_body_bold), Paragraph(w["test_tasks"], table_body_style)],
            [Paragraph("Git / GitHub", table_body_bold), Paragraph(w["git_tasks"], table_body_style)],
            [Paragraph("Expected Output", table_body_bold), Paragraph(f"<b>{w['output']}</b>", table_body_style)],
            [Paragraph("Checklist", table_body_bold), Paragraph(" • " + "<br/> • ".join(w["checklist"]), table_body_style)]
        ]
        t_domain = Table(domain_data, colWidths=[90, 450])
        t_domain.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t_domain)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=4, spaceAfter=8))

    story.append(PageBreak())

    # ================= 4. FINAL ARCHITECTURE, SCHEMAS, API & INTERVIEW GUIDE =================
    story.append(Paragraph("4. Technical Specifications, Architecture & Deliverables", h1_style))
    story.append(Spacer(1, 4))

    # 4.1 Completion Percentage
    story.append(Paragraph("4.1 Project Completion Metrics", h2_style))
    metrics_data = [
        [Paragraph("Metric", table_header_style), Paragraph("Percentage", table_header_style), Paragraph("Component Breakdown", table_header_style)],
        [Paragraph("Current Project Status", table_body_bold), Paragraph("<b>35% Completed</b>", badge_completed), Paragraph("Auth, Core Layout, Dark Theme, Base Multi-Agent Harness, MySQL foundation", table_body_style)],
        [Paragraph("Remaining Workload", table_body_bold), Paragraph("<b>65% Remaining</b>", badge_partial), Paragraph("Dataset Ingestion, Cleaning, Profiling, Text-to-SQL Agent, Dynamic Charts, PDF Reports", table_body_style)],
        [Paragraph("Target Timeline", table_body_bold), Paragraph("<b>10 Weeks (70 Days)</b>", table_body_bold), Paragraph("7 hours/week or 1 hour/day disciplined engineering sprint", table_body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[120, 100, 320])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 8))

    # 4.2 Architecture
    story.append(Paragraph("4.2 System Architecture Overview", h2_style))
    arch_desc = """
    <b>Client Layer (Next.js 14):</b> Responsive Enterprise Dark Navy UI (#0B132B / #1C2541), Tailwind CSS, Recharts for dynamic visual charts, Server-Sent Events (SSE) consumer for real-time AI reasoning streams, Monaco editor for SQL playground.<br/>
    <b>API Gateway Layer (FastAPI):</b> RESTful endpoints, JWT Auth & Rate Limiter middleware, Pydantic v2 validation models, SSE streaming response handlers.<br/>
    <b>Multi-Agent Orchestration Layer:</b> StateGraph / DAG orchestrator coordinating 5 specialized agents:<br/>
    &nbsp;&nbsp;1. <i>Ingestion & Profiling Agent:</i> Schema inference & statistical calculations via DuckDB/NumPy.<br/>
    &nbsp;&nbsp;2. <i>Data Cleaning Agent:</i> Rule-based and AI-suggested deterministic transformations.<br/>
    &nbsp;&nbsp;3. <i>Text-to-SQL Agent:</i> Few-shot SQL generator with AST validation & auto-healing error loop.<br/>
    &nbsp;&nbsp;4. <i>Visualization Agent:</i> Automatic chart type selection and Recharts JSON schema builder.<br/>
    &nbsp;&nbsp;5. <i>Executive Insight & Report Agent:</i> Synthesis of statistical anomalies and PDF report compilation.<br/>
    <b>Execution Sandbox:</b> In-memory DuckDB analytical engine and sandboxed Python execution environment.<br/>
    <b>Persistence Layer:</b> MySQL 8.0 for relational metadata, user state, chat logs, and audit trails; File Storage (Local/S3) for raw and cleaned datasets.
    """
    story.append(Paragraph(arch_desc, body_style))
    story.append(Spacer(1, 8))

    # 4.3 Folder Structure
    story.append(Paragraph("4.3 Final Folder Structure", h2_style))
    folder_text = """
    <b>medsentinel-ai-analyst/</b><br/>
    ├── <b>backend/</b><br/>
    │&nbsp;&nbsp;&nbsp;├── <b>app/</b><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>agents/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Base agent, orchestrator, sql_agent, viz_agent, cleaner_agent</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>core/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># config.py, security.py, sandbox.py, rate_limiter.py</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>models/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># SQLAlchemy models: user, dataset, profile, chat, report, audit</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>routers/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># auth, datasets, cleaner, profiler, agent_chat, reports, analytics</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>schemas/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Pydantic v2 validation DTOs</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>services/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># duckdb_service, profiler, anomaly_detector, report_generator</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── <b>main.py</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># FastAPI app entry point and CORS/middleware</i><br/>
    │&nbsp;&nbsp;&nbsp;├── <b>tests/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Pytest suite: test_auth, test_datasets, test_sql_agent, test_cleaner</i><br/>
    │&nbsp;&nbsp;&nbsp;└── <b>Dockerfile</b>, <b>requirements.txt</b>, <b>alembic.ini</b><br/>
    ├── <b>frontend/</b><br/>
    │&nbsp;&nbsp;&nbsp;├── <b>app/</b><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>datasets/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Dataset upload, table preview, column inspector</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>cleaner/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Interactive cleaning studio & version diffs</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>profiler/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Statistical charts, correlation heatmap, health score</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>analyst-chat/</b> &nbsp;&nbsp;&nbsp;<i># Conversational agent chat with live artifacts & streaming</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <b>reports/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Executive PDF report builder and export center</i><br/>
    │&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── <b>dashboard/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Main analytics summary dashboard</i><br/>
    │&nbsp;&nbsp;&nbsp;├── <b>components/</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i># Recharts wrappers, Dropzone, ChatBubble, SQLPlayground, Navbar</i><br/>
    │&nbsp;&nbsp;&nbsp;└── <b>package.json</b>, <b>tailwind.config.js</b>, <b>next.config.js</b><br/>
    └── <b>docker-compose.yml</b>, <b>README.md</b>
    """
    story.append(Paragraph(folder_text, body_style))
    story.append(Spacer(1, 8))

    # 4.4 Database Schema
    story.append(Paragraph("4.4 Complete MySQL Database Schema", h2_style))
    sql_schema_summary = """
    <b>1. users:</b> `id` (VARCHAR 36 PK), `email` (VARCHAR 255 UNIQUE), `hashed_password`, `role`, `created_at`<br/>
    <b>2. datasets:</b> `id` (VARCHAR 36 PK), `user_id` (FK), `name`, `file_path`, `row_count` (INT), `col_count` (INT), `file_size_kb` (FLOAT), `is_cleaned` (BOOL), `parent_id` (FK self), `created_at`<br/>
    <b>3. dataset_columns:</b> `id` (INT AUTO_INCREMENT PK), `dataset_id` (FK), `col_name`, `inferred_type`, `user_type`, `null_count`, `distinct_count`<br/>
    <b>4. data_profiles:</b> `id` (VARCHAR 36 PK), `dataset_id` (FK), `quality_score` (INT), `summary_stats_json` (JSON), `correlations_json` (JSON), `anomalies_json` (JSON), `created_at`<br/>
    <b>5. chat_sessions:</b> `id` (VARCHAR 36 PK), `dataset_id` (FK), `user_id` (FK), `title`, `created_at`<br/>
    <b>6. chat_messages:</b> `id` (VARCHAR 36 PK), `session_id` (FK), `role` (ENUM: user, assistant, system), `content` (TEXT), `thoughts_json` (JSON), `generated_sql` (TEXT), `chart_spec_json` (JSON), `created_at`<br/>
    <b>7. query_history:</b> `id` (VARCHAR 36 PK), `dataset_id` (FK), `user_id` (FK), `prompt` (TEXT), `generated_sql` (TEXT), `execution_time_ms` (INT), `is_successful` (BOOL), `created_at`<br/>
    <b>8. reports:</b> `id` (VARCHAR 36 PK), `dataset_id` (FK), `user_id` (FK), `title`, `file_path`, `format` (ENUM: pdf, excel, csv), `status` (ENUM: pending, ready, failed), `created_at`
    """
    story.append(Paragraph(sql_schema_summary, body_style))
    story.append(Spacer(1, 8))

    # 4.5 REST API Catalog
    story.append(Paragraph("4.5 Core REST API Catalog", h2_style))
    api_table_data = [
        [Paragraph("Method & Endpoint", table_header_style), Paragraph("Request Body / Params", table_header_style), Paragraph("Response Description", table_header_style)],
        [Paragraph("POST /api/v1/auth/login", table_body_bold), Paragraph("`{email, password}`", table_body_style), Paragraph("Returns JWT access & refresh tokens", table_body_style)],
        [Paragraph("POST /api/v1/datasets/upload", table_body_bold), Paragraph("`multipart/form-data (file, name)`", table_body_style), Paragraph("Registers dataset, infers schema, returns dataset ID", table_body_style)],
        [Paragraph("GET /api/v1/datasets/{id}/preview", table_body_bold), Paragraph("`?page=1&limit=50&sort_by=&order=`", table_body_style), Paragraph("Paginated row objects with column headers", table_body_style)],
        [Paragraph("POST /api/v1/datasets/{id}/clean", table_body_bold), Paragraph("`{strategies: ['drop_duplicates', 'impute_mean'], dry_run: false}`", table_body_style), Paragraph("Returns cleaned dataset metadata or diff preview", table_body_style)],
        [Paragraph("GET /api/v1/datasets/{id}/profile", table_body_bold), Paragraph("`None`", table_body_style), Paragraph("Full statistical summary, correlations, histograms JSON", table_body_style)],
        [Paragraph("POST /api/v1/agent/sql-query", table_body_bold), Paragraph("`{dataset_id, prompt}`", table_body_style), Paragraph("Executes generated SQL, returns rows, duration, explain", table_body_style)],
        [Paragraph("POST /api/v1/agent/chat/stream", table_body_bold), Paragraph("`{dataset_id, session_id, message}`", table_body_style), Paragraph("SSE Stream: thoughts -> SQL -> chart JSON -> response text", table_body_style)],
        [Paragraph("GET /api/v1/datasets/{id}/insights", table_body_bold), Paragraph("`None`", table_body_style), Paragraph("Categorized insights list (anomalies, trends, opportunities)", table_body_style)],
        [Paragraph("POST /api/v1/reports/generate", table_body_bold), Paragraph("`{dataset_id, sections: ['kpis', 'charts', 'insights']}`", table_body_style), Paragraph("Compiles PDF Executive Brief and returns download URL", table_body_style)]
    ]
    t_api = Table(api_table_data, colWidths=[155, 185, 200])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 8))

    # 4.6 Resume Description
    story.append(Paragraph("4.6 Resume-Ready Project Bullet Points (for CSE Freshers)", h2_style))
    resume_text = """
    <b>AI Data Analyst Agent — Full-Stack Autonomous Analytics SaaS</b><br/>
    • Built an autonomous multi-agent data analysis platform in <b>Next.js 14, FastAPI, MySQL, and DuckDB</b> that converts natural language queries to SQL and generates interactive charts with sub-second latency.<br/>
    • Engineered a robust <b>Text-to-SQL agent with AST validation and self-healing error recovery</b>, preventing harmful DML queries and achieving 94% first-pass query execution accuracy on complex aggregations.<br/>
    • Developed an automated <b>Data Cleaning & EDA Profiling Engine</b> using Scikit-Learn and NumPy that performs 1-click outlier detection, duplicate elimination, missing value imputation, and correlation matrix generation.<br/>
    • Implemented <b>real-time streaming agent thought processes via Server-Sent Events (SSE)</b> and dynamic Recharts visual rendering, enhancing user transparency during multi-step analytical reasoning.<br/>
    • Architected an automated <b>Executive PDF & Excel Report Generator</b> compiling key performance indicators, anomaly heatmaps, and AI recommendations into publication-ready C-suite briefs.
    """
    story.append(Paragraph(resume_text, body_style))
    story.append(Spacer(1, 8))

    # 4.7 Interview Questions
    story.append(Paragraph("4.7 Top Technical Interview Questions & Model Answers", h2_style))
    qa_list = [
        ("Q1: How do you prevent SQL injection when generating SQL queries dynamically using an LLM?", 
         "Answer: We use a multi-layered defense: (1) Prompt engineering enforces strict read-only queries with dialect specification; (2) An AST (Abstract Syntax Tree) validator via `sqlparse` parses the query before execution and immediately rejects any DML/DDL commands (DROP, DELETE, UPDATE, ALTER); (3) Queries are executed inside a sandboxed, read-only DuckDB in-memory database connection with execution timeouts."),
        
        ("Q2: How does your agent handle schema awareness with large datasets containing hundreds of columns?", 
         "Answer: Instead of stuffing raw data rows into the LLM context, we extract column metadata (column names, inferred data types, distinct value samples, and null ratios) into a compact schema definition. For high-dimensional datasets, we use vector similarity search (RAG) over column names and descriptions to retrieve only the top relevant columns for the specific user question."),
        
        ("Q3: How does the Self-Healing Query loop work when generated SQL fails?", 
         "Answer: When DuckDB raises a syntax error or missing column exception, the error message and the failed SQL are captured by the orchestrator state machine. They are injected into a specialized prompt that instructs the LLM: 'The previous query failed with this specific error. Identify the invalid column/syntax and return only the corrected SQL.' The agent retries up to 3 times before returning a graceful explanation to the user."),
        
        ("Q4: Why did you choose DuckDB alongside MySQL instead of running analytics directly on MySQL?", 
         "Answer: MySQL is an OLTP database optimized for transactional row writes, user authentication, and relational metadata. DuckDB is an in-process columnar OLAP engine designed specifically for analytical aggregations (SUM, AVG, GROUP BY) on parquet/CSV data, executing analytics queries up to 50x faster than traditional row-oriented databases while keeping zero infrastructure overhead."),
        
        ("Q5: How do you stream agent thoughts and intermediate steps to the Next.js frontend?", 
         "Answer: We utilize FastAPI's `StreamingResponse` using Server-Sent Events (SSE) protocol. As the orchestrator transitions through states (`planning` -> `generating_sql` -> `executing` -> `visualizing` -> `explaining`), it yields typed JSON events. The Next.js frontend uses an `EventSource` listener to update the 'Agent Thought Steps' UI in real time before the final markdown text and chart JSON are rendered.")
    ]

    for q, a in qa_list:
        story.append(Paragraph(f"<b>{q}</b>", body_bold))
        story.append(Paragraph(a, body_style))
        story.append(Spacer(1, 4))

    # Build the document
    pdf.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_filename}")

if __name__ == "__main__":
    generate_roadmap_pdf()
