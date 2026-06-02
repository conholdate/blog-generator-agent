from agent_engine.content_indexer_agent.tools.index_store import JsonlIndexStore
from agent_engine.content_indexer_agent.types import IndexRecord


def test_jsonl_index_store_loads_utf8_bom_prefixed_file(tmp_path) -> None:
    record = IndexRecord(
        id="blog::barcode/example/index.md",
        brand="aspose",
        product="barcode",
        repo_key="blog",
        repo_type="blog",
        platform="net",
        title="Example",
        topic="Example",
        source_path="barcode/example/index.md",
    )
    index_path = tmp_path / "all.jsonl"
    index_path.write_text("\ufeff" + record.model_dump_json() + "\n", encoding="utf-8")

    store = JsonlIndexStore(index_path)
    store.load()

    assert list(store.records) == [record.id]
    assert store.records[record.id].topic == "Example"
