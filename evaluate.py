"""
evaluate.py — PawPal+ AI Reliability Evaluation Script

Runs a set of structured test scenarios through the full AI pipeline
and summarizes results including confidence scores, conflict detection
accuracy, guardrail triggers, and logging reliability.

Run with: py evaluate.py
"""
from datetime import date
from pawpal_system import Owner, Dog, Cat, Task, Scheduler
from ai_engine import generate_ai_explanation, validate_schedule_safety

# ---------------------------------------------------------------------------
# Scenario builder helpers
# ---------------------------------------------------------------------------
def make_owner(name: str = "Test Owner", availability: dict = None) -> Owner:
    owner = Owner(name=name)
    owner.availability = availability or {
        date.today().strftime("%A"): {
            "early_morning": 60,
            "lunch_break":   60,
            "afternoon":     45,
            "evening":       60,
        }
    }
    owner.preferred_slots = {date.today().strftime("%A"): "early_morning"}
    return owner


def run_scenario(label: str, pet, tasks: list, owner: Owner) -> dict:
    """Run a single evaluation scenario and return results."""
    pet.tasks = tasks
    scheduler = Scheduler(owner=owner, pets=[pet])
    scheduler.flagged_tasks = []
    daily = scheduler.generate_daily_schedule_for_pet(pet, date.today())

    safety = validate_schedule_safety(pet, daily)
    result = generate_ai_explanation(pet, daily, scheduler)

    passed = True
    notes = []

    # Check confidence score was extracted
    if result["confidence"] == 0:
        passed = False
        notes.append("Confidence score not extracted")

    # Check logging occurred
    from pathlib import Path
    import json
    log_path = Path("logs/scheduler_log.json")
    if log_path.exists():
        with open(log_path) as f:
            entries = json.load(f)
        last = entries[-1]
        if last["pet"] != pet.name:
            passed = False
            notes.append("Log entry mismatch")
    else:
        passed = False
        notes.append("Log file not found")

    return {
        "scenario":    label,
        "pet":         f"{pet.name} ({pet.__class__.__name__})",
        "scheduled":   len(daily.tasks),
        "flagged":     len(result["flagged"]),
        "safety":      len(safety),
        "confidence":  result["confidence"],
        "passed":      passed,
        "notes":       notes if notes else ["OK"],
    }


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
def build_scenarios() -> list:
    today = date.today().strftime("%A")
    scenarios = []

    # Scenario 1: Dog — happy path, no conflicts
    owner1 = make_owner("Alex", {today: {"early_morning": 60, "lunch_break": 60, "afternoon": 45, "evening": 60}})
    dog1 = Dog(name="Buddy", age=3, owner=owner1)
    tasks1 = [
        Task("Breakfast",    "eating",    15, "high",   "early_morning", "daily"),
        Task("Morning walk", "exercise",  20, "high",   "early_morning", "daily"),
        Task("Vitamins",     "routine_med", 5, "medium","early_morning", "daily"),
        Task("Dinner",       "eating",    15, "high",   "evening",       "daily"),
    ]
    scenarios.append(("Scenario 1: Dog — happy path", dog1, tasks1, owner1))

    # Scenario 2: Dog — slot conflict
    owner2 = make_owner("Jordan", {today: {"early_morning": 20, "lunch_break": 60, "afternoon": 45, "evening": 60}})
    dog2 = Dog(name="Max", age=5, owner=owner2)
    tasks2 = [
        Task("Breakfast",    "eating",    15, "high", "early_morning", "daily"),
        Task("Morning walk", "exercise",  30, "high", "early_morning", "daily"),
    ]
    scenarios.append(("Scenario 2: Dog — slot conflict", dog2, tasks2, owner2))

    # Scenario 3: Cat — happy path
    owner3 = make_owner("Sam", {today: {"early_morning": 30, "lunch_break": 60, "afternoon": 45, "evening": 60}})
    cat1 = Cat(name="Luna", age=4, owner=owner3)
    tasks3 = [
        Task("Breakfast",          "eating",    10, "high",   "early_morning", "daily"),
        Task("Litter box cleaning","grooming",  10, "medium", "early_morning", "daily"),
        Task("Playtime",           "enrichment",15, "medium", "afternoon",     "daily"),
        Task("Dinner",             "eating",    10, "high",   "evening",       "daily"),
    ]
    scenarios.append(("Scenario 3: Cat — happy path", cat1, tasks3, owner3))

    # Scenario 4: Pet with no tasks — edge case
    owner4 = make_owner("Casey", {today: {"early_morning": 30}})
    dog3 = Dog(name="Rocky", age=2, owner=owner4)
    scenarios.append(("Scenario 4: Dog — no tasks", dog3, [], owner4))

    # Scenario 5: Missing feeding task — guardrail trigger
    owner5 = make_owner("Riley", {today: {"early_morning": 60, "evening": 60}})
    dog4 = Dog(name="Bella", age=6, owner=owner5)
    tasks5 = [
        Task("Morning walk", "exercise", 30, "high",   "early_morning", "daily"),
        Task("Evening walk", "exercise", 30, "medium", "evening",       "daily"),
    ]
    scenarios.append(("Scenario 5: Dog — missing feeding (guardrail)", dog4, tasks5, owner5))

    return scenarios


# ---------------------------------------------------------------------------
# Run evaluation
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 65)
    print("  🐾 PawPal+ AI — Reliability Evaluation")
    print("=" * 65)

    scenarios = build_scenarios()
    results = []

    for label, pet, tasks, owner in scenarios:
        print(f"\n  Running: {label}...")
        result = run_scenario(label, pet, tasks, owner)
        results.append(result)
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {status} | Confidence: {result['confidence']}/5 | "
              f"Scheduled: {result['scheduled']} | Conflicts: {result['flagged']} | "
              f"Safety warnings: {result['safety']}")
        print(f"  Notes: {', '.join(result['notes'])}")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    avg_confidence = sum(r["confidence"] for r in results) / total
    total_conflicts = sum(r["flagged"] for r in results)
    total_safety = sum(r["safety"] for r in results)

    print("\n" + "=" * 65)
    print("  📊 Evaluation Summary")
    print("=" * 65)
    print(f"  Tests passed:        {passed}/{total}")
    print(f"  Avg confidence:      {avg_confidence:.1f}/5")
    print(f"  Conflicts detected:  {total_conflicts}")
    print(f"  Safety warnings:     {total_safety}")
    print(f"  Logging:             {'✅ Active' if passed > 0 else '❌ Check logs/'}")
    print("=" * 65)
    print(f"\n  Overall: {'✅ System reliable' if passed == total else '⚠️ Review failed scenarios'}\n")


if __name__ == "__main__":
    main()
