import re
from dataclasses import dataclass

from app.schemas.doc_parsing import ParsedPage
from app.services.chunking.tokenizer import Tokenizer

_MARKDOWN_HEADING_PATTERN = re.compile(r"^#{1,6}\s+(?P<title>.+)$")
_NUMBERED_HEADING_PATTERN = re.compile(
    r"^(?P<number>\d{1,2}(?:\.\d{1,2}){0,3})[.)]?\s+"
    r"(?P<title>[A-Z0-9À-Ỹ].{0,100})$"
)


@dataclass(slots=True)
class DocumentChunkDraft:
    chunk_index: int
    content: str
    token_count: int
    page_number: int | None
    heading: str | None


@dataclass(slots=True)
class _Segment:
    text: str
    page_number: int | None
    heading: str | None


class TextChunker:
    """
    Heading-aware, token-windowed chunker.

    Each page is first split on detected headings so a chunk never mixes
    unrelated sections, then every resulting block is windowed into
    chunk_size_tokens pieces with chunk_overlap_tokens of overlap. Chunking
    stays within a single page so page_number citations remain accurate.
    """

    def __init__(
        self,
        tokenizer: Tokenizer,
        chunk_size_tokens: int = 800,
        chunk_overlap_tokens: int = 150,
        min_chunk_tokens: int = 100,
    ) -> None:
        if chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens must be positive")

        if chunk_overlap_tokens >= chunk_size_tokens:
            raise ValueError(
                "chunk_overlap_tokens must be smaller than "
                "chunk_size_tokens"
            )

        self._tokenizer = tokenizer
        self._chunk_size_tokens = chunk_size_tokens
        self._chunk_overlap_tokens = chunk_overlap_tokens
        self._min_chunk_tokens = min_chunk_tokens

    def chunk_pages(
        self,
        pages: list[ParsedPage],
    ) -> list[DocumentChunkDraft]:
        pieces: list[_Segment] = []

        for segment in self._split_into_segments(pages):
            for piece_text in self._split_by_tokens(segment.text):
                pieces.append(
                    _Segment(
                        text=piece_text,
                        page_number=segment.page_number,
                        heading=segment.heading,
                    )
                )

        merged = self._merge_small_trailing_pieces(pieces)

        return [
            DocumentChunkDraft(
                chunk_index=index,
                content=piece.text,
                token_count=self._tokenizer.count_tokens(piece.text),
                page_number=piece.page_number,
                heading=piece.heading,
            )
            for index, piece in enumerate(merged)
        ]

    def _split_into_segments(
        self,
        pages: list[ParsedPage],
    ) -> list[_Segment]:
        segments: list[_Segment] = []

        for page in pages:
            for heading, block_text in self._split_by_headings(page.text):
                stripped_block = block_text.strip()

                if stripped_block:
                    segments.append(
                        _Segment(
                            text=stripped_block,
                            page_number=page.page_number,
                            heading=heading,
                        )
                    )

        return segments

    @staticmethod
    def _split_by_headings(
        text: str,
    ) -> list[tuple[str | None, str]]:
        blocks: list[tuple[str | None, str]] = []

        current_heading: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            block_text = "\n".join(current_lines).strip()

            if block_text:
                blocks.append((current_heading, block_text))

        for line in text.split("\n"):
            heading = TextChunker._detect_heading(line)

            if heading is not None:
                flush()
                current_heading = heading
                current_lines = []
            else:
                current_lines.append(line)

        flush()

        return blocks or [(None, text)]

    @staticmethod
    def _detect_heading(line: str) -> str | None:
        stripped = line.strip()

        if not stripped or len(stripped) > 120:
            return None

        markdown_match = _MARKDOWN_HEADING_PATTERN.match(stripped)

        if markdown_match:
            return markdown_match.group("title").strip()

        if not stripped.endswith((".", ",", ";")):
            numbered_match = _NUMBERED_HEADING_PATTERN.match(stripped)

            if numbered_match:
                return numbered_match.group("title").strip()

        alphabetic_characters = [
            character
            for character in stripped
            if character.isalpha()
        ]

        if (
            len(alphabetic_characters) >= 3
            and len(stripped.split()) <= 12
            and not stripped.endswith((".", ",", ";", ":"))
        ):
            uppercase_ratio = sum(
                character.isupper()
                for character in alphabetic_characters
            ) / len(alphabetic_characters)

            if uppercase_ratio >= 0.9:
                return stripped

        return None

    def _split_by_tokens(self, text: str) -> list[str]:
        if not text.strip():
            return []

        tokens = self._tokenizer.encode(text)

        if len(tokens) <= self._chunk_size_tokens:
            return [text]

        pieces: list[str] = []
        step = self._chunk_size_tokens - self._chunk_overlap_tokens
        start = 0

        while start < len(tokens):
            end = min(start + self._chunk_size_tokens, len(tokens))
            piece_text = self._tokenizer.decode(tokens[start:end]).strip()

            if piece_text:
                pieces.append(piece_text)

            if end == len(tokens):
                break

            start += step

        return pieces

    def _merge_small_trailing_pieces(
        self,
        pieces: list[_Segment],
    ) -> list[_Segment]:
        if not pieces:
            return []

        merged: list[_Segment] = [pieces[0]]

        for piece in pieces[1:]:
            previous = merged[-1]
            piece_token_count = self._tokenizer.count_tokens(piece.text)

            combined_text = f"{previous.text}\n\n{piece.text}"

            can_merge = (
                piece_token_count < self._min_chunk_tokens
                and previous.page_number == piece.page_number
                and previous.heading == piece.heading
                and self._tokenizer.count_tokens(combined_text)
                <= self._chunk_size_tokens + self._min_chunk_tokens
            )

            if can_merge:
                merged[-1] = _Segment(
                    text=combined_text,
                    page_number=previous.page_number,
                    heading=previous.heading,
                )
            else:
                merged.append(piece)

        return merged
