from app.models.schemas import CandidateSeed

MOCK_PROFILES: list[CandidateSeed] = [
    CandidateSeed(
        id="jordan-hale",
        name="Jordan Hale",
        role="Product Manager",
        company="Northstar Analytics",
        relevant_experience=(
            "Jordan moved from a data science role into product management and now owns "
            "an AI forecasting workspace used by operations teams. The team bio highlights "
            "that transition and Jordan's work pairing analysts with product discovery."
        ),
        role_tags=["product manager"],
        focus_areas=["ai", "product management", "data science"],
        source_urls=["https://example.com/meetmind-demo/jordan-hale"],
        transition_from="data science",
        transition_to="product management",
    ),
    CandidateSeed(
        id="avery-kim",
        name="Avery Kim",
        role="Product Lead",
        company="Kindling Labs",
        relevant_experience=(
            "Avery was a data analyst before becoming product lead for Kindling's AI tools "
            "that draft customer-support replies. The company about page describes that "
            "career change and the support-automation launch."
        ),
        role_tags=["product lead"],
        focus_areas=["ai", "product management", "data science"],
        source_urls=["https://example.com/meetmind-demo/avery-kim"],
        transition_from="data science",
        transition_to="product management",
    ),
    CandidateSeed(
        id="priya-shah",
        name="Priya Shah",
        role="Product Manager, Applied AI",
        company="Harbor Payments",
        relevant_experience=(
            "Priya is the product manager for an AI assistant that helps support agents "
            "resolve card-payment disputes. Harbor's team page describes her earlier work "
            "on merchant onboarding."
        ),
        role_tags=["product manager"],
        focus_areas=["ai", "product management", "payments", "fintech"],
        source_urls=["https://example.com/meetmind-demo/priya-shah"],
    ),
    CandidateSeed(
        id="maya-chen",
        name="Maya Chen",
        role="Product Manager",
        company="Lumen Ledger",
        relevant_experience=(
            "Maya leads the AI assistant that helps small businesses categorize expenses "
            "and draft invoices. She previously shipped onboarding for a finance product "
            "and writes about practical AI product discovery."
        ),
        role_tags=["product manager"],
        focus_areas=["ai", "product management", "fintech"],
        source_urls=["https://example.com/meetmind-demo/maya-chen"],
    ),
    CandidateSeed(
        id="elena-vasquez",
        name="Elena Vasquez",
        role="Senior Product Manager",
        company="Copperline",
        relevant_experience=(
            "Elena leads AI tooling for clinic scheduling and patient follow-up. "
            "Copperline's conference bio credits her with launching the intake assistant "
            "and coordinating clinicians and engineers."
        ),
        role_tags=["product manager"],
        focus_areas=["ai", "product management", "healthcare"],
        source_urls=["https://example.com/meetmind-demo/elena-vasquez"],
    ),
    CandidateSeed(
        id="noah-patel",
        name="Noah Patel",
        role="Product Manager",
        company="Paperplane",
        relevant_experience=(
            "Noah is a product manager on Paperplane's AI code-review feature for "
            "developer teams. A conference speaker page summarizes his work on review "
            "workflows and developer experience."
        ),
        role_tags=["product manager"],
        focus_areas=["ai", "product management", "developer tools"],
        source_urls=["https://example.com/meetmind-demo/noah-patel"],
    ),
    CandidateSeed(
        id="sam-okonkwo",
        name="Sam Okonkwo",
        role="Data Science Manager",
        company="Fieldnote",
        relevant_experience=(
            "Sam manages data scientists building species-identification models for a "
            "field-research app. Fieldnote's team page focuses on machine learning "
            "research rather than product management."
        ),
        role_tags=["data science manager"],
        focus_areas=["data science", "machine learning"],
        source_urls=["https://example.com/meetmind-demo/sam-okonkwo"],
    ),
    CandidateSeed(
        id="riley-nguyen",
        name="Riley Nguyen",
        role="Engineering Manager",
        company="Brightroute",
        relevant_experience=(
            "Riley manages engineers on a delivery-routing platform. Brightroute's team "
            "page describes platform reliability work and does not describe a product "
            "management role."
        ),
        role_tags=["engineering manager"],
        focus_areas=["engineering", "logistics"],
        source_urls=["https://example.com/meetmind-demo/riley-nguyen"],
    ),
]

PROFILES_BY_ID = {profile.id: profile for profile in MOCK_PROFILES}
