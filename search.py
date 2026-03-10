import requests
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from dotenv import load_dotenv
from score import score_job

load_dotenv()

SEEN_FILE = "seen_jobs.json"

# ── Seen jobs tracker ─────────────────────────────────────────────
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f, indent=2)

# ── Fetch ─────────────────────────────────────────────────────────
def fetch_jobs(query, location):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-host": "jsearch.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY")
    }
    params = {
        "query": f"{query} in {location}",
        "page": "1",
        "num_pages": "1",
        "date_posted": "week"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    return data.get("data", [])

# ── Email ─────────────────────────────────────────────────────────
def send_email(subject, html_content):
    sender = os.getenv("PERSONAL_EMAIL")
    password = os.getenv("PERSONAL_EMAIL_PASSWORD")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = sender
    msg.attach(MIMEText(html_content, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, sender, msg.as_string())

# ── Card builder ──────────────────────────────────────────────────
def score_label(score):
    if score >= 70:
        return ("APPLY", "#0F4C2A", "#D1FAE5", "▲")
    elif score >= 55:
        return ("REVIEW", "#78350F", "#FEF3C7", "◆")
    else:
        return ("SKIP", "#7F1D1D", "#FEE2E2", "▼")

def build_job_card(job):
    label, text_color, bg_color, symbol = score_label(job["score"])
    reasons_html = "".join([
        f'<div style="font-size:11px;color:#64748B;padding:1px 0;letter-spacing:0.2px;">{r}</div>'
        for r in job["reasons"]
    ])
    remote_pill = (
        '<span style="display:inline-block;background:#EFF6FF;color:#1D4ED8;'
        'font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;'
        'padding:2px 8px;border-radius:3px;margin-left:8px;vertical-align:middle;">REMOTE</span>'
        if job["remote"] else ""
    )
    return f"""
    <div style="border:1px solid #E2E8F0;border-radius:8px;margin-bottom:12px;overflow:hidden;">
      <div style="background:{bg_color};padding:8px 18px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #E2E8F0;">
        <span style="font-size:9px;font-weight:800;color:{text_color};letter-spacing:2.5px;text-transform:uppercase;">{symbol} {label}</span>
        <span style="font-size:20px;font-weight:800;color:{text_color};font-family:Georgia,serif;letter-spacing:-0.5px;margin-left:auto;">{job['score']}<span style="font-size:10px;font-weight:500;opacity:0.6;">/100</span></span>
      </div>
      <div style="background:#FFFFFF;padding:16px 18px;">
        <div style="font-size:14px;font-weight:700;color:#0F172A;line-height:1.3;margin-bottom:4px;">
          {job['title']}{remote_pill}
        </div>
        <div style="font-size:12px;color:#475569;margin-bottom:12px;letter-spacing:0.2px;">
          {job['company']} &nbsp;·&nbsp; {job['location']}
        </div>
        <div style="border-left:2px solid #E2E8F0;padding-left:12px;margin-bottom:14px;">
          {reasons_html}
        </div>
        <a href="{job['apply_link']}"
           style="display:inline-block;background:#0F172A;color:#FFFFFF;
                  font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
                  padding:8px 18px;border-radius:4px;text-decoration:none;">
          View Role →
        </a>
      </div>
    </div>
    """

# ── Fetch and score ───────────────────────────────────────────────
searches = [
    ("Senior Product Manager", "Vancouver Canada"),
    ("Product Manager", "Remote Canada"),
    ("Senior Product Manager fintech", "Canada"),
    ("Product Manager payments", "Canada"),
    ("Senior Product Manager", "Remote Canada"),
    ("Lead Product Manager", "Canada"),
]

seen_ids = load_seen()
all_jobs = []

for query, location in searches:
    jobs = fetch_jobs(query, location)
    for job in jobs:
        result = score_job(job)
        if result["rejected"]:
            continue
        job_id = f"{result['title']}|{result['company']}"
        if job_id in seen_ids:
            continue
        all_jobs.append(result)

# Deduplicate within this run
this_run_seen = set()
unique_jobs = []
for job in all_jobs:
    key = f"{job['title']}|{job['company']}"
    if key not in this_run_seen:
        this_run_seen.add(key)
        unique_jobs.append(job)

# Sort by score descending
unique_jobs.sort(key=lambda x: x["score"], reverse=True)

# Save all new job IDs to seen file
for job in unique_jobs:
    seen_ids.add(f"{job['title']}|{job['company']}")
save_seen(seen_ids)

# ── Stats ─────────────────────────────────────────────────────────
total = len(unique_jobs)
apply_count = sum(1 for j in unique_jobs if j["score"] >= 70)
review_count = sum(1 for j in unique_jobs if 55 <= j["score"] < 70)

# ── Subject line ──────────────────────────────────────────────────
new_count = apply_count + review_count
if new_count > 0:
    subject = f"🎯 {new_count} new PM role{'s' if new_count != 1 else ''} worth your time — {date.today().strftime('%b %d, %Y')}"
else:
    subject = f"📭 No new PM roles today — {date.today().strftime('%b %d, %Y')}"

# ── Build email ───────────────────────────────────────────────────
html_email = f"""
<html>
<head>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet"/>
</head>
<body style="margin:0;padding:0;background:#F1F5F1;font-family:'Plus Jakarta Sans',Arial,sans-serif;">
<div style="max-width:600px;margin:32px auto;">

  <!-- Header -->
  <div style="background:#0A1A0E;padding:36px 36px 28px;border-radius:12px 12px 0 0;">
    <div style="font-family:'DM Mono',monospace;font-size:9px;color:#4A7C59;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px;">
      The Aventurine Tech Hub &nbsp;·&nbsp; {date.today().strftime("%b %d, %Y")}
    </div>
    <div style="font-size:11px;font-weight:800;color:#6BAF80;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;margin-bottom:6px;">Luster</div>
    <div style="font-size:28px;font-weight:800;color:#FFFFFF;letter-spacing:-0.8px;line-height:1.1;margin-bottom:20px;">
      Job Availability<br/>
      <span style="color:#6BAF80;">Briefing</span>
    </div>
    <div style="display:flex;gap:0;border:1px solid #1E3A24;border-radius:6px;overflow:hidden;">
      <div style="flex:1;padding:12px 16px;border-right:1px solid #1E3A24;">
        <div style="font-size:22px;font-weight:800;color:#FFFFFF;">{total}</div>
        <div style="font-size:9px;color:#4A7C59;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">New Roles</div>
      </div>
      <div style="flex:1;padding:12px 16px;border-right:1px solid #1E3A24;">
        <div style="font-size:22px;font-weight:800;color:#6BAF80;">{apply_count}</div>
        <div style="font-size:9px;color:#4A7C59;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">Apply Now</div>
      </div>
      <div style="flex:1;padding:12px 16px;">
        <div style="font-size:22px;font-weight:800;color:#C9A84C;">{review_count}</div>
        <div style="font-size:9px;color:#4A7C59;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">Worth Review</div>
      </div>
    </div>
  </div>

  <!-- Body -->
  <div style="background:#F8FAF8;padding:24px 28px;border-left:1px solid #DDE8DD;border-right:1px solid #DDE8DD;">

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:#0F4C2A;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #D1FAE5;">▲ Apply Now</div>' if apply_count > 0 else ''}
    {"".join([build_job_card(j) for j in unique_jobs if j["score"] >= 70])}

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:#78350F;letter-spacing:2px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:8px;border-bottom:2px solid #FEF3C7;">◆ Worth Reviewing</div>' if review_count > 0 else ''}
    {"".join([build_job_card(j) for j in unique_jobs if 55 <= j["score"] < 70])}

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:#94A3B8;letter-spacing:2px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:8px;border-bottom:1px solid #E2E8F0;">▼ Skipped This Round</div>' if any(j["score"] < 55 for j in unique_jobs) else ''}
    {"".join([build_job_card(j) for j in unique_jobs if j["score"] < 55])}

  </div>

  <!-- Footer -->
  <div style="background:#0A1A0E;padding:16px 36px;border-radius:0 0 12px 12px;display:flex;justify-content:space-between;align-items:center;">
    <div style="font-family:'DM Mono',monospace;font-size:10px;color:#2D5A3D;">Luster · The Aventurine Tech Hub</div>
    <div style="font-family:'DM Mono',monospace;font-size:10px;color:#2D5A3D;">{date.today()}</div>
  </div>

</div>
</body>
</html>
"""

if total == 0:
    print("✓ No new roles found. Skipping email.")
else:
    send_email(subject, html_email)
    print(f"✓ Digest sent — {total} new roles · {apply_count} apply · {review_count} review")
