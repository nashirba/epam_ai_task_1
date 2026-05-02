from pathlib import Path

from pia.rag.loaders import load_documents


def test_load_documents_finds_all_sources(tmp_path: Path):
    (tmp_path / "personal/notes").mkdir(parents=True)
    (tmp_path / "personal/notes/x.md").write_text("---\ntype: thesis\n---\n\n# X\n\nbody")
    (tmp_path / "personal/holdings.json").write_text('{"as_of":"2026-05-02","positions":[]}')
    (tmp_path / "public/news").mkdir(parents=True)
    (tmp_path / "public/news/n.md").write_text(
        "---\nsource: t\nurl: u\npublished: 2026-05-01\n---\n\n# N\n\nbody"
    )
    (tmp_path / "public/bank_rates").mkdir(parents=True)
    (tmp_path / "public/bank_rates/halyk.json").write_text(
        '{"bank":"H","snapshot_date":"2026-05-02","products":[]}'
    )

    docs = list(load_documents(tmp_path))
    sources = {d.source for d in docs}
    assert {"user_note", "user_holdings", "news", "bank_rates"} <= sources
