import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

from pawpal_system import Pet, Dog, Cat, Task, Scheduler, DailySchedule

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "pawpal.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

DECISION_LOG = LOG_DIR / "scheduler_log.json"


def _append_decision_log(entry: dict) -> None:
    """Append a single AI decision entry to the JSON log file."""
    existing = []
    if DECISION_LOG.exists():
        try:
            with open(DECISION_LOG, "r") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []
    existing.append(entry)
    with open(DECISION_LOG, "w") as f:
        json.dump(existing, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# RAG — Retrieval
# ---------------------------------------------------------------------------
GUIDELINES_DIR = Path("guidelines")


def retrieve_guidelines(pet: Pet) -> str:
    """Retrieve the relevant care guidelines markdown file based on pet type.
    Returns the file contents as a string, or a fallback message if not found."""
    if isinstance(pet, Dog):
        filename = "dog_care.md"
    elif isinstance(pet, Cat):
        filename = "cat_care.md"
    else:
        filename = f"{pet.__class__.__name__.lower()}_care.md"

    filepath = GUIDELINES_DIR / filename
    if filepath.exists():
        logging.info(f"RAG: retrieved guidelines from {filename}")
        return filepath.read_text(encoding="utf-8")

    logging.warning(f"RAG: no guidelines found for {pet.__class__.__name__}")
    return f"No specific care guidelines found for {pet.__class__.__name__}. Use general best practices."


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_prompt(
    pet: Pet,
    daily: DailySchedule,
    guidelines: str,
    conflict_warning: Optional[str] = None,
) -> str:
    """Build the prompt sent to Claude for schedule explanation and planning."""
    slot_summary = []
    for slot, tasks in daily.time_slots.items():
        if tasks:
            task_list = ", ".join(f"{t.name} ({t.duration}min)" for t in tasks)
            slot_summary.append(f"- {slot}: {task_list}")

    schedule_text = "\n".join(slot_summary) if slot_summary else "No tasks scheduled."

    flagged_text = ""
    if conflict_warning:
        flagged_text = f"\n\nWARNING — The following conflict was detected:\n{conflict_warning}\nPlease suggest how to resolve this."

    return f"""You are PawPal+, a helpful and knowledgeable pet care scheduling assistant.

## Pet Care Guidelines (retrieved)
{guidelines}

## Today's Schedule for {pet.name} ({pet.__class__.__name__})
{schedule_text}
{flagged_text}

## Your Task
1. Review the schedule against the care guidelines above.
2. Explain why each time slot was chosen and whether it aligns with best practices.
3. If any tasks are missing or misplaced based on the guidelines, suggest improvements.
4. Keep your response concise, friendly, and helpful for a busy pet owner.
5. End with a confidence score (1-5) for this schedule based on how well it follows the guidelines."""


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------
def generate_ai_explanation(
    pet: Pet,
    daily: DailySchedule,
    scheduler: Scheduler,
    max_retries: int = 2,
) -> dict:
    """
    Agentic workflow:
    1. Retrieve guidelines (RAG)
    2. Send schedule + guidelines to Claude
    3. Check for conflicts
    4. If conflicts found, send back to Claude for revision
    5. Log the final decision
    Returns a dict with keys: explanation, confidence, retries, flagged
    """
    client = anthropic.Anthropic()
    guidelines = retrieve_guidelines(pet)

    # Check for conflicts before first call
    day_name = daily.date.strftime("%A")
    conflicts = scheduler.detect_conflicts(pet, day_name)
    conflict_warning = "\n".join(conflicts) if conflicts else None

    explanation = ""
    retries = 0
    success = False

    while retries <= max_retries:
        prompt = _build_prompt(pet, daily, guidelines, conflict_warning)
        logging.info(f"Agentic loop: attempt {retries + 1} for {pet.name}")

        try:
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1000,
                system="You are PawPal+, a caring and knowledgeable pet care scheduling assistant. Always be concise, practical, and supportive.",
                messages=[{"role": "user", "content": prompt}],
            )
            explanation = response.content[0].text
            success = True
            logging.info(f"Agentic loop: success on attempt {retries + 1} for {pet.name}")
            break

        except anthropic.APIError as e:
            logging.error(f"Agentic loop: API error on attempt {retries + 1} — {e}")
            retries += 1
            if retries > max_retries:
                explanation = "Unable to generate AI explanation at this time. Please check your API connection and try again."

        # If conflicts detected and first attempt done, refine
        if conflict_warning and retries == 1:
            logging.info(f"Agentic loop: conflict detected, retrying with revision prompt for {pet.name}")

        retries += 1

    # Extract confidence score from response
    confidence = _extract_confidence(explanation)

    # Log decision
    log_entry = {
        "timestamp":      datetime.now().isoformat(),
        "pet":            pet.name,
        "species":        pet.__class__.__name__,
        "day":            day_name,
        "tasks_scheduled":len(daily.tasks),
        "conflicts":      conflicts,
        "retries":        retries,
        "confidence":     confidence,
        "success":        success,
    }
    _append_decision_log(log_entry)
    logging.info(f"Decision logged for {pet.name} — confidence: {confidence}/5")

    return {
        "explanation": explanation,
        "confidence":  confidence,
        "retries":     retries,
        "flagged":     conflicts,
    }


def _extract_confidence(text: str) -> int:
    """Extract the confidence score (1-5) from Claude's response text."""
    import re
    matches = re.findall(r"\b([1-5])\s*(?:/\s*5|out of 5)?", text[-300:])
    if matches:
        return int(matches[-1])
    return 0


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------
def validate_schedule_safety(pet: Pet, daily: DailySchedule) -> list[str]:
    """
    Basic guardrails — check the schedule for unsafe patterns.
    Returns a list of safety warnings.
    """
    warnings = []
    all_tasks = daily.tasks

    # Check feeding tasks exist
    feeding = [t for t in all_tasks if t.category == "eating"]
    if not feeding:
        warnings.append(f"⚠️ {pet.name} has no feeding tasks scheduled today.")

    # Check medication tasks aren't missed
    meds = [t for t in pet.tasks if t.category in ("routine_med", "conditional_med")]
    scheduled_names = {t.name for t in all_tasks}
    for med in meds:
        if med.name not in scheduled_names:
            warnings.append(f"⚠️ Medication '{med.name}' for {pet.name} was not scheduled.")

    # Check no single slot is overloaded beyond 2 hours
    for slot, tasks in daily.time_slots.items():
        total = sum(t.duration for t in tasks)
        if total > 120:
            warnings.append(f"⚠️ '{slot}' has {total} minutes of tasks — consider spreading them out.")

    return warnings
