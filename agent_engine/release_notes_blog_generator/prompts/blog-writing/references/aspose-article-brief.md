# Aspose article brief, keyword map, feature matrix, and QA scorecard

Read this at step 1, before outlining. The brief is where SEO and LLM optimisation start — not a pass at the end.

The standard every post is measured against:

> Search intent + working technical solution + original explanation + verifiable evidence + clear structure.

A technically incorrect post does not ship, however strong its SEO.

---

## 1. The article brief

Fill in every row before outlining. A blank or guessed row means the post is not ready — get the answer from the user or from `docs/`.

| Field | What to define | Example |
|---|---|---|
| Primary task | The one thing the developer wants to do, as a task not a topic | Convert a CorelDRAW file to a PNG image programmatically |
| Target audience | One primary language and platform | .NET developer |
| Product + SDK | Exact Aspose product and platform | Aspose.Imaging for .NET |
| Input → output | What goes in, what comes out | `input.cdr` → `output.png` |
| Search intent | Definition / how-to / comparison / troubleshooting / decision | How-to (implementation) |
| Primary question | The exact phrase a reader would type | "How to convert CDR to PNG in .NET" |
| Definitive answer | One or two sentences; becomes the intro and snippet | Load the CDR with `Image.Load()` and save with `Save()`, letting the `.png` extension set the format |
| Related questions | 3–8 questions users actually ask | What is CDR? How do I load it? Can I control the PNG output? Does it work for multiple pages? |
| Product entities | Products, formats, and API concepts to name consistently | Aspose.Imaging for .NET, CDR, PNG, `Image.Save` |
| Unique value | What this post does better than the ten that exist | Complete tested example plus an explanation of each API call and the output limitations |
| Evidence | The specific docs/reference/example/test pages backing each claim | Links into `docs/` for `Image.Load` and `Image.Save` |
| New / update / consolidate | Whether to create, revise, or merge | New post |
| Expected outcome | What the reader can do afterwards | Convert a single CDR file, and adapt the loop for a batch |

---

## 2. Keyword map

Use it to understand demand. Do not turn it into phrases that must appear in every paragraph. Use the primary keyword naturally in the title, intro, one or two headings, the URL, and the meta description.

| Type | Example |
|---|---|
| Primary | Convert CDR to PNG in .NET |
| Related term | CDR to PNG converter in C# |
| Task variation | Export CDR as PNG programmatically |
| Product entity | Aspose.Imaging for .NET |
| API concept | `Image.Save` |
| User question | How to convert CorelDRAW to PNG? |

---

## 3. Feature-to-article matrix

Many posts here are driven by SDK features, releases, and newly supported formats. Do not turn every feature into a "What is X?" post — map the feature to the developer's actual task.

| Feature / capability | Primary developer task | Article type | Unique value | Working title shape |
|---|---|---|---|---|
| New API method | How to use the method | How-to | Working example + explanation | "How to Add Recipients to an Email in .NET" |
| New supported format | How to process the format | How-to / feature | Input/output workflow | "How to Read <format> Files in .NET" |
| New conversion capability | How to convert files | Tutorial | Complete implementation | "Convert <A> to <B> in .NET" |
| API behaviour change | What changed and how to use it | Technical update | Before/after explanation | "What Changed in <feature> and How to Use It" |
| Performance improvement | How to optimise processing | Technical guide | Practical trade-offs | "How to Speed Up <operation> in .NET" |
| Bug fix / limitation | How to avoid an issue | Troubleshooting | Clear diagnosis and solution | "How to Fix <error> in .NET" |

"How to Add Recipients to an Email in .NET" beats "What Is Email Recipient Management?" — it matches the task and forces an implementation-focused post.

---

## 4. Input/output declaration

For any conversion or processing post, put an explicit block near the top of the solution section. It is the fact an AI system most often needs to lift.

```
Input:    input.cdr
Output:   output.png
Library:  Aspose.Imaging for .NET
Language: C#
```

---

## 5. The 100-point QA scorecard

Score the finished post. Recommended to publish: 85+ with no critical technical error. This is an editorial gate, not a substitute for judgement.

| Criterion | Points |
|---|---|
| Search intent is clear and matched | 10 |
| Technical accuracy and tested code | 25 |
| Original value and useful explanation | 20 |
| Answer-first structure | 15 |
| SEO metadata and headings | 10 |
| Internal linking and topic relevance | 10 |
| Accessibility and technical SEO | 5 |
| LLM clarity and evidence | 5 |
| **Total** | **100** |

Critical rule: a technically incorrect article does not pass on good SEO. If the code is wrong, the score is irrelevant.

---

## 6. Minimum viable checklist (daily use)

- Intent: what exact developer problem does this solve?
- Product: is the correct Aspose product and SDK identified?
- Code: is the example correct, complete, and tested?
- Answer: does the introduction answer the question immediately?
- Structure: can the article be understood from its headings alone?
- Originality: what useful insight does it add beyond the docs?
- Evidence: are important claims verifiable in `docs/`?
- SEO: are the title, metadata, URL, and internal links appropriate?
- LLM: can an AI system extract the main answer accurately?
- Quality: is there any generic filler or unsupported claim?
