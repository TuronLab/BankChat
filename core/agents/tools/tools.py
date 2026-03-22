import json
from typing import Literal

from core.session_manager.session import Session


def get_account_balance(session: Session, iban: str) -> str:
    """
    Retrieves the balance and currency for a specific IBAN.

    Args:
        session (Session): The current user session.
        iban (str): The IBAN to check.
    """
    accounts = session.client.client_data.get("accounts", [])
    for acc in accounts:
        if acc["iban"] == iban:
            return f"Balance for {iban}: {acc['balance']} {acc['currency']}"
    return "Error: IBAN not found in client records."


def get_total_liquidity(session: Session) -> str:
    """
    Calculates the total balance across all accounts for the user.
    """
    accounts = session.client.client_data.get("accounts", [])
    if not accounts:
        return "No accounts found for this client."

    total = sum(acc["balance"] for acc in accounts)
    currency = accounts[0]["currency"]  # Assuming primary currency
    return f"Total combined balance: {total} {currency}"


def get_client_profile_summary(session: Session) -> str:
    """
    Retrieves the customer's tier, risk level, and recent interaction history.
    Use this to personalize the greeting or context.
    """
    data = session.client.client_data
    summary = {
        "tier": data.get("customer_type"),
        "risk": data.get("risk_level"),
        "recent_topic": data.get("history")[0]["topic"] if data.get("history") else "None"
    }
    return json.dumps(summary)


def get_expert_contact_details(
        session: Session,
        domain: Literal[
            "yacht_insurance", "wealth_management", "estate_planning", "corporate_accounts", "general_support"]
) -> str:
    """
    Retrieves high-touch contact information. Use this when the client's intent is clear.

    Args:
        session (Session): Injected session data.
        domain (str): The specific department requested.
    """
    client_type = session.client.client_data.get("customer_type", "regular")

    # Premium White-Glove Database
    premium_contacts = {
        "yacht_insurance": "Direct Line to Marine Specialist: +49 89 1234 567 (24/7 Priority)",
        "wealth_management": "Your Private Banker, Marc Schmidt: +49 89 1234 568",
        "estate_planning": "Luxury Estates Division: bespoke.estates@firm.com",
        "corporate_accounts": "Corporate Desk: +49 89 1234 569",
        "general_support": "Dedicated Concierge: +49 89 1234 000"
    }

    # Standard Database
    standard_contacts = {
        "general_support": "Customer Service: 0800 555 444 (9:00 - 17:00)",
        "wealth_management": "Please visit your local branch for investment inquiries."
    }

    if client_type == "premium":
        return premium_contacts.get(domain, premium_contacts["general_support"])

    return standard_contacts.get(domain, standard_contacts["general_support"])


def get_client_financial_overview(session: Session) -> str:
    """
    Returns all accounts, balances, and the client's tier.
    Use this at the start of a complex inquiry to understand the client's holdings.
    """
    data = session.client.client_data
    return json.dumps({
        "name": data.get("name"),
        "tier": data.get("customer_type"),
        "accounts": data.get("accounts"),
        "risk_level": data.get("risk_level")
    })
