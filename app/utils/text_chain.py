from typing import Callable
import re

ADDRESS_COMPONENTS_LIST = ["вул", "буд", "область", "м", "район", "кв", "c"]


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

    def get(self):
        return self.value
