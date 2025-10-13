from fastapi import FastAPI

from lab.api.models.iris import PredictResponse, PredictRequest
from lab.inference import load_model, predict_class

app = FastAPI()
model = load_model()


@app.get("/")
def welcome_root():
    return {"message": "Welcome to the ML API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    return PredictResponse(prediction=predict_class(model, request.features))
