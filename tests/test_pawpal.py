import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Dog, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures — reusable test setup
# ---------------------------------------------------------------------------
@pytest.fixture
def owner():
    return Owner(name="Test Owner")


@pytest.fixture
def dog(owner):
    return Dog(name="Buddy", age=3, owner=owner, breed="Golden Retriever")


@pytest.fixture
def sample_task():
    return Task(
        name="Morning walk",
        category="exercise",
        duration=30,
        priority="high",
        time_slot="early_morning",
        frequency="once",
    )


@pytest.fixture
def daily_task():
    return Task(
        name="Breakfast",
        category="eating",
        duration=10,
        priority="high",
        time_slot="early_morning",
        frequency="daily",
        due_date=date.today(),
    )


@pytest.fixture
def weekly_task():
    return Task(
        name="Grooming",
        category="grooming",
        duration=20,
        priority="medium",
        time_slot="afternoon",
        frequency="weekly",
        due_date=date.today(),
    )


# ---------------------------------------------------------------------------
# Test 1: Task Completion — once
# Verify that mark_complete() changes status and returns None for a one-off task
# ---------------------------------------------------------------------------
def test_mark_complete_once(sample_task):
    assert sample_task.completed is False
    result = sample_task.mark_complete()
    assert sample_task.completed is True
    assert result is None


# ---------------------------------------------------------------------------
# Test 2: Task Addition
# Verify that adding a task to a Pet increases that pet's task count
# ---------------------------------------------------------------------------
def test_add_task_increases_count(dog, sample_task):
    initial_count = len(dog.tasks)
    dog.tasks.append(sample_task)
    assert len(dog.tasks) == initial_count + 1


# ---------------------------------------------------------------------------
# Test 3: Recurring task — daily
# Verify that mark_complete() returns a new Task due tomorrow
# ---------------------------------------------------------------------------
def test_mark_complete_daily(daily_task):
    next_task = daily_task.mark_complete()
    assert daily_task.completed is True
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.completed is False


# ---------------------------------------------------------------------------
# Test 4: Recurring task — weekly
# Verify that mark_complete() returns a new Task due in 7 days
# ---------------------------------------------------------------------------
def test_mark_complete_weekly(weekly_task):
    next_task = weekly_task.mark_complete()
    assert weekly_task.completed is True
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)
    assert next_task.completed is False


# ---------------------------------------------------------------------------
# Test 5: Conflict detection
# Verify that detect_conflicts() catches slot overflow and returns a warning
# ---------------------------------------------------------------------------
def test_detect_conflicts(owner, dog):
    owner.availability = {
        "Monday": {"early_morning": 20}
    }
    dog.tasks = [
        Task(name="Morning walk", category="exercise", duration=20,
             priority="high", time_slot="early_morning", frequency="once"),
        Task(name="Breakfast", category="eating", duration=15,
             priority="high", time_slot="early_morning", frequency="once"),
    ]
    scheduler = Scheduler(owner=owner, pets=[dog])
    warnings = scheduler.detect_conflicts(dog, "Monday")
    assert len(warnings) == 1
    assert "early_morning" in warnings[0]


# ---------------------------------------------------------------------------
# Test 6: Sorting correctness
# Verify tasks are returned in natural day order
# ---------------------------------------------------------------------------
def test_sort_by_time(owner, dog):
    dog.tasks = [
        Task(name="Dinner",      category="eating",     duration=15,
             priority="high",   time_slot="evening",       frequency="once"),
        Task(name="Playtime",    category="enrichment", duration=20,
             priority="medium", time_slot="afternoon",     frequency="once"),
        Task(name="Breakfast",   category="eating",     duration=10,
             priority="high",   time_slot="early_morning", frequency="once"),
        Task(name="Lunch snack", category="eating",     duration=10,
             priority="medium", time_slot="lunch_break",   frequency="once"),
    ]
    scheduler = Scheduler(owner=owner, pets=[dog])
    sorted_tasks = scheduler.sort_by_time(dog.tasks)
    slots = [t.time_slot for t in sorted_tasks]
    assert slots == ["early_morning", "lunch_break", "afternoon", "evening"]


# ---------------------------------------------------------------------------
# Test 7: Edge case — pet with no tasks
# Verify that scheduling a pet with no tasks produces no conflicts or errors
# ---------------------------------------------------------------------------
def test_pet_with_no_tasks(owner, dog):
    owner.availability = {"Monday": {"early_morning": 30}}
    dog.tasks = []
    scheduler = Scheduler(owner=owner, pets=[dog])
    warnings = scheduler.detect_conflicts(dog, "Monday")
    assert warnings == []
    daily = scheduler.generate_daily_schedule_for_pet(dog, date.today())
    assert daily.tasks == []