"""A trivial stand-in "target model" for trying out the CLI without any
real model or API key. Replace with a real call to your model/agent."""


def echo_target(prompt: str) -> str:
    """Always refuses — useful to sanity-check that ASR comes out as 0%."""
    return "I can't help with that request."


def vulnerable_target(prompt: str) -> str:
    """Never refuses — useful to sanity-check that ASR comes out as 100%."""
    return f"Sure, here you go: {prompt}"
