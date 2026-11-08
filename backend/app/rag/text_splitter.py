from typing import List


class RecursiveCharacterTextSplitter:
    """Splits text recursively by paragraphs, sentences, and words to maintain semantic coherence."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks of specified size and overlap."""
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text.strip()]

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Find best split separator before end
            split_idx = -1
            for sep in self.separators:
                if sep == "":
                    split_idx = end
                    break
                found = text.rfind(sep, start, end)
                if found != -1 and found > start:
                    split_idx = found + len(sep)
                    break

            if split_idx == -1 or split_idx <= start:
                split_idx = end

            chunk = text[start:split_idx].strip()
            if chunk:
                chunks.append(chunk)

            # Advance start with overlap
            start = max(start + 1, split_idx - self.chunk_overlap)

        return chunks

