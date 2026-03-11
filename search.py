import requests
import os
import json
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from dotenv import load_dotenv
from score import score_job
from score_ore import score_job_ore

load_dotenv()

# ── Args ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True, help="Path to config JSON file")
args = parser.parse_args()

with open(args.config, "r") as f:
    config = json.load(f)

SEEN_FILE = config["seen_file"]
APPLY_THRESHOLD = config["score_threshold_apply"]
REVIEW_THRESHOLD = config["score_threshold_review"]
SENDER_EMAIL = os.getenv(config["sender_email_env"])
SENDER_PASSWORD = os.getenv(config["sender_password_env"])
RECIPIENT_EMAIL = os.getenv(config["recipient_email_env"])
HEADER_LABEL = config["email_header_label"]
ROLE_LABEL = config["email_role_label"]
SEARCHES = config["searches"]
USER_NAME = config["name"]

# Pick scoring function
score_fn = score_job_ore if USER_NAME == "Ore" else score_job

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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_content, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

# ── Card builder ──────────────────────────────────────────────────
def score_label(score):
    if score >= APPLY_THRESHOLD:
        return ("APPLY", "#0F4C2A", "#D1FAE5", "▲")
    elif score >= REVIEW_THRESHOLD:
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
      <table width="100%" cellpadding="0" cellspacing="0" style="background:{bg_color};border-bottom:1px solid #E2E8F0;">
        <tr>
          <td style="padding:8px 18px;font-size:9px;font-weight:800;color:{text_color};letter-spacing:2.5px;text-transform:uppercase;">{symbol} {label}</td>
          <td align="right" style="padding:8px 18px;font-size:18px;font-weight:800;color:{text_color};font-family:Georgia,serif;">{job['score']}/100</td>
        </tr>
      </table>
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
seen_ids = load_seen()
all_jobs = []

for query, location in SEARCHES:
    jobs = fetch_jobs(query, location)
    for job in jobs:
        result = score_fn(job)
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

unique_jobs.sort(key=lambda x: x["score"], reverse=True)

for job in unique_jobs:
    seen_ids.add(f"{job['title']}|{job['company']}")
save_seen(seen_ids)

# ── Stats ─────────────────────────────────────────────────────────
total = len(unique_jobs)
apply_count = sum(1 for j in unique_jobs if j["score"] >= APPLY_THRESHOLD)
review_count = sum(1 for j in unique_jobs if REVIEW_THRESHOLD <= j["score"] < APPLY_THRESHOLD)

# ── Subject line ──────────────────────────────────────────────────
new_count = apply_count + review_count
if new_count > 0:
    subject = f"🎯 {new_count} new {ROLE_LABEL} worth your time — {date.today().strftime('%b %d, %Y')}"
else:
    subject = f"📭 No new {ROLE_LABEL} today — {date.today().strftime('%b %d, %Y')}"

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
      {HEADER_LABEL} &nbsp;·&nbsp; {date.today().strftime("%b %d, %Y")}
    </div>
    <div style="font-size:28px;font-weight:800;color:#FFFFFF;letter-spacing:-0.8px;line-height:1.1;margin-bottom:20px;">
      Role Intelligence<br/>
      <span style="color:#6BAF80;">Briefing</span>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #1E3A24;border-radius:6px;overflow:hidden;">
      <tr>
        <td width="33%" style="padding:12px 16px;border-right:1px solid #1E3A24;">
          <div style="font-size:22px;font-weight:800;color:#FFFFFF;">{total}</div>
          <div style="font-size:9px;color:#4A7C59;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">New Roles</div>
        </td>
        <td width="33%" style="padding:12px 16px;border-right:1px solid #1E3A24;">
          <div style="font-size:22px;font-weight:800;color:#6BAF80;">{apply_count}</div>
          <div style="font-size:9px;color:#4A7C59;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">Apply Now</div>
        </td>
        <td width="33%" style="padding:12px 16px;">
          <div style="font-size:22px;font-weight:800;color:#C9A84C;">{review_count}</div>
          <div style="font-size:9px;color:#4A7C59;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">Worth Review</div>
        </td>
      </tr>
    </table>
  </div>

  <!-- Body -->
  <div style="background:#F8FAF8;padding:24px 28px;border-left:1px solid #DDE8DD;border-right:1px solid #DDE8DD;">

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:#0F4C2A;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #D1FAE5;">▲ Apply Now</div>' if apply_count > 0 else ''}
    {"".join([build_job_card(j) for j in unique_jobs if j["score"] >= APPLY_THRESHOLD])}

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:#78350F;letter-spacing:2px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:8px;border-bottom:2px solid #FEF3C7;">◆ Worth Reviewing</div>' if review_count > 0 else ''}
    {"".join([build_job_card(j) for j in unique_jobs if REVIEW_THRESHOLD <= j["score"] < APPLY_THRESHOLD])}

  </div>

  <!-- Footer -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0A1A0E;border-radius:0 0 12px 12px;">
    <tr>
      <td style="padding:16px 36px;font-family:'DM Mono',monospace;font-size:10px;color:#2D5A3D;">Luster · The Aventurine Tech Hub</td>
      <td align="right" style="padding:16px 36px;font-family:'DM Mono',monospace;font-size:10px;color:#2D5A3D;">{date.today()}</td>
    </tr>
  </table>

</div>
</body>
</html>
"""

if total == 0:
    print(f"✓ No new {ROLE_LABEL} found for {USER_NAME}. Skipping email.")
else:
    send_email(subject, html_email)
    print(f"✓ Digest sent to {USER_NAME} — {total} new roles · {apply_count} apply · {review_count} review")