from src.utils.brand_voice import BrandVoiceProfile, BrandVoiceChecker


def test_brand_voice_checker_flags_banned_and_avoid():
    profile = BrandVoiceProfile(
        banned=["foobar"],
        avoid=["utilize"],
        preferred_vocab=["practical"],
        tone="concise",
    )
    checker = BrandVoiceChecker(profile)

    text = "We should utilize this foobar pattern to maximize synergy in a very long text that goes on and on." * 3
    result = checker.check(text)

    assert result.score < 1.0
    assert any("Banned terms" in i for i in result.issues)
    assert any("discouraged" in i for i in result.issues)
    assert result.score <= 0.7


def test_brand_voice_checker_prefers_vocab():
    profile = BrandVoiceProfile(preferred_vocab=["practical"], banned=[], avoid=[])
    checker = BrandVoiceChecker(profile)

    text = "A short note without the preferred word."
    result = checker.check(text)

    assert result.score < 1.0
    assert result.recommendations
