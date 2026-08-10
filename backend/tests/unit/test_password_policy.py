import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


def test_password_shorter_than_eight_characters_is_rejected():
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password="short")


def test_eight_character_password_is_accepted():
    password = "12345678"

    user = UserCreate(email="user@example.com", password=password)

    assert user.password == password


def test_password_over_seventy_two_utf8_bytes_is_rejected():
    password = "😀" * 19

    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password=password)


def test_normal_valid_password_round_trips_unchanged():
    password = "correct-horse-battery-staple"

    user = UserCreate(email="user@example.com", password=password)

    assert user.password == password
