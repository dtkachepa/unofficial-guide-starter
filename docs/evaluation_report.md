# Milestone 6 Evaluation Report

Evaluation command:

```powershell
uv run python scripts\evaluate_milestone6.py
```

Raw outputs were saved to `docs/milestone6_evaluation_outputs.json`.

| Question | Expected answer | Actual system response summary | Retrieved chunks / source titles | Judgment | Explanation |
|---|---|---|---|---|---|

| What are the most common student complaints about YU meal plans? | High costs, restrictive or mandatory plans, poor value, confusing fees, limited flexibility, and food-access concerns. | The system said plans were overpriced, mandatory for on-campus students, and caused students to worry about affording food or skipping meals. | Students are Hungry; Housing and Cafeteria Rates Rise; No Money, No Food; University Plans Info Session | Accurate | The response was supported by retrieved meal-plan criticism and dining-cost chunks. |

| How did dining costs and meal plan rules affect food access for students? | Students struggled with balances, skipped or rationed meals, and were limited by rules about where/how funds could be used. | The system cited insufficient daily funds, discount/cost mismatch, no-sharing rules, and disadvantage to out-of-town students. | Students are Hungry; Meal Plan or Meal Scam?; Administration Admits Failure at Meal Plan Town Halls; Sharing Is Caring? | Accurate | The response stayed grounded in meal-plan and cafeteria-policy sources. |

| What differences appear between Beren and Wilf campus dining or cost concerns? | Compare Beren cafeteria pricing/availability, Wilf/Beren rate increases, and campus-specific food options. | The system compared Wilf food options with Beren options and noted cafeteria price-plan increases. | Cafeteria Concerns; Housing and Cafeteria Rates Rise; Cafeteria Concerns; Cafeteria Concerns | Accurate | The retrieved chunks were concentrated but relevant to the campus comparison. |

| How did YU administration respond to criticism about dining plans and fees? | Mention info sessions, town halls, cost explanations, and admissions or acknowledgments of failure/concerns. | The system said administration would review material with Dining Services and that town halls explained cafeteria overhead costs. | Students are Hungry; No Money, No Food; Administration Admits Failure at Meal Plan Town Halls; Sharing Is Caring? | Accurate | The town-hall article directly supported the administrative response. |

| What non-dining student experience issues appear in the source set, such as community support? | Identify bureaucracy/administrative disorganization and CS community support, workload, belonging, or imposter syndrome. | The system answered mostly about tuition affordability, dining-plan well-being, transparency, and communication. | University Plans Info Session; Students are Hungry; Students are Hungry; University Plans Info Session | Partially accurate | Retrieval missed the bureaucracy and CS community documents, so generation answered from dining/admin-fee chunks. |

| What parking options are available for graduate students? | Refuse because the corpus does not contain graduate parking information. | The system said it did not have enough information from the provided documents. | Housing and Cafeteria Rates Rise; Sharing Is Caring?; Cafeteria Concerns; Meal Plan or Meal Scam? | Accurate | Weakly related chunks were retrieved, but the relevance guard caused the system to refuse instead of hallucinating. |

## Honest Failure Case

The broad non-dining question failed partially because retrieval returned dining/admin-fee chunks instead of `Disorganization at its Core: YU Bureaucracy` or `The Creation of a Community`. The generation layer stayed grounded to the retrieved context, but that context was incomplete for the intended question.

