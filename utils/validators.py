"""Валидация пользовательского ввода."""

import re


def validate_positive_number(text: str) -> float | None:
    """Возвращает число ≥ 0 или None при невалидном вводе."""
    text = text.strip().replace(",", ".")
    try:
        value = float(text)
        if value < 0:
            return None
        return value
    except ValueError:
        return None


def validate_positive_integer(text: str) -> int | None:
    """Возвращает целое число ≥ 0 или None."""
    value = validate_positive_number(text)
    if value is None:
        return None
    return int(value)


def validate_phone(text: str) -> str | None:
    """
    Нормализует российский номер телефона.
    Принимает форматы: 89991234567, +79991234567, 8(999)123-45-67 и т.д.
    Возвращает строку вида +7 (999) 123-45-67 или None.
    """
    digits = re.sub(r"\D", "", text)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    else:
        return None

    if not digits.startswith("7"):
        return None

    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def sanitize_text(text: str, max_length: int = 200) -> str:
    """Очищает текстовый ввод от потенциально опасных символов."""
    text = text.strip()
    text = re.sub(r"[<>\"']", "", text)
    return text[:max_length]
