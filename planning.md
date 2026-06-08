# Project 1 Planning: The Unofficial Guide

This planning document is written to define the intended RAG pipeline.

## 1. Domain

The domain is an unofficial guide to Yeshiva University student life, focused on dining, meal plans, housing and cafeteria costs and CS student community experiences.

This knowledge is valuable because it reflects student-facing experiences that may not appear in official university pages. The corpus is mostly student newspaper reporting and opinion, so it can help answer practical questions about how students describe policies, costs, administrative responses, and community support.

## 2. Documents

The project uses 10 local `.txt` files in `data/raw/`. Each file contains metadata fields for title, source URL, type, and topic, followed by article text.

| # | Local file | Title | Source URL | Type | Topic |
|---|---|---|---|---|---|
| 1 | `data/raw/01_meal_plan_or_meal_scam.txt` | Meal Plan or Meal Scam? | https://yuobserver.org/2017/09/meal-plan-meal-scam/ | Student newspaper / opinion | Meal plans, dining costs, student complaints |
| 2 | `data/raw/02_students_are_hungry_meal_plan.txt` | Students are Hungry: A Call for YU to Alter the New Meal Plan | https://yuobserver.org/2019/10/students-are-hungry-a-call-for-yu-to-alter-the-new-meal-plan/ | Student newspaper / opinion | Meal plan changes, affordability, student criticism |
| 3 | `data/raw/03_no_money_no_food_meal_plan.txt` | No Money, No Food: How YU's New Meal Plan is Harming Students | https://yucommentator.org/2019/11/students-are-infuriated-as-new-meal-plans-leaves-them-without-money-or-food/ | Student newspaper / reporting | Meal plan structure, student frustration, food access |
| 4 | `data/raw/04_beren_cafeteria_concerns.txt` | Cafeteria Concerns: A Look at Dining on the Beren Campus | https://yuobserver.org/2024/05/cafeteria-concerns-a-look-at-dining-on-the-beren-campus/ | Student newspaper / reporting | Beren Campus dining, cafeteria pricing, food availability |
| 5 | `data/raw/05_housing_cafeteria_rates.txt` | Housing and Cafeteria Rates Rise on Beren and Wilf Campuses | https://yucommentator.org/2022/07/housing-and-cafeteria-rates-rise-on-beren-and-wilf-campuses/ | Student newspaper / reporting | Housing rates, cafeteria rates, campus costs |
| 6 | `data/raw/06_sharing_is_caring_caf_policies.txt` | Sharing Is Caring? An Inquiry into YU's Caf Policies, Part I | https://yucommentator.org/2025/04/sharing-is-caring-an-inquiry-into-yus-caf-policies-part-i/ | Student newspaper / reporting | Cafeteria policies, meal sharing, meal plan rules |
| 7 | `data/raw/07_new_dining_plan_fees_info_session.txt` | University Plans Info Session Regarding New Dining Plan Fees | https://yucommentator.org/2019/11/university-plans-info-session-regarding-new-dining-plan-fees/ | Student newspaper / reporting | Dining plan fees, university response, student concerns |
| 8 | `data/raw/08_meal_plan_town_halls.txt` | Administration Admits Failure at Meal Plan Town Halls | https://yucommentator.org/2019/11/administration-admits-failure-at-meal-plan-town-halls/ | Student newspaper / reporting | Meal plan town halls, administrative response, student criticism |
| 9 | `data/raw/09_yu_bureaucracy.txt` | Disorganization at its Core: YU Bureaucracy | https://yuobserver.org/2024/02/disorganization-at-its-core-yu-bureaucracy/ | Student newspaper / opinion | University bureaucracy, advising, administrative disorganization |
| 10 | `data/raw/10_creation_of_a_community_cs.txt` | The Creation of a Community | https://yuobserver.org/2021/12/the-creation-of-a-community/ | Student newspaper / feature | CS student community, workload, imposter syndrome, support |

## 3. Architecture

The RAG system will use this pipeline:

Document Ingestion: local `.txt` files in `data/raw/`
-> Cleaning: remove metadata headers, boilerplate, and empty lines
-> Chunking: paragraph-aware chunking
-> Embedding: `sentence-transformers` model `all-MiniLM-L6-v2`
-> Vector Store: ChromaDB
-> Retrieval: top-k semantic search with `k=4`
-> Generation: Groq `llama-3.3-70b-versatile`
-> Interface: Gradio web app

![RAG Architecture](images/RAG%20Architecture.png)

## 4. Chunking Strategy

**Chunk size:** Target about 700 characters.

**Overlap:** About 100 characters.

**Method:** Use paragraph-aware chunking. The ingestion code should preserve paragraph boundaries where possible, add paragraphs to a chunk until the target size is reached, then start the next chunk with a small overlap from the previous chunk.

**Reasoning:** These documents are article-style student newspaper pieces. Their ideas usually span paragraphs, and paragraph boundaries help keep claims, examples, quotes, and context together. A purely mechanical split every 500 characters could separate a complaint from the explanation or source context that makes it useful. Chunks should be readable and mostly self-contained.

