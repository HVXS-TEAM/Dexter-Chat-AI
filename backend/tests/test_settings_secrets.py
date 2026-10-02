from app.config import Settings


def test_llm_api_keys_are_masked_in_settings_representation():
    settings = Settings(
        llm_api_key="test-provider-secret",
        llm_api_key_cerebras="test-cerebras-secret",
        llm_api_key_sambanova="test-sambanova-secret",
    )

    representation = repr(settings)
    assert "test-provider-secret" not in representation
    assert "test-cerebras-secret" not in representation
    assert "test-sambanova-secret" not in representation
    assert "**********" in representation