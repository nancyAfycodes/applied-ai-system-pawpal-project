import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import anthropic

from pawpal_system import Pet, Dog, Cat, Task, Scheduler, DailySchedule

# Set to True to use mock responses instead of real API calls
MOCK_MODE = True

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
# RAG — Retrieval helpers
# ---------------------------------------------------------------------------
GUIDELINES_DIR = Path("guidelines")

SEASONAL_NOTES = {
    "summer": "⚠️ It's summer — ensure walks are scheduled before 8am or after 6pm to avoid heat. Add a midday hydration check.",
    "spring": "🌱 Spring shedding season is active — consider increasing grooming frequency this week.",
    "fall":   "🍂 Fall is a great time for longer walks — cooler temperatures support extended outdoor activity.",
    "winter": "❄️ Winter safety reminder — check paws after outdoor walks for ice or salt irritation.",
}


def _get_current_season() -> str:
    """Return the current season based on the month."""
    month = date.today().month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "fall"
    return "winter"


def _normalize_breed(breed: str) -> str:
    """Normalize breed name to a filename-safe string."""
    return breed.lower().strip().replace(" ", "_").replace("-", "_")


def _build_schedule_summary(daily: DailySchedule) -> str:
    """Build a plain text summary of scheduled tasks per slot."""
    lines = []
    for slot, tasks in daily.time_slots.items():
        if tasks:
            task_list = ", ".join(t.name for t in tasks)
            lines.append(f"- {slot.replace('_', ' ').title()}: {task_list}")
    return "\n".join(lines) if lines else "No tasks scheduled."


def _build_breed_line(pet: Pet) -> str:
    """Return breed source line for the sources section."""
    if hasattr(pet, "breed") and pet.breed:
        return f"- ✅ Breed-specific guidelines ({pet.breed})"
    return "- ℹ️ No breed specified — base guidelines used"


