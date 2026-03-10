def score_job(job):
    title = (job.get("job_title") or "").lower()
    location = (job.get("job_location") or "").lower()
    description = (job.get("job_description") or "").lower()  # full description, no truncation
    is_remote = job.get("job_is_remote") or False
    min_salary = job.get("job_min_salary")
    max_salary = job.get("job_max_salary")
    apply_link = job.get("job_apply_link") or job.get("job_google_link") or ""
    company = job.get("employer_name") or "Unknown"

    score = 0
    reasons = []

    # ── Domain (30%) ──────────────────────────────────────────────
    fintech_keywords = [
        "fintech", "payments", "payment rails", "payment processing",
        "payment platform", "payment gateway", "payment infrastructure",
        "digital banking", "mobile banking", "neobank", "banking platform",
        "banking app", "open banking", "embedded finance",
        "merchant services", "merchant platform", "merchant acquiring",
        "card issuing", "card payments", "card network",
        "cross-border payments", "money transfer", "remittance",
        "financial services", "financial technology", "financial platform",
        "kyc", "aml", "fraud detection", "transaction monitoring",
        "settlement", "reconciliation", "disbursement", "payout",
        "wallet", "digital wallet", "e-wallet",
        "lending platform", "credit platform", "loan origination",
        "treasury", "liquidity", "fx", "foreign exchange",
        "compliance fintech", "regtech", "payment product",
        "acquiring", "issuing", "payment operations",
    ]

    b2b_keywords = [
        "b2b saas", "enterprise saas", "saas platform", "b2b platform",
        "enterprise platform", "enterprise software", "enterprise product",
        "api platform", "api product", "developer platform", "developer tools",
        "developer experience", "platform product", "infrastructure product",
        "compliance platform", "operations platform", "workflow platform",
        "b2b software", "business software", "multi-tenant",
        "self-serve platform", "admin platform", "dashboard product",
    ]

    consumer_keywords = [
        "consumer app", "consumer product", "consumer experience",
        "b2c mobile", "mobile app", "mobile product",
        "ios", "android", "app store",
        "subscription product", "subscription growth",
        "user retention", "user acquisition", "user activation",
        "consumer fintech", "consumer banking", "personal finance",
        "growth product", "engagement product",
    ]

    adjacent_keywords = [
        "healthtech", "health technology", "digital health",
        "edtech", "e-learning platform",
        "e-commerce platform", "marketplace platform",
        "insurtech", "proptech", "legaltech", "regtech",
        "logistics platform", "supply chain platform",
    ]

    # Count hits in full description
    fintech_hits = sum(1 for w in fintech_keywords if w in description)
    b2b_hits = sum(1 for w in b2b_keywords if w in description)
    consumer_hits = sum(1 for w in consumer_keywords if w in description)
    adjacent_hits = sum(1 for w in adjacent_keywords if w in description)

    # Title keywords count as +1 hit toward the threshold
    fintech_title_keywords = ["fintech", "payments", "payment", "financial", "finance", "banking", "wallet", "lending", "credit"]
    b2b_title_keywords = ["platform", "saas", "enterprise", "b2b", "api"]
    consumer_title_keywords = ["consumer", "mobile", "growth", "app"]

    if any(w in title for w in fintech_title_keywords):
        fintech_hits += 1
    if any(w in title for w in b2b_title_keywords):
        b2b_hits += 1
    if any(w in title for w in consumer_title_keywords):
        consumer_hits += 1

    # 2-hit threshold maintained
    domain_score = 0
    if fintech_hits >= 2:
        domain_score = 10
        reasons.append("✅ FinTech/Payments domain")
    elif b2b_hits >= 2:
        domain_score = 9
        reasons.append("✅ B2B SaaS domain")
    elif consumer_hits >= 2:
        domain_score = 8
        reasons.append("✅ Consumer mobile domain")
    elif adjacent_hits >= 1:
        domain_score = 6
        reasons.append("⚠️ Adjacent domain — verify fit")
    elif fintech_hits == 1 or b2b_hits == 1 or consumer_hits == 1:
        domain_score = 5
        reasons.append("⚠️ Possible domain fit — verify before applying")
    else:
        domain_score = 3
        reasons.append("❌ Weak domain fit")
    score += domain_score * 0.30

    # ── Role Type (25%) ───────────────────────────────────────────
    role_score = 0
    if any(w in title for w in ["senior product manager", "lead product", "principal product",
                                 "head of product", "group product manager", "director of product"]):
        role_score = 10
        reasons.append("✅ Senior/Lead PM title")
    elif any(w in title for w in ["product manager", "product owner"]):
        role_score = 8
        reasons.append("✅ PM title")
    elif "product" in title:
        role_score = 5
        reasons.append("⚠️ Product-adjacent title — verify scope")
    else:
        role_score = 2
        reasons.append("❌ Not a PM role")
    score += role_score * 0.25

    # ── Compensation (20%) ────────────────────────────────────────
    if min_salary and min_salary >= 120000:
        comp_score = 10
        salary_note = f"✅ Salary: ${min_salary:,}–${max_salary:,}" if max_salary else f"✅ Salary: ${min_salary:,}+"
    elif min_salary and min_salary >= 100000:
        comp_score = 8
        salary_note = f"✅ Salary: ${min_salary:,}–${max_salary:,}" if max_salary else f"✅ Salary: ${min_salary:,}+"
    elif min_salary and min_salary >= 80000:
        comp_score = 6
        salary_note = f"⚠️ Salary: ${min_salary:,} (below target)"
    elif min_salary:
        comp_score = 0
        salary_note = f"❌ Salary: ${min_salary:,} (below minimum)"
    else:
        comp_score = 6
        salary_note = "⚠️ Salary not listed — verify"
    reasons.append(salary_note)
    score += comp_score * 0.20

    # ── Remote (15%) ──────────────────────────────────────────────
    if is_remote:
        remote_score = 10
        reasons.append("✅ Remote role")
    elif "vancouver" in location:
        remote_score = 7
        reasons.append("⚠️ Vancouver office — verify hybrid days")
    elif "canada" in location:
        remote_score = 5
        reasons.append("⚠️ Canada-based — verify remote policy")
    else:
        remote_score = 2
        reasons.append("❌ Not remote, not Vancouver")
    score += remote_score * 0.15

    # ── Hard rejects ──────────────────────────────────────────────
    reject = False
    reject_reason = ""
    if any(w in title for w in ["data analyst", "business analyst", "operations manager", "marketing manager"]):
        reject = True
        reject_reason = "❌ Not a PM role"
    if "4 days" in description and "hybrid" in description:
        reject = True
        reject_reason = "❌ Office 4 days/week"
    if "must be located in" in description and "canada" not in description:
        reject = True
        reject_reason = "❌ Location-locked outside Canada"

    return {
        "title": job.get("job_title") or "Unknown Title",
        "company": company,
        "location": job.get("job_location") or "Unknown Location",
        "remote": is_remote,
        "apply_link": apply_link,
        "score": round(score * 10),
        "reasons": reasons,
        "rejected": reject,
        "reject_reason": reject_reason,
        "description": (job.get("job_description") or "")[:500]
    }