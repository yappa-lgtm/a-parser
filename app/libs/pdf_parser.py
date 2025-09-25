import logging
from io import BytesIO
from typing import Optional

import fitz
import PyPDF4
from PyPDF4.generic import NameObject, ArrayObject
from PyPDF4.pdf import ContentStream
from PyPDF4.utils import b_

from utils.decode import decode_text

logger = logging.getLogger(__name__)


class PdfParser:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content
        self._reset_reader()

    def _reset_reader(self):
        self.buffer = BytesIO(self.content)
        self.reader = PyPDF4.PdfFileReader(self.buffer)
        self.writer = PyPDF4.PdfFileWriter()
        self.total_pages = self.reader.getNumPages()

    def text(self) -> str:
        text_list = []

        for page_num in range(self.total_pages):
            page = self.reader.getPage(page_num)
            page_text = self._extract_page_text(page)
            if page_text:
                text_list.append(page_text)

        return "\n".join(text_list)

    def remove_text(self, remove_list: list[str]) -> "PdfParser":
        if not remove_list:
            return self

        self._process_pages_for_text_removal(remove_list)
        self._rebuild_content_after_changes()
        return self

    def remove_by_operands(self, remove_operands: list[str]) -> "PdfParser":
        if not remove_operands:
            return self

        self._process_pages_for_operand_removal(remove_operands)
        self._rebuild_content_after_changes()
        return self

    def save_to_bytes(self) -> bytes:
        try:
            if self.writer.getNumPages() == 0:
                for page_num in range(self.total_pages):
                    page = self.reader.getPage(page_num)
                    self.writer.addPage(page)

            output_buffer = BytesIO()
            self.writer.write(output_buffer)
            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Помилка при створенні bytes: {e}")
            return self.content

    def get_image_by_index(self, image_index: int) -> Optional[tuple[bytes, str]]:
        try:
            doc = fitz.open("pdf", self.content)
            current_image_count = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    if current_image_count == image_index:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        doc.close()
                        return image_bytes, image_ext

                    current_image_count += 1

            doc.close()
            logger.warning(f"Зображення з індексом {image_index} не знайдено")
            return None

        except Exception as e:
            logger.error(
                f"Помилка при витягуванні зображення з індексом {image_index}: {e}"
            )
            return None

    def _process_pages_for_operand_removal(self, remove_operands: list[str]):
        for page_num in range(self.total_pages):
            page = self.reader.getPage(page_num)

            if "/Contents" not in page:
                self.writer.addPage(page)
                continue

            modified_page = self._remove_operands_from_page(page, remove_operands)
            self.writer.addPage(modified_page)

    def _remove_operands_from_page(self, page, remove_operands: list[str]):
        content_object = page["/Contents"].getObject()

        if isinstance(content_object, ArrayObject):
            new_contents = ArrayObject()
            for content in content_object:
                cleaned_content = self._clean_content_stream(
                    content.getObject(), remove_operands, "Do"
                )
                new_contents.append(cleaned_content)
            page[NameObject("/Contents")] = new_contents
        else:
            cleaned_content = self._clean_content_stream(
                content_object, remove_operands, "Do"
            )
            page[NameObject("/Contents")] = cleaned_content

        return page

    def _process_pages_for_text_removal(self, remove_list: list[str]):
        for page_num in range(self.total_pages):
            page = self.reader.getPage(page_num)

            if "/Contents" not in page:
                self.writer.addPage(page)
                continue

            modified_page = self._remove_text_from_page(page, remove_list)
            self.writer.addPage(modified_page)

    def _remove_text_from_page(self, page, remove_list: list[str]):
        content_object = page["/Contents"].getObject()

        if isinstance(content_object, ArrayObject):
            new_contents = ArrayObject()
            for content in content_object:
                cleaned_content = self._clean_content_stream(
                    content.getObject(), remove_list, "Tj"
                )
                new_contents.append(cleaned_content)
            page[NameObject("/Contents")] = new_contents
        else:
            cleaned_content = self._clean_content_stream(
                content_object, remove_list, "Tj"
            )
            page[NameObject("/Contents")] = cleaned_content

        return page

    def _clean_content_stream(
        self, content_object, remove_items: list[str], operator_type: str
    ):
        try:
            content_stream = ContentStream(content_object, self.reader)
            cleaned_operations = []

            for operands, operator in content_stream.operations:
                should_remove = False

                if operator == b_(operator_type) and operands:
                    if operator_type == "Tj":
                        text = decode_text(operands[0])
                        should_remove = any(item in text for item in remove_items)
                    elif operator_type == "Do":
                        should_remove = operands[0] in remove_items

                if not should_remove:
                    cleaned_operations.append((operands, operator))

            content_stream.operations = cleaned_operations
            return content_stream

        except Exception as e:
            logger.error(f"Помилка при очищенні потоку контенту: {e}")
            return content_object

    def _extract_page_text(self, page) -> str:
        if "/Contents" not in page:
            return ""

        text_list = []
        content_object = page["/Contents"].getObject()

        if isinstance(content_object, ArrayObject):
            for content in content_object:
                text_list.extend(self._extract_from_content_stream(content.getObject()))
        else:
            text_list.extend(self._extract_from_content_stream(content_object))

        return "\n".join(text_list)

    def _extract_from_content_stream(self, content_object) -> list[str]:
        text_list = []
        try:
            content_stream = ContentStream(content_object, self.reader)
            for operands, operator in content_stream.operations:
                if operator == b_("Tj") and operands:
                    text = decode_text(operands[0])
                    text_list.append(text)
                elif operator == b_("TJ") and operands:
                    for element in operands[0]:
                        if hasattr(element, "original_bytes"):
                            text = decode_text(element)
                            text_list.append(text)
        except Exception as e:
            logger.error(f"Помилка при обробці потоку контенту: {e}")

        return text_list

    def _rebuild_content_after_changes(self):
        temp_buffer = BytesIO()
        self.writer.write(temp_buffer)

        self.content = temp_buffer.getvalue()
        temp_buffer.close()

        self._reset_reader()
