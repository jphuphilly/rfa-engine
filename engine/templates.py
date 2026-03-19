"""
Message templates for the RFA Engine debate loop.
"""

CRITIC_ROUND_1_TEMPLATE = """IDEA TO EVALUATE:

{current_idea}

---

This is Round 1. You are seeing this idea for the first time.
Provide your 2 most important objections with severity tags and
Skepticism Scores."""

CRITIC_ROUND_N_TEMPLATE = """REVISED IDEA (Round {round_number}):

{current_idea}

---

PREVIOUS ROUND CONTEXT:
The Architect made these changes in response to criticism:

{architect_changes}

Your previous objections and scores were:
{previous_objections}

Your Skepticism Scores last round: {previous_scores}

---

Re-evaluate. For each previous objection:
- If genuinely addressed: reduce Skepticism Score (justify the change)
- If cosmetically addressed: maintain or increase score
- If not addressed: maintain score

You may replace resolved objections with NEW ones if the rewrite
introduced new problems. Output exactly 2 objections total.

Concede a FATAL only if Skepticism Score drops by at least 3 points."""

ARCHITECT_TEMPLATE = """CURRENT IDEA VERSION:

{current_idea}

---

ROUND {round_number} CRITIQUES:

FROM THE CUSTOMER:
{customer_critique}

FROM THE HATER:
{hater_critique}

FROM THE BUILDER:
{builder_critique}

FROM THE VC:
{vc_critique}

FROM THE GROWTH OPERATOR:
{growth_critique}

FROM THE INDIE:
{indie_critique}

---

Total objections: 12 (2 per critic × 6 critics)

Produce six outputs:
1. WHAT I CHANGED AND WHY (flag SUBTRACTION vs ADDITION)
2. WHAT I REFUSED TO CHANGE AND WHY
3. TRADEOFFS MADE
4. OBJECTION STATUS (all 12)
5. THE REVISED IDEA
6. NEXT BUILD PROMPT

Remember: PREFER SUBTRACTION OVER ADDITION."""

ASSUMPTION_TEST_TEMPLATE = """FINAL IDEA VERSION (after {total_rounds} rounds):

{final_idea}

---

VERDICT: {verdict}

SURVIVING OBJECTIONS:
{surviving_objections}

---

Produce Critical Assumption Test. Top 2-3 load-bearing assumptions.
Fastest real-world test for each. Every test needs a pass/fail number."""

QUICK_STRIKE_INPUT_TEMPLATE = """IDEA (Quick Strike — 60-second gut check):

{current_idea}

---

Single most important objection. 2-3 sentences max."""

QUICK_STRIKE_SYNTHESIS_TEMPLATE = """IDEA:
{current_idea}

---

SIX CRITIC OBJECTIONS:

CUSTOMER: {customer_objection}
HATER: {hater_objection}
BUILDER: {builder_objection}
VC: {vc_objection}
GROWTH: {growth_objection}
INDIE: {indie_objection}

---

Produce Quick Strike brief: Threat Level, Top 3 Risks, Quick Build Prompt.
Under 300 words."""

QUICK_STRIKE_SUFFIX = """
--- QUICK STRIKE MODE ---

You are in QUICK STRIKE mode. 60-second gut check.

OUTPUT: Exactly 1 objection. Your single most important concern.

Format:
- Severity: [FATAL], [MAJOR], or [MINOR]
- Skepticism Score: (1-10)
- Objection: 2-3 sentences maximum.

Pick the ONE thing that would make you say "stop" or "change direction." """
