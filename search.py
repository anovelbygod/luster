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

# ── Theme config ──────────────────────────────────────────────────
def get_theme(user_name):
    if user_name == "Ore":
        return {
            "header_bg": "#3D1A24",
            "header_border": "#6B2A38",
            "eyebrow_color": "#C9707A",
            "title_color": "#F5E6E8",
            "title_accent": "#E8A0A8",
            "stat_border": "rgba(201,112,122,0.2)",
            "stat_num_1": "#FFFFFF",
            "stat_num_2": "#E8A0A8",
            "stat_num_3": "#C9A84C",
            "stat_label": "#C9707A",
            "body_bg": "#FFF0F3",
            "body_border": "#F5D0D8",
            "section_apply_color": "#8B3A44",
            "section_apply_border": "#F5C0C8",
            "section_review_color": "#78350F",
            "section_review_border": "#FEF3C7",
            "card_apply_bg": "#FCE8EC",
            "card_apply_text": "#8B3A44",
            "card_review_bg": "#FEF3C7",
            "card_review_text": "#78350F",
            "card_skip_bg": "#FEE2E2",
            "card_skip_text": "#7F1D1D",
            "card_body_bg": "#FFFFFF",
            "card_title_color": "#2A0A10",
            "card_meta_color": "#8B3A44",
            "card_reason_color": "#64748B",
            "card_border": "#F0D0D8",
            "btn_bg": "#3D1A24",
            "btn_color": "#FFFFFF",
            "footer_bg": "#3D1A24",
            "footer_color": "#9B5A64",
            "font_url": "https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:ital,wght@0,700;1,700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap",
            "title_font": "'Playfair Display', Georgia, serif",
        }
    else:
        return {
            "header_bg": "#0A1A0E",
            "header_border": "#1E3A24",
            "eyebrow_color": "#4A7C59",
            "title_color": "#FFFFFF",
            "title_accent": "#6BAF80",
            "stat_border": "#1E3A24",
            "stat_num_1": "#FFFFFF",
            "stat_num_2": "#6BAF80",
            "stat_num_3": "#C9A84C",
            "stat_label": "#4A7C59",
            "body_bg": "#F8FAF8",
            "body_border": "#DDE8DD",
            "section_apply_color": "#0F4C2A",
            "section_apply_border": "#D1FAE5",
            "section_review_color": "#78350F",
            "section_review_border": "#FEF3C7",
            "card_apply_bg": "#D1FAE5",
            "card_apply_text": "#0F4C2A",
            "card_review_bg": "#FEF3C7",
            "card_review_text": "#78350F",
            "card_skip_bg": "#FEE2E2",
            "card_skip_text": "#7F1D1D",
            "card_body_bg": "#FFFFFF",
            "card_title_color": "#0F172A",
            "card_meta_color": "#475569",
            "card_reason_color": "#64748B",
            "card_border": "#E2E8F0",
            "btn_bg": "#0F172A",
            "btn_color": "#FFFFFF",
            "footer_bg": "#0A1A0E",
            "footer_color": "#2D5A3D",
            "font_url": "https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap",
            "title_font": "'Plus Jakarta Sans', Arial, sans-serif",
        }

# ── Card builder ──────────────────────────────────────────────────
def score_label(score, theme):
    if score >= APPLY_THRESHOLD:
        return ("APPLY", theme["card_apply_text"], theme["card_apply_bg"], "▲")
    elif score >= REVIEW_THRESHOLD:
        return ("REVIEW", theme["card_review_text"], theme["card_review_bg"], "◆")
    else:
        return ("SKIP", theme["card_skip_text"], theme["card_skip_bg"], "▼")

