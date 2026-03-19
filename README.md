# RFA Engine

**The 5-minute argument you need before every weekend build.**

```
rfa "An app that helps men track daily habits with AI coaching"
```

Six AI personas — each hunting for a different way your idea dies — tear it apart in parallel. An Architect rewrites it. The critics re-evaluate. You get a verdict, the surviving risks, and a paste-ready build prompt.

```
═══════════════════════════════════════════════════
  RFA ENGINE — VERDICT: KILL (No-progress)
═══════════════════════════════════════════════════

  SURVIVING RISKS:
  • Zero defensibility — any incumbent can clone this in a sprint (VC, 9/10)
  • Gendered positioning shrinks audience with no product justification (Hater, 7/10)
  • No acquisition path — "men's self-improvement" space is carpet-bombed (Growth, 6/10)

  NEXT BUILD PROMPT:
  ──────────────────
  Pivot to: SMS accountability check-in service for people doing
  75 Hard. No app. No AI branding. Daily text, structured reply,
  pattern-aware response. Charge $19/month via Stripe on day one.

  ASSUMPTIONS TO TEST:
  1. Will men pay $19/mo for SMS accountability?
     → Stripe link in r/75Hard, 72hrs, pass = 5 purchases
  2. Does 1 SMS/day feel like coaching, not spam?
     → 10 manual recruits, track reply rate past day 5

  Full debate: ./output/20260319_153745.json
  Est. API cost: ~$0.89
═══════════════════════════════════════════════════
```

---

## Install

```bash
git clone https://github.com/rfa-engine/rfa-engine
cd rfa-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

## Quickstart

```bash
# Full RFA (3-5 minutes, 3 rounds)
python rfa.py "your idea here"

# Quick Strike (30 seconds, gut check)
python rfa.py "your idea" --quick

# From a file
python rfa.py --file pitch.md

# Verbose — see the full debate
python rfa.py "your idea" --verbose

