import pandas as pd
from io import BytesIO


class XlsParser:
    def __init__(self, content: bytes):
        self.df = pd.read_excel(BytesIO(content), sheet_name=0, header=None)

    def cell(self, row: int, col: int) -> str | None:
        try:
            value = self.df.iloc[row, col]
            if pd.isna(value):
                return None
            return str(value)
        except IndexError:
            return None
