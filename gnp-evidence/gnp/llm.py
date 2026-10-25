"""Thin wrapper around the Claude Messages API.

The key is read from the ANTHROPIC_API_KEY environment variable only.
GNP_MOCK=1 switches to an offline test mode used for development: no model is
called and every output is labelled TEST MODE.
"""
import json
import os
import re

MODEL = os.environ.get('GNP_MODEL', 'claude-sonnet-5-5')


def mock_mode():
    return os.environ.get('GNP_MOCK') == '1'


class LLM:
    def __init__(self):
        self.mock = mock_mode()
        self.calls = 0
        if not self.mock:
            if not os.environ.get('ANTHROPIC_API_KEY'):
                raise SystemExit('Set ANTHROPIC_API_KEY first (or GNP_MOCK=1 for offline test mode).')
            import anthropic
            self.client = anthropic.Anthropic()

    def complete(self, system, user, max_tokens=8000):
        self.calls += 1
        msg = self.client.messages.create(model=MODEL, max_tokens=max_tokens, system=system,
                                          messages=[{'role': 'user', 'content': user}])
        return ''.join(b.text for b in msg.content if getattr(b, 'type', '') == 'text')


def extract_json(text):
    """Pull the first JSON array or object out of a model reply."""
    text = re.sub(r'^```(json)?|```$', '', text.strip(), flags=re.M).strip()
    for open_c, close_c in (('[', ']'), ('{', '}')):
        a, b = text.find(open_c), text.rfind(close_c)
        if a != -1 and b > a:
            try:
                return json.loads(text[a:b + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError('No JSON found in model reply')
