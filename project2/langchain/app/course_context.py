
from app.extract import codes_in


def resolve_course(
    question: str,
    history: list[dict]
) -> str | None:

    # Explicit course code in current question
    codes = list(dict.fromkeys(codes_in(question)))

    if len(codes) == 1:
        return codes[0]

    if len(codes) > 1:
        return None

    # Search previous student messages only
    for message in reversed(history[-12:]):

        if message.get("role") != "user":
            continue

        previous_codes = list(
            dict.fromkeys(
                codes_in(message.get("content", ""))
            )
        )

        if len(previous_codes) == 1:
            return previous_codes[0]

        if len(previous_codes) > 1:
            return None

    return None
