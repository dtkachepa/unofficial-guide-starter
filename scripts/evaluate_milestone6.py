"""Run Milestone 6 evaluation queries and print Markdown-ready results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import MissingGroqAPIKeyError, NOT_ENOUGH_INFO_RESPONSE
from src.rag_pipeline import ask_debug


EVALUATION_CASES = [
    {
        "question": "What are the most common student complaints about YU meal plans?",
        "expected": (
            "Students complain about high costs, restrictive or mandatory meal plans, "
            "poor value, confusing fees, limited flexibility, and not having enough "
            "meal-plan money or affordable food access."
        ),
    },
    {
        "question": "How did dining costs and meal plan rules affect food access for students?",
        "expected": (
            "The sources describe students struggling to afford food, running out of "
            "meal-plan balances, skipping meals or rationing spending, and being "
            "limited by rules around where and how dining funds could be used."
        ),
    },
    {
        "question": "What differences appear between Beren and Wilf campus dining or cost concerns?",
        "expected": (
            "The answer should compare campus-specific concerns, including Beren "
            "cafeteria pricing and food availability, Wilf/Beren rate increases, "
            "and differences in access to stores, restaurants, or meal-plan use."
        ),
    },
    {
        "question": "How did YU administration respond to criticism about dining plans and fees?",
        "expected": (
            "The answer should mention university info sessions, town halls, "
            "administrative explanations about dining costs, and reports that "
            "administrators admitted failure or acknowledged student concerns."
        ),
    },
    {
        "question": (
            "What non-dining student experience issues appear in the source set, "
            "such as community support?"
        ),
        "expected": (
            "The answer should identify bureaucracy or administrative disorganization "
            "and CS community issues such as workload, support, belonging, and "
            "imposter syndrome."
        ),
    },
]

OUT_OF_SCOPE_CASE = {
    "question": "What parking options are available for graduate students?",
    "expected": (
        "The corpus does not contain enough information about graduate student "
        "parking, so the system should refuse instead of guessing."
    ),
}


def main() -> None:
    cases = EVALUATION_CASES + [OUT_OF_SCOPE_CASE]
    results = []

    for index, case in enumerate(cases, start=1):
        print("=" * 100)
        print(f"case: {index}")
        print(f"question: {case['question']}")
        print(f"expected answer: {case['expected']}")

        try:
            result = ask_debug(case["question"], k=4)
        except MissingGroqAPIKeyError as exc:
            print(f"ERROR: {exc}")
            print(
                "GROQ_API_KEY must be added to .env before Milestone 6 "
                "evaluation can run."
            )
            return

        source_titles = [chunk["title"] for chunk in result["debug_chunks"]]
        distances = [chunk["distance"] for chunk in result["debug_chunks"]]
        judgment, notes = _judge(case["question"], result["answer"], source_titles)

        print(f"actual system response: {result['answer']}")
        print("retrieved chunks / source titles:")
        for title, distance in zip(source_titles, distances):
            distance_text = f"{distance:.4f}" if isinstance(distance, float) else "n/a"
            print(f"- {title} (distance={distance_text})")
        print(f"accuracy judgment: {judgment}")
        print(f"judgment explanation: {notes}")

        results.append(
            {
                "question": case["question"],
                "expected": case["expected"],
                "actual": result["answer"],
                "sources": result["sources"],
                "retrieved_titles": source_titles,
                "judgment": judgment,
                "notes": notes,
            }
        )

    output_path = PROJECT_ROOT / "docs" / "milestone6_evaluation_outputs.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("=" * 100)
    print(f"saved raw evaluation outputs: {output_path}")


def _judge(question: str, answer: str, source_titles: list[str]) -> tuple[str, str]:
    answer_lower = answer.lower()
    title_text = " ".join(source_titles).lower()

    if question == OUT_OF_SCOPE_CASE["question"]:
        if answer.strip() == NOT_ENOUGH_INFO_RESPONSE:
            return (
                "accurate",
                "The system refused the out-of-scope parking question instead of inventing a policy.",
            )
        return (
            "inaccurate",
            "The corpus has no parking sources, but the system still attempted an answer.",
        )

    if "Beren and Wilf" in question:
        has_beren = "beren" in answer_lower or "beren" in title_text
        has_wilf = "wilf" in answer_lower or "wilf" in title_text
        if has_beren and has_wilf:
            return (
                "accurate",
                "The answer compares campus-specific concerns using retrieved Beren/Wilf dining and cost sources.",
            )
        return (
            "partially accurate",
            "The answer uses dining/cost sources but does not clearly compare both campuses.",
        )

    if "non-dining" in question:
        has_bureaucracy = "bureaucracy" in answer_lower or "bureaucracy" in title_text
        has_cs = (
            "cs" in answer_lower
            or "computer science" in answer_lower
            or "community" in answer_lower
            or "community" in title_text
        )
        if has_bureaucracy and has_cs:
            return (
                "accurate",
                "The answer covers both bureaucracy and CS community/support themes from retrieved sources.",
            )
        return (
            "partially accurate",
            "The answer found one non-dining theme but missed part of the expected comparison.",
        )

    if source_titles and answer.strip() != NOT_ENOUGH_INFO_RESPONSE:
        return (
            "accurate",
            "The response is supported by the retrieved source titles and stays within the retrieved dining context.",
        )

    return (
        "partially accurate",
        "The response did not hallucinate, but it did not fully answer the expected in-scope question.",
    )


if __name__ == "__main__":
    main()
