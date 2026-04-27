#!/usr/bin/env python3
"""
Generate README-FULL.pdf for AgentSuite.
Uses reportlab for professional PDF output.
Output: <repo-root>/README-FULL.pdf
"""

from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# reportlab imports
# ---------------------------------------------------------------------------
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import (
    HexColor, white
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon
)
from reportlab.graphics import renderPDF

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
BRAND_DARK   = HexColor("#1A1A2E")   # deep navy
BRAND_MID    = HexColor("#16213E")   # dark slate
BRAND_ACCENT = HexColor("#0F3460")   # medium blue
BRAND_VIVID  = HexColor("#E94560")   # crimson accent
BRAND_LIGHT  = HexColor("#F5F5F5")   # near-white background
BRAND_GREY   = HexColor("#6B7280")   # muted text
BRAND_GREEN  = HexColor("#10B981")   # pass / success
MONO_BG      = HexColor("#1E293B")   # code block background
MONO_FG      = HexColor("#E2E8F0")   # code block text

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH  = REPO_ROOT / "README-FULL.pdf"

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
BASE = getSampleStyleSheet()

def _style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=BASE[parent])
    for k, v in kw.items():
        setattr(s, k, v)
    return s

H1 = _style("H1", "Heading1",
    fontSize=22, textColor=BRAND_DARK, leading=28,
    spaceBefore=24, spaceAfter=8, fontName="Helvetica-Bold")

H2 = _style("H2", "Heading2",
    fontSize=16, textColor=BRAND_ACCENT, leading=22,
    spaceBefore=18, spaceAfter=6, fontName="Helvetica-Bold")

H3 = _style("H3", "Heading3",
    fontSize=13, textColor=BRAND_DARK, leading=18,
    spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold")

BODY = _style("BODY", "Normal",
    fontSize=10, textColor=HexColor("#111827"), leading=16,
    spaceBefore=4, spaceAfter=4, fontName="Helvetica")

BODY_SMALL = _style("BODY_SMALL", "Normal",
    fontSize=9, textColor=HexColor("#374151"), leading=14,
    spaceBefore=2, spaceAfter=2, fontName="Helvetica")

BULLET = _style("BULLET", "Normal",
    fontSize=10, textColor=HexColor("#111827"), leading=15,
    spaceBefore=2, spaceAfter=2, fontName="Helvetica",
    leftIndent=18, bulletIndent=6)

CODE = _style("CODE", "Normal",
    fontSize=8.5, textColor=MONO_FG, leading=13,
    fontName="Courier", backColor=MONO_BG,
    leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=6)

CAPTION = _style("CAPTION", "Normal",
    fontSize=9, textColor=BRAND_GREY, leading=13,
    spaceBefore=2, spaceAfter=8, alignment=TA_CENTER,
    fontName="Helvetica-Oblique")

COVER_TITLE = _style("COVER_TITLE", "Normal",
    fontSize=36, textColor=white, leading=44,
    fontName="Helvetica-Bold", alignment=TA_CENTER)

COVER_SUB = _style("COVER_SUB", "Normal",
    fontSize=16, textColor=HexColor("#CBD5E1"), leading=22,
    fontName="Helvetica", alignment=TA_CENTER)

COVER_META = _style("COVER_META", "Normal",
    fontSize=12, textColor=HexColor("#94A3B8"), leading=18,
    fontName="Helvetica", alignment=TA_CENTER)

TOC_SECTION = _style("TOC_SECTION", "Normal",
    fontSize=12, textColor=BRAND_DARK, leading=20,
    fontName="Helvetica-Bold", leftIndent=0)

TOC_ITEM = _style("TOC_ITEM", "Normal",
    fontSize=10, textColor=BRAND_GREY, leading=16,
    fontName="Helvetica", leftIndent=20)

LABEL = _style("LABEL", "Normal",
    fontSize=8, textColor=white, leading=11,
    fontName="Helvetica-Bold", alignment=TA_CENTER,
    backColor=BRAND_ACCENT)


# ---------------------------------------------------------------------------
# Helper flowables
# ---------------------------------------------------------------------------

class HRule(Flowable):
    """Full-width coloured rule."""
    def __init__(self, color=BRAND_ACCENT, thickness=1, width=None):
        super().__init__()
        self.color = color
        self.thickness = thickness
        self._width = width

    def wrap(self, availW, availH):
        self.width = self._width or availW
        self.height = self.thickness + 4
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.thickness / 2, self.width, self.thickness / 2)


class SectionBadge(Flowable):
    """Coloured section number badge."""
    def __init__(self, number, color=BRAND_VIVID):
        super().__init__()
        self.number = str(number)
        self.color = color

    def wrap(self, availW, availH):
        self.width, self.height = 28, 28
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 0, 26, 26, 4, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(13, 7, self.number)


def code_block(text):
    """Return a code-block paragraph."""
    lines = text.strip().split("\n")
    safe = "<br/>".join(
        line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for line in lines
    )
    return Paragraph(safe, CODE)


def bullet(text):
    return Paragraph(f"• {text}", BULLET)


