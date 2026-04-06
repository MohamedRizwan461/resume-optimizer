import os
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()

_AI_BACKEND = os.getenv("AI_BACKEND", "claude_cli")
_ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
_CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
_TIMEOUT = 120  # seconds


def optimize_resume(resume_text: str, jd_text: str, score_result: dict) -> dict:
    """
    Use Claude to rewrite the resume to better match the job description.

    Returns:
        {
            "optimized_text": str,
            "changes_made": List[str],
        }
    """
    prompt = _build_prompt(resume_text, jd_text, score_result)

    if _AI_BACKEND == "anthropic_api" and _ANTHROPIC_API_KEY:
        return _call_anthropic_api(prompt)
    else:
        return _call_claude_cli(prompt)


def _build_prompt(resume_text: str, jd_text: str, score_result: dict) -> str:
    missing = ", ".join(score_result.get("missing_keywords", [])[:20])
    return f"""You are a professional resume editor. Your job is to lightly edit the existing resume so it better matches the job description — NOT rewrite it from scratch, and NOT make it sound AI-generated.

=== WHAT YOU MUST NEVER DO ===
- Never use these AI buzzwords: leveraged, spearheaded, utilized, passionate, dynamic, synergize, holistic, robust, cutting-edge, state-of-the-art, best-in-class, innovative, transformative, orchestrated, pioneered, catalyzed, streamlined (unless already in original)
- Never fabricate metrics, credentials, or experience not in the original resume
- Never start every bullet with the same verb — vary them
- Never use passive voice ("was responsible for")
- Never add fluffy filler phrases ("demonstrated ability to", "proven track record of")
- Never use first person ("I built", "I managed") — omit the subject entirely

=== ATS FORMAT RULES (follow exactly) ===
Line 1: Full name only
Line 2: Phone | Email | City, State | LinkedIn URL (all on one line, pipe-separated)
Blank line
SUMMARY (optional, 2 sentences max, factual only)
Blank line
EXPERIENCE
Company Name | Job Title | City, State
Month Year – Month Year  (or "Present")
• Bullet: action verb + what you did + result/scope if it exists in original
• Keep bullets to 1 line when possible
Blank line between each job
EDUCATION
School Name | Degree, Field | Year – Year
GPA: X.X (only if above 3.0)
SKILLS
Category: skill1, skill2, skill3
PROJECTS (if present)
Project Name | Date
• What it does, what tech was used

Rules:
- Section headers ALL CAPS, no decorations
- Bullets use • character only
- No tables, no columns, no special characters except | and •
- Dates: "Jan 2023 – Mar 2025" format
- One blank line between sections, NO blank lines between bullets within a job

=== KEYWORD INTEGRATION ===
Weave in ONLY keywords that genuinely fit the person's actual experience: {missing}
Do not force keywords where they don't belong.

=== YOUR TASK ===
1. Keep the person's own voice — make edits feel natural, not polished-by-AI
2. Tighten wordy bullets to be punchy and specific
3. Add relevant keywords from the JD where they authentically fit
4. Ensure every section follows the ATS format above exactly
5. Summary should reflect the JD role, written in 3rd-person omitted style ("Robotics engineer with 3 years..." not "I am a robotics engineer...")

JOB DESCRIPTION:
{jd_text}

ORIGINAL RESUME:
{resume_text}

Respond ONLY with a valid JSON object (no markdown, no code fences, no extra text before or after):
{{
  "optimized_resume": "<full resume text, use actual newline characters>",
  "changes_made": [
    "Specific change 1 — e.g. Added 'ROS2' to Skills under Robotics",
    "Specific change 2 — e.g. Tightened bullet at Job X to include scope"
  ]
}}"""


def _call_claude_cli(prompt: str) -> dict:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        output = result.stdout.strip()
        return _parse_claude_response(output)
    except subprocess.TimeoutExpired:
        return _fallback_response("Claude CLI timed out after 120s. Try a shorter resume or increase _TIMEOUT.")
    except FileNotFoundError:
        return _fallback_response("Claude CLI not found. Ensure `claude` is installed and in PATH.")
    except Exception as e:
        return _fallback_response(f"Claude CLI error: {str(e)}")


def _call_anthropic_api(prompt: str) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=_ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        output = message.content[0].text.strip()
        return _parse_claude_response(output)
    except Exception as e:
        return _fallback_response(f"Anthropic API error: {str(e)}")


def _parse_claude_response(output: str) -> dict:
    # Strip markdown code fences if present
    output = output.strip()
    if output.startswith("```"):
        lines = output.split("\n")
        # Remove first line (```json or ```) and last line (```)
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        output = "\n".join(inner).strip()

    # Try direct JSON parse first
    try:
        data = json.loads(output)
        return {
            "optimized_text": data.get("optimized_resume", "").strip(),
            "changes_made": data.get("changes_made", []),
        }
    except json.JSONDecodeError:
        pass

    # Fallback: extract JSON object with regex (handles extra text around JSON)
    import re
    match = re.search(r'\{.*\}', output, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return {
                "optimized_text": data.get("optimized_resume", "").strip(),
                "changes_made": data.get("changes_made", []),
            }
        except json.JSONDecodeError:
            pass

    # Last resort: treat entire output as the resume text
    return {
        "optimized_text": output,
        "changes_made": ["Resume updated to match job description"],
    }


def _fallback_response(error_msg: str) -> dict:
    return {
        "optimized_text": "",
        "changes_made": [f"Error: {error_msg}"],
    }
