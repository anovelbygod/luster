# Luster

> Find the stage.

**Luster** is an AI-powered Vancouver PM job search agent built by [The Aventurine Tech Hub](https://github.com/anovelbygod).

It runs targeted searches across LinkedIn, Indeed, Glassdoor, and Google Jobs for senior PM roles in Vancouver and Remote Canada — scores each role against a personalised profile, filters out noise, and delivers a curated digest to your inbox. Only new roles you haven't seen before are surfaced each run.

🔗 **Part of the Aventurine suite:** [Arcspect](https://arcspect.netlify.app) · Luster · Clarity

---

## What it does

- Searches 6 targeted queries across Vancouver and Remote Canada
- Scores every role 0–100 across four weighted dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Domain | 30% | FinTech, B2B SaaS, Consumer Mobile fit |
| Role Type | 25% | Seniority and PM scope |
| Compensation | 20% | Against a defined salary floor |
| Remote | 15% | Remote Canada or Vancouver-based |

- Hard rejects: office 3+ days, non-Canada lock, analytics roles, under $100K USD
- Deduplicates across runs — only new roles surface each time
- Sends a designed HTML digest email with Apply / Review / Skip sections

---

## Scoring thresholds

| Score | Action |
|-------|--------|
| 70–100 | ▲ Apply Now |
| 55–69 | ◆ Worth Reviewing |
| 0–54 | ▼ Skipped |

---

## Built with

- **Python** — core agent logic
- **JSearch API** (RapidAPI) — aggregates LinkedIn, Indeed, Glassdoor, Google Jobs
- **Gmail SMTP** — delivers the digest
- **seen_jobs.json** — local deduplication tracker

---

## Setup

\`\`\`bash
git clone https://github.com/anovelbygod/luster.git
cd luster
pip install requests python-dotenv
\`\`\`

Create a \`.env\` file:

\`\`\`
RAPIDAPI_KEY=your-jsearch-key
PERSONAL_EMAIL=your@gmail.com
PERSONAL_EMAIL_PASSWORD=your-gmail-app-password
\`\`\`

Run:

\`\`\`bash
python3 search.py
\`\`\`

---

## File structure

\`\`\`
luster/
  search.py        ← fetches, scores, builds and sends the digest
  score.py         ← scoring engine (domain, role, comp, remote)
  seen_jobs.json   ← auto-generated, tracks previously seen roles
  .env             ← API keys (never committed)
  .gitignore
  README.md
\`\`\`

---

## Roadmap

- [x] Multi-query search (6 targeted searches per run)
- [x] Scoring engine with 4 weighted dimensions
- [x] Seen jobs deduplication
- [x] Designed HTML email digest
- [x] Aventurine brand identity
- [ ] Salary extraction from job description text
- [ ] Scheduled automation (cron / GitHub Actions)
- [ ] Cover letter drafting for 70+ scored roles

---

## The Aventurine Suite

| Agent | Role | Status |
|-------|------|--------|
| [Arcspect](https://arcspect.netlify.app) | Build the product | ✅ Live |
| Luster | Find the stage | ✅ Live |
| Clarity | Run the operation | 🔒 Private |

*The name Luster comes from aventurescence — the shimmer that comes from within aventurine quartz. Luster surfaces the roles worth your attention. The ones that catch the light.*

---

*Built

cat > README.md << 'EOF'
# Luster

> Find the stage.

**Luster** is an AI-powered Vancouver PM job search agent built by [The Aventurine Tech Hub](https://github.com/anovelbygod).

It runs targeted searches across LinkedIn, Indeed, Glassdoor, and Google Jobs for senior PM roles in Vancouver and Remote Canada — scores each role against a personalised profile, filters out noise, and delivers a curated digest to your inbox. Only new roles you haven't seen before are surfaced each run.

🔗 **Part of the Aventurine suite:** [Arcspect](https://arcspect.netlify.app) · Luster · Clarity

---

## What it does

- Searches 6 targeted queries across Vancouver and Remote Canada
- Scores every role 0–100 across four weighted dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Domain | 30% | FinTech, B2B SaaS, Consumer Mobile fit |
| Role Type | 25% | Seniority and PM scope |
| Compensation | 20% | Against a defined salary floor |
| Remote | 15% | Remote Canada or Vancouver-based |

- Hard rejects: office 3+ days, non-Canada lock, analytics roles, under $100K USD
- Deduplicates across runs — only new roles surface each time
- Sends a designed HTML digest email with Apply / Review / Skip sections

---

## Scoring thresholds

| Score | Action |
|-------|--------|
| 70–100 | ▲ Apply Now |
| 55–69 | ◆ Worth Reviewing |
| 0–54 | ▼ Skipped |

---

## Built with

- **Python** — core agent logic
- **JSearch API** (RapidAPI) — aggregates LinkedIn, Indeed, Glassdoor, Google Jobs
- **Gmail SMTP** — delivers the digest
- **seen_jobs.json** — local deduplication tracker

---

## Setup

\`\`\`bash
git clone https://github.com/anovelbygod/luster.git
cd luster
pip install requests python-dotenv
\`\`\`

Create a \`.env\` file:

\`\`\`
RAPIDAPI_KEY=your-jsearch-key
PERSONAL_EMAIL=your@gmail.com
PERSONAL_EMAIL_PASSWORD=your-gmail-app-password
\`\`\`

Run:

\`\`\`bash
python3 search.py
\`\`\`

---

## File structure

\`\`\`
luster/
  search.py        ← fetches, scores, builds and sends the digest
  score.py         ← scoring engine (domain, role, comp, remote)
  seen_jobs.json   ← auto-generated, tracks previously seen roles
  .env             ← API keys (never committed)
  .gitignore
  README.md
\`\`\`

---

## Roadmap

- [x] Multi-query search (6 targeted searches per run)
- [x] Scoring engine with 4 weighted dimensions
- [x] Seen jobs deduplication
- [x] Designed HTML email digest
- [x] Aventurine brand identity
- [ ] Salary extraction from job description text
- [ ] Scheduled automation (cron / GitHub Actions)
- [ ] Cover letter drafting for 70+ scored roles

---

## The Aventurine Suite

| Agent | Role | Status |
|-------|------|--------|
| [Arcspect](https://arcspect.netlify.app) | Build the product | ✅ Live |
| Luster | Find the stage | ✅ Live |
| Clarity | Run the operation | 🔒 Private |

*The name Luster comes from aventurescence — the shimmer that comes from within aventurine quartz. Luster surfaces the roles worth your attention. The ones that catch the light.*

---

*Built by [Efe Ogufere](https://github.com/anovelbygod) · The Aventurine Tech Hub Ltd.*
