from lib.rag.rag_extractor import RAGExtractor


class _FakeEmbedding:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return list(self._values)


class _FakeEmbedder:
    def embed_batch(self, chunks, batch_size=32, show_progress=True):
        return [_FakeEmbedding([float(i), 0.0]) for i, _ in enumerate(chunks)]


class _CollisionDetectingVectorStore:
    def __init__(self):
        self.ids = []

    def clear(self):
        self.ids = []

    def count(self):
        return len(self.ids)

    def add_chunks(self, chunks, embeddings, metadatas=None, ids=None):
        if ids is None:
            raise AssertionError("IDs are expected for this test")
        duplicate_ids = set(ids).intersection(self.ids)
        if duplicate_ids:
            raise ValueError(f"Duplicate IDs: {sorted(duplicate_ids)}")
        self.ids.extend(ids)
        return len(chunks)

    def get_stats(self):
        return {
            "total_chunks": len(self.ids),
            "by_category": {},
        }


def test_repeated_extraction_without_clear_existing_uses_unique_ids(tmp_path):
    extractor = RAGExtractor(str(tmp_path), embedder=_FakeEmbedder())
    extractor.vector_store = _CollisionDetectingVectorStore()

    source_file = tmp_path / "source.txt"
    source_file.write_text("ignored", encoding="utf-8")

    # Keep extraction deterministic and independent from content extraction.
    extractor._extract_text = lambda _filepath: "chunk A\n\nchunk B"
    extractor._split_into_chunks = lambda _text: ["chunk A", "chunk B"]

    extractor.extract_from_document(str(source_file), clear_existing=False)
    extractor.extract_from_document(str(source_file), clear_existing=False)

    assert extractor.vector_store.ids == [
        "doc_0000",
        "doc_0001",
        "doc_0002",
        "doc_0003",
    ]
