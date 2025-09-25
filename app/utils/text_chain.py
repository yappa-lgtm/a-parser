from typing import Callable
import re

ADDRESS_COMPONENTS_LIST = ["вул", "буд", "область", "м", "район", "кв", "c"]

SHORT_ADMINISTRATIVE_BUILDING_DICT = {
    "товариство з обмеженою відповідальністю": "ТОВ",
    "приватне підприємство": "ПП",
    "фізична особа-підприємець": "ФОП",
    "державне підприємство": "ДП",
    "акціонерне товариство": "АТ",
    "публічне акціонерне товариство": "ПАТ",
    "закрите акціонерне товариство": "ЗАТ",
    "командитне товариство": "КТ",
    "повне товариство": "ПТ",
    "обслуговуючий кооператив": "ОК",
    "об'єднання співвласників багатоквартирного будинку": "ОСББ",
}

LATIN_TO_UKRAINIAN_DICT = {
    "i": "і",
    "I": "І",
    "e": "є",
    "E": "Є",
}


class TextChain:
    def __init__(self, value: any = ""):
        self.value = value

    def apply(self, func: Callable, *args, **kwargs):
        if self.value is not None:
            self.value = func(self.value, *args, **kwargs)
        return self

    def capitalize_each_word(self):
        return self.apply(
            lambda text: (
                " ".join(w.capitalize() for w in text.split())
                if isinstance(text, str)
                else text
            )
        )

    def normalize_address(self):
        def _normalize(text):
            if not isinstance(text, str):
                return text

            for keyword in ADDRESS_COMPONENTS_LIST:
                pattern = rf"\b{keyword}(\.)?(\s|$)"
                text = re.sub(
                    pattern,
                    lambda m: keyword.lower() + (m.group(1) or "") + m.group(2),
                    text,
                    flags=re.IGNORECASE,
                )
            return text

        return self.apply(_normalize)

    def clean_whitespace(self):
        def _clean(text):
            if not isinstance(text, str):
                return text

            return re.sub(r"\s+", " ", text).strip()

        return self.apply(_clean)

    def normalize_document_number(self):
        def _normalize(text):
            if not isinstance(text, str):
                return text

            clean = text.strip()
            if re.match(r"^[A-ZА-ЯІЇЄ]{2}", clean, re.IGNORECASE):
                return f"{clean[:2]}\u00a0{clean[2:]}"
            return clean

        return self.apply(_normalize)

    def normalize_ukrainian_chars(self):
        def _normalize(text):
            if not isinstance(text, str):
                return text

            result = text
            for latin, cyrillic in LATIN_TO_UKRAINIAN_DICT.items():
                result = result.replace(latin, cyrillic)

            return result

        return self.apply(_normalize)

    def shorten_organization_name(self):
        def _shorten(text):
            if not isinstance(text, str):
                return text

            result = text
            for full_name, short_name in SHORT_ADMINISTRATIVE_BUILDING_DICT.items():
                pattern = rf"\b{re.escape(full_name)}\b"
                result = re.sub(pattern, short_name, result, flags=re.IGNORECASE)

            return result

        return self.apply(_shorten)

    def format_connected_date(self):
        def _format(text):
            if not isinstance(text, str):
                return text

            if re.match(r"^\d{8}", text.strip()):
                date_str = text.strip()
                day = date_str[:2]
                month = date_str[2:4]
                year = date_str[4:8]
                return f"{day}.{month}.{year}"

            return text

        return self.apply(_format)

    def normalize_quotes(self):
        def _normalize(text):
            if not isinstance(text, str):
                return text

            normalized = re.sub(r'[«»"]', '"', text)

            result = ""
            quote_stack = []

            for i, char in enumerate(normalized):
                if char == '"':
                    if len(quote_stack) == 0:
                        result += "«"
                        quote_stack.append("«")
                    elif len(quote_stack) == 1:
                        next_quote_index = normalized.find('"', i + 1)
                        if next_quote_index != -1:
                            result += "«"
                            quote_stack.append("«")
                        else:
                            result += "»"
                            quote_stack.pop()
                    else:
                        result += "»"
                        quote_stack.pop()
                else:
                    result += char

            return result

        return self.apply(_normalize)

    def get(self):
        return self.value
