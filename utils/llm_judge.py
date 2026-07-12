def llm_judge(question, truth, answer):

    prompt = f"""
You are a factual evaluator.

Question:
{question}

Reference:
{truth}

Answer:
{answer}

Return only JSON.

{{
    "hallucination": true/false,
    "score": 0-10,
    "reason":"..."
}}
"""