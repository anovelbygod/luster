def score_job_ore(job):
    title = (job.get("job_title") or "").lower()
    location = (job.get("job_location") or "").lower()
    description = (job.get("job_description") or "").lower()
    is_remote = job.get("job_is_remote") or False
    min_salary = job.get("job_min_salary")
    max_salary = job.get("job_max_salary")
    apply_link = job.get("job_apply_link") or job.get("job_google_link") or ""
    company = job.get("employer_name") or "Unknown"

    score = 0
    reasons = []
    bilingual_bonus = 0

    # ── Hard rejects ──────────────────────────────────────────────
    reject = False
    reject_reason = ""

    hard_reject_titles = [
        "data analyst", "business analyst", "data scientist",
        "field sales", "territory sales", "outside sales",
        "director", "vice president", "vp ", "head of sales",
        "software engineer", "developer", "graphic designer",
        "financial analyst", "financial modell"
    ]
    if any(w in title for w in hard_reject_titles):
        reject = True
        reject_reason = "❌ Title auto-reject"

    if "agency experience required" in description and "not required" not in description:
        reject = True
        reject_reason = "❌ Agency experience required"

    if "6+ years" in description or "six years" in description:
        reject = True
        reject_reason = "❌ 6+ years required"

    if "commission only" in description or "base salary" not in description and "ote" not in description and min_salary and min_salary < 40000:
        reject = True
        reject_reason = "❌ Commission-only or below minimum comp"

    if "must be located in" in description and "canada" not in description:
        reject = True
        reject_reason = "❌ Location-locked outside Canada"

    if "driver's licence required" in description or "driver's license required" in description:
        reject = True
        reject_reason = "❌ Field sales — driver's licence required"

    if reject:
        return {
            "title": job.get("job_title") or "Unknown Title",
            "company": company,
            "location": job.get("job_location") or "Unknown Location",
            "remote": is_remote,
            "apply_link": apply_link,
            "score": 0,
            "reasons": [reject_reason],
            "rejected": True,
            "reject_reason": reject_reason,
            "description": (job.get("job_description") or "")[:500]
        }

    # ── 1. Experience Match (25%) ─────────────────────────────────
    exp_score = 0
    if any(w in title for w in ["customer success manager", "account manager", "client success",
                                  "client relationship", "partner manager"]):
        if "2" in description or "3" in description or "4" in description:
            exp_score = 10
            reasons.append("✅ CSM/AM title, 2–4 yr range")
        else:
            exp_score = 7
            reasons.append("✅ CSM/AM title")
    elif any(w in title for w in ["marketing coordinator", "marketing specialist",
                                   "digital marketing", "performance marketing"]):
        exp_score = 7
        reasons.append("✅ Digital marketing title — certs bridge gap")
    elif any(w in title for w in ["inside sales", "business development", "account executive"]):
        exp_score = 5
        reasons.append("⚠️ Sales-adjacent — verify account ownership component")
    else:
        exp_score = 2
        reasons.append("❌ Weak title match")
    score += exp_score * 0.25

    # ── 2. Responsibilities Alignment (20%) ───────────────────────
    resp_score = 0
    renewal_keywords = ["renewal", "upsell", "expansion", "retention", "business review",
                         "account health", "qbr", "churn", "onboarding", "adoption"]
    marketing_keywords = ["meta ads", "google ads", "seo", "sem", "social media",
                           "campaign", "performance marketing", "influencer", "semrush", "meltwater"]
    renewal_hits = sum(1 for w in renewal_keywords if w in description)
    marketing_hits = sum(1 for w in marketing_keywords if w in description)

    if renewal_hits >= 3:
        resp_score = 10
        reasons.append("✅ Strong renewal/upsell/retention focus")
    elif renewal_hits >= 1:
        resp_score = 7
        reasons.append("⚠️ Some renewal/retention signals")
    elif marketing_hits >= 2:
        resp_score = 7
        reasons.append("✅ Digital marketing responsibilities match")
    elif marketing_hits >= 1:
        resp_score = 4
        reasons.append("⚠️ Light marketing signals")
    else:
        resp_score = 2
        reasons.append("❌ No renewal, retention, or marketing signals")
    score += resp_score * 0.20

    # ── 3. Industry Fit (15%) ─────────────────────────────────────
    tier1_keywords = ["saas", "digital marketing", "hr tech", "e-commerce", "ecommerce",
                       "hospitality tech", "travel tech", "retail media", "performance marketing",
                       "martech", "adtech"]
    tier2_keywords = ["financial services", "fintech", "healthcare tech", "logistics",
                       "supply chain", "professional services", "wellness", "fitness tech"]
    tier3_keywords = ["manufacturing", "cpg", "fmcg", "gaming", "hardware", "field services"]

    tier1_hits = sum(1 for w in tier1_keywords if w in description)
    tier2_hits = sum(1 for w in tier2_keywords if w in description)
    tier3_hits = sum(1 for w in tier3_keywords if w in description)

    if tier1_hits >= 1:
        ind_score = 9
        reasons.append("✅ Strong industry fit (SaaS/marketing/HR tech)")
    elif tier2_hits >= 1:
        ind_score = 7
        reasons.append("⚠️ Adjacent industry — acceptable fit")
    elif tier3_hits >= 1:
        ind_score = 3
        reasons.append("❌ Weak industry fit")
    else:
        ind_score = 5
        reasons.append("⚠️ Industry unclear — verify")
    score += ind_score * 0.15

    # ── 4. Compensation (10%) ─────────────────────────────────────
    # Convert to CAD rough equivalent (using ~1.36 USD/CAD)
    is_csm_am = any(w in title for w in ["customer success", "account manager", "client success",
                                           "client relationship", "partner manager"])
    if min_salary:
        cad_min = min_salary * 1.36 if min_salary < 50000 else min_salary  # assume CAD if large
        if is_csm_am:
            if cad_min >= 80000:
                comp_score = 10
                salary_note = f"✅ Salary: ${min_salary:,}+ (strong)"
            elif cad_min >= 65000:
                comp_score = 7
                salary_note = f"✅ Salary: ${min_salary:,}+ (on target)"
            elif cad_min >= 60000:
                comp_score = 4
                salary_note = f"⚠️ Salary: ${min_salary:,} (below target)"
            else:
                comp_score = 0
                salary_note = f"❌ Salary: ${min_salary:,} (below minimum)"
        else:
            if cad_min >= 55000:
                comp_score = 10
                salary_note = f"✅ Salary: ${min_salary:,}+ (strong for marketing)"
            elif cad_min >= 45000:
                comp_score = 7
                salary_note = f"✅ Salary: ${min_salary:,}+ (on target)"
            elif cad_min >= 42000:
                comp_score = 4
                salary_note = f"⚠️ Salary: ${min_salary:,} (at floor)"
            else:
                comp_score = 0
                salary_note = f"❌ Salary: ${min_salary:,} (below minimum)"
    else:
        comp_score = 5
        salary_note = "⚠️ Salary not listed — verify"
    reasons.append(salary_note)
    score += comp_score * 0.10

    # ── 5. Location & Work Mode (10%) ─────────────────────────────
    if is_remote:
        loc_score = 10
        reasons.append("✅ Remote Canada")
    elif "vancouver" in location:
        loc_score = 7
        reasons.append("⚠️ Vancouver hybrid — check office days")
    elif "canada" in location:
        loc_score = 5
        reasons.append("⚠️ Canada-based — verify remote policy")
    else:
        loc_score = 0
        reasons.append("❌ Not remote, not Vancouver")
    score += loc_score * 0.10

    # ── 6. Experience Requirements Realism (10%) ──────────────────
    realism_score = 0
    if "2 years" in description or "2-4 years" in description or "2+ years" in description:
        realism_score = 10
        reasons.append("✅ 2–4 yr requirement — realistic fit")
    elif "4 years" in description or "3 years" in description or "3+ years" in description:
        realism_score = 7
        reasons.append("⚠️ 3–4 yr requirement — certs help bridge gap")
    elif "5 years" in description or "5+ years" in description:
        realism_score = 3
        reasons.append("❌ 5+ yr requirement — stretch")
    else:
        realism_score = 6
        reasons.append("⚠️ Experience requirement unclear")
    score += realism_score * 0.10

    # ── 7. Company & Culture Signal (10%) ─────────────────────────
    culture_score = 0
    positive_signals = ["smb", "mid-market", "relationship", "coaching", "growth",
                         "people-first", "collaborative", "mentorship", "team culture"]
    negative_signals = ["high volume", "cold call", "100 calls", "aggressive",
                         "churn and burn", "cutthroat", "agency experience required"]

    positive_hits = sum(1 for w in positive_signals if w in description)
    negative_hits = sum(1 for w in negative_signals if w in description)

    if positive_hits >= 2 and negative_hits == 0:
        culture_score = 10
        reasons.append("✅ Positive culture signals")
    elif positive_hits >= 1 and negative_hits == 0:
        culture_score = 7
        reasons.append("⚠️ Some positive culture signals")
    elif negative_hits >= 1:
        culture_score = 2
        reasons.append("❌ Negative culture signals detected")
    else:
        culture_score = 5
        reasons.append("⚠️ Culture signals neutral/unclear")
    score += culture_score * 0.10

    # ── Bilingual bonus ───────────────────────────────────────────
    if "french" in description or "bilingual" in description:
        bilingual_bonus = 0.3
        reasons.append("🌟 Bilingual English/French valued — bonus applied")

    final_score = round(score * 10 + bilingual_bonus)

    return {
        "title": job.get("job_title") or "Unknown Title",
        "company": company,
        "location": job.get("job_location") or "Unknown Location",
        "remote": is_remote,
        "apply_link": apply_link,
        "score": final_score,
        "reasons": reasons,
        "rejected": False,
        "reject_reason": "",
        "description": (job.get("job_description") or "")[:500]
    }