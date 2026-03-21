import pytest
from pathlib import Path

from core.session_manager.models import Client
from core.data.load_data import JSONCustomerDataLoader


# ---------- Helpers ----------

def write_jsonl(tmp_path: Path, lines: str) -> Path:
    file = tmp_path / "data.jsonl"
    file.write_text(lines, encoding="utf-8")
    return file


# ---------- Tests ----------

def test_load_all(tmp_path):
    file = write_jsonl(
        tmp_path,
        '{"name": "John Doe", "phone": "+34123456789", "type_client": "retail"}\n'
        '{"name": "Jane Doe", "phone": "+44123456789", "type_client": "business"}\n'
    )

    loader = JSONCustomerDataLoader(file)
    data = loader.load_all(file)

    assert len(data) == 2
    assert all(isinstance(c, Client) for c in data)

    assert data[0].client_name == "John Doe"
    assert data[1].client_name == "Jane Doe"


def test_find_customer_by_name_and_phone(tmp_path):
    file = write_jsonl(
        tmp_path,
        '{"name": "John Doe", "phone": "+34123456789", "type_client": "retail", "accounts": []}\n'
    )

    loader = JSONCustomerDataLoader(file)

    result = loader.find_customer(name="John Doe", phone="+34123456789")

    assert result is not None
    assert isinstance(result, Client)
    assert result.client_name == "John Doe"


def test_find_customer_name_normalization(tmp_path):
    file = write_jsonl(
        tmp_path,
        '{"name": "José García", "phone": "+34111111111", "type_client": "retail", "accounts": []}\n'
    )

    loader = JSONCustomerDataLoader(file)

    result = loader.find_customer(
        name="Garcia Jose",
        phone="+34111111111"
    )

    assert result is not None
    assert result.client_name == "José García"


def test_find_customer_phone_normalization(tmp_path):
    file = write_jsonl(
        tmp_path,
        '{"name": "John Doe", "phone": "+34123456789", "type_client": "retail", "accounts": []}\n'
    )

    loader = JSONCustomerDataLoader(file)

    result = loader.find_customer(
        name="John Doe",
        phone="123456789"
    )

    assert result is not None


def test_find_customer_by_iban(tmp_path):
    file = write_jsonl(
        tmp_path,
        '{"name": "John Doe", "phone": "+34123456789", "type_client": "retail", '
        '"accounts": [{"iban": "ES12 3456 7890"}]}\n'
    )

    loader = JSONCustomerDataLoader(file)

    result = loader.find_customer(
        name="John Doe",
        iban="ES1234567890"
    )

    assert result is not None
    assert result.mentioned_iban == "ES12 3456 7890"


def test_find_customer_requires_two_fields(tmp_path):
    file = write_jsonl(
        tmp_path,
        '{"name": "John Doe", "phone": "+34123456789", "type_client": "retail", "accounts": []}\n'
    )

    loader = JSONCustomerDataLoader(file)

    with pytest.raises(ValueError):
        loader.find_customer(name="John Doe")