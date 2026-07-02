def to_cents(amount: float | int) -> int:
    return int(round(amount * 100))


def to_ksh(cents: int) -> float:
    return round(cents / 100, 2)


def to_cents_safe(amount: float | int | None) -> int:
    if amount is None:
        return 0
    return to_cents(amount)
