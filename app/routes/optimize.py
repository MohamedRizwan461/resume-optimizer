from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from app.schemas import OptimizeResponse, HealthResponse
from app.services.resume_parser import parse_resume
from app.services.ats_scorer import score_resume
from app.services.ai_optimizer import optimize_resume
from app.services.exporter import export_pdf

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(
    resume: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description: str = Form(..., description="Job description text"),
):
    if not resume.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = resume.filename.rsplit(".", 1)[-1].lower() if "." in resume.filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    file_bytes = await resume.read()
    if len(file_bytes) > 5 * 1024 * 1024:  # 5 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    try:
        original_text = parse_resume(file_bytes, resume.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

    if not original_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the resume. Ensure the file is not scanned/image-only.")

    score_result = score_resume(original_text, job_description)
    ai_result = optimize_resume(original_text, job_description, score_result)

    return OptimizeResponse(
        original_text=original_text,
        optimized_text=ai_result.get("optimized_text") or original_text,
        match_score=score_result["match_score"],
        missing_keywords=score_result["missing_keywords"],
        present_keywords=score_result["present_keywords"],
        ats_issues=score_result["ats_issues"],
        changes_made=ai_result.get("changes_made", []),
    )


@router.post("/export")
async def export(optimized_text: str = Form(...)):
    if not optimized_text.strip():
        raise HTTPException(status_code=400, detail="No resume text to export")
    try:
        pdf_bytes = export_pdf(optimized_text)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=optimized_resume.pdf"},
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
