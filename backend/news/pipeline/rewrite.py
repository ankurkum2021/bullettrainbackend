from __future__ import annotations

import re
from datetime import date

MEDIA_BRIEF_PREFIX = re.compile(r"^Media\s+Brief:\s*", re.IGNORECASE)
MULTISPACE = re.compile(r"\s+")
GENERIC_SUMMARY_MARKERS = (
    "Unofficial one-line pointer",
    "Official NHSRCL release (",
)


def clean_headline(title: str) -> str:
    t = MEDIA_BRIEF_PREFIX.sub("", title).strip()
    return MULTISPACE.sub(" ", t)


def _is_generic_summary(text: str) -> bool:
    return any(m in text for m in GENERIC_SUMMARY_MARKERS)


def normalize_source_name(name: str) -> str:
    lower = (name or "").lower()
    if "nhsrcl" in lower:
        return "NHSRCL"
    if "pib" in lower or "press information" in lower:
        return "PIB"
    if "tender" in lower:
        return "NHSRCL"
    return (name or "Official source").split("—")[0].strip()[:40]


def source_site_label(source_name: str) -> str:
    name = normalize_source_name(source_name)
    if name == "NHSRCL":
        return "nhsrcl.in"
    if name == "PIB":
        return "pib.gov.in"
    return "official source"


def _topic_blurb(headline: str) -> str:
    h = headline.lower()
    if "energis" in h or "ohe" in h or "electrif" in h:
        return (
            "Overhead line equipment (OHE) or substation work on the MAHSR corridor — "
            "a commissioning milestone, not an announced passenger timetable."
        )
    if "traction substation" in h or " tss" in f" {h}":
        return (
            "Power infrastructure for the Mumbai–Ahmedabad bullet train: traction substations "
            "and grid connections are part of systems commissioning ahead of any commercial run."
        )
    if "train" in h and ("making" in h or "trainset" in h or "b28" in h):
        return (
            "Rolling-stock testing for early Gujarat operations stays separate from later "
            "Japanese trainset deliveries NHSRCL has cited for the wider corridor."
        )
    if "tunnel" in h or "viaduct" in h or "bridge" in h or "portal beam" in h:
        return (
            "Civil works on viaducts, bridges, or tunnels — physical progress on the alignment; "
            "opening dates remain subject to NHSRCL announcement."
        )
    if "station" in h and ("civil" in h or "superstructure" in h or "campus" in h):
        return (
            "Station or urban-planning activity linked to HSR stops — construction or outreach, "
            "not a published fare or schedule."
        )
    if "sabarmati" in h or "depot" in h or "yard" in h:
        return (
            "Terminal or depot infrastructure at the northern end of the 508 km corridor — "
            "depot readiness is not the same as a passenger launch date."
        )
    if "signalling" in h or "telecom" in h or "tender" in h:
        return (
            "Systems or procurement signal on the corridor — useful for tracking commissioning "
            "prepareness, not a confirmed in-service date."
        )
    if "physical progress" in h or "ministry" in h or "pib" in h:
        return (
            "Government-reported physical progress on MAHSR — check the original release for "
            "percentages; this site does not invent project statistics."
        )
    return (
        "Construction or policy update on India's Mumbai–Ahmedabad high-speed rail programme. "
        "Passenger service dates are not confirmed unless NHSRCL publishes them."
    )


def write_feed_teaser(headline: str) -> str:
    """One short line for home / list cards (~25 words)."""
    clean = clean_headline(headline)
    if "energis" in clean.lower() and "surat" in clean.lower():
        return (
            "Surat–Bilimora section OHE energisation — commissioning step on the first Gujarat stretch."
        )
    if len(clean) <= 100:
        return clean
    short = clean[:97].rsplit(" ", 1)[0]
    return f"{short}…"


def write_card_summary(headline: str) -> str:
    """~2 sentences for list view."""
    clean = clean_headline(headline)
    return f"{clean} {_topic_blurb(clean)}"


def write_article_body(headline: str, published_on: date, source_site: str) -> str:
    """Full on-site article (SEO, no external wall)."""
    clean = clean_headline(headline)
    when = f"{published_on.day} {published_on.strftime('%B %Y')}"

    p1 = (
        f"On {when}, NHSRCL issued an update on the Mumbai–Ahmedabad High Speed Rail (MAHSR) "
        f"programme: {clean}."
    )
    p2 = _topic_blurb(clean)
    p3 = (
        f"This page is an unofficial summary for bullet train station readers. "
        f"Primary source: {source_site}. We do not publish fares, timetables, or opening dates "
        f"that NHSRCL has not announced."
    )
    return "\n\n".join((p1, p2, p3))


def rewrite_article_fields(*, title: str, summary: str, published_on: date, source_name: str) -> dict:
    headline = clean_headline(title)
    site = source_site_label(source_name)
    out = {
        "title": headline,
        "teaser": write_feed_teaser(headline),
        "summary": write_card_summary(headline) if _is_generic_summary(summary) else summary.strip(),
        "body": write_article_body(headline, published_on, site),
        "source_name": normalize_source_name(source_name),
    }
    if _is_generic_summary(summary) or len(out["summary"]) > 320:
        out["summary"] = write_card_summary(headline)
    return out