def retrieve_guidelines(pet: Pet) -> str:
    """
    Enhanced RAG retriever — merges up to three sources:
    1. Base pet care guidelines (dog_care.md or cat_care.md)
    2. Breed-specific guidelines (if available)
    3. Seasonal care guidelines (based on current month)
    Returns combined context string with source labels.
    """
    sources = []

    # Source 1 — base pet guidelines
    if isinstance(pet, Dog):
        base_file = "dog_care.md"
    elif isinstance(pet, Cat):
        base_file = "cat_care.md"
    else:
        base_file = f"{pet.__class__.__name__.lower()}_care.md"

    base_path = GUIDELINES_DIR / base_file
    if base_path.exists():
        sources.append(("Base Care Guidelines", base_path.read_text(encoding="utf-8")))
        logging.info(f"RAG: retrieved base guidelines from {base_file}")
    else:
        sources.append(("Base Care Guidelines", f"No specific guidelines found for {pet.__class__.__name__}."))
        logging.warning(f"RAG: no base guidelines found for {pet.__class__.__name__}")

    # Source 2 — breed-specific guidelines
    if hasattr(pet, "breed") and pet.breed:
        breed_file = f"{_normalize_breed(pet.breed)}.md"
        breed_path = GUIDELINES_DIR / "breeds" / breed_file
        if breed_path.exists():
            sources.append(("Breed-Specific Guidelines", breed_path.read_text(encoding="utf-8")))
            logging.info(f"RAG: retrieved breed guidelines from {breed_file}")
        else:
            logging.info(f"RAG: no breed guidelines found for {pet.breed} — skipping")

    # Source 3 — seasonal guidelines
    season = _get_current_season()
    season_path = GUIDELINES_DIR / "seasonal" / f"{season}.md"
    if season_path.exists():
        sources.append(("Seasonal Care Guidelines", season_path.read_text(encoding="utf-8")))
        logging.info(f"RAG: retrieved seasonal guidelines for {season}")
    else:
        logging.warning(f"RAG: no seasonal guidelines found for {season}")

    # Merge all sources
    merged = "\n\n---\n\n".join(
        f"## {label}\n{content}" for label, content in sources
    )
    logging.info(f"RAG: merged {len(sources)} source(s) for {pet.name}")
    return merged


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
# Mock response
# ---------------------------------------------------------------------------
def _mock_response(pet: Pet, daily: DailySchedule, conflicts: list[str]) -> str:
    """Return a realistic mock AI explanation for testing without API credits."""
    season = _get_current_season()
    breed_note = f" ({pet.breed})" if hasattr(pet, "breed") and pet.breed else ""
    schedule_text = _build_schedule_summary(daily)
    seasonal_note = SEASONAL_NOTES.get(season, "")
    breed_line = _build_breed_line(pet)

    conflict_note = ""
    if conflicts:
        conflict_note = f"\n\n⚠️ Conflict detected: {conflicts[0]} I recommend spreading tasks across additional time slots to resolve this."

    pet_type = "dogs" if isinstance(pet, Dog) else "cats"

    return f"""## PawPal+ Schedule Analysis for {pet.name} ({pet.__class__.__name__}{breed_note})

### Schedule Review
{schedule_text}

### Alignment with Care Guidelines
The current schedule covers the essential care needs for {pet.name}. Here's a quick review:

- **Feeding tasks** are correctly placed in the morning and evening slots, which aligns with the twice-daily feeding guideline for adult {pet_type}.
- **Exercise tasks** are well distributed across the day, supporting physical and mental wellbeing.
- **Medication/supplement tasks** are scheduled in the morning, which is the recommended time for consistency and absorption.
{conflict_note}

### Seasonal Consideration ({season.title()})
{seasonal_note}

### Suggestions
- Consider adding an enrichment or playtime task in the afternoon slot if time allows.
- Ensure fresh water is always available alongside feeding tasks.
- Keep task times consistent day-to-day to support {pet.name}'s routine and reduce anxiety.

### Sources Retrieved
- ✅ Base {pet.__class__.__name__} care guidelines
{breed_line}
- ✅ {season.title()} seasonal care guidelines

### Confidence Score
Based on the schedule's alignment with care guidelines: **4/5**

> 🤖 *This is a mock response for testing. Connect your Anthropic API key with credits to enable real AI analysis.*"""


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

    # Use mock response if MOCK_MODE is enabled
    if MOCK_MODE:
        logging.info(f"Mock mode: returning mock response for {pet.name}")
        explanation = _mock_response(pet, daily, conflicts)
        confidence = _extract_confidence(explanation)
        log_entry = {
            "timestamp":       datetime.now().isoformat(),
            "pet":             pet.name,
            "species":         pet.__class__.__name__,
            "day":             daily.date.strftime("%A"),
            "tasks_scheduled": len(daily.tasks),
            "conflicts":       conflicts,
            "retries":         0,
            "confidence":      confidence,
            "success":         True,
            "mock":            True,
        }
        _append_decision_log(log_entry)
        return {
            "explanation": explanation,
            "confidence":  confidence,
            "retries":     0,
            "flagged":     conflicts,
        }

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

        if conflict_warning and retries == 1:
            logging.info(f"Agentic loop: conflict detected, retrying with revision prompt for {pet.name}")

        retries += 1

    confidence = _extract_confidence(explanation)

    log_entry = {
        "timestamp":       datetime.now().isoformat(),
        "pet":             pet.name,
        "species":         pet.__class__.__name__,
        "day":             day_name,
        "tasks_scheduled": len(daily.tasks),
        "conflicts":       conflicts,
        "retries":         retries,
        "confidence":      confidence,
        "success":         success,
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
    matches = re.findall(r"\b([1-5])\s*(?:/\s*5|out of 5)?", text[-300:])
    if matches:
        return int(matches[-1])
    return 0


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------
def validate_schedule_safety(pet: Pet, daily: DailySchedule) -> list[str]:
    """Check the schedule for unsafe patterns and return a list of warnings."""
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