from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

model_name = "facebook/roberta-hate-speech-dynabench-r1-target"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def is_toxic(text: str, threshold=0.5):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

    # Class 1 is 'toxic', Class 0 is 'non-toxic'
    toxic_score = probs[0][1].item()
    return toxic_score >= threshold, toxic_score

text = ""
flagged, score = is_toxic(text)
print(f"Toxic: {flagged}, Score: {score:.2f}")