# All options
python rfa.py --help
```

---

## The Panel

| # | Persona | Kills ideas that… |
|---|---------|-------------------|
| 1 | **The Customer** | Nobody actually wants |
| 2 | **The Hater** | Already exist or already failed |
| 3 | **The Builder** | Can't actually be built at this scope |
| 4 | **The VC** | Aren't real businesses |
| 5 | **The Growth Operator** | Have no realistic path to users |
| 6 | **The Indie** | Are overbuilt for what they're trying to test |
| 7 | **The Architect** | *(doesn't kill — rebuilds)* |

---

## Three Debate Logs

These three runs show RFA at work on different types of problems: a scope-bloat kill, a form-factor pivot, and a clean pass to BUILD.

---

### Log 1 — Habit Tracker → KILL (No-progress)

**Idea:** "An app that helps men track daily habits with AI coaching"

**Round 1 scores:**

| Critic | Objection 1 | Objection 2 |
|--------|-------------|-------------|
| Customer | [MAJOR:7] Gendering is meaningless | [MAJOR:6] AI coaching feels hollow |
| Hater | [FATAL:9] Habitica + ChatGPT already exist free | [MAJOR:7] Gendered app failure pattern |
| Builder | [MAJOR:6] AI coaching is 8-week iceberg | [MAJOR:5] LLM costs invert unit economics |
| VC | [FATAL:9] Zero defensibility | [FATAL:8] Consumer habit app economics broken |
| Growth | [MAJOR:6] No distribution wedge | [MAJOR:6] No natural growth loop |
| Indie | [FATAL:8] AI coaching is infinite scope trap | [MAJOR:6] "For men" is demographic not problem |

**Architect Round 1 — pivot:**

Killed the native app. Killed "habit tracker" as the category. Killed "AI coaching" as positioning. Killed the generic "for men" framing.

Rebuilt as: SMS-based daily check-in service for people doing 75 Hard. One protocol, structured data, pattern-aware AI operating silently on the backend. $19/month via Stripe. Launch as concierge (founder texts users manually) before writing a line of automation code.

**Round 2 scores after rewrite:**

| Critic | Change | New score |
|--------|--------|-----------|
| Customer | Gendering resolved, coaching concern addressed | [MAJOR:5] [MAJOR:5] |
| Hater | Free alternative FATAL dropped to MAJOR | [MAJOR:6] [MAJOR:7] |
| Builder | AI iceberg resolved by killing AI | [MAJOR:5] [MAJOR:5] |
| VC | Defensibility FATAL **survives** | [FATAL:9] [MAJOR:9] |
| Growth | Distribution improved, loop still weak | [MAJOR:6] [MAJOR:5] |
| Indie | Scope concern drops to MINOR | [MINOR:3] [MAJOR:5] |

**Exit:** VC's defensibility FATAL survived two consecutive rounds → **KILL (No-progress)**

**What this tells you:** The core problem isn't scope or positioning — it's that SMS accountability check-ins have no moat. Any larger player can replicate it in weeks. The idea needs a structural defensibility answer (proprietary data, community flywheel, or radical focus that incumbents won't match) before it's worth building.

---

### Log 2 — BoardOS → PIVOT (Form-factor)

**Idea:** "A platform that helps startup founders run better board meetings — agenda builder, decision tracker, AI-generated board updates, investor portal, and equity cap table viewer all in one."

**Round 1 — top objections:**

- **[FATAL:9] (Hater):** Carta already does the equity/cap table layer. Notion + GPT does the agenda/updates layer. You're building middleware between two incumbents with established relationships, sales teams, and integrations.
- **[FATAL:8] (VC):** Founder-to-board communication is a relationship problem, not a software problem. The CEO who has a bad board relationship won't fix it with a portal. The one who has a good relationship doesn't need one.
- **[MAJOR:7] (Builder):** "Investor portal" sounds like two weeks of work. It's six months — SSO, permission tiers, audit logs, SOC 2 prep, legal review of what investors can and can't see, and every investor has a different preferred format.

**Architect Round 1 — form-factor pivot:**

*Subtraction:* Killed the equity layer (Carta owns this). Killed the investor portal (compliance nightmare). Killed the cap table viewer (commodity, not differentiating). Killed "platform" framing entirely.

*What remained:* The one piece nobody does well — the **72-hour before/after ritual** around a board meeting. Pre-meeting brief (one page, sent 48 hours before), live decision log during the meeting (captures what was actually decided, not just discussed), and the 24-hour post-meeting memo that prevents the "what did we agree to?" confusion two weeks later.

*Revised idea:* A lightweight board meeting ritual tool — three documents, one workflow, $49/month. No portal. No equity. No integrations. Just the before/during/after meeting layer. Sell to founders directly via a cold email sequence ("Your last board meeting probably had 3 follow-up conversations about what was decided. Here's how to stop that.").

**Round 2:** All FATALs resolved. 3 MAJORs remain (growth loop, pricing, and whether founders will pay for "just three docs"). Dynamic stop triggered at round 2 — 70% MINOR after Architect narrows scope further.

**Verdict: PIVOT (Form-factor)**

**Surviving risk:** Pricing at $49/month is above impulse-buy but below budget-line for most founders — will sit in "evaluate later" purgatory. Assumption test: Stripe link on a one-page Carrd site, posted in a founder Slack, 72 hours. Pass = 3 purchases.

---

### Log 3 — RFA on Itself → BUILD (Narrow)

**Idea:** "RFA Engine — an open-source CLI tool that runs structured adversarial AI debates on startup ideas, returning a verdict, surviving risks, and a paste-ready build prompt."

This is RFA running a debate on its own existence. Results below.

**Round 1 — notable objections:**

- **[MAJOR:7] (Hater):** There are already AI brainstorming and feedback tools — ChatGPT, Perplexity, even custom GPTs for startup critique. The "structured debate with personas" framing is clever but the question is whether it produces materially better output than a well-prompted ChatGPT conversation.
- **[MAJOR:6] (VC):** Open-source CLI with no monetization path. Even if it gets GitHub stars, the path from "useful tool" to "business" requires either a hosted version (which the builder explicitly doesn't want to build) or a consulting wedge (which requires the builder's time to scale).
- **[MAJOR:5] (Growth):** CLI tools have a narrow distribution funnel — developers and technical founders. The target user (a solo builder vibe-coding on a weekend) may not have a terminal habit strong enough to reach for a CLI tool before starting to build.

**Architect Round 1:**

Refused to change the CLI format — that's a core constraint, not a weakness. The tool is for people who already live in terminals. That's a filter, not a flaw.

Resolved the Hater objection: the output that separates RFA from a GPT conversation is the **debate log as artifact** — a shareable, publishable record of an idea being systematically attacked and rebuilt. The value isn't just the verdict; it's the content that gets posted on Hacker News, turned into a newsletter issue, or handed to a co-founder as a pre-mortem.

Resolved the Growth objection: distribution is via the README itself. Three complete debate logs as the demo. Post on HN ("I made an AI debate engine — then I made it roast itself"). The repo IS the content.

Resolved the VC objection: this is explicitly not a venture play. Revenue via consulting (manual RFA sessions for founders) and content (debate logs as blog posts). Validated as a genuine service before the CLI is finished.

**Round 2:** All FATALs: 0. MAJORs: 2 (content moat durability and consulting-to-product conversion path). Dynamic stop triggered — 75% MINOR.

**Verdict: BUILD (Narrow)**

**Surviving risks:**
- Content moat durability: debate log format could be replicated by any newsletter writer (Growth, 5/10)
- Consulting path requires founder's time to scale, doesn't automate easily (VC, 5/10)

**Assumption tests:**
1. Will 3 founders pay $200 for a manual RFA session this week? → Post offer in one founder Slack, 48 hours. Pass = 2 responses.
2. Will the HN post get traction? → Submit "Show HN: RFA Engine — adversarial AI debate on any idea," track 24-hour karma. Pass = 50+ points.

---

## Modes

| Mode | Flag | Use when |
|------|------|----------|
| Full RFA | *(default)* | Pre-build checkpoint, 3-5 minutes |
| Quick Strike | `--quick` | Mid-sprint gut check, ~30 seconds |
| Feature | `--mode feature` | Evaluating a specific feature decision |
| Positioning | `--mode positioning` | Testing messaging or audience framing |

## Options

```
rfa "idea" --rounds 5          # More rounds (default: 3)
rfa "idea" --verbose            # Full debate in terminal
rfa "idea" --amp-after 1        # Amplify after round 1 instead of 2
rfa --file pitch.md             # Read from file
rfa --url https://yourapp.com   # Fetch from URL
```

## What it outputs

**Short (default):**
- Verdict: BUILD / PIVOT / KILL with subtype
- Surviving risks: 3-5 bullets with attribution and scores
- Next build prompt: paste-ready, includes "do NOT" constraints
- Assumptions to test: 2-3 with specific pass/fail metrics
- Full debate saved to `./output/{timestamp}.json`
- Estimated API cost

**Verbose (`--verbose`):**
- Everything above, plus every critic's full objection text, the Architect's complete 6-output rewrite, and round-by-round score evolution.

## Exit conditions

| Condition | Trigger | Verdict |
|-----------|---------|---------|
| All resolved | 0 FATAL + 0 MAJOR | BUILD |
| Dynamic stop | ≥70% MINOR, no new FATAL | BUILD or PIVOT |
| No progress | Same FATAL in 2 consecutive rounds | KILL |
| Max rounds | Hit round limit | By final score |

If FATAL objections survive all rounds, the CLI requires you to type `OVERRIDE` to proceed.

## Dependencies

```
anthropic        # Claude API
python-dotenv    # .env loading
httpx            # URL fetching
beautifulsoup4   # HTML extraction
rich             # Terminal formatting
```

## Cost

Each Full RFA run on `claude-opus-4-6` costs approximately **$0.50–1.50** depending on idea complexity and number of rounds. Quick Strike costs approximately **$0.10–0.25**.

## License

MIT

---

*"Did you RFA it?"*
