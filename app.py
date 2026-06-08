"""Gradio query interface for the Milestone 5 RAG pipeline."""

from __future__ import annotations

import gradio as gr

from src.generator import MissingGroqAPIKeyError
from src.rag_pipeline import ask_debug


EXAMPLE_QUESTIONS = [
    "What are the most common student complaints about YU meal plans?",
    "How did dining costs and meal plan rules affect food access for students?",
    "How did YU administration respond to criticism about dining plans and fees?",
    "What concerns do students raise about YU bureaucracy?",
    "What does the CS community article say about support and imposter syndrome?",
    "What parking options are available for graduate students?",
]


def answer_question(question: str, k: int) -> tuple[str, str, str]:
    if not question.strip():
        return "", "", ""

    try:
        result = ask_debug(question, k=int(k))
    except MissingGroqAPIKeyError as exc:
        return str(exc), "", ""
    except Exception as exc:
        return f"Error: {exc}", "", ""

    return (
        result["answer"],
        _format_sources(result["sources"]),
        _format_debug_chunks(result["debug_chunks"]),
    )


def _format_sources(sources: list[dict[str, str]]) -> str:
    if not sources:
        return "No sources returned."

    lines = []
    for source in sources:
        title = source.get("title") or "Untitled source"
        url = source.get("source_url") or ""
        if url:
            lines.append(f"- [{title}]({url})")
        else:
            lines.append(f"- {title}")

    return "\n".join(lines)


def _format_debug_chunks(chunks: list[dict[str, object]]) -> str:
    if not chunks:
        return "No retrieved chunks."

    sections = []
    for index, chunk in enumerate(chunks, start=1):
        distance = chunk.get("distance")
        distance_text = f"{distance:.4f}" if isinstance(distance, float) else "n/a"
        title = chunk.get("title") or "Untitled source"
        preview = chunk.get("preview") or ""
        url = chunk.get("source_url") or ""
        topic = chunk.get("topic") or ""
        chunk_index = chunk.get("chunk_index")

        sections.append(
            "\n".join(
                [
                    f"### {index}. {title}",
                    f"- Distance: `{distance_text}`",
                    f"- Chunk: `{chunk_index}`",
                    f"- Topic: {topic}",
                    f"- URL: {url}",
                    "",
                    str(preview),
                ]
            )
        )

    return "\n\n".join(sections)


with gr.Blocks(title="YU Student Life RAG") as demo:
    gr.Markdown("# YU Student Life Query")
    with gr.Row():
        question_input = gr.Textbox(
            label="Ask a question",
            lines=3,
            placeholder="Ask about YU dining, student complaints or community support.",
        )
        k_slider = gr.Slider(
            minimum=2,
            maximum=8,
            value=4,
            step=1,
            label="Top-k retrieval",
        )

    submit_button = gr.Button("Ask", variant="primary")

    answer_output = gr.Textbox(label="Answer", lines=8)
    sources_output = gr.Markdown(label="Sources")
    debug_output = gr.Markdown(label="Retrieved chunks")

    gr.Examples(
        examples=EXAMPLE_QUESTIONS,
        inputs=question_input,
    )

    submit_button.click(
        fn=answer_question,
        inputs=[question_input, k_slider],
        outputs=[answer_output, sources_output, debug_output],
    )
    question_input.submit(
        fn=answer_question,
        inputs=[question_input, k_slider],
        outputs=[answer_output, sources_output, debug_output],
    )


if __name__ == "__main__":
    demo.launch()
