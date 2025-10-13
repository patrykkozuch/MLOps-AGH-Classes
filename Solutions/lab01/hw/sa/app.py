from fastapi import FastAPI

from sa.api.models.sa import PredictRequest, PredictResponse

app = FastAPI()


@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    return PredictResponse(prediction="Test")
