import pytest
from pathlib import Path
import tempfile
import json

from core.data.load_data import JSONCustomerDataLoader


# ---------- Fixtures ----------

@pytest.fixture
def sample_data_file():
    data = [
        {
            "name": "John Doe",
            "phone": "+34123456789",
            "accounts": [{"iban": "ES91 2100 0418 4502 0005 1332"}],
        },
        {
            "name": "María García",
            "phone": "+34987654321",
            "accounts": [{"iban": "ES76 1234 5678 9012 3456 7890"}],
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        for record in data:
            tmp.write(json.dumps(record) + "\n")
        tmp_path = Path(tmp.name)

    yield tmp_path

    tmp_path.unlink()


@pytest.fixture
def loader(sample_data_file):
    return JSONCustomerDataLoader(sample_data_file)


# ---------- Tests for load_all ----------

def test_load_all_reads_all_records(sample_data_file):
    loader = JSONCustomerDataLoader(sample_data_file)
    assert len(loader.data) == 2


# ---------- Tests for validation ----------

def test_find_customer_requires_two_fields(loader):
    with pytest.raises(ValueError):
        loader.find_customer(name="John Doe")


# ---------- Matching tests ----------

def test_find_customer_by_name_and_phone(loader):
    result = loader.find_customer(
        name="John Doe",
        phone="123456789"  # without prefix
    )
    assert result is not None
    assert result["name"] == "John Doe"


def test_find_customer_name_order_irrelevant(loader):
    result = loader.find_customer(
        name="Doe John",
        phone="123456789"
    )
    assert result is not None
    assert result["name"] == "John Doe"


def test_find_customer_name_with_accents(loader):
    result = loader.find_customer(
        name="Maria Garcia",  # no accent
        phone="987654321"
    )
    assert result is not None
    assert result["name"] == "María García"


def test_find_customer_by_phone_and_iban(loader):
    result = loader.find_customer(
        phone="987654321",
        iban="ES7612345678901234567890"
    )
    assert result is not None
    assert result["name"] == "María García"


def test_find_customer_iban_formatting(loader):
    result = loader.find_customer(
        phone="987654321",
        iban="ES76 1234 5678 9012 3456 7890"  # with spaces
    )
    assert result is not None
    assert result["name"] == "María García"


def test_find_customer_no_match(loader):
    result = loader.find_customer(
        name="Unknown Person",
        phone="000000000"
    )
    assert result is None


# ---------- Normalization helpers ----------

def test_normalize_name():
    normalized = JSONCustomerDataLoader._normalize_name("García María")
    assert normalized == "garcia maria"


def test_normalize_phone_removes_prefix():
    normalized = JSONCustomerDataLoader._normalize_phone("+34123456789")
    assert normalized == "123456789"


def test_normalize_iban():
    normalized = JSONCustomerDataLoader._normalize_iban("es91 2100 0418 4502 0005 1332")
    assert normalized == "ES9121000418450200051332"