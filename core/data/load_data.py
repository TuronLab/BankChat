import json
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Optional
import unicodedata
import re

from core.session_manager.models import Client


class BaseDataLoader(ABC):
    """
    Abstract base class for data loaders.

    This class defines the interface that all concrete data loaders must implement,
    allowing easy replacement of the underlying data source (JSON, database, API, etc.).
    """

    @abstractmethod
    def _dump_data_to_client_object(self, client_data: dict):
        pass

    @staticmethod
    @abstractmethod
    def load_all(data_path: Path) -> List[Client]:
        """
        Load all records from the data source.

        Returns:
            List[Dict]: A list of all customer records.
        """
        pass

    @abstractmethod
    def find_customer(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        iban: Optional[str] = None,
    ) -> Optional[Client]:
        """
        Find a customer using at least two identifiers.

        Args:
            name (Optional[str]): Customer full name.
            phone (Optional[str]): Customer phone number.
            iban (Optional[str]): Customer IBAN.

        Returns:
            Optional[Dict]: The matched customer record or None if not found.

        Raises:
            ValueError: If fewer than two identifiers are provided.
        """
        pass


class JSONCustomerDataLoader(BaseDataLoader):
    """
    Concrete implementation of BaseDataLoader for JSON-like in-memory data.

    Includes preprocessing for:
    - Name normalization (case, accents, order)
    - Phone normalization (with/without country prefix)
    - IBAN normalization
    """

    def __init__(self, data_path: Path):
        """
        Initialize the data loader.

        Args:
            data (List[Dict]): List of customer records.
        """
        self.data = self.load_all(data_path)

    @staticmethod
    def _dump_data_to_client_object(client_data: dict):
        return Client(
            client_name=client_data.get("name"),
            phone=client_data.get("phone"),
            mentioned_iban=None,
            type_client=client_data.get("type_client"),
            client_data=client_data
        )

    def load_all(self, data_path: Path) -> List[Client]:
        """
        Return all customer records.

        Returns:
            List[Dict]: All customers.
        """
        data = []

        with data_path.open("r", encoding="utf-8-sig") as f:
            data = [self._dump_data_to_client_object(l) for l in json.load(f)]

        return data

    def find_customer(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        iban: Optional[str] = None,
    ) -> Optional[Client]:
        """
        Find a customer requiring at least two matching fields.

        Matching is tolerant to:
        - Name order and accents
        - Phone format and country prefix
        - IBAN formatting

        Args:
            name (Optional[str]): Customer name.
            phone (Optional[str]): Phone number.
            iban (Optional[str]): IBAN.

        Returns:
            Optional[Client]: Matching customer or None.

        Raises:
            ValueError: If fewer than two fields are provided.
        """
        provided_fields = [name, phone, iban]
        if sum(field is not None for field in provided_fields) < 2:
            raise ValueError("At least two fields must be provided for search.")

        normalized_name = self._normalize_name(name) if name else None
        normalized_phone = self._normalize_phone(phone) if phone else None
        normalized_iban = self._normalize_iban(iban) if iban else None

        for customer in self.data:
            matches = 0

            # Name matching
            if normalized_name:
                customer_name = self._normalize_name(customer.client_name)
                if customer_name == normalized_name:
                    matches += 1

            # Phone matching
            if normalized_phone:
                customer_phone = self._normalize_phone(customer.phone)
                if customer_phone == phone or self._normalize_phone(phone) == self._normalize_phone(customer_phone):
                    matches += 1

            # IBAN matching
            mentioned_iban = None
            if normalized_iban:
                for acc in customer.client_data.get("accounts", []):
                    customer_iban = self._normalize_iban(acc.get("iban"))
                    if customer_iban == normalized_iban:
                        mentioned_iban = acc.get("iban")
                        matches += 1
                        break

            if matches >= 2:
                client_found = deepcopy(customer)
                client_found.mentioned_iban = mentioned_iban
                return client_found

        return None

    # ---------- Normalization Helpers ----------

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize a name by:
        - Lowercasing
        - Removing accents
        - Ignoring order of words

        Args:
            name (str): Raw name.

        Returns:
            str: Normalized name.
        """
        name = name.lower()

        # Remove accents
        name = ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )

        # Split, sort to make it non-order-sensitive, and rejoin
        tokens = sorted(name.split())
        return " ".join(tokens)

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """
        Normalize phone numbers by removing the country prefixes.

        Args:
            phone (str): Raw phone.

        Returns:
            str: Normalized phone.
        """
        prefixes_list = [
            "+1", "+52", "+55", "+54", "+57", "+56", "+58", "+51", "+593", "+53", "+591", "+506", "+507", "+598",
            "+34", "+49", "+33", "+39", "+44", "+7", "+380", "+48", "+40", "+31", "+32", "+30", "+351", "+46", "+47",
            "+86", "+91", "+81", "+82", "+62", "+90", "+63", "+66", "+84", "+972", "+60", "+65", "+92", "+880", "+966",
            "+20", "+27", "+234", "+254", "+212", "+213", "+256", "+233", "+237", "+225", "+221", "+255", "+249",
            "+218", "+216", "+61", "+64", "+679", "+675", "+676", "+98", "+964", "+962", "+961", "+965", "+971",
            "+968", "+974", "+973", "+967" ]

        prefix_regex = re.compile(
            r'^(' + '|'.join(re.escape(p) for p in sorted(prefixes_list, key=len, reverse=True)) + r')'
        )
        return prefix_regex.sub('', phone, count=1)

    @staticmethod
    def _normalize_iban(iban: str) -> str:
        """
        Normalize IBAN by removing spaces and uppercasing.

        Args:
            iban (str): Raw IBAN.

        Returns:
            str: Normalized IBAN.
        """
        return iban.replace(" ", "").upper()