from src.utils.seo_optimizer import SEOOptimizer


def test_meta_description_truncation():
    seo = SEOOptimizer()
    text = "This is a long description " * 10
    meta = seo.generate_meta_description(text, max_len=60)
    assert len(meta) <= 60
    assert meta.endswith("...")


def test_keyword_embedding_and_density():
    seo = SEOOptimizer(primary_keywords=["ai", "cloud"])
    content = "AI is changing the world."
    updated = seo.embed_keywords(content)
    density = seo.keyword_density(updated)
    assert "ai" in updated.lower()
    assert density["ai"] > 0


def test_slug_creation():
    seo = SEOOptimizer()
    slug = seo.make_slug("AI & ML in 2025: What's Next?")
    assert slug == "ai-ml-in-2025-what-s-next"
