from fastapi import FastAPI
import torch
from pydantic import BaseModel
from transformers import AutoModel, AutoTokenizer

app = FastAPI()

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/multi-qa-mpnet-base-cos-v1")

# Load model
model = AutoModel.from_pretrained("sentence-transformers/multi-qa-mpnet-base-cos-v1")
model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
model.load_state_dict(torch.load("model_quantized.pth", map_location="cpu"))
model.eval()
model = torch.compile(model)

class InferenceRequest(BaseModel):
    text: str

@app.post("/infer")
def infer(request: InferenceRequest):
    inputs = tokenizer(request.text, return_tensors="pt", padding=True, truncation=True)
    with torch.inference_mode():
        outputs = model(**inputs)
    return {"embedding": outputs.last_hidden_state.mean(dim=1).tolist()}
