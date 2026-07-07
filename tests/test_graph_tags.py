import datetime as dt

from brain.graph import build

TODAY = dt.date(2026, 7, 2)


def test_tags_attached_from_tags_yaml(sandbox):
    (sandbox / "tags.yaml").write_text(
        "storage:\n  label: Storage\n  topics: [databases, indexing]\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    byid = {n["id"]: n for n in g["nodes"]}
    # tags land on every node whose id is one of the tag's topics...
    assert byid["databases"]["tags"] == ["storage"]
    assert byid["indexing"]["tags"] == ["storage"]
    # ...and nowhere else.
    assert byid["authentication"]["tags"] == []
    # the top-level tag list carries the display label + a member count.
    tags = {t["id"]: t for t in g["tags"]}
    assert tags["storage"]["label"] == "Storage"
    assert tags["storage"]["count"] == 2


def test_topic_can_carry_multiple_tags(sandbox):
    (sandbox / "tags.yaml").write_text(
        "storage:\n  label: Storage\n  topics: [databases]\n"
        "exam:\n  label: Exam\n  topics: [databases, authentication]\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    byid = {n["id"]: n for n in g["nodes"]}
    assert byid["databases"]["tags"] == ["exam", "storage"]  # sorted
    assert byid["authentication"]["tags"] == ["exam"]


def test_no_tags_file_is_empty_and_harmless(sandbox):
    # conftest never copies tags.yaml, so the sandbox has none.
    g = build(today=TODAY)
    assert g["tags"] == []
    assert all(n["tags"] == [] for n in g["nodes"])


def test_lone_topic_string_is_accepted(sandbox):
    # "edit freely" means forgetting list syntax is expected input:
    # a bare string is one topic, not an iterable of characters.
    (sandbox / "tags.yaml").write_text(
        "storage:\n  label: Storage\n  topics: databases\n", encoding="utf-8"
    )
    g = build(today=TODAY)
    byid = {n["id"]: n for n in g["nodes"]}
    assert byid["databases"]["tags"] == ["storage"]


def test_malformed_tag_is_skipped_not_fatal(sandbox, capsys):
    # a tag whose value isn't a mapping is skipped with a message; the rest
    # of the file (and the export) still goes through.
    (sandbox / "tags.yaml").write_text(
        "broken: [databases]\nstorage:\n  label: Storage\n  topics: [databases]\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    assert [t["id"] for t in g["tags"]] == ["storage"]
    assert "broken" in capsys.readouterr().out


def test_unmatched_topics_are_reported(sandbox, capsys):
    # unmatched topic ids stay ignored (by design) but are named at export
    # time, so a typo doesn't read as the tag being broken.
    (sandbox / "tags.yaml").write_text(
        "storage:\n  label: Storage\n  topics: [databases, no-such-topic]\n",
        encoding="utf-8",
    )
    g = build(today=TODAY)
    tags = {t["id"]: t for t in g["tags"]}
    assert tags["storage"]["count"] == 1
    assert "no-such-topic" in capsys.readouterr().out
