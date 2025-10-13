import joblib

from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression


def load_transformer():
    model = SentenceTransformer("models/sentence_transformer.model")
    print("Sentence Transformer loaded")
    return model


def load_classifier() -> LogisticRegression:
    model = joblib.load("models/classifier.joblib")
    print("Classifier loaded")
    return model


def analyze_sentiment(
    sentence: str, transformer: SentenceTransformer, classifier: LogisticRegression
) -> str:
    embedding = transformer.encode([sentence])
    prediction = classifier.predict(embedding)[0]
    return ("negative", "neutral", "positive")[prediction]
