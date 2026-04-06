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
    return f"""You are an expert resume writer and ATS optimization specialist.

TASK: Rewrite the resume below to better match the job description. Focus on:
1. Naturally incorporating these missing keywords: {missing}
2. Strengthening bullet points with quantifiable achievements and action verbs
3. Rewriting the summary/objective to align with the role
4. Keeping ALL original experience, education, and facts — do not fabricate anything
5. Maintaining a clean, ATS-friendly plain-text format

JOB DESCRIPTION:
{jd_text}

ORIGINAL RESUME:
{resume_text}

Respond ONLY with a JSON object in this exact format (no markdown, no extra text):
{{
  "optimized_resume": "<full optimized resume text with \\n for newlines>",
  "changes_made": [
    "Brief description of change 1",
    "Brief description of change 2"
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
    if output.startswith("```"):
        lines = output.split("\n")
        output = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        data = json.loads(output)
        return {
            "optimized_text": data.get("optimized_resume", ""),
            "changes_made": data.get("changes_made", []),
        }
    except json.JSONDecodeError:
        # Claude returned plain text instead of JSON — treat the whole output as the resume
        return {
            "optimized_text": output,
            "changes_made": ["Resume rewritten to better match job description"],
        }


def _fallback_response(error_msg: str) -> dict:
    return {
        "optimized_text": "",
        "changes_made": [f"Error: {error_msg}"],
    }
