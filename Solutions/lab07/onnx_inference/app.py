from fastapi import FastAPI
import onnxruntime as ort
from pydantic import BaseModel
from transformers import AutoTokenizer
import numpy as np

app = FastAPI()

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/multi-qa-mpnet-base-cos-v1")

# Load ONNX model
ort_session = ort.InferenceSession("model_optimized.onnx", providers=["CPUExecutionProvider"])

class InferenceRequest(BaseModel):
    text: str

@app.post("/infer")
def infer(request: InferenceRequest):
    inputs = tokenizer(request.text, return_tensors="np", padding=True, truncation=True)
    outputs = ort_session.run(None, {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    })
    return {"embedding": np.mean(outputs[0], axis=1).tolist()}
