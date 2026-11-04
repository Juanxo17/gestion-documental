from datetime import UTC, datetime


def ahora_utc() -> datetime:
    ahora = datetime.now(UTC)
    return ahora.replace(microsecond=ahora.microsecond // 1000 * 1000)
