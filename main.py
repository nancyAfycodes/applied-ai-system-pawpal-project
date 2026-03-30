from datetime import date
from tabulate import tabulate
from pawpal_system import Owner, Dog, Cat, Task, Scheduler, CATEGORY_EMOJI, PRIORITY_BADGE

# ---------------------------------------------------------------------------
# 1. Create Owner
# ---------------------------------------------------------------------------
owner = Owner(name="Alex")

owner.availability = {
    "Sunday": {
        "early_morning": 60,
        "lunch_break":   60,
        "afternoon":     45,
        "evening":       60,
    },
    "Monday": {
        "early_morning": 30,
        "lunch_break":   60,
        "afternoon":     45,
        "evening":       60,
    },
    "Tuesday": {
        "early_morning": 20,
        "lunch_break":   30,
        "afternoon":     60,
        "evening":       90,
    },
}

owner.preferred_slots = {
    "Sunday":  "early_morning",
    "Monday":  "early_morning",
    "Tuesday": "evening",
}

# ---------------------------------------------------------------------------
# 2. Create Pets
# ---------------------------------------------------------------------------
buddy = Dog(
    name="Buddy",
    age=3,
    owner=owner,
    breed="Golden Retriever",
    birthday=date(2022, 4, 10),
    vet_info="Dr. Paws Clinic — (626) 555-0192",
    health_notes="No known conditions. Daily fish oil supplement.",
)

luna = Cat(
    name="Luna",
    age=5,
    owner=owner,
    breed="Domestic Shorthair",
    birthday=date(2020, 8, 22),
    vet_info="Dr. Paws Clinic — (626) 555-0192",
    health_notes="Sensitive stomach. Grain-free diet recommended.",
)

# ---------------------------------------------------------------------------
# 3. Add Tasks to Pets
# ---------------------------------------------------------------------------
buddy.tasks = [
    Task(name="Morning walk",     category="exercise",    duration=30, priority="high",   time_slot="early_morning", frequency="daily"),
    Task(name="Breakfast",        category="eating",      duration=15, priority="high",   time_slot="early_morning", frequency="daily"),
    Task(name="Fish oil vitamin", category="routine_med", duration=5,  priority="medium", time_slot="early_morning", frequency="daily"),
    Task(name="Afternoon walk",   category="exercise",    duration=30, priority="medium", time_slot="afternoon",     frequency="daily"),
    Task(name="Dinner",           category="eating",      duration=15, priority="high",   time_slot="evening",       frequency="daily"),
]

luna.tasks = [
    Task(name="Breakfast",           category="eating",     duration=10, priority="high",   time_slot="early_morning", frequency="daily"),
    Task(name="Litter box cleaning", category="grooming",   duration=10, priority="medium", time_slot="early_morning", frequency="daily"),
    Task(name="Playtime",            category="enrichment", duration=20, priority="medium", time_slot="afternoon",     frequency="daily"),
    Task(name="Dinner",              category="eating",     duration=10, priority="high",   time_slot="evening",       frequency="daily"),
]

# ---------------------------------------------------------------------------
# 4. Helpers
# ---------------------------------------------------------------------------
SLOT_LABELS = {
    "early_morning": "🌅 Early Morning",
    "lunch_break":   "☀️  Lunch Break",
    "afternoon":     "🌤️  Afternoon",
    "evening":       "🌙 Evening",
}

def build_schedule_table(daily: "DailySchedule") -> str:
    rows = []
    for slot, label in SLOT_LABELS.items():
        tasks = daily.time_slots.get(slot, [])
        if tasks:
            for t in tasks:
                emoji = CATEGORY_EMOJI.get(t.category, "📋")
                status = "✅" if t.completed else "⭕"
                rows.append([
                    label,
                    f"{emoji} {t.name}",
                    f"{t.duration} min",
                    PRIORITY_BADGE.get(t.priority, t.priority),
                    status,
                ])
            label = ""  # only show slot label once per group
    return tabulate(
        rows,
        headers=["Time Slot", "Task", "Duration", "Priority", "Status"],
        tablefmt="rounded_outline",
    )

# ---------------------------------------------------------------------------
# 5. Run Scheduler and Print
# ---------------------------------------------------------------------------
today = date.today()
scheduler = Scheduler(owner=owner, pets=[buddy, luna])

print(f"\n  🐾 PawPal+ — Today's Schedule ({today.strftime('%A, %Y-%m-%d')})\n")

for pet in [buddy, luna]:
    scheduler.flagged_tasks = []
    daily = scheduler.generate_daily_schedule_for_pet(pet, today)

    species = "🐶" if isinstance(pet, Dog) else "🐱"
    print(f"{'=' * 60}")
    print(f"  {species} {pet.name} ({pet.__class__.__name__})")
    print(f"{'=' * 60}")
    print(build_schedule_table(daily))
    print(f"\n  Scheduled: {len(daily.tasks)} task(s)")

    if scheduler.flagged_tasks:
        print(f"\n  ⚠️  Flagged (could not be scheduled):")
        flagged_rows = [
            [f"🔴 {t.name}", f"{t.duration} min", PRIORITY_BADGE.get(t.priority, t.priority)]
            for t in scheduler.flagged_tasks
        ]
        print(tabulate(flagged_rows, headers=["Task", "Duration", "Priority"], tablefmt="rounded_outline"))
    print()

# ---------------------------------------------------------------------------
# 6. Conflict Detection
# ---------------------------------------------------------------------------
print(f"{'=' * 60}")
print("  🔍 Conflict Detection")
print(f"{'=' * 60}")
today_name = today.strftime("%A")
for pet in [buddy, luna]:
    conflicts = scheduler.detect_conflicts(pet, today_name)
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        species = "🐶" if isinstance(pet, Dog) else "🐱"
        print(f"  ✅ No conflicts detected for {species} {pet.name}.")
print(f"{'=' * 60}\n")