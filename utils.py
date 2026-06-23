def clean_text(text: str) -> str:
    if not text:
        return ""

    return " ".join(text.strip().split())


def is_command(text: str) -> bool:
    if not text:
        return False

    return text.startswith("/")