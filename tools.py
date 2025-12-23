import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

# 1. Domain Blacklist (Directories & Socials)
BLACKLIST_DOMAINS = [
    "zoominfo.com", "rocketreach.co", "craft.co", "linkedin.com", 
    "glassdoor.com", "indeed.com", "yelp.com", "yellowpages.com", 
    "crunchbase.com", "owler.com", "dnb.com", "hoovers.com",
    "bloomberg.com", "pitchbook.com", "g2.com", "capterra.com",
    "thomasnet.com", "alibaba.com", "amazon.com", "ebay.com",
    "reddit.com", "quora.com", "pinterest.com", "instagram.com",
    "facebook.com", "youtube.com", "medium.com", "cosmosourcing.com",
    "fortunebusinessinsights.com", "veridion.com", "customcarryingcases.net" 
]

# 2. Title Blacklist (Blogs, Reports, Lists)
BLACKLIST_TITLES = [
    "market size", "market share", "growth analysis", "forecast",
    "top 10", "top 5", "top 8", "best", "list of", "directory",
    "alternatives", "competitors", "suppliers for", "sourcing agents",
    "trends", "statistics", "report", "research", "association"
]

# ----------------------------------------------------------------------
# 3. SEO SNAPSHOT FUNCTION (New Implementation for Serper API)
# ----------------------------------------------------------------------
def get_seo_snapshot(url: str, client_name: str) -> str:
    """
    Gathers key SEO data (organic results, knowledge panel, related searches)
    for the client's domain and industry using the Serper API.
    """
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        return "Error: SERPER_API_KEY not found."

    search_query = f"{client_name} marketing agency audit"
    serper_url = "https://google.serper.dev/search"
    
    # Payload for structured SEO data
    payload = json.dumps({
        "q": search_query,
        "gl": "us",
        "hl": "en",
        "autocorrect": False,
        "safe": "active"
    })

    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", serper_url, headers=headers, data=payload, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: Serper API request failed: {e}"
    except Exception as e:
        return f"Error: Failed to process Serper response: {e}"

    # --- Process and Filter Results ---
    summary_parts = []
    
    # 1. Organic Results (Filtered)
    organic_results = data.get('organic', [])
    filtered_results = []
    
    # Normalize the client URL for filtering
    normalized_client_url = url.replace('https://', '').replace('http://', '').strip('/')

    for result in organic_results:
        link = result.get('link', '').lower()
        title = result.get('title', '').lower()
        
        # Skip blacklisted domains
        if any(domain in link for domain in BLACKLIST_DOMAINS):
            continue
        
        # Skip blacklisted titles (e.g., reports, generic lists)
        if any(word in title for word in BLACKLIST_TITLES):
            continue
            
        # Skip the client's own website
        if normalized_client_url in link.replace('https://', '').replace('http://', '').strip('/'):
            continue
            
        filtered_results.append(f" - {result.get('title', 'No Title')} | Link: {link}")

    if filtered_results:
        summary_parts.append("### Top Relevant Organic Search Results (Excluding Client and Directories):")
        summary_parts.extend(filtered_results[:5]) # Take top 5
    else:
        summary_parts.append("### Top Relevant Organic Search Results: None found (check blacklists/query).")

    # 2. Knowledge Panel (Authority Signal)
    knowledge_panel = data.get('knowledgeGraph') or data.get('searchInformation', {}).get('snippet')
    if knowledge_panel:
        summary_parts.append("\n### Knowledge Panel/Authority Snippet:")
        # Prioritize structured KG data
        if data.get('knowledgeGraph'):
            for key, value in data['knowledgeGraph'].items():
                if isinstance(value, str) and key not in ['type', 'description', 'website']:
                    summary_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
            summary_parts.append(f"- Description: {data['knowledgeGraph'].get('description', 'N/A')}")
        else: # Fallback to search snippet
            summary_parts.append(f"- Snippet: {knowledge_panel}")
    
    # 3. Related Searches (Audience Intent)
    related_searches = data.get('relatedSearches', [])
    if related_searches:
        summary_parts.append("\n### Related Searches (Audience/Intent):")
        summary_parts.append(" - " + ", ".join([s['query'] for s in related_searches][:5]))

    # 4. Summary for the current client's website (simple check)
    if not any(normalized_client_url in res.get('link', '').replace('https://', '').replace('http://', '').strip('/') for res in organic_results):
        summary_parts.append(f"\n### Domain Authority Check:")
        summary_parts.append(f"- WARNING: The client's domain ({url}) does not appear on the first page of search results for its own brand search ('{search_query}'). This is a critical SEO/branding issue.")
    
    return "\n".join(summary_parts)


