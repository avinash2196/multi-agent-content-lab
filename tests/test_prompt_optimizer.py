from src.utils.prompt_optimizer import PromptOptimizer


def test_prompt_optimizer_combines_fields():
    optimizer = PromptOptimizer()

    prompt = optimizer.optimize("A calm lake", style="watercolor", context="portfolio cover")

    assert "A calm lake" in prompt
    assert "Style: watercolor" in prompt
    assert "Context: portfolio cover" in prompt
    assert "High quality" in prompt
    assert prompt.count("|") >= 2


def test_prompt_optimizer_strips_and_defaults():
    optimizer = PromptOptimizer()

    prompt = optimizer.optimize("   Idea   ")

    assert prompt.startswith("Idea")
    assert "Style:" not in prompt
    assert "Context:" not in prompt