def build_job_card(job, theme):
    label, text_color, bg_color, symbol = score_label(job["score"], theme)
    reasons_html = "".join([
        f'<div style="font-size:11px;color:{theme["card_reason_color"]};padding:1px 0;letter-spacing:0.2px;">{r}</div>'
        for r in job["reasons"]
    ])
    remote_pill = (
        '<span style="display:inline-block;background:#EFF6FF;color:#1D4ED8;'
        'font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;'
        'padding:2px 8px;border-radius:3px;margin-left:8px;vertical-align:middle;">REMOTE</span>'
        if job["remote"] else ""
    )
    return f"""
    <div style="border:1px solid {theme['card_border']};border-radius:8px;margin-bottom:12px;overflow:hidden;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:{bg_color};border-bottom:1px solid {theme['card_border']};">
        <tr>
          <td style="padding:8px 18px;font-size:9px;font-weight:800;color:{text_color};letter-spacing:2.5px;text-transform:uppercase;">{symbol} {label}</td>
          <td align="right" style="padding:8px 18px;font-size:18px;font-weight:800;color:{text_color};font-family:Georgia,serif;">{job['score']}/100</td>
        </tr>
      </table>
      <div style="background:{theme['card_body_bg']};padding:16px 18px;">
        <div style="font-size:14px;font-weight:700;color:{theme['card_title_color']};line-height:1.3;margin-bottom:4px;">
          {job['title']}{remote_pill}
        </div>
        <div style="font-size:12px;color:{theme['card_meta_color']};margin-bottom:12px;letter-spacing:0.2px;">
          {job['company']} &nbsp;·&nbsp; {job['location']}
        </div>
        <div style="border-left:2px solid {theme['card_border']};padding-left:12px;margin-bottom:14px;">
          {reasons_html}
        </div>
        <a href="{job['apply_link']}"
           style="display:inline-block;background:{theme['btn_bg']};color:{theme['btn_color']};
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
theme = get_theme(USER_NAME)
new_count = apply_count + review_count

if USER_NAME == "Ore":
    if new_count > 0:
        subject = f"Hey Pookie 💌 — {new_count} new role{'s' if new_count != 1 else ''} worth your time"
    else:
        subject = f"Hey Pookie 💌 — No new roles today, but I'm still looking"
else:
    if new_count > 0:
        subject = f"🎯 {new_count} new {ROLE_LABEL} worth your time — {date.today().strftime('%b %d, %Y')}"
    else:
        subject = f"📭 No new {ROLE_LABEL} today — {date.today().strftime('%b %d, %Y')}"

# ── Build email ───────────────────────────────────────────────────
greeting_line = f"Hey Pookie 💌 &nbsp;·&nbsp; {date.today().strftime('%b %d, %Y')}" if USER_NAME == "Ore" else f"{HEADER_LABEL} &nbsp;·&nbsp; {date.today().strftime('%b %d, %Y')}"
footer_tag = "Luster · made with love 💌" if USER_NAME == "Ore" else "Luster · The Aventurine Tech Hub"

html_email = f"""
<html>
<head>
  <link href="{theme['font_url']}" rel="stylesheet"/>
</head>
<body style="margin:0;padding:0;background:#F1F5F1;font-family:'Plus Jakarta Sans',Arial,sans-serif;">
<div style="max-width:600px;margin:32px auto;">

  <!-- Header -->
  <div style="background:{theme['header_bg']};padding:36px 36px 28px;border-radius:12px 12px 0 0;">
    <div style="font-family:'DM Mono',monospace;font-size:9px;color:{theme['eyebrow_color']};letter-spacing:3px;text-transform:uppercase;margin-bottom:14px;">
      {greeting_line}
    </div>
    <div style="font-size:28px;font-weight:800;color:{theme['title_color']};font-family:{theme['title_font']};letter-spacing:-0.8px;line-height:1.1;margin-bottom:20px;">
      Career Intelligence<br/>
      <span style="color:{theme['title_accent']};font-style:italic;">Briefing</span>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {theme['stat_border']};border-radius:6px;overflow:hidden;">
      <tr>
        <td width="33%" style="padding:12px 16px;border-right:1px solid {theme['stat_border']};">
          <div style="font-size:22px;font-weight:800;color:{theme['stat_num_1']};">{total}</div>
          <div style="font-size:9px;color:{theme['stat_label']};letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">New Roles</div>
        </td>
        <td width="33%" style="padding:12px 16px;border-right:1px solid {theme['stat_border']};">
          <div style="font-size:22px;font-weight:800;color:{theme['stat_num_2']};">{apply_count}</div>
          <div style="font-size:9px;color:{theme['stat_label']};letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">Apply Now</div>
        </td>
        <td width="33%" style="padding:12px 16px;">
          <div style="font-size:22px;font-weight:800;color:{theme['stat_num_3']};">{review_count}</div>
          <div style="font-size:9px;color:{theme['stat_label']};letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">Worth Review</div>
        </td>
      </tr>
    </table>
  </div>

  <!-- Body -->
  <div style="background:{theme['body_bg']};padding:24px 28px;border-left:1px solid {theme['body_border']};border-right:1px solid {theme['body_border']};">

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:' + theme["section_apply_color"] + ';letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid ' + theme["section_apply_border"] + ';">▲ Apply Now</div>' if apply_count > 0 else ''}
    {"".join([build_job_card(j, theme) for j in unique_jobs if j["score"] >= APPLY_THRESHOLD])}

    {'<div style="font-family:DM Mono,monospace;font-size:9px;color:' + theme["section_review_color"] + ';letter-spacing:2px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:8px;border-bottom:2px solid ' + theme["section_review_border"] + ';">◆ Worth Reviewing</div>' if review_count > 0 else ''}
    {"".join([build_job_card(j, theme) for j in unique_jobs if REVIEW_THRESHOLD <= j["score"] < APPLY_THRESHOLD])}

  </div>

  <!-- Footer -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:{theme['footer_bg']};border-radius:0 0 12px 12px;">
    <tr>
      <td style="padding:16px 36px;font-family:'DM Mono',monospace;font-size:10px;color:{theme['footer_color']};">{footer_tag}</td>
      <td align="right" style="padding:16px 36px;font-family:'DM Mono',monospace;font-size:10px;color:{theme['footer_color']};">{date.today()}</td>
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