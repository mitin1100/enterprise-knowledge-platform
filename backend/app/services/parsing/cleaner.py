import re
import unicodedata
from collections import Counter
from dataclasses import dataclass


_CONTROL_CHARACTERS_PATTERN = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)

_MULTIPLE_SPACES_PATTERN = re.compile(r"[ \t]+")
_MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{3,}")
_PAGE_NUMBER_PATTERN = re.compile(
    r"^\s*(?:page\s*)?\d+(?:\s*(?:/|of)\s*\d+)?\s*$",
    flags=re.IGNORECASE,
)

_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*•▪◦‣⁃]|\d+[.)]|[a-zA-Z][.)])\s+"
)


@dataclass(slots=True)
class PageContent:
    page_number: int
    text: str


class TextCleaner:
    def __init__(
        self,
        header_footer_ratio: float = 0.6,
        max_output_chars: int = 10_000_000,
    ) -> None:
        if not 0.0 < header_footer_ratio <= 1.0:
            raise ValueError(
                "header_footer_ratio must be between 0 and 1."
            )

        self._header_footer_ratio = header_footer_ratio
        self._max_output_chars = max_output_chars

    def clean_pages(
        self,
        pages: list[PageContent],
    ) -> tuple[str, list[str]]:
        if not pages:
            return "", []

        warnings: list[str] = []

        normalized_pages = [
            PageContent(
                page_number=page.page_number,
                text=self.normalize_unicode(page.text),
            )
            for page in pages
        ]

        repeated_boundaries = self._detect_repeated_boundaries(
            normalized_pages
        )

        cleaned_pages: list[str] = []

        for page in normalized_pages:
            cleaned_page = self._clean_page(
                text=page.text,
                repeated_boundaries=repeated_boundaries,
            )

            if cleaned_page:
                cleaned_pages.append(cleaned_page)

        final_text = "\n\n".join(cleaned_pages).strip()
        final_text = self._final_cleanup(final_text)

        if len(final_text) > self._max_output_chars:
            final_text = final_text[: self._max_output_chars]
            warnings.append(
                "Parsed text exceeded the maximum output size and "
                "was truncated."
            )

        return final_text, warnings

    def clean_text(self, text: str) -> str:
        normalized = self.normalize_unicode(text)
        return self._final_cleanup(normalized)

    @staticmethod
    def normalize_unicode(text: str) -> str:
        if not text:
            return ""

        text = text.replace("\x00", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # NFKC converts compatibility characters into a normalized form.
        text = unicodedata.normalize("NFKC", text)
        text = _CONTROL_CHARACTERS_PATTERN.sub("", text)

        return text

    def _detect_repeated_boundaries(
        self,
        pages: list[PageContent],
    ) -> set[str]:
        """
        Detect repeated first/last lines across pages.

        Only boundary lines are considered to reduce the chance of removing
        legitimate repeated content inside the document body.
        """
        if len(pages) < 3:
            return set()

        candidates: Counter[str] = Counter()

        for page in pages:
            lines = self._meaningful_lines(page.text)

            if not lines:
                continue

            boundary_lines = lines[:2] + lines[-2:]

            for line in set(boundary_lines):
                normalized_line = self._normalize_boundary_line(line)

                if normalized_line:
                    candidates[normalized_line] += 1

        minimum_occurrences = max(
            2,
            int(len(pages) * self._header_footer_ratio),
        )

        return {
            line
            for line, count in candidates.items()
            if count >= minimum_occurrences
        }

    def _clean_page(
        self,
        text: str,
        repeated_boundaries: set[str],
    ) -> str:
        lines = text.splitlines()
        cleaned_lines: list[str] = []

        for line_index, line in enumerate(lines):
            line = _MULTIPLE_SPACES_PATTERN.sub(" ", line).strip()

            if not line:
                cleaned_lines.append("")
                continue

            is_boundary = (
                line_index <= 2
                or line_index >= max(0, len(lines) - 3)
            )

            normalized_boundary = self._normalize_boundary_line(line)

            if (
                is_boundary
                and normalized_boundary in repeated_boundaries
            ):
                continue

            if is_boundary and _PAGE_NUMBER_PATTERN.fullmatch(line):
                continue

            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)
        text = self._join_wrapped_lines(text)

        return self._final_cleanup(text)

    @staticmethod
    def _meaningful_lines(text: str) -> list[str]:
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    @staticmethod
    def _normalize_boundary_line(line: str) -> str:
        normalized = line.strip().lower()
        normalized = re.sub(r"\d+", "<number>", normalized)
        normalized = _MULTIPLE_SPACES_PATTERN.sub(" ", normalized)

        # Ignore lines that are too short or too long to be useful
        # as a header/footer signature.
        if len(normalized) < 3 or len(normalized) > 200:
            return ""

        return normalized

    def _join_wrapped_lines(self, text: str) -> str:
        """
        Join lines that look like layout wrapping while preserving titles,
        bullets and paragraph boundaries.
        """
        lines = text.splitlines()
        output: list[str] = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                output.append("")
                continue

            if not output or output[-1] == "":
                output.append(stripped)
                continue

            previous = output[-1]

            should_join = (
                not self._ends_sentence(previous)
                and not _BULLET_PATTERN.match(stripped)
                and not self._looks_like_heading(previous)
                and stripped[:1].islower()
            )

            if should_join:
                output[-1] = f"{previous} {stripped}"
            else:
                output.append(stripped)

        return "\n".join(output)

    @staticmethod
    def _ends_sentence(text: str) -> bool:
        return text.rstrip().endswith(
            (".", "!", "?", ":", ";", "。", "！", "？")
        )

    @staticmethod
    def _looks_like_heading(text: str) -> bool:
        stripped = text.strip()

        if len(stripped) > 120:
            return False

        if stripped.endswith((".", ",", ";")):
            return False

        alphabetic_characters = [
            character
            for character in stripped
            if character.isalpha()
        ]

        if not alphabetic_characters:
            return False

        uppercase_ratio = (
            sum(character.isupper() for character in alphabetic_characters)
            / len(alphabetic_characters)
        )

        return uppercase_ratio >= 0.8

    @staticmethod
    def _final_cleanup(text: str) -> str:
        text = "\n".join(
            line.rstrip()
            for line in text.splitlines()
        )

        text = _MULTIPLE_NEWLINES_PATTERN.sub("\n\n", text)

        return text.strip()
    