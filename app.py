import streamlit as st
from pawpal_system import Owner, Dog, Cat, Task, Scheduler, CATEGORY_EMOJI, PRIORITY_BADGE
from datetime import date

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pets" not in st.session_state:
    st.session_state.pets = []

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Section 1: Owner + Pet Info
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Info")

owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat"])

st.markdown("#### Owner Availability (minutes per slot)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    early_morning = st.number_input("Early morning", min_value=0, max_value=120, value=30)
with col2:
    lunch_break = st.number_input("Lunch break", min_value=0, max_value=120, value=60)
with col3:
    afternoon = st.number_input("Afternoon", min_value=0, max_value=120, value=45)
with col4:
    evening = st.number_input("Evening", min_value=0, max_value=120, value=60)

preferred_slot = st.selectbox(
    "Preferred time slot for today",
    ["early_morning", "lunch_break", "afternoon", "evening"]
)

if st.button("Save owner & pet"):
    # Create Owner
    owner = Owner(name=owner_name)
    today_name = date.today().strftime("%A")
    owner.availability = {
        today_name: {
            "early_morning": early_morning,
            "lunch_break":   lunch_break,
            "afternoon":     afternoon,
            "evening":       evening,
        }
    }
    owner.preferred_slots = {today_name: preferred_slot}
    st.session_state.owner = owner

    # Create Pet
    if species == "dog":
        pet = Dog(name=pet_name, age=0, owner=owner)
    else:
        pet = Cat(name=pet_name, age=0, owner=owner)

    st.session_state.pets = [pet]
    st.session_state.tasks = []
    st.success(f"Saved! Owner: {owner_name} | Pet: {pet_name} ({species})")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add Tasks
# ---------------------------------------------------------------------------
st.subheader("Tasks")
st.caption("Add tasks for your pet. These will feed into the scheduler.")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    category = st.selectbox("Category", ["eating", "exercise", "grooming", "enrichment", "routine_med", "conditional_med"])
with col4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col5:
    time_slot = st.selectbox(
        "Time slot",
        ["early_morning", "lunch_break", "afternoon", "evening", "flexible"]
    )

if st.button("Add task"):
    if st.session_state.pets:
        task = Task(
            name=task_title,
            category=category,
            duration=int(duration),
            priority=priority,
            time_slot=time_slot,
            frequency="once",
        )
        st.session_state.pets[0].tasks.append(task)
        emoji = CATEGORY_EMOJI.get(category, "📋")
        st.session_state.tasks.append({
            "title": f"{emoji} {task_title}",
            "duration (mins)": int(duration),
            "category": category,
            "priority": priority,
            "time slot": time_slot,
        })
        st.success(f"Task '{task_title}' added!")
    else:
        st.warning("Please save an owner and pet first.")

if st.session_state.tasks:
    st.write("Current tasks:")
    for i, task in enumerate(st.session_state.tasks):
        col_task, col_del = st.columns([6, 1])
        with col_task:
            st.write(f"{i}. {task['title']} | {task['duration (mins)']} min | {task['priority']} | {task['time slot']}")
        with col_del:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.tasks.pop(i)
                st.session_state.pets[0].tasks.pop(i)
                st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Generate Schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.owner:
        st.warning("Please save an owner and pet first.")
    elif not st.session_state.pets or not st.session_state.pets[0].tasks:
        st.warning("Please add at least one task before generating a schedule.")
    else:
        owner = st.session_state.owner
        pets = st.session_state.pets
        scheduler = Scheduler(owner=owner, pets=pets)
        today = date.today()
        pet = pets[0]

        # Reset flags and generate
        scheduler.flagged_tasks = []
        daily = scheduler.generate_daily_schedule_for_pet(pet, today)
        st.session_state.scheduler = scheduler

        # Display schedule
        st.markdown(f"### {pet.name}'s Schedule — {daily.day_of_week}, {today}")

        SLOT_LABELS = {
            "early_morning": "🌅 Early Morning",
            "lunch_break":   "☀️ Lunch Break",
            "afternoon":     "🌤️ Afternoon",
            "evening":       "🌙 Evening",
        }

        for slot, label in SLOT_LABELS.items():
            tasks = daily.time_slots.get(slot, [])
            st.markdown(f"**{label}**")
            if tasks:
                for t in tasks:
                    emoji = CATEGORY_EMOJI.get(t.category, "📋")
                    badge = PRIORITY_BADGE.get(t.priority, t.priority)
                    st.checkbox(
                        f"{emoji} {t.name} — {t.duration} min | {badge}",
                        key=f"{slot}_{t.name}"
                    )
            else:
                st.caption("No tasks scheduled.")

        st.divider()

        # Explain plan
        with st.expander("Schedule explanation", expanded=False):
            st.text(scheduler.explain_plan(expanded=True))

        # Flagged tasks
        if scheduler.flagged_tasks:
            st.warning(f"{len(scheduler.flagged_tasks)} task(s) could not be scheduled:")
            for t in scheduler.flagged_tasks:
                st.markdown(f"- **{t.name}** ({t.priority} priority, {t.duration} min)")