def page_header_footer(canvas, doc):
    canvas.saveState()
    w, h = LETTER

    # header bar
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, h - 36, w, 36, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(0.65 * inch, h - 22, "AgentSuite — Technical Reference")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 0.65 * inch, h - 22, "v0.7.0")

    # footer
    canvas.setFillColor(BRAND_LIGHT)
    canvas.rect(0, 0, w, 28, fill=1, stroke=0)
    canvas.setFillColor(BRAND_GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.65 * inch, 10, "© 2026 AgentSuite — MIT License")
    canvas.drawRightString(w - 0.65 * inch, 10, f"Page {doc.page}")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Architecture diagram (reportlab Drawing)
# ---------------------------------------------------------------------------

def arch_diagram_main():
    """Full system architecture drawing."""
    W, H = 480, 310
    d = Drawing(W, H)

    def box(x, y, w, h, fill=BRAND_ACCENT, rx=6):
        d.add(Rect(x, y, w, h, rx=rx, ry=rx,
                   fillColor=fill, strokeColor=None))

    def label(x, y, text, size=9, color=white, bold=False):
        font = "Helvetica-Bold" if bold else "Helvetica"
        d.add(String(x, y, text, fontSize=size,
                     fillColor=color, fontName=font))

    def hline(x1, y1, x2, y2, color=BRAND_GREY, width=1):
        d.add(Line(x1, y1, x2, y2,
                   strokeColor=color, strokeWidth=width))

    # Background
    box(0, 0, W, H, fill=HexColor("#0F172A"), rx=10)

    # Title bar
    box(10, H - 40, W - 20, 30, fill=BRAND_VIVID, rx=6)
    label(W / 2 - 80, H - 30, "AgentSuite v0.7.0 — System Architecture",
          size=11, bold=True)

    # Entry points row
    entry_y = H - 90
    for i, (title, sub) in enumerate([
        ("CLI", "typer"),
        ("MCP Server", "stdio JSON-RPC"),
        ("Python API", "registry.py"),
    ]):
        x = 20 + i * 158
        box(x, entry_y, 140, 44, fill=BRAND_MID, rx=5)
        label(x + 10, entry_y + 28, title, size=10, bold=True)
        label(x + 10, entry_y + 12, sub, size=8, color=HexColor("#94A3B8"))

    # Arrow down from entry points to BaseAgent
    mid_x = W / 2
    hline(mid_x, entry_y, mid_x, entry_y - 26,
          color=BRAND_VIVID, width=2)

    # BaseAgent box
    ba_y = entry_y - 70
    box(W / 2 - 90, ba_y, 180, 44, fill=BRAND_ACCENT, rx=6)
    label(W / 2 - 70, ba_y + 28, "BaseAgent", size=10, bold=True)
    label(W / 2 - 78, ba_y + 12, "5-stage pipeline kernel", size=8,
          color=HexColor("#BAE6FD"))

    # Pipeline stages
    stages = ["intake", "extract", "spec", "execute", "qa"]
    stg_y = ba_y - 50
    stg_w = 78
    stg_gap = 6
    total_w = len(stages) * stg_w + (len(stages) - 1) * stg_gap
    stg_x0 = (W - total_w) / 2

    colors = [HexColor("#065F46"), HexColor("#1E40AF"),
              HexColor("#7C3AED"), HexColor("#92400E"), HexColor("#991B1B")]
    for i, (stg, col) in enumerate(zip(stages, colors)):
        x = stg_x0 + i * (stg_w + stg_gap)
        box(x, stg_y, stg_w, 30, fill=col, rx=4)
        label(x + stg_w / 2 - len(stg) * 3, stg_y + 10, stg, size=8.5)

    # Connector from BaseAgent to stages
    hline(mid_x, ba_y, mid_x, stg_y + 30,
          color=BRAND_VIVID, width=2)

    # Agents row
    agents = ["Founder", "Design", "Product", "Engineering",
              "Marketing", "Trust/Risk", "CIO"]
    ag_y = stg_y - 60
    ag_w = (W - 20) / len(agents) - 4
    for i, ag in enumerate(agents):
        x = 10 + i * (ag_w + 4)
        box(x, ag_y, ag_w, 36, fill=HexColor("#1E3A5F"), rx=4)
        short = ag if len(ag) <= 8 else ag[:7] + "."
        label(x + ag_w / 2 - len(short) * 3, ag_y + 14,
              short, size=7.5)

    # Connectors from stages row to agents row
    for i in range(len(agents)):
        ax = 10 + i * (ag_w + 4) + ag_w / 2
        hline(ax, stg_y, ax, ag_y + 36,
              color=HexColor("#334155"), width=1)

    # Kernel box
    kernel_y = ag_y - 50
    box(W / 2 - 100, kernel_y, 200, 36, fill=HexColor("#134E4A"), rx=6)
    label(W / 2 - 64, kernel_y + 20, "_kernel/ store", size=10, bold=True)
    label(W / 2 - 80, kernel_y + 6, "approved artifacts persisted per project-slug",
          size=7.5, color=HexColor("#6EE7B7"))

    # Arrow from agents to kernel
    hline(mid_x, ag_y, mid_x, kernel_y + 36,
          color=BRAND_GREEN, width=1.5)

    return d


