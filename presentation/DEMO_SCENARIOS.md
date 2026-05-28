# PARCHED — Presentation Demo Scenarios
> Live model: https://jed08-parched.hf.space/

Each scenario below has exact slider configs and talking points.
Run them **in this order** — the story builds on itself.

---

## DEMO 1 — The Collapse (Scenario A)
> **Narrative:** "Let's see what happens with zero regulation."

| Parameter | Value |
|---|---|
| Scenario | **A — Unregulated** |
| Seed | 42 |
| Data Centers | 4 |
| Initial Basin % | 80 |
| Stress α | 4.0 |
| Recharge ML/d | 50 |
| DC Budget ML | 15 (irrelevant here) |

**What to do:**
1. Hit Apply & Reset, then Play
2. Let it run until Basin crosses 40% (around year 5–6)
3. Pause — point out the slope change on the Basin Level chart
4. Hit Step a few times to show the daily freefall

**What to say:**
- "For the first 4 years, basin looks fine — 0.07% decline per year"
- "The moment it crosses 40%, two feedbacks kick in simultaneously"
- "Recharge collapses to 5% efficiency. DCs demand more water because intake is now warmer"
- "Watch the slope — that's the 9.25× acceleration we measured"
- "Basin goes from Stressed to Critical in months, not years"

**Key numbers to point at:**
- BASIN card turning orange → yellow → red
- Net ML/day going increasingly negative (bottom of Aquifer Gauge)
- Farm Yield Loss starting to tick up
- Complaints spiking

---

## DEMO 2 — Reactive Policy (Scenario B)
> **Narrative:** "What if we had a regulator — but a slow one?"

| Parameter | Value |
|---|---|
| Scenario | **B — Reactive** |
| Seed | **42** (same seed as Demo 1!) |
| Data Centers | 4 |
| Initial Basin % | 80 |
| Stress α | 4.0 |
| Recharge ML/d | 50 |

**What to do:**
1. Apply & Reset, then Play
2. Let it run to completion
3. Point at the DC Capacity chart — the regulator cap fires eventually

**What to say:**
- "Same seed, same random events — only the policy changes"
- "The regulator only activates at 30% basin — which is AFTER the tipping point at 40%"
- "You can see the cap fires… but the basin is already in freefall"
- "Outcome: collapse still happens, just a few weeks later"
- "This is our H3 finding: reactive policy at conventional thresholds is structurally identical to no policy"

**Key numbers to point at:**
- Compare Basin Level curve with Demo 1 — nearly identical
- "Active cap" indicator in Regulator row at bottom left (appears briefly before collapse)

---

## DEMO 3 — Proactive Cap (Scenario C)
> **Narrative:** "What actually works."

| Parameter | Value |
|---|---|
| Scenario | **C — Proactive** |
| Seed | **42** (same seed!) |
| Data Centers | 4 |
| Initial Basin % | 80 |
| Stress α | 4.0 |
| Recharge ML/d | 50 |
| **DC Budget ML** | **15** |

**What to do:**
1. Apply & Reset, then Play
2. Let it run the full 10 years
3. Point at the DC Capacity chart — flat ceiling at 15 ML/day

**What to say:**
- "Same seed again. Only difference: a hard daily cap of 15 ML on total DC water use, from day 1"
- "DC expansion is blocked the moment it would breach the ceiling"
- "Farms stay healthy — they're no longer being starved by DC expansion"
- "Basin holds above 40% for the entire 10-year window"
- "This is the +65% delay finding — and in this run, no collapse at all"

**Key numbers to point at:**
- DC Capacity chart flattening at the yellow dashed line (15 ML)
- Farm Health bars staying green the whole run
- Basin % staying in the green/stable range

---

## DEMO 4 — The Stress Test (Scenario A, High α)
> **Narrative:** "What happens in a hotter climate?"

| Parameter | Value |
|---|---|
| Scenario | **A — Unregulated** |
| Seed | 42 |
| Data Centers | 4 |
| Initial Basin % | 80 |
| **Stress α** | **8.0** ← change this |
| Recharge ML/d | 50 |

**What to do:**
1. Apply & Reset, then Play
2. Compare the Basin Level curve to Demo 1

**What to say:**
- "α controls how much extra water DCs need when the basin is already low — warm intake water means worse cooling efficiency"
- "At α=8 (vs default 4), once basin crosses 40% the feedback is twice as strong"
- "Collapse happens 1–2 years earlier"
- "This models what happens when you layer climate stress on top of AI growth — risks compound, they don't just add"

---

## DEMO 5 — Already Stressed Basin (Scenario A, Low Start)
> **Narrative:** "What if the aquifer is already depleted before the data centers arrive?"

| Parameter | Value |
|---|---|
| Scenario | **A — Unregulated** |
| Seed | 42 |
| Data Centers | 4 |
| **Initial Basin %** | **40** ← change this |
| Stress α | 4.0 |
| Recharge ML/d | 50 |

**What to do:**
1. Apply & Reset, then Play
2. Watch — basin starts right at the tipping point

**What to say:**
- "Many real basins are already over-allocated before a hyperscaler even breaks ground"
- "Starting at 40% means we're already AT the stress threshold on day 1"
- "Collapse is nearly immediate — the model never even enters a 'stable' phase"
- "This is why basin baseline assessment before permitting matters"

---

## DEMO 6 — Staggered Entry (Scenario D)
> **Narrative:** "Does spacing out the data centers buy us safety?"

| Parameter | Value |
|---|---|
| Scenario | **D — Staggered** |
| Seed | 42 |
| Data Centers | 4 |
| Initial Basin % | 80 |
| Stress α | 4.0 |
| Recharge ML/d | 50 |

**What to do:**
1. Apply & Reset, then Play
2. Watch DC Capacity chart — DCs come online in steps at year 0, 2, 4

**What to say:**
- "DCs enter the basin one cluster at a time instead of all at once"
- "Demand grows more gradually — the basin lasts about 1–1.5 years longer"
- "But: all 4 DCs still eventually run at full capacity"
- "The endpoint is the same — collapse still happens"
- "Staggering entry buys time, not safety"

---

## Recommended Presentation Order

```
Demo 1 (A, default)   →  establish the problem / show the collapse
Demo 2 (B, same seed) →  show why reactive policy fails
Demo 3 (C, same seed) →  show the only design that works
Demo 4 (A, high α)    →  show climate compounding risk
Demo 5 (A, 40% start) →  show real-world baseline context
Demo 6 (D, staggered) →  address "can't we just space them out?"
```

Using the **same seed (42) for Demos 1–3** is the key rhetorical move — it proves the policy is the variable, not luck.

---

## Quick Reference Card

| Scenario | Collapse? | When | Best for showing |
|---|---|---|---|
| A default | ✅ Yes | ~6 yr | The core problem |
| B reactive | ✅ Yes | ~6.1 yr | Policy failure |
| C proactive | ❌ No (10yr window) | Never | The solution |
| D staggered | ✅ Yes | ~7.5 yr | False hope |
| A α=8 | ✅ Yes | ~4 yr | Climate risk |
| A basin=40% | ✅ Yes | ~1 yr | Pre-stressed basin |
