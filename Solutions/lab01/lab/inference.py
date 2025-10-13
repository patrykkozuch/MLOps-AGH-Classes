import joblib
from sklearn.ensemble import RandomForestClassifier


def load_model(filename="model.pkl") -> RandomForestClassifier:
    model = joblib.load(filename)
    print(f"Model loaded from {filename}")
    return model


def predict_class(model: RandomForestClassifier, features: list) -> str:
    prediction = model.predict([features])[0]
    return ["setosa", "versicolor", "virginica"][prediction]