def pipeline_diagram():
    """5-stage pipeline detail drawing."""
    W, H = 480, 90
    d = Drawing(W, H)

    stages = [
        ("1 intake", "Read inputs,\nvalidate schema", HexColor("#065F46")),
        ("2 extract", "LLM extracts\nstructured context", HexColor("#1E40AF")),
        ("3 spec", "Generate 9\nspec artifacts", HexColor("#7C3AED")),
        ("4 execute", "Render 8\nbrief templates", HexColor("#92400E")),
        ("5 qa / approval", "Score rubric,\ngate promotion", HexColor("#991B1B")),
    ]
    bw = 84
    gap = 12
    total = len(stages) * bw + (len(stages) - 1) * gap
    x0 = (W - total) / 2

    for i, (title, sub, col) in enumerate(stages):
        x = x0 + i * (bw + gap)
        d.add(Rect(x, 20, bw, 60, rx=6, ry=6,
                   fillColor=col, strokeColor=None))
        d.add(String(x + bw / 2 - len(title) * 3.2, 66,
                     title, fontSize=8.5, fillColor=white,
                     fontName="Helvetica-Bold"))
        for j, line in enumerate(sub.split("\n")):
            d.add(String(x + bw / 2 - len(line) * 2.8, 46 - j * 12,
                         line, fontSize=7.5, fillColor=HexColor("#CBD5E1"),
                         fontName="Helvetica"))
        # Arrow
        if i < len(stages) - 1:
            ax = x + bw + 2
            d.add(Line(ax, 50, ax + gap - 2, 50,
                       strokeColor=HexColor("#E94560"), strokeWidth=2))
            # arrowhead
            d.add(Polygon(
                [ax + gap - 2, 50, ax + gap - 8, 54, ax + gap - 8, 46],
                fillColor=HexColor("#E94560"), strokeColor=None
            ))

    return d


# ---------------------------------------------------------------------------
# Agent data
# ---------------------------------------------------------------------------

