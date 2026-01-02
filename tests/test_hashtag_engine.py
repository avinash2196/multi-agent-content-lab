from src.utils.hashtag_engine import HashtagEngine


def test_hashtag_generation_uniqueness_and_limit():
    engine = HashtagEngine(max_length=10)
    tags = engine.generate("AI in healthcare and diagnostics", count=4)
    assert len(tags) == 4
    assert len(set(tags)) == 4
    assert all(tag.startswith('#') for tag in tags)
    assert all(len(tag) <= 11 for tag in tags)  # include '#'
