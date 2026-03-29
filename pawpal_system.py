from datetime import date
from typing import Optional


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
class Owner:
    """Represents a pet owner with availability windows and preferences."""

    def __init__(self, name: str):
        self.name = name

        # availability: { "Monday": { "early_morning": 30, "lunch_break": 60, ... }, ... }
        self.availability: dict[str, dict[str, int]] = {}

        # preferred_slots: { "Monday": "early_morning", "Tuesday": "lunch_break", ... }
        self.preferred_slots: dict[str, str] = {}

    def __repr__(self):
        return f"Owner(name={self.name!r})"


# ---------------------------------------------------------------------------
# Pet (abstract base)
# ---------------------------------------------------------------------------
class Pet:
    """Base class for all pets. Holds attributes common to every pet type."""

    def __init__(self, name: str, age: int, owner: Owner):
        self.name = name
        self.age = age
        self.owner = owner
        self.tasks: list["Task"] = []

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, age={self.age})"


# ---------------------------------------------------------------------------
# Dog (inherits Pet)
# ---------------------------------------------------------------------------
class Dog(Pet):
    """A dog with breed-specific attributes. Inherits all Pet attributes."""

    def __init__(
        self,
        name: str,
        age: int,
        owner: Owner,
        breed: str = "",
        birthday: Optional[date] = None,
        vet_info: str = "",
        health_notes: str = "",  # placeholder for future Health class
    ):
        super().__init__(name, age, owner)
        self.breed = breed
        self.birthday = birthday
        self.vet_info = vet_info
        self.health_notes = health_notes  # «future: Health»


# ---------------------------------------------------------------------------
# Cat (inherits Pet)
# ---------------------------------------------------------------------------
class Cat(Pet):
    """A cat with breed-specific attributes. Inherits all Pet attributes."""

    def __init__(
        self,
        name: str,
        age: int,
        owner: Owner,
        breed: str = "",
        birthday: Optional[date] = None,
        vet_info: str = "",
        health_notes: str = "",  # placeholder for future Health class
    ):
        super().__init__(name, age, owner)
        self.breed = breed
        self.birthday = birthday
        self.vet_info = vet_info
        self.health_notes = health_notes  # «future: Health»


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------
VALID_CATEGORIES = {
    "eating",
    "exercise",
    "grooming",
    "enrichment",
    "routine_med",
    "conditional_med",
}

VALID_PRIORITIES = {"high", "medium", "low"}

VALID_TIME_SLOTS = {
    "early_morning",
    "lunch_break",
    "afternoon",
    "evening",
    "flexible",
}

VALID_FREQUENCIES = {"once", "twice", "weekly"}


class Task:
    """Represents a single care task assigned to a pet."""

    def __init__(
        self,
        name: str,
        category: str,
        duration: int,
        priority: str = "medium",
        time_slot: str = "flexible",
        frequency: str = "once",
        is_conditional: bool = False,
    ):
        self.name = name
        self.category = category        # eating | exercise | grooming | enrichment | routine_med | conditional_med
        self.duration = duration        # minutes
        self.priority = priority        # high | medium | low
        self.time_slot = time_slot      # early_morning | lunch_break | afternoon | evening | flexible
        self.frequency = frequency      # once | twice | weekly
        self.completed = False
        self.is_conditional = is_conditional  # True = only active when pet is sick

    def __repr__(self):
        return (
            f"Task(name={self.name!r}, priority={self.priority!r}, "
            f"duration={self.duration}min, completed={self.completed})"
        )


# ---------------------------------------------------------------------------
# DailySchedule
# ---------------------------------------------------------------------------
class DailySchedule:
    """Holds the task plan for a single day."""

    def __init__(self, schedule_date: date):
        self.date = schedule_date                   # day_of_week derived via .strftime("%A")
        self.tasks: list[Task] = []
        self.time_slots: dict[str, list[Task]] = {  # slot → tasks assigned to it
            "early_morning": [],
            "lunch_break": [],
            "afternoon": [],
            "evening": [],
        }
        self.completed_tasks: list[Task] = []       # powers the check-off list

    @property
    def day_of_week(self) -> str:
        return self.date.strftime("%A")

    def __repr__(self):
        return f"DailySchedule(date={self.date}, tasks={len(self.tasks)})"


