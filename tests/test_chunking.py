from src.chunking.text_splitter import MarkdownTextSplitter


def test_chunking_respects_overlap():
    splitter = MarkdownTextSplitter(chunk_size=10, chunk_overlap=2)
    text = " ".join(f"word{i}" for i in range(30))
    chunks = splitter.split(text)

    assert len(chunks) > 2
    assert all(len(chunk.split()) <= 10 for chunk in chunks)

