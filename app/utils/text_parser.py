def parse_field(text: str, key: str, next_keys: list[str]) -> str | None:
    lines = text.split("\n")

    try:
        key_index = lines.index(key)
    except ValueError:
        return None

    if key_index + 1 >= len(lines):
        return None

    next_line = lines[key_index + 1]

    if next_line in next_keys:
        return None

    result_lines = []

    for i in range(key_index + 1, len(lines)):
        current_line = lines[i]

        if current_line in next_keys:
            break

        result_lines.append(current_line)

    return "\n".join(result_lines) if result_lines else None
