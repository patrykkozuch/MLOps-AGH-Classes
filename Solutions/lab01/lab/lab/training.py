import joblib

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


def load_data():
    data = load_iris()
    X, y, class_names = data.data, data.target, data.target_names
    return X, y, class_names


def train_model(X, y, class_names):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.classes_ = class_names

    print("Training model...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("Training accuracy: ", model.score(X_train, y_train))
    print("Test accuracy: ", accuracy)

    return model


def save_model(model, filename="models/iris_rf.pkl"):
    joblib.dump(model, filename)
    print(f"Model saved to {filename}")


if __name__ == "__main__":
    X, y, class_names = load_data()
    model = train_model(X, y, class_names)
    save_model(model)
