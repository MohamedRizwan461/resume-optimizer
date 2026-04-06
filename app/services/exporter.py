import os
from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "resume_export.html"


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
