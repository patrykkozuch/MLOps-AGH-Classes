import pytest

from sa.inference import load_classifier
from sa.inference import load_transformer


def test_load_transformer():
    transformer = load_transformer()
    assert transformer is not None


def test_load_classifier():
    classifier = load_classifier()
    assert classifier is not None


@pytest.mark.parametrize(
    "sentence,expected_sentiment",
    [
        ("I love programming!", "positive"),
        ("I hate bugs.", "negative"),
        ("It's an average day.", "neutral"),
    ],
)
def test_analyze_sentiment(sentence, expected_sentiment):
    transformer = load_transformer()
    classifier = load_classifier()
    sentiment = ("negative", "neutral", "positive")[
        classifier.predict(transformer.encode([sentence]))[0]
    ]
    assert sentiment == expected_sentiment
