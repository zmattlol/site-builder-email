"""Utilities for generating personalized outreach drafts."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_BENEFITS = [
    "give new customers a clear place to learn about your services",
    "make it easier for people to call, book, or request a quote",
    "help your business look more established when people find you online",
]


INDUSTRY_BENEFITS = {
    "restaurant": [
        "show your menu, hours, and location in one place",
        "make it easier for customers to call in orders or reservations",
        "keep your latest specials and updates easy to find",
    ],
    "contractor": [
        "show recent work and build trust before the first call",
        "make quote requests easier from mobile devices",
        "highlight service areas and the types of jobs you take on",
    ],
    "salon": [
        "show services, pricing, and hours in one easy place",
        "make it easier for clients to book or call directly",
        "share your style, reviews, and photos with new visitors",
    ],
    "medical": [
        "help patients quickly find your services, hours, and contact details",
        "make it easier for people to request appointments",
        "present your practice in a clear and trustworthy way",
    ],
}


def _value(lead: Mapping[str, Any], key: str) -> str:
    raw = lead.get(key, "")
    if raw is None:
        return ""
    return str(raw).strip()


def _benefits_for_lead(lead: Mapping[str, Any]) -> list[str]:
    custom_focus = _value(lead, "benefits_focus")
    if custom_focus:
        parsed = [piece.strip() for piece in custom_focus.split(",") if piece.strip()]
        if parsed:
            return parsed[:3]

    business_type = _value(lead, "business_type").lower()
    for keyword, benefits in INDUSTRY_BENEFITS.items():
        if keyword in business_type:
            return benefits

    return DEFAULT_BENEFITS


def build_email_draft(lead: Mapping[str, Any], sender_name: str = "Your Name") -> dict[str, str]:
    """Create a concise, low-pressure outreach draft for a single business."""
    business_name = _value(lead, "business_name") or "your business"
    contact_name = _value(lead, "contact_name") or business_name
    location = _value(lead, "location")
    google_profile = _value(lead, "google_profile_url")
    offer_summary = _value(lead, "offer_summary") or (
        "build and set up a personalized website that fits your business"
    )
    observed_gap = _value(lead, "observed_gap") or (
        "I could not find a dedicated website linked with your online presence"
    )
    notes = _value(lead, "notes")
    benefits = _benefits_for_lead(lead)

    subject = f"Quick idea for {business_name}'s online presence"

    intro_parts = [f"I was looking at {business_name}"]
    if location:
        intro_parts.append(f"in {location}")
    if google_profile:
        intro_parts.append("and found your Google Business Profile")
    intro = " ".join(intro_parts) + "."

    body_lines = [
        f"Hi {contact_name},",
        "",
        intro,
        observed_gap + ".",
        "",
        f"I help small businesses {offer_summary}, and I thought {business_name} could benefit from having one simple place online that feels polished and personal to your brand.",
        "",
        "A site like that can help:",
    ]

    for benefit in benefits:
        body_lines.append(f"- {benefit}")

    body_lines.extend(
        [
            "",
            "This would not need to be anything overly complicated. The goal would simply be to make it easier for people who already find you online to learn about what you do and take the next step.",
        ]
    )

    if notes:
        body_lines.extend(["", f"A few notes I had while looking at your business: {notes}"])

    body_lines.extend(
        [
            "",
            "If that is something you would be interested in, I would be happy to send over a few ideas for what a simple first version could look like.",
            "",
            f"Best,\n{sender_name}",
        ]
    )

    return {
        "subject": subject,
        "body": "\n".join(body_lines),
    }

