from typing import Callable, Optional
import re

RESERVED_WORD_LIST = ["ВМД", "ТЗ"]

ADDRESS_COMPONENTS_LIST = [
    "вул",
    "буд",
    "область",
    "м",
    "район",
    "районів",
    "кв",
    "з",
    "c",
    "р-н",
    "с",
    "обл",
    "та",
]

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

COLORS_DICT = {
    "СІРИЙ": "сірого",
    "ЧЕРВОНИЙ": "червоного",
    "СИНІЙ": "синього",
    "ЧОРНИЙ": "чорного",
    "БІЛИЙ": "білого",
    "ЗЕЛЕНИЙ": "зеленого",
    "ЖОВТИЙ": "жовтого",
    "КОРИЧНЕВИЙ": "коричневого",
    "ФІОЛЕТОВИЙ": "фіолетового",
    "РОЖЕВИЙ": "рожевого",
    "ОРАНЖЕВИЙ": "оранжевого",
    "БЕЖЕВИЙ": "бежевого",
    "ЗОЛОТИЙ": "золотого",
    "СРІБНИЙ": "срібного",
    "ТЕМНО-СІРИЙ": "темно-сірого",
    "СВІТЛО-СІРИЙ": "світло-сірого",
    "ТЕМНО-СИНІЙ": "темно-синього",
    "СВІТЛО-СИНІЙ": "світло-синього",
    "ТЕМНО-ЗЕЛЕНИЙ": "темно-зеленого",
    "СВІТЛО-ЗЕЛЕНИЙ": "світло-зеленого",
    "БОРДОВИЙ": "бордового",
    "МЕТАЛІК": "металік",
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

            words = re.split(r"(\s|,|[.])", text)

            normalized_words = []
            for w in words:
                if w.lower() in ADDRESS_COMPONENTS_LIST:
                    normalized_words.append(w.lower())
                else:
                    normalized_words.append(w.capitalize())

            return "".join(normalized_words)

        return self.apply(_normalize)

    def normalize_reserved_words(self):
        def _normalize(text):
            if not isinstance(text, str):
                return text

            words = re.split(r"(\s|,|[.])", text)

            normalized_words = []
            for w in words:
                if w.upper() in RESERVED_WORD_LIST:
                    normalized_words.append(w.upper())
                else:
                    normalized_words.append(w.lower())

            return "".join(normalized_words)

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

            clean = text.strip().replace(" ", "")

            match = re.match(
                r"^([A-ZА-ЯІЇЄ]{2})(\d+)([A-ZА-ЯІЇЄ]{0,2})$", clean, re.IGNORECASE
            )
            if match:
                part1, digits, part2 = match.groups()
                if part2:
                    return f"{part1}\u00a0{digits}\u00a0{part2}"
                return f"{part1}\u00a0{digits}"
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

    def normalize_color(self):
        def _normalize(text):
            if not isinstance(text, str):
                return text

            return COLORS_DICT[text] or text.lower()

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

    def cut_between(self, start: Optional[str] = None, end: Optional[str] = None):
        def cut(text):
            if not isinstance(text, str):
                return text

            def is_in(pointer: str):
                return pointer in text

            if start and end:
                if not is_in(start) and not is_in(end):
                    return text

                pattern = rf"{re.escape(start)}(.*?){re.escape(end)}"
                match = re.search(pattern, text)
                return match.group(1).strip() if match else None
            elif start:
                if not is_in(start):
                    return text

                pattern = rf"{re.escape(start)}(.*)"
                match = re.search(pattern, text)
                return match.group(1).strip() if match else None
            elif end:
                if not is_in(end):
                    return text

                pattern = rf"(.*?)" + re.escape(end)
                match = re.search(pattern, text)
                return match.group(1).strip() if match else text
            else:
                return text

        return self.apply(cut)

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

    def shorten_full_name(self):
        def _shorten(text):
            if not isinstance(text, str):
                return text

            splited = text.split(" ")
            return f"{splited[0]} {splited[1][0]}.{splited[2][0]}."

        return self.apply(_shorten)

    def get(self):
        return self.value
