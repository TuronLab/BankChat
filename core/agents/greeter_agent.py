import os
import re
from typing import Any, Dict

from config import ASSETS_PATH
from core.agents.models import GreeterAgentResponse
from core.data.load_data import BaseDataLoader
from core.session_manager.session import Session
from core.agents.agent_base import AgentWithInferencerBase
from core.utils import read_markdown


class DataExtractorAgent(AgentWithInferencerBase):
    """
    Agent that extracts name, phone, and IBAN from a message.

    Strategy:
    1. Use regex in preprocess.
    2. If any field is missing, fallback to the inferencer
       using structured output (generate_structured).
    """

    NAME_REGEX = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b")
    PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\d{6,14}\b")
    IBAN_REGEX = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")

    def __init__(self, inferencer: Any, database_loader: BaseDataLoader):
        super().__init__(inferencer=inferencer)
        self.database_loader = database_loader

    def try_find_user_data_with_regex(self, message: str) -> Dict[str, Any]:
        """
        Extract available data using regex.
        """
        extracted = {}

        name_match = self.NAME_REGEX.search(message)
        phone_match = self.PHONE_REGEX.search(message)
        iban_match = self.IBAN_REGEX.search(message)

        if name_match:
            extracted["name"] = name_match.group(1)

        if phone_match:
            extracted["phone"] = phone_match.group(0)

        if iban_match:
            extracted["iban"] = iban_match.group(0)

        return {
            "original_message": message,
            "extracted": extracted,
        }

    def step(self, message: str, session: Session) -> GreeterAgentResponse:
        """
        Extract structured data.

        - If regex finds everything → return immediately.
        - Otherwise → call generate_structured for missing fields.
        """
        processed = self.try_find_user_data_with_regex(message)
        extracted = processed["extracted"]

        # If everything is already found, return early
        customer = self.database_loader.find_customer(
            name=extracted.get("name"),
            phone=extracted.get("phone"),
            iban=extracted.get("iban")
        )
        if customer is not None:
            return GreeterAgentResponse(
                client=customer,
                message=read_markdown(os.path.join(ASSETS_PATH, "greeter_agent", "successful_logging_message.md"))
            )

        # Define the expected schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"]},
                "phone": {"type": ["string", "null"]},
                "iban": {"type": ["string", "null"]},
            },
            "required": ["name", "phone", "iban"],
            "additionalProperties": False,
        }

        # Call structured inference
        structured_output = self.inferencer.generate_structured(
            [
                {
                    "role": "user",
                    "content": f"""
Extract the following information from this message:

Message:
{processed["original_message"]}
""",
                }
            ],
            schema=schema,
        )

        # If we have found information enough for the identification of the client
        if sum(bool(structured_output.get(k)) for k in ("name", "phone", "iban")) >= 2:
            customer = self.database_loader.find_customer(name=structured_output.get("name"), phone=structured_output.get("phone"), iban=structured_output.get("iban"))
            # If we have found him in the database
            if customer is not None:
                session.client = customer
                return GreeterAgentResponse(
                    client=customer,
                    message=read_markdown(os.path.join(ASSETS_PATH, "greeter_agent", "successful_logging_message.md"))
                )
            else:  # If we haven't found him, we return a message with more detail about the name found
                user_metadata = " | ".join([structured_output.get(k) for k in ("name", "phone", "iban") if bool(structured_output.get(k))])
                return GreeterAgentResponse(
                    message=read_markdown(
                        os.path.join(ASSETS_PATH, "greeter_agent", "user_not_found_message.md")
                    ).replace("{{USER_DATA}}", user_metadata)
                )

        return GreeterAgentResponse(message=read_markdown(os.path.join(ASSETS_PATH, "greeter_agent", "error_authentication.md")))
