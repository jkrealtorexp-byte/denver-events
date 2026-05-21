import anthropic
import os
from datetime import datetime, timedelta

def get_weekend_dates():
    today = datetime.utcnow()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    friday = today + timedelta(days=days_until_friday)
    sunday = friday + timedelta(days=2)

    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    if friday.month == sunday.month:
        date_range = f"{months[friday.month-1]} {friday.day}–{sunday.day}, {sunday.year}"
    else:
        date_range = f"{months[friday.month-1]} {friday.day} – {months[sunday.month-1]} {sunday.day}, {sunday.year}"

    return friday, sunday, date_range

def extract_between(text, start, end):
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1:
        return None
    return text[s+len(start):e].strip()

def generate_html():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    friday, sunday, date_range = get_weekend_dates()

    prompt = f"""Search the web for events happening in Denver metro area from {friday.strftime('%B %d')} to {sunday.strftime('%B %d, %Y')}.

Search for:
- "Denver family events {friday.strftime('%B %d')} {sunday.strftime('%B %d %Y')}"
- "Red Rocks concerts {friday.strftime('%B %Y')}"
- "Denver sports {friday.strftime('%B %d %Y')}"
- "Denver free events this weekend {friday.strftime('%B %Y')}"
- "Denver festivals {friday.strftime('%B %Y')}"

Find real events with actual names, venues, dates and times. Target audience is Denver metro families.
Categories: Family Events, Sports (Rockies/Rapids/Avalanche/Broncos/Nuggets), Concerts.

Then output TWO complete HTML files in this exact format:

===INDEX_HTML_START===
[Complete standalone HTML page with:
- DOCTYPE, head with Google Fonts Lato loaded, responsive meta tag
- Title: What's Happening in Denver This Weekend
- CSS: html+body background #162a3d, font Lato, .wrap max-width 960px margin auto
- Orange date bar: {date_range}
- Category headers with orange left border (color #f5821f)
- 2-column CSS grid of event cards (background #1a3349, border-radius 4px, padding 14px)
- Card content: meta (orange, uppercase, 10px, day/time/FREE), title (white bold 15px), venue (color #8aabcc 12px), short desc (color #ccddee 11px), Details/Tickets link in orange
- Responsive single column on mobile via media query
- Bottom spacer 20px]
===INDEX_HTML_END===

===EMAIL_HTML_START===
[Email-safe HTML using only tables and inline styles, max-width 600px:
- Outer table bgcolor #162a3d
- Orange date bar row: {date_range}
- Category header rows with orange left border
- 2-column table rows for event cards (bgcolor #1a3349)
- Each card: meta div (orange, uppercase), title (white bold), venue (color #8aabcc) — NO links on cards
- Final row: centered orange button linking to https://jeremykanehomes.com/this-weekend-in-denver with text "See Full Details & Tickets →"
- All styles inline, no external CSS]
===EMAIL_HTML_END==="""

    print("Calling Claude with web search...")
    response = client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10000,
        betas=["web-search-2025-03-05"],
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 10
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            full_text += block.text

    index_html = extract_between(full_text, "===INDEX_HTML_START===", "===INDEX_HTML_END===")
    email_html = extract_between(full_text, "===EMAIL_HTML_START===", "===EMAIL_HTML_END===")

    return index_html, email_html

if __name__ == "__main__":
    print("Generating Denver weekend events...")
    index_html, email_html = generate_html()

    if index_html:
        with open("index.html", "w") as f:
            f.write(index_html)
        print("✓ index.html updated")
    else:
        print("✗ Could not parse index.html from response")

    if email_html:
        with open("email.html", "w") as f:
            f.write(email_html)
        print("✓ email.html updated")
    else:
        print("✗ Could not parse email.html from response")
