from app.models.schemas import OutreachRequest, OutreachResponse

OUTREACH_DISCLAIMER = (
    "This draft uses only the candidate fields you submitted and your context. "
    "It was written from a template, not a live language model. "
    "Read it before sending and remove anything that is not accurate."
)


def generate_outreach(request: OutreachRequest) -> OutreachResponse:
    """Build a short note from known fields.

    Swap this for LLMClient.complete when outreach should vary more. The model
    prompt should be limited to the same fields so it does not invent biography.
    """
    candidate = request.candidate
    first_name = candidate.name.split()[0]
    opening = _opening(request.tone, first_name, candidate.role, candidate.company)
    paragraphs = [opening, f'My goal: "{request.query}"']

    if request.background:
        paragraphs.append(f"A bit of context on me: {request.background}")
    if request.interests:
        paragraphs.append(f"Topics I care about right now: {request.interests}")

    evidence = candidate.match_reasons[0]
    paragraphs.append(f"I thought your background might be relevant because: {evidence}")
    paragraphs.append("Would you be open to a 20-minute conversation in the next few weeks?")
    paragraphs.append("Thank you,\n[Your name]")

    return OutreachResponse(
        candidate_name=candidate.name,
        subject=f"Learning from your work at {candidate.company}",
        message="\n\n".join(paragraphs),
        result_source="mock",
        disclaimer=OUTREACH_DISCLAIMER,
    )


def _opening(tone: str, first_name: str, role: str, company: str) -> str:
    if tone == "direct":
        return (
            f"Hi {first_name} — I'm reaching out because your work as {role} at {company} "
            "lines up with a conversation I'm hoping to have."
        )
    if tone == "curious":
        return (
            f"Hi {first_name}, I came across your work as {role} at {company} and wanted "
            "to ask how you think about the problems on your team."
        )
    return (
        f"Hi {first_name}, I hope you're doing well. I'm trying to learn from people "
        f"doing work like yours as {role} at {company}."
    )
