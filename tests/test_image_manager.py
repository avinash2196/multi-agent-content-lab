from src.utils.image_manager import ImageManager


def test_image_manager_add_and_primary():
    mgr = ImageManager()
    entries = mgr.add_images(
        key="session1",
        urls=["http://img/1.png", "http://img/2.png"],
        prompt="sunset",
        aspect_ratio="1024x1024",
        created=123,
    )

    assert len(entries) == 2
    assert mgr.primary("session1").url == "http://img/1.png"


def test_image_manager_alt_text_update():
    mgr = ImageManager()
    mgr.add_images(key="s", urls=["http://img/a.png"], prompt="p", aspect_ratio="1:1", created=1)

    ok = mgr.set_alt_text("s", "http://img/a.png", "alt text")

    assert ok is True
    assert mgr.list_images("s")[0].alt_text == "alt text"
