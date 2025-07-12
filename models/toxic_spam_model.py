# Optional AI dependencies
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    import torch.nn.functional as F
    
    model_name = "facebook/roberta-hate-speech-dynabench-r1-target"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    AI_AVAILABLE = True
except ImportError as e:
    print(f"AI dependencies not available: {e}")
    print("Using fallback toxicity detection...")
    AI_AVAILABLE = False
    tokenizer = None
    model = None

def is_toxic(text: str, threshold=0.5):
    if not AI_AVAILABLE:
        # Simple fallback: check for obvious toxic words
        toxic_words = ["spam", "hate", "toxic", "abuse", "inappropriate"]
        text_lower = text.lower()
        for word in toxic_words:
            if word in text_lower:
                return True, 0.8
        return False, 0.1
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

    # Class 1 is 'toxic', Class 0 is 'non-toxic'
    toxic_score = probs[0][1].item()
    return toxic_score >= threshold, toxic_score

if __name__ == "__main__":
    text = ""
    flagged, score = is_toxic(text)
    print(f"Toxic: {flagged}, Score: {score:.2f}")
