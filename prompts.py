# prompts.py

# 1. SYSTEM PROMPT
SYSTEM_PROMPT_AUDIT = """
You are a world-class Chief Marketing Officer (CMO).
Your goal is to analyze raw business data and produce strategic, high-impact insights.
Tone: Strategic, Insightful, Direct, Professional.
"""

# 2. MASTER AUDIT DOCUMENT PROMPT
USER_PROMPT_MASTER_AUDIT = """
You are writing a **Master Marketing Audit Document** for {client_name}.

**Data Provided:**
1. **Website Content:** {client_text}
2. **SEO Snapshot:** {seo_snapshot}
3. **Competitor Summary:** {competitor_data}
4. **Technical & Performance Data:** {pagespeed_scores}
5. **Business Context:** {business_type}

**Structure (Must follow this Markdown sequence):**

# Master Marketing Audit: {client_name}

## 1. Client Overview & Core Strategy
* **Business Type:** {business_type}
* **Core Value Proposition:** (Analyze {client_text})
* **Target Audience:** (Infer from {client_text})

## 2. Website Audit Summary (UX, Speed, Mobile)
* **Performance Snapshot:**
{pagespeed_scores}
* **Critical Analysis:** Based on the 'Technical Audit Report' above, identify the single biggest bottleneck affecting user experience.
* **Business Impact:** Explain clearly how specific scores are likely hurting revenue (e.g., "High bounce rates on mobile").
* **Actionable Fix:** Select the #1 opportunity and detail the steps to fix it.

## 3. SEO & Content Strategy
* **On-Page SEO Audit:** (Analyze {seo_snapshot} and {client_text}. Comment on title tags, headings, and internal linking structure.)
* **Content Gap Analysis:** (Recommend 3 high-value, unmet content topics based on {client_text} and implied search intent.)
* **Actionable Fix:** Recommend the highest-impact content piece to create now.

## 4. Competitive Landscape
* **Competitive Table:** (Reference the JSON table provided below.)
* **Positioning Analysis:** Summarize {client_name}'s market position relative to its competitors (unique strengths vs. shared weaknesses).
* **Actionable Fix:** Propose a single messaging change to immediately differentiate {client_name} in the market.

## 5. Summary & Next Steps
* **Top 3 Strategic Priorities:** (List the three most important, non-technical marketing actions.)
* **30-Day Execution Plan:** (List 5 concrete, first-step tasks for the marketing team.)
"""

# 3. COMPETITOR JSON PROMPT (Strict Structure - Competitors Only)
USER_PROMPT_COMPETITOR_JSON = """
Analyze these Competitors: {competitor_data}.

Return a JSON object representing a comparison table comparing these competitors across key features.
The JSON must have this exact structure.
IMPORTANT: You MUST replace "Actual Name of Comp 1", etc., with the REAL company names found in the competitor data.

{{
  "columns": ["Feature", "Actual Name of Comp 1", "Actual Name of Comp 2", "Actual Name of Comp 3"],
  "rows": [
    ["Core Offering", "Comp 1 offering", "Comp 2 offering", "Comp 3 offering"],
    ["Target Audience", "Comp 1 target", "Comp 2 target", "Comp 3 target"],
    ["Unique Selling Point", "Comp 1 USP", "Comp 2 USP", "Comp 3 USP"],
    ["Weakness", "Comp 1 Weakness", "Comp 2 Weakness", "Comp 3 Weakness"]
  ]
}}
Do not output markdown. Output RAW JSON only.
"""

# 4. VIDEO SCRIPT PROMPT
USER_PROMPT_VIDEO_SCRIPT = """
Based on the client's website context below, write a **12-Second Video Ad Script/Prompt** tailored for LinkedIn/Meta. This text will be used by the video AI to generate both the visuals and the integrated voiceover.

**Client Context:**
{website_summary}

**Requirements (CRITICAL):**
- **TOTAL WORD COUNT MUST BE 20-30 WORDS.** This ensures a smooth, clear reading pace and visual pacing for 12 seconds.
- **Narrative Flow:** Ensure the script text contains clear, short sentences for the voiceover.
- **Output ONLY the script text.**
"""