# ---------------------------------------------------------------------------
# WeeklySchedule
# ---------------------------------------------------------------------------
class WeeklySchedule:
    """A 7-day schedule composed of DailySchedule objects."""

    def __init__(self, owner: Owner, pet: Pet, week_start_date: date):
        self.owner = owner
        self.pet = pet
        self.week_start_date = week_start_date
        self.daily_schedules: list[DailySchedule] = []  # populated by Scheduler

    def __repr__(self):
        return (
            f"WeeklySchedule(owner={self.owner.name!r}, "
            f"pet={self.pet.name!r}, week_start={self.week_start_date})"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
class Scheduler:
    """
    The scheduling brain of PawPal+.
    Takes owner availability + pet tasks and produces a prioritized plan.
    """

    def __init__(self, owner: Owner, pets: list[Pet]):
        self.owner = owner
        self.pets = pets
        self.tasks: list[Task] = []          # all tasks across all pets
        self.flagged_tasks: list[Task] = []  # tasks that couldn't be scheduled (conflicts)

        # Collect tasks from all pets on init
        for pet in self.pets:
            self.tasks.extend(pet.tasks)

    # ------------------------------------------------------------------
    # Core scheduling methods
    # ------------------------------------------------------------------

    def generate_daily_schedule(self, schedule_date: date) -> DailySchedule:
        """Produce a DailySchedule for a given date based on owner availability."""
        daily = DailySchedule(schedule_date)
        day_name = schedule_date.strftime("%A")
        availability = self.owner.availability.get(day_name, {})
        preferred = self.owner.preferred_slots.get(day_name)

        prioritized = self.prioritize_tasks()
        assignments = self.assign_time_slots(prioritized, availability, preferred)

        for slot, slot_tasks in assignments.items():
            daily.time_slots[slot].extend(slot_tasks)
            daily.tasks.extend(slot_tasks)

        return daily

    def generate_weekly_schedule(self, week_start: date) -> WeeklySchedule:
        """Produce a WeeklySchedule starting from week_start (typically a Monday)."""
        from datetime import timedelta
        weekly = WeeklySchedule(self.owner, self.pets[0] if self.pets else None, week_start)
        for i in range(7):
            day = week_start + timedelta(days=i)
            weekly.daily_schedules.append(self.generate_daily_schedule(day))
        return weekly

    def prioritize_tasks(self) -> list[Task]:
        """Sort tasks by priority (high → medium → low), then by duration (shorter first)."""
        order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            self.tasks,
            key=lambda t: (order.get(t.priority, 99), t.duration),
        )

    def _find_slot(
        self,
        task: Task,
        candidates: list[str],
        remaining_time: dict[str, int],
        assignments: dict[str, list[Task]],
    ) -> bool:
        """Try to fit a task into the first candidate slot with enough time.
        Returns True if assigned, False if no slot was available."""
        for slot in candidates:
            if slot in remaining_time and remaining_time[slot] >= task.duration:
                assignments[slot].append(task)
                remaining_time[slot] -= task.duration
                return True
        return False

    def assign_time_slots(
        self,
        tasks: list[Task],
        availability: dict[str, int],
        preferred_slot: Optional[str] = None,
    ) -> dict[str, list[Task]]:
        """
        Map tasks to available time slots.
        Preferred slot is filled first; remaining slots filled in order.
        Tasks that don't fit are added to flagged_tasks.
        """
        assignments: dict[str, list[Task]] = {
            s: [] for s in ["early_morning", "lunch_break", "afternoon", "evening"]
        }
        remaining_time = {slot: mins for slot, mins in availability.items()}

        slot_order = list(remaining_time.keys())
        if preferred_slot and preferred_slot in slot_order:
            slot_order.remove(preferred_slot)
            slot_order.insert(0, preferred_slot)

        for task in tasks:
            if task.is_conditional:
                continue
            candidates = [task.time_slot] if task.time_slot != "flexible" else slot_order
            if not self._find_slot(task, candidates, remaining_time, assignments):
                self.flagged_tasks.append(task)

        return assignments

    def flag_conflicts(self) -> list[Task]:
        """Return the list of tasks that could not be scheduled."""
        return self.flagged_tasks

    def explain_plan(self, expanded: bool = False) -> str:
        """
        Return a summary explanation of the scheduling decisions.
        Pass expanded=True for a detailed breakdown (used by st.expander in UI).
        """
        if not expanded:
            flagged = len(self.flagged_tasks)
            scheduled = len(self.tasks) - flagged
            return (
                f"Scheduled {scheduled} task(s) across available time slots. "
                f"{flagged} task(s) flagged due to conflicts."
            )

        lines = ["=== Detailed Schedule Explanation ==="]
        for task in self.tasks:
            if task in self.flagged_tasks:
                lines.append(f"[FLAGGED] {task.name} — could not fit in any available slot.")
            else:
                lines.append(
                    f"[OK] {task.name} — priority: {task.priority}, "
                    f"duration: {task.duration}min, slot: {task.time_slot}."
                )
        return "\n".join(lines)