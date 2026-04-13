"""
Email generation service.
Produces personalized, warm outreach emails to businesses without websites.
"""

import random


# ---------------------------------------------------------------------------
# Subject line variants — picked by hash of business name for consistency
# ---------------------------------------------------------------------------

_SUBJECTS = [
    "Quick question about {business_name}'s online presence",
    "Helping {business_name} get found online",
    "A simple idea for {business_name}",
    "{business_name} — have you considered a website?",
    "One small thing that could bring more customers to {business_name}",
    "I noticed {business_name} doesn't have a website yet",
]


def generate_subject(lead: dict) -> str:
    name = lead.get("business_name", "your business")
    template = _SUBJECTS[hash(name) % len(_SUBJECTS)]
    return template.format(business_name=name)


# ---------------------------------------------------------------------------
# Industry-specific benefit snippets
# ---------------------------------------------------------------------------

_INDUSTRY_SNIPPETS = {
    "restaurant": "Customers search for menus and hours online before deciding where to eat — a site makes sure they find you first.",
    "salon":      "People look for photos of work, pricing, and booking options before choosing a salon. A site handles all of that 24/7.",
    "plumber":    "When a pipe bursts at midnight, people Google for help immediately. A site puts your number right in front of them.",
    "electrician":"Homeowners and contractors search online for licensed electricians — a professional site builds that trust instantly.",
    "contractor": "Showing off past projects online is one of the strongest ways to win new bids before you even pick up the phone.",
    "retail":     "Even a simple site with your hours, location, and product highlights can bring foot traffic you'd otherwise miss.",
    "landscaping":"Before-and-after photos on a site are incredibly persuasive for homeowners shopping for landscaping services.",
    "cleaning":   "Trust matters a lot for home cleaning. A professional site with reviews and pricing removes hesitation right away.",
    "auto":       "Car owners often search for shops by neighborhood and reviews. A site helps you show up and stand out.",
    "gym":        "People want to see class schedules, pricing, and photos before committing to a gym. A site answers all of that.",
    "law":        "A professional site signals credibility, surfaces your practice areas, and makes it easy for clients to reach you.",
    "medical":    "Patients look for providers online before calling. A clear, simple site can be the first step toward a new patient relationship.",
    "dental":     "New patients nearly always check online before booking. A site with your hours, services, and friendly photos builds confidence.",
}

_DEFAULT_SNIPPET = (
    "Most people search online before deciding which local business to call. "
    "A clean, simple website puts your name in front of them at exactly the right moment."
)


def _get_industry_snippet(industry: str) -> str:
    if not industry:
        return _DEFAULT_SNIPPET
    key = industry.lower().strip()
    for k, v in _INDUSTRY_SNIPPETS.items():
        if k in key:
            return v
    return _DEFAULT_SNIPPET


# ---------------------------------------------------------------------------
# Greeting variants
# ---------------------------------------------------------------------------

def _greeting(lead: dict) -> str:
    name = (lead.get("contact_name") or "").strip()
    if name:
        first = name.split()[0]
        return f"Hi {first},"
    return "Hi there,"


# ---------------------------------------------------------------------------
# Main email body generator
# ---------------------------------------------------------------------------

def generate_email_body(lead: dict, settings: dict) -> str:
    business_name   = lead.get("business_name", "your business")
    industry        = lead.get("industry", "")
    location        = lead.get("location", "")
    notes           = lead.get("notes", "")
    your_name       = settings.get("your_name", "")
    your_title      = settings.get("your_title", "Web Designer")
    your_phone      = settings.get("your_phone", "")
    your_website    = settings.get("your_website", "")
    service_blurb   = settings.get("service_blurb", "").strip()
    sender_email    = settings.get("sender_email", "")

    industry_snippet = _get_industry_snippet(industry)
    location_line    = f" in {location}" if location else ""
    greeting         = _greeting(lead)

    if service_blurb:
        service_section = f"<p>{service_blurb}</p>"
    else:
        service_section = """
        <p>
          I specialize in building clean, professional websites for local businesses — 
          simple enough to manage yourself, but polished enough to make a strong first impression. 
          I handle everything: design, copy, mobile optimization, and getting it live. 
          No tech headaches on your end.
        </p>"""

    phone_line = f"<br>📞 {your_phone}" if your_phone else ""
    website_line = f'<br>🌐 <a href="{your_website}" style="color:#4F46E5;">{your_website}</a>' if your_website else ""
    title_line = f"<br><span style='color:#6B7280;'>{your_title}</span>" if your_title else ""

    notes_section = ""
    if notes:
        notes_section = f"""
        <p style="color:#374151;">
          <em>P.S. — {notes}</em>
        </p>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: #f9fafb;
      margin: 0;
      padding: 0;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 32px auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .header {{
      background: linear-gradient(135deg, #4F46E5, #7C3AED);
      padding: 32px 40px;
      color: white;
    }}
    .header h2 {{
      margin: 0 0 4px 0;
      font-size: 22px;
      font-weight: 700;
    }}
    .header p {{
      margin: 0;
      opacity: 0.85;
      font-size: 14px;
    }}
    .body {{
      padding: 36px 40px;
      color: #1f2937;
      font-size: 15px;
      line-height: 1.7;
    }}
    .body p {{
      margin: 0 0 16px 0;
    }}
    .highlight-box {{
      background: #EEF2FF;
      border-left: 4px solid #4F46E5;
      border-radius: 6px;
      padding: 16px 20px;
      margin: 24px 0;
      font-size: 14px;
      color: #3730a3;
    }}
    .cta {{
      display: inline-block;
      background: #4F46E5;
      color: white !important;
      text-decoration: none;
      padding: 12px 28px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 15px;
      margin: 8px 0 24px 0;
    }}
    .footer {{
      border-top: 1px solid #e5e7eb;
      padding: 24px 40px;
      font-size: 13px;
      color: #6b7280;
    }}
    .sig-name {{
      font-weight: 700;
      color: #111827;
      font-size: 15px;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h2>A quick note about {business_name}</h2>
      <p>Personal outreach from {your_name or "a local web designer"}</p>
    </div>
    <div class="body">
      <p>{greeting}</p>

      <p>
        I came across <strong>{business_name}</strong>{location_line} and wanted to reach out 
        personally. I noticed you don't currently have a website — and I thought I'd share 
        a quick thought on why that might be worth changing.
      </p>

      <div class="highlight-box">
        💡 {industry_snippet}
      </div>

      {service_section}

      <p>
        Here's what a site for <strong>{business_name}</strong> could include:
      </p>
      <ul style="margin:0 0 16px 0; padding-left:20px;">
        <li>Your services, hours, and contact info — always up to date</li>
        <li>A professional look that builds trust before the first call</li>
        <li>Google-friendly setup so local customers can find you</li>
        <li>Mobile-optimized so it looks great on any phone</li>
      </ul>

      <p>
        I keep things simple and affordable — and I'd love to put together a quick 
        concept for <strong>{business_name}</strong> if it's something you'd be open to exploring. 
        No pressure at all.
      </p>

      <p>
        If this sounds interesting, feel free to reply to this email or give me a call. 
        I'm happy to answer any questions.
      </p>

      {notes_section}

      <p>Warm regards,</p>
      <p>
        <span class="sig-name">{your_name or "Your Name"}</span>
        {title_line}
        {phone_line}
        {website_line}
        {"<br>" + sender_email if sender_email else ""}
      </p>
    </div>
    <div class="footer">
      You're receiving this because your business appeared in a local search. 
      If you'd prefer not to hear from me, just reply "no thanks" and I'll remove you immediately.
    </div>
  </div>
</body>
</html>"""

    return html
