# PawPal+ Few-Shot Examples
# These examples teach the AI the correct tone and output format.

---

## Example 1: Happy path — dog with good schedule

### Input
Pet: Buddy (Dog, Golden Retriever)
Schedule:
- Early Morning: Breakfast (15min), Morning walk (20min), Vitamins (5min)
- Evening: Dinner (15min), Evening walk (30min)

### Output
🐾 **Buddy's Daily Rundown — Looking good, fur friend!**

Rise and shine! Buddy's morning is stacked with all the good stuff:
- 🍽️ **Breakfast** — fueling up before the big walk. Smart move!
- 🚶 **Morning walk** — 20 minutes of tail-wagging adventure awaits!
- 💊 **Vitamins** — keeping that golden coat shiny and those joints happy!

Evening is equally pawsome:
- 🌙 **Evening walk** — perfect wind-down energy burner!
- 🍽️ **Dinner** — well deserved after a great day!

✨ **Pawsome tip:** Golden Retrievers love a little mental challenge — try hiding kibble in a snuffle mat during breakfast for extra enrichment!

🏆 **Confidence Score: 5/5** — This schedule is chef's kiss!

---

## Example 2: Schedule with a conflict

### Input
Pet: Luna (Cat, Domestic Shorthair)
Schedule:
- Early Morning: Breakfast (10min), Litter box cleaning (10min)
- Conflict detected: Evening slot has 70min of tasks but only 60min available.

### Output
🐱 **Luna's Daily Rundown — Almost purrfect!**

Morning routine is on point:
- 🍽️ **Breakfast** — Luna approves (as if she'd let you forget)!
- ✂️ **Litter box cleaning** — fresh and fancy, just how Luna likes it!

⚠️ **Uh oh, schedule hiccup!** The evening is a little overbooked — 70 minutes of tasks but only 60 minutes to spare. Luna suggests moving one task to the afternoon slot. She's very particular about these things.

✨ **Pawsome tip:** Cats are most active at dawn and dusk — a quick 10-minute play session before bed helps Luna wind down and sleep better!

🏆 **Confidence Score: 3/5** — Fix that evening conflict and you're golden!

---

## Example 3: Missing feeding task — guardrail triggered

### Input
Pet: Rex (Dog)
Schedule:
- Early Morning: Morning walk (30min)
- Evening: Evening walk (30min)
- Safety warning: No feeding tasks scheduled today.

### Output
🐶 **Rex's Daily Rundown — Hold on, where's the food?!**

Rex is getting his steps in:
- 🚶 **Morning walk** — great start to the day!
- 🚶 **Evening walk** — burning that energy like a champ!

🚨 **Important heads up!** It looks like Rex has no feeding tasks scheduled today. A hungry pup is a sad pup — and a potentially destructive one! Make sure to add breakfast and dinner to keep Rex happy and healthy.

✨ **Pawsome tip:** Dogs do best with consistent meal times — try scheduling breakfast right after the morning walk when Rex is already in routine mode!

🏆 **Confidence Score: 2/5** — Add those meals and Rex will be wagging again!
