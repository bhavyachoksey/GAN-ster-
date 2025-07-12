import os
from sentence_transformers import SentenceTransformer, util

# Load sentence embedding model
model = SentenceTransformer("all-mpnet-base-v2")

# Expanded question database (20 sample entries)
questions = [
    {
        "id": 1,
        "title": "What are the benefits of studying at NMIMS?",
        "body": "NMIMS is a prestigious university in Mumbai offering courses in business, law, and engineering.",
        "tags": ["nmims", "education", "university", "mumbai"]
    },
    {
        "id": 2,
        "title": "How to prepare for law admission in India?",
        "body": "I'm planning to apply to law colleges and want guidance on entrance exams and preparation.",
        "tags": ["law", "admission", "education", "india"]
    },
    {
        "id": 3,
        "title": "Best engineering colleges in India",
        "body": "Looking for top engineering institutes for undergraduate programs in India.",
        "tags": ["engineering", "colleges", "india"]
    },
    {
        "id": 4,
        "title": "Tips for cracking CAT exam",
        "body": "What are some effective strategies to score well in the CAT exam?",
        "tags": ["cat", "mba", "entrance", "exam"]
    },
    {
        "id": 5,
        "title": "How is life at IIT Bombay?",
        "body": "IIT Bombay offers a vibrant campus life with top-notch academic resources and research opportunities.",
        "tags": ["iit", "bombay", "campus", "life"]
    },
    {
        "id": 6,
        "title": "Difference between BBA and BMS",
        "body": "Which is better for a management career: BBA or BMS?",
        "tags": ["bba", "bms", "management", "career"]
    },
    {
        "id": 7,
        "title": "Top 5 commerce colleges in Mumbai",
        "body": "Can someone recommend the best commerce colleges in Mumbai for undergraduate studies?",
        "tags": ["commerce", "mumbai", "colleges"]
    },
    {
        "id": 8,
        "title": "Is NMIMS better than Symbiosis for MBA?",
        "body": "I am comparing NMIMS and Symbiosis for my MBA program. Any insights on academics and placements?",
        "tags": ["nmims", "symbiosis", "mba", "comparison"]
    },
    {
        "id": 9,
        "title": "What is the admission process for Delhi University?",
        "body": "I want to apply to DU for undergraduate programs. What is the procedure?",
        "tags": ["du", "admission", "delhi", "university"]
    },
    {
        "id": 10,
        "title": "How to write a good Statement of Purpose?",
        "body": "I'm applying to graduate school. Tips on how to draft a compelling SOP?",
        "tags": ["sop", "gradschool", "writing"]
    },
    {
        "id": 11,
        "title": "Should I take a gap year after school?",
        "body": "What are the pros and cons of taking a gap year before joining college?",
        "tags": ["gapyear", "career", "college"]
    },
    {
        "id": 12,
        "title": "Best scholarships for Indian students abroad",
        "body": "What scholarships can Indian students apply for while going to the US or Europe?",
        "tags": ["scholarship", "studyabroad", "india"]
    },
    {
        "id": 13,
        "title": "Which programming languages should I learn in 2025?",
        "body": "I'm a beginner in coding and want to know which languages are in demand.",
        "tags": ["programming", "career", "technology"]
    },
    {
        "id": 14,
        "title": "Is data science a good career option?",
        "body": "I'm considering a switch to data science. What skills are required and what are the job prospects?",
        "tags": ["datascience", "career", "jobs"]
    },
    {
        "id": 15,
        "title": "How to become a product manager?",
        "body": "I want to transition from software development to product management. What's the best path?",
        "tags": ["productmanager", "career", "tech"]
    },
    {
        "id": 16,
        "title": "How to study effectively for exams?",
        "body": "Tips on time management, revision, and concentration for college exams.",
        "tags": ["study", "productivity", "exams"]
    },
    {
        "id": 17,
        "title": "What is the average salary of an MBA graduate in India?",
        "body": "Can someone share salary expectations for fresh MBA graduates from tier-1 institutes?",
        "tags": ["mba", "salary", "india"]
    },
    {
        "id": 18,
        "title": "Best online courses for UI/UX design",
        "body": "I'm looking to learn UI/UX. What are some good online courses or platforms?",
        "tags": ["uiux", "design", "online"]
    },
    {
        "id": 19,
        "title": "Is freelancing a sustainable career?",
        "body": "I want to start freelancing full-time. Is it a good long-term plan?",
        "tags": ["freelance", "career", "remote"]
    },
    {
        "id": 20,
        "title": "Tips for writing research papers",
        "body": "I'm writing my first research paper. What structure and style should I follow?",
        "tags": ["research", "writing", "papers"]
    },
]

# Create embeddings once per question
for q in questions:
    combined_text = q["title"] + " " + q["body"]
    q["embedding"] = model.encode(combined_text, convert_to_tensor=True)

# Smart search using cosine similarity
def smart_search(query, questions, top_k=3):
    query_embedding = model.encode(query, convert_to_tensor=True)

    results = []
    for q in questions:
        score = util.cos_sim(query_embedding, q["embedding"]).item()
        results.append((q, score))

    # Sort by similarity
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# Example usage
if __name__ == "__main__":
    user_query = input("🔍 Enter your search query: ").strip()
    results = smart_search(user_query, questions)

    print("\n📌 Top Relevant Results:")
    for q, score in results:
        print(f"\n▶ Score: {score:.2f}")
        print(f"   Title: {q['title']}")
        print(f"   Body: {q['body']}")
        print(f"   Tags: {', '.join(q['tags'])}")
