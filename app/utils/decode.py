def decode_text(text_data: any, encoding="utf-16be") -> str:
    if isinstance(text_data, bytes):
        return text_data.decode(encoding, errors="ignore")
    elif isinstance(text_data, str):
        return text_data
    return str(text_data)