# ----------------------------------------------------------------------
# 4. TECHNICAL AUDIT FUNCTION (Unchanged from previous versions)
# ----------------------------------------------------------------------
def get_pagespeed_insights(url: str) -> str:
    """
    Fetches Google Pagespeed Insights data and formats it for the LLM.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        return "Error: GOOGLE_API_KEY not found."

    # Use the PageSpeed Insights API endpoint
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={google_api_key}&strategy=mobile"

    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: Pagespeed API request failed: {e}"
    except Exception as e:
        return f"Error: Failed to process Pagespeed response: {e}"

    # Extract relevant data
    try:
        lighthouse_result = data.get('lighthouseResult', {})
        audits = lighthouse_result.get('audits', {})
        categories = lighthouse_result.get('categories', {})

        # 1. Main Scores
        scores = {
            "Performance": int(categories.get('performance', {}).get('score', 0) * 100),
            "SEO": int(categories.get('seo', {}).get('score', 0) * 100),
            "Accessibility": int(categories.get('accessibility', {}).get('score', 0) * 100)
        }

        # 2. Core Web Vitals (Prefer Field Data if available, otherwise Lab Data)
        metrics = {}
        
        # Check for Crux (Field) data first
        metrics_source = data.get('loadingExperience', {}).get('metrics', {})
        
        if metrics_source:
            metrics["LCP"] = metrics_source.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("category", "Unavailable")
            metrics["CLS"] = metrics_source.get("CUMULATIVE_LAYOUT_SHIFT", {}).get("category", "Unavailable")
            metrics["INP"] = metrics_source.get("INTERACTION_TO_NEXT_PAINT", {}).get("category", "Unavailable")
        else:
            # Fallback to Lab Data
            metrics["LCP"] = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
            metrics["CLS"] = audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A")
            metrics["INP"] = "N/A (Lab Data)"

        # 3. Top Opportunities (Specific Technical Fixes)
        opportunities = []
        for key, audit in audits.items():
            if audit.get("details", {}).get("type") == "opportunity" and audit.get("score", 1) < 0.9:
                opportunities.append(f"- {audit['title']}: {audit.get('displayValue', '')}")
        
        top_opps = "\n".join(opportunities[:3]) if opportunities else "No major technical issues found."

        # Format the detailed report
        report = f"""
--- TECHNICAL AUDIT REPORT (Mobile Strategy) ---
SCORES:
- Performance: {scores['Performance']}/100
- SEO: {scores['SEO']}/100
- Accessibility: {scores['Accessibility']}/100

CORE WEB VITALS (User Experience):
- Loading Speed (LCP): {metrics['LCP']}
- Visual Stability (CLS): {metrics['CLS']}
- Interactivity (INP): {metrics['INP']}

TOP 3 TECHNICAL OPPORTUNITIES (Actionable Fixes):
{top_opps}
"""
        return report.strip()

    except Exception as e:
        return f"Error: Failed to parse Pagespeed data: {e}"

# ----------------------------------------------------------------------
# 5. COMPETITOR FUNCTION (Unchanged from previous versions)
# ----------------------------------------------------------------------
def get_competitors(client_name: str) -> str:
    """
    Finds direct competitors for a given business using Serper API.
    """
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        return "Error: SERPER_API_KEY not found."
    
    # Target competitor identification
    search_query = f"top competitors for {client_name} digital marketing agency"
    serper_url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": search_query,
        "gl": "us",
        "hl": "en",
        "autocorrect": False
    })
    
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", serper_url, headers=headers, data=payload, timeout=10)
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: Serper API request failed: {e}"
    except Exception as e:
        return f"Error: Failed to process Serper response: {e}"

    # --- Process and Filter Results ---
    competitor_list = []
    
    # 1. Process Organic Results
    organic_results = data.get('organic', [])
    for result in organic_results:
        link = result.get('link', '').lower()
        title = result.get('title', '').lower()

        # Skip blacklisted domains (directories, social media, etc.)
        if any(domain in link for domain in BLACKLIST_DOMAINS):
            continue
        
        # Skip blacklisted titles (generic reports, lists, etc.)
        if any(word in title for word in BLACKLIST_TITLES):
            continue
            
        # Skip the client itself
        if client_name.lower().replace(' ', '') in title.replace(' ', ''):
             continue

        snippet = result.get('snippet', 'No description available.')
        competitor_list.append(f" - Title: {result.get('title')}. Snippet: {snippet}. Link: {link}")

    if not competitor_list:
        return f"Error: No relevant competitors found for query: '{search_query}'. The list was filtered or the query was poor."

    return "\n".join(competitor_list)