## 5. Retrieval Approach

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`.

**Why this model:** It runs locally, is free, has no API rate limits, and is sufficient for a small course project with 10 article-style documents.

**Vector store:** ChromaDB.

**Metadata stored per chunk:** source filename, title, source URL, and chunk index. This metadata is needed for citation-style output and debugging retrieval results.

**Top-k:** Retrieve the top 4 chunks per query.

**Retrieval behavior:** The app should use semantic search over embedded chunks and pass the 4 most relevant chunks into the generation step. The generated answer should be grounded in retrieved context and should avoid making claims not supported by the retrieved chunks.

## 6. Evaluation Plan

| # | Question | Expected answer |
|---|---|---|
| 1 | What are the most common student complaints about YU meal plans? | Students complain about cost, restrictive meal plan rules, insufficient food access, confusing fees, and limited value for money. |
| 2 | How did dining costs and meal plan rules affect food access for students? | The system should explain that students described meal plans and fees as making it harder or more expensive to access food, especially when balances, restrictions, or pricing did not match student needs. |
| 3 | What differences appear between Beren and Wilf campus dining or cost concerns? | The system should compare concerns mentioned in the sources, such as campus-specific cafeteria rates, food options, or student experiences. |
| 4 | How did YU administration respond to criticism about dining plans and fees? | The system should mention info sessions, town halls, administrative explanations, and/or admissions of failure depending on retrieved documents. |
| 5 | What non-dining student experience issues appear in the source set, such as bureaucracy or CS community support? | The system should identify bureaucracy/administrative disorganization and CS community support, workload, belonging, or imposter syndrome. |

Evaluation will check whether answers are grounded in retrieved chunks, whether source titles or URLs are available for attribution, and whether the response avoids unsupported claims. Failure analysis should note whether problems came from cleaning, chunking, retrieval, or generation.

## 7. Anticipated Challenges

1. **Noisy article text:** Manually copied articles may still contain stray boilerplate, captions, author notes, or repeated site text. The cleaning step should remove obvious metadata and empty lines, but results must be inspected.

2. **Overlapping topics across documents:** Meal plans, dining fees, cafeteria rates, and food access appear in multiple sources. Retrieval may return several similar chunks, so evaluation should check whether the answer synthesizes across sources instead of overusing one article.

3. **Subjective student opinions:** Several documents are opinion pieces or include student criticism. The system should present these as student perspectives rather than verified official facts unless the retrieved article supports a stronger claim.

4. **Possible missing context:** The corpus is intentionally small. Some questions may need official policy context or newer information that is not in these 10 documents. The app should say when the provided sources do not contain enough evidence.

5. **Chunk boundary failures:** If chunks split important details, retrieval may return a complaint without the explanation, date, or administrative response. Paragraph-aware chunking and 100-character overlap should reduce this risk.

## 8. AI Tool Plan

AI tools will be used to generate boilerplate ingestion, chunking, ChromaDB, retrieval, Groq generation, and Gradio interface code. I will verify outputs against the real documents, adjust chunking and retrieval settings, and write honest evaluation and failure analysis.

**Milestone 3: Ingestion and chunking**

I will give the AI tool the Domain, Documents, Architecture, and Chunking Strategy sections. I expect it to produce code that reads `data/raw/*.txt`, separates metadata from article body text, cleans obvious boilerplate and empty lines, and creates paragraph-aware chunks around 700 characters with 100 characters overlap. I will verify the output by printing chunk counts, sample chunks, metadata fields, and character lengths.

**Milestone 4: Embedding and retrieval**

I will give the AI tool the Retrieval Approach section. I expect it to produce code that embeds chunks with `sentence-transformers/all-MiniLM-L6-v2`, stores vectors and metadata in ChromaDB, and retrieves the top 4 chunks for a query. I will verify retrieval using the five evaluation questions and by checking whether the returned chunks come from relevant source files.

**Milestone 5: Generation and interface**

I will give the AI tool the Architecture, Retrieval Approach, and Evaluation Plan sections. I expect it to produce a Gradio app that accepts a question, retrieves relevant ChromaDB chunks, sends context to Groq `llama-3.3-70b-versatile`, and returns a grounded answer with source information. I will verify that answers cite or name the relevant sources and do not invent facts outside the retrieved context.

## Milestone 2 Checklist

| Requirement | Status |
|---|---|
| Domain section included | Ready |
| Documents section included and based on `data/raw/` plus `docs/source_inventory.md` | Ready |
| Architecture section included | Ready |
| Architecture image included | Ready |
| Mermaid diagram source saved in `rag_architecture.mmd` | Ready |
| Chunking Strategy section included | Ready |
| Retrieval Approach section included | Ready |
| Evaluation Plan section included with 5 questions | Ready |
| Anticipated Challenges section included | Ready |
| AI Tool Plan section included | Ready |
| Ready for implementation | Ready |
