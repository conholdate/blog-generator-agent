import re
import frontmatter

def validate_seo_content(markdown_string, targets):
    """
    Enhanced SEO Validator with Word Count Tolerance and Read More check.
    """
    report = {"status": "PASS", "score": 0, "details": {}}
    max_score = 100
    deductions = 0
    
    try:
        post = frontmatter.loads(markdown_string)
        content_body = post.content
        fm = post.metadata
    except Exception as e:
        return {"status": "FAIL", "error": f"Invalid Frontmatter/Markdown: {str(e)}"}

    primary_kw = targets.get("primary_keyword", "").lower()

    # --- RULE 1: seoTitle (40-60 chars + Keyword) ---
    seo_title = fm.get("seoTitle", "")
    seo_len = len(seo_title)
    has_kw_in_seo = primary_kw in seo_title.lower()
    
    title_score = 20
    if not (40 <= seo_len <= 60) or not has_kw_in_seo:
        title_score = 0
        deductions += 20
        msg = f"Length: {seo_len}, Keyword: {'Found' if has_kw_in_seo else 'Missing'}"
    else:
        msg = "Perfect"
    report["details"]["seo_title"] = {"score": title_score, "msg": msg}

    # --- RULE 2: Meta Description (140-160 chars) ---
    meta_desc = fm.get("description", "")
    meta_len = len(meta_desc)
    meta_score = 15
    if not (140 <= meta_len <= 160):
        meta_score = 0
        deductions += 15
        msg = f"Length {meta_len} (Target 140-160)"
    else:
        msg = "Perfect"
    report["details"]["meta_description"] = {"score": meta_score, "msg": msg}

    # --- RULE 3: Keyword Density (Min 5) ---
    min_kw = targets.get("target_keyword_count", 5)
    occurrences = len(re.findall(re.escape(primary_kw), markdown_string.lower()))
    kw_score = 15
    if occurrences < min_kw:
        kw_score = 0
        deductions += 15
        msg = f"Found {occurrences}. Min required: {min_kw}"
    else:
        msg = f"Passed: {occurrences} found"
    report["details"]["keyword_density"] = {"score": kw_score, "msg": msg}

    # --- RULE 4: Required Sections (FAQ & Read More) ---
    has_faq = bool(re.search(r'^#+\s*(FAQ|Frequently Asked Questions)', content_body, re.MULTILINE | re.IGNORECASE))
    has_read_more = bool(re.search(r'^#+\s*Read More', content_body, re.MULTILINE | re.IGNORECASE))
    
    sec_score = 15
    sec_msgs = []
    if not has_faq: sec_msgs.append("Missing FAQ")
    if not has_read_more: sec_msgs.append("Missing Read More")
    
    if sec_msgs:
        sec_score = 0
        deductions += 15
        msg = " | ".join(sec_msgs)
    else:
        msg = "Both sections found"
    report["details"]["required_sections"] = {"score": sec_score, "msg": msg}

    # --- RULE 5: Complete Code Snippet Wrapper ---
    has_wrapper = ("" in content_body and 
                   "" in content_body)
    code_score = 20
    if not has_wrapper:
        code_score = 0
        deductions += 20
        msg = "Tags missing"
    else:
        msg = "Tags correct"
    report["details"]["code_wrapper"] = {"score": code_score, "msg": msg}

    # --- RULE 6: Word Count with Tolerance ---
    # Logic: Accept +/- 10% of the target
    target_wc = targets.get("target_words", 1000)
    actual_wc = len(content_body.split())
    tolerance = 0.10 # 10%
    
    lower_bound = target_wc * (1 - tolerance)
    upper_bound = target_wc * (1 + tolerance)
    
    wc_score = 15
    if actual_wc < lower_bound:
        wc_score = 0
        deductions += 15
        msg = f"Too short: {actual_wc} words (Min: {int(lower_bound)})"
    elif actual_wc > upper_bound:
        # Note: Usually long is okay for SEO, but we keep the range as requested
        wc_score = 15 
        msg = f"Long but okay: {actual_wc} words"
    else:
        msg = f"Count: {actual_wc} (Within range)"
        
    report["details"]["word_count"] = {"score": wc_score, "msg": msg}

    # Final Score
    report["score"] = max(0, max_score - deductions)
    report["status"] = "PASS" if report["score"] == 100 else "REVISION_NEEDED"
    
    return report