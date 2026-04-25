# Model Card — PawPal+ AI

> A standardized documentation file describing the AI system built for PawPal+, covering model details, intended use, limitations, bias considerations, and testing results.

---

## 1. Model Overview

| Field | Details |
|-------|---------|
| **Project Name** | PawPal+ AI |
| **Base Project** | PawPal+ Pet Care Scheduler (Modules 1–3) |
| **Model Used** | Anthropic Claude Sonnet (claude-sonnet-4-5) |
| **Interface** | Streamlit Web App |
| **AI Features** | RAG, Agentic Workflow, Few-Shot Specialization |
| **Current Mode** | Mock mode (MOCK_MODE = True) — real API requires credits |
| **Version** | Module 4 — AI-Integrated Extension |

---

## 2. Intended Use

### Primary Use Case
PawPal+ AI is designed to help busy pet owners plan and organize daily care routines for their dogs and cats. It generates a prioritized daily schedule based on owner availability, retrieves relevant pet care guidelines, and uses AI to explain scheduling decisions in a friendly, actionable way.

### Intended Users
- Pet owners with dogs or cats who want structured daily care routines
- Pet owners with limited time who need help prioritizing tasks
- Students and developers learning AI-integrated application design

### Out-of-Scope Uses
- Veterinary diagnosis or medical advice — PawPal+ is a scheduling tool only
- Care planning for exotic, wild, or prohibited animals
- Use as a substitute for professional veterinary consultation

---

## 3. AI System Details

### Retrieval-Augmented Generation (RAG)
The system retrieves up to three knowledge sources before generating any AI response:
- **Base guidelines** — general care guidelines per pet type (dog or cat)
- **Breed-specific guidelines** — targeted advice for specific breeds (Golden Retriever, Bichon Frise, Pomeranian, Persian)
- **Seasonal guidelines** — care adjustments based on the current season (spring, summer, fall, winter)

All sources are stored as markdown files in the `guidelines/` folder and merged into a single context block sent to the AI.

### Agentic Workflow
When real API credits are available, the system runs a four-step reasoning chain:
1. **Analyze** — identify schedule gaps against retrieved guidelines
2. **Propose** — suggest specific task adjustments
3. **Validate** — check proposals against owner availability and detected conflicts
4. **Explain** — produce a final friendly summary with confidence score

Each step is logged independently in `logs/pawpal.log` and `logs/scheduler_log.json`.

### Few-Shot Specialization
The AI uses a specialized system prompt with three curated input/output examples that constrain its tone to fun and playful — consistent use of emojis, pet-specific vocabulary, and a "Pawsome tip" at the end of every response. This measurably differs from a baseline prompt with no examples.

---

## 4. Guardrails and Safety

| Guardrail | What It Checks |
|-----------|---------------|
| Missing feeding tasks | Warns if no eating category task is scheduled |
| Unscheduled medications | Warns if a medication task was not assigned to a slot |
| Slot overload | Warns if a single time slot exceeds 120 minutes of tasks |
| Conflict detection | Flags if total task duration in a slot exceeds available time |
| API error handling | Catches `anthropic.APIError` and returns a safe fallback message |
| Mock mode fallback | Returns a structured mock response when API credits are unavailable |

**Note:** There are currently no restrictions on pet type input. A future guardrail should validate pet type against an approved list before generating schedules or AI analysis.

---

## 5. Bias and Limitations

### Known Biases
- **Schedule bias** — the system assumes a standard 9-to-5 work schedule. Shift workers or people with non-traditional hours are not well supported.
- **User-controlled guidelines** — the owner decides task priorities, which may reflect personal preference rather than evidence-based pet care recommendations.
- **Breed coverage** — only four breeds currently have specific guidelines. All other breeds fall back to general pet type guidelines.

### Known Limitations
- Currently supports dogs and cats only — other pet types are not supported
- Mock mode produces static responses that do not dynamically adapt to every unique schedule scenario
- Confidence scores in mock mode are fixed at 4/5 and do not reflect actual schedule quality
- No time tracking — the system does not compare allocated versus actual time spent on tasks
- No multi-pet weekly view — each session handles one pet at a time

---

## 6. AI Collaboration

### How AI Was Used
Claude was used throughout all phases of the project — from initial UML design brainstorming to code generation, debugging, and refactoring. The approach was always to stay in control of direction while using AI to accelerate implementation.

### Helpful Suggestion
The most valuable suggestion came during the initial design phase. The original plan was two classes (`User` and `Pet`). Claude suggested a more modular structure with dedicated classes for `Task`, `DailySchedule`, `WeeklySchedule`, and `Scheduler`. This decision shaped the entire project and made both phases significantly easier to build and extend.

### Flawed Suggestion
The most consistent challenge was generated code with cognitive complexity scores exceeding the linter's allowed limit of 15. Methods like `assign_time_slots()` and `_mock_response()` required multiple rounds of refactoring. This reinforced that AI-generated code should always be reviewed against project standards before being committed.

---

## 7. Testing Results

### Automated Test Suite
**Result: 7/7 passed**

| Test | Status |
|------|--------|
| Task marked complete (once) | ✅ |
| Task addition increases pet task count | ✅ |
| Daily recurring task generates next occurrence | ✅ |
| Weekly recurring task generates next occurrence | ✅ |
| Conflict detection catches slot overflow | ✅ |
| Sort by time returns natural day order | ✅ |
| Pet with no tasks produces no errors | ✅ |

### Evaluation Script Results
**Result: 5/5 scenarios passed**

| Scenario | Confidence | Conflicts | Safety Warnings |
|----------|-----------|-----------|-----------------|
| Dog — happy path | 4/5 | 0 | 0 |
| Dog — slot conflict | 4/5 | 1 | 0 |
| Cat — happy path | 4/5 | 0 | 0 |
| Dog — no tasks | 4/5 | 0 | 1 |
| Dog — missing feeding | 4/5 | 0 | 1 |

**Average confidence: 4.0/5 | Logging: ✅ Active | Overall: ✅ System reliable**

---

## 8. Ethical Considerations

- PawPal+ is a scheduling and planning tool — it is **not** a substitute for professional veterinary advice
- Users should consult a licensed veterinarian for any health-related decisions
- The system logs all AI decisions — users should be aware that schedule data is stored locally in `logs/`
- Care guidelines are based on general best practices and may not apply to every individual animal's specific health needs
- The system should not be used to plan care for exotic, wild, or legally prohibited animals

---

## 9. Future Improvements

- Add time tracking — compare allocated vs actual time spent per task and generate weekly adjustment graphs
- Validate pet type against an approved list before generating schedules
- Expand breed coverage to include more dog and cat breeds
- Support non-standard work schedules (shift work, remote work, flexible hours)
- Enable multi-pet weekly view in a single session
- Activate real API integration once credits are available (`MOCK_MODE = False`)
