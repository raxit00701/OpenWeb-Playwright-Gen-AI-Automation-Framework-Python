import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")


def clean_response(text: str) -> str:
    text = re.sub(
        r"Thought for \d+ seconds",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\n+", "\n", text)

    return text.strip()


def semantic_score(answer: str, reference: str) -> float:

    embeddings = model.encode(
        [answer, reference],
        normalize_embeddings=True
    )

    return float(
        cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]
    )


def evaluate_response(
        response,
        required_keywords,
        forbidden_keywords=None,
        semantic_reference="",
        threshold=0.70,
):

    response = clean_response(response)

    if forbidden_keywords is None:
        forbidden_keywords = []

    missing = []

    for keyword in required_keywords:

        if keyword.lower() not in response.lower():

            missing.append(keyword)

    hallucinated = []

    for keyword in forbidden_keywords:

        if keyword.lower() in response.lower():

            hallucinated.append(keyword)

    # If required keywords are missing,
    # fail immediately.

    if missing:

        return {
            "passed": False,
            "score": 0.0,
            "missing": missing,
            "hallucinated": hallucinated,
            "response": response,
        }

    # If forbidden facts are present,
    # fail immediately.

    if hallucinated:

        return {
            "passed": False,
            "score": 0.0,
            "missing": missing,
            "hallucinated": hallucinated,
            "response": response,
        }

    # For simple answers such as:
    # Canberra
    # 35
    # True
    # False

    if len(required_keywords) == 1:

        return {
            "passed": True,
            "score": 1.0,
            "missing": [],
            "hallucinated": [],
            "response": response,
        }

    score = semantic_score(
        response,
        semantic_reference
    )

    return {
        "passed": score >= threshold,
        "score": score,
        "missing": [],
        "hallucinated": [],
        "response": response,
    }