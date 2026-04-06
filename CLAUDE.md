# CLAUDE.md — Resume Optimizer

> This file is **self-updating**. Every time Claude makes a mistake, learns something new, or discovers a better approach while working on this project, it MUST update the Mistake Log below. This prevents repeating the same errors.

---

## Who I Am Working With

**Rizwan** (Mohamed Rizwan Ameer John) — Robotics & Autonomous Systems Engineer, MS CS @ Governors State University. Expert in assistive robotics, autonomous navigation, and embedded AI. Patent-holding inventor and IEEE YESIST12 Finalist. Technically sharp — skip preamble, lead with the answer.

---

## Project Overview

AI-powered resume tailoring web app. Upload a resume (PDF/DOCX), paste a job description, get:
- ATS match score (TF-IDF keyword similarity)
- Missing/present keyword analysis
- Claude-rewritten resume sections
- Side-by-side diff view (original vs optimized)
- PDF export of the optimized resume

**Stack**: FastAPI + vanilla HTML/JS frontend + Claude CLI (`claude -p`) for AI + pdfplumber/python-docx for parsing + WeasyPrint for export.

---

## Architecture Rules

1. **AI provider is isolated** — only change AI backend in `app/services/ai_optimizer.py`. Never call `claude` CLI or Anthropic SDK directly from routes.
2. **Resume parsing is isolated** — only `app/services/resume_parser.py` handles PDF/DOCX. Supports those two formats only.
3. **ATS scoring is pure Python** — `app/services/ats_scorer.py` uses TF-IDF, no AI calls. Keep it fast and deterministic.
4. **Routes are thin** — routes in `app/routes/optimize.py` only validate input and call services. No business logic in routes.
5. **Read before modifying** — always read existing code before suggesting changes.
6. **No over-engineering** — only build what's needed. No speculative abstractions.

---

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Start dev server
uvicorn main:app --reload

# Open browser
# http://localhost:8000
```

---

## AI Backend Configuration

Current default: **Claude Code CLI** (`claude -p`)

To switch to Anthropic API later:
```
# .env
AI_BACKEND=anthropic_api
ANTHROPIC_API_KEY=sk-ant-...
```

The switch is handled in `app/services/ai_optimizer.py` — no other files need changes.

---

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, mounts static files, includes router |
| `app/routes/optimize.py` | POST /api/optimize, GET /api/health, POST /api/export |
| `app/services/resume_parser.py` | PDF/DOCX → plain text |
| `app/services/ats_scorer.py` | TF-IDF match score + keyword extraction |
| `app/services/ai_optimizer.py` | Claude CLI subprocess wrapper (API-switchable) |
| `app/services/exporter.py` | WeasyPrint HTML→PDF export |
| `app/schemas.py` | Pydantic request/response models |
| `static/index.html` | Single-page UI |
| `static/js/app.js` | Frontend logic — upload, fetch, diff view |
| `templates/resume_export.html` | WeasyPrint PDF template |

---

## Mistake Log

> **HOW THIS WORKS**: When Claude makes a mistake — wrong assumption, bad approach, misread intent, tool failure — it appends an entry here with the date, what went wrong, and the rule learned. This prevents repeating the same mistake.

### Format
```
### [YYYY-MM-DD] — Short description of mistake
**What happened**: ...
**Root cause**: ...
**Rule learned**: ...
```

---

### [2026-04-05] — Initialization
No mistakes logged yet. This file was created on first session. Claude will update this section as the collaboration evolves.

---

## Session Notes

- Rizwan runs Windows 11 with bash shell (Git Bash). Use Unix path syntax in shell commands.
- Primary working dir for this project: `C:\Users\rizwa\Desktop\resume-optimizer`
- Claude Code CLI is available in PATH as `claude`
- WeasyPrint may need GTK/Cairo binaries on Windows — use `weasyprint` pip package + install GTK if export fails
- `claude -p` non-interactive mode has 120s timeout — increase in `ai_optimizer.py` if needed

---

*Last updated: 2026-04-05 | Updated by: Claude Sonnet 4.6*