AGENTS = [
    {
        "name": "Founder Agent",
        "version": "v0.1.0",
        "cmd": "agentsuite founder run",
        "cli_flags": ["business-goal", "project-slug", "inputs-dir"],
        "inputs": ["business_goal", "project_slug", "inputs_dir"],
        "spec_artifacts": [
            "brand-system.md", "founder-voice-guide.md",
            "product-positioning.md", "audience-map.md",
            "claims-and-proof-library.md", "visual-style-guide.md",
            "campaign-production-workflow.md", "asset-qa-checklist.md",
            "reusable-prompt-library.md",
        ],
        "brief_templates": [
            "ad-copy", "email-campaign", "landing-page", "press-release",
            "social-post", "video-script", "product-launch", "blog-post",
        ],
        "primary_artifact": "brand-system.md",
        "description": (
            "Codifies organizational identity into a reusable brand operating system. "
            "Outputs a complete brand kernel — voice, positioning, visual language, "
            "and proof points — that downstream agents consume to stay on-brand."
        ),
        "rubric": [
            "Brand voice consistency", "Positioning clarity", "Audience specificity",
            "Claims verifiability", "Visual coherence", "Template completeness",
            "Prompt reusability", "QA coverage", "Artifact linkage",
        ],
    },
    {
        "name": "Design Agent",
        "version": "v0.2.0",
        "cmd": "agentsuite design run",
        "cli_flags": ["target-audience", "campaign-goal", "channel"],
        "inputs": ["target_audience", "campaign_goal", "channel"],
        "spec_artifacts": [
            "visual-direction.md", "design-brief.md",
            "mood-board-spec.md", "brand-rules-extracted.md",
            "image-generation-prompt.md", "revision-instructions.md",
            "design-qa-report.md", "accessibility-audit-template.md",
            "final-asset-acceptance-checklist.md",
        ],
        "brief_templates": [
            "banner-ad", "email-header", "social-graphic",
            "landing-hero", "deck-slide", "print-flyer",
            "video-thumbnail", "icon-set",
        ],
        "primary_artifact": "visual-direction.md",
        "description": (
            "Transforms brand identity into a complete set of visual direction and design spec artifacts. "
            "Produces a visual direction brief, mood-board spec, brand-rules extraction, "
            "image generation prompts, revision instructions, and a final asset acceptance checklist "
            "that creative and engineering teams can act on directly."
        ),
        "rubric": [
            "Visual direction clarity", "Brand rule fidelity", "Mood-board specificity",
            "Prompt reusability", "Revision instruction actionability", "Accessibility coverage",
            "Channel appropriateness", "Handoff clarity", "QA completeness",
        ],
    },
    {
        "name": "Product Agent",
        "version": "v0.3.0",
        "cmd": "agentsuite product run",
        "cli_flags": ["product-name", "target-users", "core-problem", "project-slug"],
        "inputs": ["product_name", "target_users", "core_problem"],
        "spec_artifacts": [
            "product-requirements-doc.md", "user-story-map.md",
            "feature-prioritization.md", "success-metrics.md",
            "competitive-analysis.md", "user-persona-map.md",
            "acceptance-criteria.md", "product-roadmap.md",
            "risk-register.md",
        ],
        "brief_templates": [
            "sprint-planning-brief", "stakeholder-update", "launch-announcement",
            "feature-spec", "user-interview-guide", "a-b-test-plan",
            "demo-script", "investor-update",
        ],
        "primary_artifact": "product-requirements-doc.md",
        "description": (
            "Converts PM intent into a structured product specification packet. "
            "Outputs a full PRD, journey maps, prioritized feature list, and "
            "a coding-ready handoff package that engineering agents consume directly."
        ),
        "rubric": [
            "Problem clarity", "User empathy depth", "Feature prioritization rigor",
            "Metric specificity", "Competitive awareness", "Constraint realism",
            "Release criteria completeness", "Stakeholder alignment", "Handoff readiness",
        ],
    },
    {
        "name": "Engineering Agent",
        "version": "v0.4.0",
        "cmd": "agentsuite engineering run",
        "cli_flags": ["system-name", "problem-domain", "tech-stack", "scale-requirements"],
        "inputs": ["system_name", "problem_domain", "tech_stack"],
        "spec_artifacts": [
            "architecture-decision-record.md", "system-design.md",
            "api-spec.md", "data-model.md", "security-review.md",
            "deployment-plan.md", "runbook.md", "tech-debt-register.md",
            "performance-requirements.md",
        ],
        "brief_templates": [
            "sprint-ticket", "code-review-checklist", "incident-report",
            "capacity-plan", "on-call-handoff", "release-checklist",
            "postmortem", "vendor-evaluation",
        ],
        "primary_artifact": "architecture-decision-record.md",
        "description": (
            "Converts system requirements into a complete engineering specification packet. "
            "Covers architecture decisions, API contracts, data models, security posture, "
            "deployment strategy, and operational runbooks for day-2 operations."
        ),
        "rubric": [
            "Architecture soundness", "API contract completeness", "Data model normalization",
            "Security coverage", "Deployment reproducibility", "Observability design",
            "Tech-debt transparency", "Performance baseline", "Runbook operability",
        ],
    },
    {
        "name": "Marketing Agent",
        "version": "v0.5.0",
        "cmd": "agentsuite marketing run",
        "cli_flags": ["brand-name", "campaign-goal", "target-market"],
        "inputs": ["brand_name", "campaign_goal", "target_market"],
        "spec_artifacts": [
            "campaign-brief.md", "audience-profile.md",
            "messaging-framework.md", "content-calendar.md",
            "channel-strategy.md", "seo-keyword-plan.md",
            "competitive-positioning.md", "launch-plan.md",
            "measurement-framework.md",
        ],
        "brief_templates": [
            "ad-creative-brief", "influencer-brief", "pr-outreach",
            "email-sequence", "social-campaign", "content-series",
            "event-brief", "analyst-briefing",
        ],
        "primary_artifact": "campaign-brief.md",
        "description": (
            "Produces a full go-to-market packet from brand identity and campaign goal. "
            "Covers audience targeting, channel mix, messaging architecture, content plan, "
            "SEO strategy, and measurement framework — everything a growth team needs to execute."
        ),
        "rubric": [
            "Audience precision", "Channel-message fit", "Messaging differentiation",
            "Content calendar completeness", "SEO keyword depth", "Competitive clarity",
            "Launch sequencing", "Metric specificity", "Brief reusability",
        ],
    },
    {
        "name": "Trust/Risk Agent",
        "version": "v0.6.0",
        "cmd": "agentsuite trust-risk run",
        "cli_flags": ["product-name", "risk-domain", "stakeholder-context"],
        "inputs": ["product_name", "risk_domain", "stakeholder_context"],
        "spec_artifacts": [
            "threat-model.md", "risk-register.md",
            "control-framework.md", "incident-response-plan.md",
            "compliance-matrix.md", "vendor-risk-assessment.md",
            "security-policy.md", "audit-readiness-report.md",
            "residual-risk-acceptance.md",
        ],
        "brief_templates": [
            "breach-notification", "executive-risk-summary",
            "penetration-test-brief", "remediation-tracker",
            "risk-acceptance-form", "security-awareness-brief",
            "tabletop-exercise-scenario", "vendor-security-questionnaire",
        ],
        "primary_artifact": "threat-model.md",
        "description": (
            "Produces a complete security and risk governance packet. "
            "Covers threat modeling (STRIDE/DREAD), risk quantification, "
            "control mapping, incident response playbooks, compliance matrices "
            "(SOC 2, ISO 27001, GDPR), and vendor risk assessment."
        ),
        "rubric": [
            "Threat coverage breadth", "Risk quantification rigor", "Control completeness",
            "Incident response operability", "Compliance accuracy", "Vendor risk depth",
            "Policy enforceability", "Audit readiness", "Residual risk transparency",
        ],
    },
    {
        "name": "CIO Agent",
        "version": "v0.7.0",
        "cmd": "agentsuite cio run",
        "cli_flags": ["organization-name", "strategic-priorities", "it-maturity-level"],
        "inputs": ["organization_name", "strategic_priorities", "it_maturity_level"],
        "spec_artifacts": [
            "it-strategy.md", "technology-roadmap.md",
            "vendor-portfolio.md", "digital-transformation-plan.md",
            "it-governance-framework.md", "enterprise-architecture.md",
            "budget-allocation-model.md", "workforce-development-plan.md",
            "it-risk-appetite-statement.md",
        ],
        "brief_templates": [
            "board-technology-briefing", "it-steering-committee-agenda",
            "vendor-review-summary", "project-portfolio-status",
            "digital-initiative-proposal", "it-investment-case",
            "technology-modernization-pitch", "quarterly-it-review",
        ],
        "primary_artifact": "it-strategy.md",
        "description": (
            "Produces a board-ready IT strategy packet aligned to organizational priorities. "
            "Covers multi-year technology roadmap, vendor portfolio rationalization, "
            "enterprise architecture, digital transformation sequencing, and IT governance "
            "frameworks for enterprise scale."
        ),
        "rubric": [
            "Strategic alignment", "Roadmap sequencing", "Vendor rationalization",
            "Architecture coherence", "Transformation prioritization", "Governance rigor",
            "Budget defensibility", "Workforce planning", "Risk appetite clarity",
        ],
    },
]


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def simple_table(data, col_widths, header=True):
    """Render a simple styled table."""
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_ACCENT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, BRAND_LIGHT]),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    rows = []
    for i, row in enumerate(data):
        rows.append([Paragraph(str(cell), BODY_SMALL) for cell in row])
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def build_pdf():
    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.55 * inch,
        title="AgentSuite — Technical Reference v0.7.0",
        author="AgentSuite",
        subject="Complete architecture, API reference, and pipeline documentation",
    )

    story = []

    # -----------------------------------------------------------------------
    # COVER PAGE
    # -----------------------------------------------------------------------
    # Full-bleed cover via a custom flowable
    class CoverPage(Flowable):
        def wrap(self, aw, ah):
            self.width, self.height = aw, ah
            return aw, ah

        def draw(self):
            c = self.canv
            w, h = LETTER
            # Background gradient simulation (two rects)
            c.setFillColor(BRAND_DARK)
            c.rect(0, 0, w, h, fill=1, stroke=0)
            c.setFillColor(BRAND_MID)
            c.rect(0, 0, w, h * 0.55, fill=1, stroke=0)

            # Accent bar
            c.setFillColor(BRAND_VIVID)
            c.rect(0, h * 0.72, w, 6, fill=1, stroke=0)

            # Title
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 40)
            c.drawCentredString(w / 2, h * 0.76, "AgentSuite")
            c.setFont("Helvetica", 20)
            c.setFillColor(HexColor("#CBD5E1"))
            c.drawCentredString(w / 2, h * 0.70, "Technical Reference")

            # Version badge
            c.setFillColor(BRAND_VIVID)
            c.roundRect(w / 2 - 45, h * 0.63, 90, 26, 5, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(w / 2, h * 0.635, "v0.7.0")

            # Subtitle
            c.setFillColor(HexColor("#94A3B8"))
            c.setFont("Helvetica", 12)
            c.drawCentredString(
                w / 2, h * 0.58,
                "Complete architecture, API reference, and pipeline documentation"
            )

            # Agent list
            agents = ["Founder", "Design", "Product", "Engineering",
                      "Marketing", "Trust/Risk", "CIO"]
            c.setFont("Helvetica", 10)
            c.setFillColor(HexColor("#64748B"))
            c.drawCentredString(w / 2, h * 0.52,
                " · ".join(agents))

            # Bottom metadata
            c.setFillColor(HexColor("#1E293B"))
            c.rect(0, 0, w, 60, fill=1, stroke=0)
            c.setFillColor(HexColor("#64748B"))
            c.setFont("Helvetica", 9)
            c.drawString(0.75 * inch, 28, "MIT License — github.com/scottconverse/AgentSuite")
            c.drawRightString(w - 0.75 * inch, 28,
                f"Generated {date.today().strftime('%B %d, %Y')}")

    story.append(CoverPage())
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # TABLE OF CONTENTS
    # -----------------------------------------------------------------------
    story.append(Paragraph("Table of Contents", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 12))

    toc = [
        ("1", "System Architecture", [
            "Entry Points (CLI · MCP · Python API)",
            "BaseAgent and Specification Kernel",
            "Kernel Promotion Flow",
        ]),
        ("2", "5-Stage Pipeline", [
            "Stage 1: Intake", "Stage 2: Extract", "Stage 3: Spec",
            "Stage 4: Execute", "Stage 5: QA / Approval Gate",
        ]),
        ("3", "Agent Reference", [
            "Founder Agent (v0.1.0)", "Design Agent (v0.2.0)",
            "Product Agent (v0.3.0)", "Engineering Agent (v0.4.0)",
            "Marketing Agent (v0.5.0)", "Trust/Risk Agent (v0.6.0)",
            "CIO Agent (v0.7.0)",
        ]),
        ("4", "MCP Integration", [
            "Claude Code / Cowork configuration",
            "Codex configuration", "Tool namespace reference",
        ]),
        ("5", "Configuration Reference", [
            "Environment variables", "Provider selection", "Cost caps",
        ]),
        ("6", "QA Rubric System", [
            "9-dimension scoring", "Pass threshold", "Revision flow",
        ]),
    ]

    for num, section, subs in toc:
        story.append(Paragraph(f"<b>{num}. {section}</b>", TOC_SECTION))
        for sub in subs:
            story.append(Paragraph(f"› {sub}", TOC_ITEM))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 1: SYSTEM ARCHITECTURE
    # -----------------------------------------------------------------------
    story.append(Paragraph("1. System Architecture", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "AgentSuite exposes seven role-specific reasoning agents through three "
        "co-equal entry points: a CLI (built with Typer), an MCP server "
        "(stdio JSON-RPC, compatible with Claude Code, Codex, and any "
        "MCP-capable harness), and a Python API via the agent registry. "
        "All three surfaces share the same underlying agent implementations — "
        "there is no privileged path.",
        BODY
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "Every agent inherits from <b>BaseAgent</b>, which owns the 5-stage "
        "pipeline, cost accounting, artifact persistence, and the approval gate. "
        "Agents specialize BaseAgent with role-specific prompts, rubrics, "
        "artifact manifests, and brief templates. This means adding a new agent "
        "is a configuration task, not a structural change.",
        BODY
    ))
    story.append(Spacer(1, 12))

    # Main arch diagram
    story.append(renderPDF.GraphicsFlowable(arch_diagram_main()))
    story.append(Paragraph(
        "Figure 1 — AgentSuite system architecture. Entry points converge on BaseAgent; "
        "approved artifacts are persisted to the _kernel/ store per project-slug.",
        CAPTION
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Kernel Promotion", H2))
    story.append(Paragraph(
        "When a run is approved (via <font face='Courier'>agentsuite &lt;agent&gt; approve</font> "
        "or the MCP <font face='Courier'>&lt;agent&gt;_approve</font> tool), all spec artifacts "
        "and brief templates are promoted from the ephemeral run directory "
        "(<font face='Courier'>.agentsuite/runs/&lt;run-id&gt;/</font>) into the long-lived "
        "kernel store (<font face='Courier'>.agentsuite/_kernel/&lt;project-slug&gt;/</font>). "
        "Downstream agents read the kernel automatically — a Marketing Agent run "
        "picks up the Founder Agent's approved brand-system.md without any "
        "manual configuration.",
        BODY
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 2: 5-STAGE PIPELINE
    # -----------------------------------------------------------------------
    story.append(Paragraph("2. The 5-Stage Pipeline", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Every AgentSuite agent runs the same five-stage pipeline, controlled "
        "by BaseAgent. Stages are sequential; each stage checkpoints its output "
        "to <font face='Courier'>_state.json</font> before proceeding so that "
        "interrupted runs can resume from the last completed stage.",
        BODY
    ))
    story.append(Spacer(1, 10))

    story.append(renderPDF.GraphicsFlowable(pipeline_diagram()))
    story.append(Paragraph(
        "Figure 2 — The 5-stage pipeline. Each stage writes checkpointed output "
        "before advancing. The QA gate blocks promotion until the rubric score passes.",
        CAPTION
    ))
    story.append(Spacer(1, 10))

    pipeline_detail = [
        ("Stage", "Name", "Input", "Output", "LLM call?"),
        ("1", "Intake", "inputs_dir, CLI flags", "inputs_manifest.json", "No"),
        ("2", "Extract", "inputs_manifest.json", "extracted_context.json", "Yes — structured extraction"),
        ("3", "Spec", "extracted_context.json", "9 spec artifacts + consistency_report.json", "Yes — one call per artifact"),
        ("4", "Execute", "Spec artifacts + kernel", "8 brief templates + export-manifest.json", "Yes — one call per template"),
        ("5", "QA", "All spec + execute artifacts", "qa_report.md + qa_scores.json", "Yes — rubric scoring"),
    ]

    story.append(simple_table(
        pipeline_detail,
        col_widths=[0.45 * inch, 0.9 * inch, 1.5 * inch, 2.2 * inch, 1.3 * inch]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Approval Gate", H2))
    story.append(Paragraph(
        "After Stage 5 completes, the run pauses at the approval gate. "
        "The run is not automatically promoted — a human (or an orchestrating "
        "agent) must review <font face='Courier'>qa_report.md</font> and issue "
        "an explicit approval command. If the QA score is below 7.0, the agent "
        "flags the run as <b>requires_revision</b> and documents which rubric "
        "dimensions failed. The run can be re-executed after addressing the "
        "identified gaps.",
        BODY
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 3: AGENT REFERENCE
    # -----------------------------------------------------------------------
    story.append(Paragraph("3. Agent Reference", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "Each agent specializes BaseAgent with role-specific prompts, artifact "
        "manifests, brief templates, and QA rubric dimensions. All agents "
        "produce the same structural pattern: 9 spec artifacts, 8 brief "
        "templates, qa_report.md, qa_scores.json, _state.json, and _meta.json. "
        "17–26 total artifacts per run depending on the agent.",
        BODY
    ))
    story.append(Spacer(1, 6))

    for ag in AGENTS:
        story.append(Spacer(1, 8))
        story.append(HRule(color=BRAND_LIGHT, thickness=0.5))
        story.append(Paragraph(
            f"{ag['name']} <font color='#E94560'>{ag['version']}</font>", H2
        ))

        story.append(Paragraph(ag["description"], BODY))
        story.append(Spacer(1, 6))

        # CLI command
        story.append(Paragraph("<b>CLI command</b>", H3))
        flags = ag.get("cli_flags", ["business-goal", "project-slug", "inputs-dir"])
        flag_lines = " \\\n  --".join(flags)
        story.append(code_block(
            f"agentsuite {ag['cmd'].split('agentsuite ')[1]} \\\n"
            f"  --{flag_lines}"
        ))
        story.append(Spacer(1, 4))

        # Three-column details table
        spec_text = "\n".join(f"• {a}" for a in ag["spec_artifacts"])
        brief_text = "\n".join(f"• {b}" for b in ag["brief_templates"])
        detail_data = [
            ["Inputs", "Spec Artifacts (Stage 3)", "Brief Templates (Stage 4)"],
            [
                "\n".join(f"• {i}" for i in ag["inputs"]),
                spec_text,
                brief_text,
            ],
        ]
        t = Table(
            [[Paragraph(str(cell), BODY_SMALL) for cell in row]
             for row in detail_data],
            colWidths=[1.5 * inch, 3.0 * inch, 2.35 * inch]
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_ACCENT),
            ("TEXTCOLOR",  (0, 0), (-1, 0), white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 9),
            ("BACKGROUND", (0, 1), (-1, -1), BRAND_LIGHT),
            ("FONTNAME",   (0, 1), (-1, -1), "Courier"),
            ("FONTSIZE",   (0, 1), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)

        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>Primary artifact:</b> "
            f"<font face='Courier'>{ag['primary_artifact']}</font>   "
            f"<b>QA rubric dimensions:</b> {', '.join(ag['rubric'][:5])} …",
            BODY_SMALL
        ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 4: MCP INTEGRATION
    # -----------------------------------------------------------------------
    story.append(Paragraph("4. MCP Integration", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "AgentSuite ships an MCP server (<font face='Courier'>agentsuite-mcp</font>) "
        "that exposes all agents as callable tools over stdio JSON-RPC. Any "
        "MCP-capable harness can wire it in — Claude Code, Codex, Cowork, "
        "or a custom integration.",
        BODY
    ))

    story.append(Paragraph("Claude Code / Cowork (.mcp.json)", H2))
    story.append(code_block("""{
  "mcpServers": {
    "agentsuite": {
      "command": "uvx",
      "args": ["agentsuite-mcp"],
      "env": {
        "AGENTSUITE_ENABLED_AGENTS": "founder,design,product,engineering,marketing,trust-risk,cio",
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}"""))

    story.append(Paragraph("Codex (~/.codex/mcp.toml)", H2))
    story.append(code_block("""[servers.agentsuite]
command = "uvx"
args    = ["agentsuite-mcp"]

[servers.agentsuite.env]
AGENTSUITE_ENABLED_AGENTS = "founder,design,product,engineering,marketing,trust-risk,cio"
ANTHROPIC_API_KEY         = "sk-ant-..." """))

    story.append(Paragraph("No-install invocation (uvx)", H2))
    story.append(code_block(
        'uvx --from git+https://github.com/scottconverse/AgentSuite.git agentsuite-mcp'
    ))

    story.append(Paragraph("MCP Tool Namespace", H2))
    story.append(Paragraph(
        "Each agent exposes five tools. The cross-agent tools are always available "
        "regardless of <font face='Courier'>AGENTSUITE_ENABLED_AGENTS</font>.",
        BODY
    ))

    mcp_tools = [
        ("Tool", "Description"),
        ("<agent>_run", "Start a new run for the specified agent"),
        ("<agent>_approve", "Promote a completed run to the kernel store"),
        ("<agent>_get_status", "Return current stage and artifact count for a run"),
        ("<agent>_list_runs", "List all runs for a project slug"),
        ("<agent>_resume", "Resume an interrupted run from last checkpoint"),
        ("agentsuite_list_agents", "List all enabled agents and their versions"),
        ("agentsuite_kernel_artifacts", "List all approved artifacts in the kernel"),
        ("agentsuite_cost_report", "Return cost breakdown for all runs"),
    ]

    story.append(simple_table(
        mcp_tools,
        col_widths=[2.5 * inch, 4.35 * inch]
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 5: CONFIGURATION
    # -----------------------------------------------------------------------
    story.append(Paragraph("5. Configuration Reference", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "All AgentSuite behaviour is controlled through environment variables. "
        "No config file is required — set variables in your shell, in your "
        "MCP server env block, or in a <font face='Courier'>.env</font> file "
        "in the project root.",
        BODY
    ))
    story.append(Spacer(1, 8))

    config_data = [
        ("Variable", "Default", "Purpose"),
        ("AGENTSUITE_ENABLED_AGENTS", "founder",
         "Comma-separated agent names to expose. Controls which MCP tools are registered."),
        ("AGENTSUITE_OUTPUT_DIR", ".agentsuite",
         "Root directory for all run artifacts and the kernel store."),
        ("AGENTSUITE_LLM_PROVIDER", "(auto-detect)",
         "Force provider: anthropic | openai | gemini | ollama. Auto-detects from available API keys."),
        ("AGENTSUITE_COST_CAP_USD", "5.0",
         "Hard kill switch. Run aborts if cumulative LLM cost exceeds this value."),
        ("AGENTSUITE_EXPOSE_STAGES", "false",
         "Set 'true' to expose individual stage tools (intake, extract, spec, execute, qa) via MCP."),
        ("ANTHROPIC_API_KEY", "(none)",
         "Anthropic Claude API key. Used when provider is 'anthropic' or auto-detected."),
        ("OPENAI_API_KEY", "(none)",
         "OpenAI API key. Used when provider is 'openai' or auto-detected."),
        ("GOOGLE_API_KEY / GEMINI_API_KEY", "(none)",
         "Google Gemini API key. Used when provider is 'gemini' or auto-detected."),
    ]

    story.append(simple_table(
        config_data,
        col_widths=[2.1 * inch, 1.2 * inch, 3.55 * inch]
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Provider Resolution Order", H2))
    story.append(Paragraph(
        "When <font face='Courier'>AGENTSUITE_LLM_PROVIDER</font> is not set, "
        "AgentSuite auto-detects in this order: "
        "<b>Anthropic → OpenAI → Gemini → Ollama</b>. "
        "Ollama is used only if a daemon is reachable at "
        "<font face='Courier'>localhost:11434</font> and no cloud API keys are present. "
        "To run fully offline, ensure no cloud API keys are set and Ollama is running "
        "with at least one Gemma 4 model pulled.",
        BODY
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Ollama Model Selection", H2))
    ollama_data = [
        ("Model tag", "Size", "Use case"),
        ("gemma4:e2b", "~3 GB", "Laptop-class, fastest inference, reduced quality"),
        ("gemma4:e4b", "~5 GB", "Recommended — balanced quality and speed"),
        ("gemma4:26b-moe", "~15 GB", "High-end workstation, best quality, slowest"),
    ]
    story.append(simple_table(
        ollama_data,
        col_widths=[1.8 * inch, 0.9 * inch, 4.15 * inch]
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 6: QA RUBRIC SYSTEM
    # -----------------------------------------------------------------------
    story.append(Paragraph("6. QA Rubric System", H1))
    story.append(HRule(color=BRAND_VIVID, thickness=2))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Every AgentSuite run is scored against a 9-dimension rubric before "
        "the approval gate. Rubric evaluation is performed by the LLM itself "
        "in Stage 5 (QA), using a structured prompt that asks for a score "
        "(0–10) and a brief justification for each dimension. "
        "Scores are written to <font face='Courier'>qa_scores.json</font> "
        "and a human-readable summary is written to <font face='Courier'>qa_report.md</font>.",
        BODY
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Scoring Mechanics", H2))
    rubric_data = [
        ("Field", "Value", "Notes"),
        ("Dimensions per agent", "9", "Role-specific; see Section 3 for per-agent lists"),
        ("Score range per dimension", "0 – 10", "Integer scale, LLM-evaluated"),
        ("Aggregate score", "Mean of 9 dimensions", "Rounded to 1 decimal place"),
        ("Pass threshold", "7.0", "Runs at or above 7.0 are promotion-eligible"),
        ("Requires-revision flag", "< 7.0", "Run is flagged; failing dimensions are listed"),
        ("Output files", "qa_scores.json + qa_report.md", "Both written at end of Stage 5"),
    ]
    story.append(simple_table(
        rubric_data,
        col_widths=[2.0 * inch, 1.8 * inch, 3.05 * inch]
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Revision Flow", H2))
    story.append(Paragraph(
        "If a run receives a <b>requires_revision</b> status, the workflow is:",
        BODY
    ))
    for step in [
        "Review qa_report.md — it lists each failing dimension with a score and justification.",
        "Update the input artifacts in the inputs_dir to address the identified gaps.",
        "Re-run the agent with the same --project-slug to create a new run-id.",
        "The new run reads updated inputs and re-executes all five stages.",
        "If the new run scores ≥ 7.0, issue the approve command to promote to kernel.",
    ]:
        story.append(bullet(step))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Sample qa_scores.json", H2))
    story.append(code_block("""{
  "run_id": "founder-20260427-143201",
  "agent": "founder",
  "aggregate_score": 8.2,
  "pass_threshold": 7.0,
  "status": "approved",
  "dimensions": {
    "brand_voice_consistency":  { "score": 9, "justification": "Voice is distinctive and ..." },
    "positioning_clarity":      { "score": 8, "justification": "Positioning statement is ..." },
    "audience_specificity":     { "score": 8, "justification": "Segments are well-defined ..." },
    "claims_verifiability":     { "score": 7, "justification": "Most claims include ..."   },
    "visual_coherence":         { "score": 9, "justification": "Color and typography ..."  },
    "template_completeness":    { "score": 8, "justification": "All 8 templates present ..." },
    "prompt_reusability":       { "score": 8, "justification": "Prompts are parameterized ..." },
    "qa_coverage":              { "score": 7, "justification": "Checklist covers main ..."  },
    "artifact_linkage":         { "score": 9, "justification": "Cross-references are ..."  }
  }
}"""))

    story.append(Spacer(1, 10))
    story.append(HRule(color=BRAND_LIGHT, thickness=1))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>AgentSuite v0.7.0</b> · MIT License · "
        "github.com/scottconverse/AgentSuite · "
        f"Generated {date.today().strftime('%B %d, %Y')}",
        CAPTION
    ))

    # -----------------------------------------------------------------------
    # BUILD
    # -----------------------------------------------------------------------
    doc.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)
    print(f"PDF written -> {OUT_PATH}")
    print(f"Size: {OUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_pdf()
