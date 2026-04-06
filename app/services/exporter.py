import io
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "resume_export.html"


def export_docx(optimized_text: str) -> bytes:
    """
    Convert plain resume text to a formatted, editable Word (.docx) document.
    Returns raw .docx bytes.
    """
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin   = Inches(1.0)
        section.right_margin  = Inches(1.0)

    # Remove default empty paragraph
    for para in doc.paragraphs:
        _delete_paragraph(para)

    lines = optimized_text.split("\n")
    first_line = True

    for line in lines:
        stripped = line.strip()

        if not stripped:
            doc.add_paragraph()
            continue

        # All-caps short line → section heading
        if stripped.isupper() and len(stripped) < 60:
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after  = Pt(2)
            # Underline the heading with a bottom border via style trick
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), '1a1a1a')
            pBdr.append(bottom)
            pPr.append(pBdr)

        # Bullet point
        elif stripped.startswith(("•", "-", "*")):
            bullet_text = stripped.lstrip("•-* ").strip()
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(bullet_text)
            run.font.size = Pt(10.5)
            p.paragraph_format.space_after = Pt(1)

        # First non-empty line → treat as name (large, bold, centered)
        elif first_line:
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            run.font.size = Pt(16)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(2)

        # Regular line
        else:
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.font.size = Pt(10.5)
            p.paragraph_format.space_after = Pt(1)

        if stripped:
            first_line = False

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _delete_paragraph(para):
    p = para._element
    p.getparent().remove(p)


def export_pdf(optimized_text: str) -> bytes:
    """
    Render optimized resume text as a PDF using WeasyPrint.
    Returns raw PDF bytes.
    """
    try:
        from weasyprint import HTML
        html_content = _render_html(optimized_text)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        raise RuntimeError(
            "WeasyPrint is not installed or missing system dependencies. "
            "On Windows, install GTK3 runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer"
        )


def _render_html(resume_text: str) -> str:
    """Convert plain resume text to HTML using the export template."""
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    # Convert plain text lines to HTML paragraphs
    lines = resume_text.split("\n")
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_lines.append("<br>")
        elif stripped.startswith(("•", "-", "*")):
            html_lines.append(f"<li>{stripped.lstrip('•-* ')}</li>")
        elif stripped.isupper() and len(stripped) < 60:
            html_lines.append(f"<h2>{stripped}</h2>")
        else:
            html_lines.append(f"<p>{stripped}</p>")

    body = "\n".join(html_lines)
    return template.replace("{{RESUME_BODY}}", body)
