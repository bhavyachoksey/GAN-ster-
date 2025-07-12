import re

# Optional AI dependencies
try:
    import spacy
    from keybert import KeyBERT
    from sentence_transformers import SentenceTransformer
    
    # Load models
    embedding_model = SentenceTransformer("all-mpnet-base-v2")
    kw_model = KeyBERT(model=embedding_model)
    nlp = spacy.load("en_core_web_sm")
    AI_AVAILABLE = True
except ImportError as e:
    print(f"AI dependencies not available: {e}")
    print("Using fallback tag extraction...")
    AI_AVAILABLE = False
    embedding_model = None
    kw_model = None
    nlp = None

# Text cleaner
def clean_text(text):
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower().strip()

# Filter single, meaningful words only (noun/adjective/proper)
def is_good_single_word(word):
    if not AI_AVAILABLE:
        # Simple fallback without spacy
        return (
            len(word.split()) == 1
            and not word.isdigit()
            and len(word) > 2
            and word.isalpha()
        )
    
    doc = nlp(word)
    return (
        len(word.split()) == 1
        and all(token.pos_ in {"NOUN", "PROPN", "ADJ"} for token in doc)
        and not word.isdigit()
        and len(word) > 2
    )

# Fallback tag extraction without AI
def extract_tags_fallback(title, body, top_k=10):
    """Simple keyword extraction without AI dependencies"""
    text = clean_text(title + " " + body)
    words = text.split()
    
    # Filter meaningful words
    tags = []
    seen = set()
    
    for word in words:
        if (word not in seen and 
            is_good_single_word(word) and 
            len(word) > 3):  # Longer words are likely more meaningful
            tags.append(word)
            seen.add(word)
            if len(tags) >= top_k:
                break
    
    return tags

# Main tag extractor
def extract_single_word_tags(title, body, top_k=10):
    if not AI_AVAILABLE:
        return extract_tags_fallback(title, body, top_k)
    
    text = clean_text(title + " " + body)

    raw_keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 1),  # only single words
        stop_words="english",
        use_mmr=False,
        top_n=top_k + 20
    )

    seen = set()
    tags = []

    for kw, score in raw_keywords:
        kw = kw.lower().strip()
        if kw in seen or not is_good_single_word(kw):
            continue
        seen.add(kw)
        tags.append(kw)
        if len(tags) >= top_k:
            break

    return tags

# Entry point
def auto_tag_question(question, top_k=5):
    tags = extract_single_word_tags(question["title"], question["body"], top_k=top_k)
    question["tags"] = tags
    return question

# Example run
if __name__ == "__main__":
    question = {
        "title": "I am thinking of applying for colege in mumbai and NMIMS is the top recommendation on shaala.com what are your thoughts?",
        "body": "NMIMS, or Narsee Monjee Institute of Management Studies, is a prestigious university located in Mumbai. It offers a variety of undergraduate and postgraduate programs across various fields such as business, engineering, law, and more. NMIMS is known for its strong academic reputation and industry connections, which can provide valuable opportunities for students. The university has a well-established faculty with expertise in their respective fields, providing students with high-quality education. Additionally, NMIMS has modern facilities and resources to support student learning and research activities. The university's emphasis on practical learning through internships and industry projects can enhance students' employability and career prospects. As a top recommendation on shaala.com, NMIMS is likely to have positive reviews and feedback from current and former students. However, it is essential to conduct thorough research and consider factors such as program offerings, campus culture, location, and tuition fees before making a decision to apply. Visiting the campus, attending information sessions, and talking to current students or alumni can provide further insights into the university and help you make an informed choice. Ultimately, choosing a college is a personal decision, so it's crucial to weigh all aspects and determine if NMIMS aligns with your academic and career goals"}

    tagged = auto_tag_question(question, top_k=5)
    print("Title:", tagged["title"])
    print("Body:", tagged["body"][:300] + "...")
    print("Tags:", ", ".join(tagged["tags"]))
