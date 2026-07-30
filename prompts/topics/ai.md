# AI, ML research, and agentic coding

## AI checks

Primary sources:

- OpenAI blog, changelog, status, model docs.
- Anthropic news, docs, status.
- Google DeepMind, Google AI, Gemini docs, Google Cloud AI release notes.
- Meta AI, Llama releases, PyTorch blog.
- Mistral, Cohere, xAI, Perplexity, Hugging Face.
- NVIDIA developer blog and CUDA release notes.
- arXiv cs.CL, cs.LG, cs.AI, cs.CR for unusually relevant papers.
- Papers with Code trending.
- Latent Space, Import AI, The Batch for context.

Daily queries:

- New model releases and deprecations.
- API pricing, rate limit, context window, tool use, structured output,
  multimodal, coding model, agent, and retrieval changes.
- Open model weights, license changes, quantization, inference serving, GPU
  memory, and benchmark corrections.
- AI security issues: prompt injection, data exfiltration, model supply chain,
  dependency compromise, jailbreaks with real impact.

Always include the model identifier, release date, source, and concrete change
when known.

## ML research checks

Collection: `fetch_papers` (`swe_digest.sources.papers`) pulls the `[papers]`
categories and queries from the watchlist via the arXiv API, with arXiv RSS and
the committed `data/snapshots/papers/` snapshot as fallbacks. The `snapshots`
workflow accumulates results every six hours. Paper findings go in the
`ML research` section.

Primary sources:

- arXiv listings: cs.LG, cs.CL, cs.AI, cs.CR.
- Papers with Code and alphaXiv trending.
- Hugging Face Papers daily.
- Lab publications: DeepMind, Meta AI, OpenAI, Anthropic, Allen AI, Mistral.
- Import AI and The Batch for context.

Selection rules:

- Include only papers with clear engineering relevance or strong ecosystem
  attention.
- Record title, authors or lab, date, and the concrete result or method.
- Do not restate benchmark numbers without the reported method.
- Label preprints as developing until independently reproduced.
- Do not include a paper only because it trends.
- Rank against the day. A typical fetch holds 110 to 140 arXiv entries and a
  heavy one several hundred, and zero or one clearing the bar is the normal
  outcome. Omit `ML research` rather than publishing the best of a weak field.

## Agentic coding checks

Primary sources:

- Claude Code, Cursor, GitHub Copilot, and other coding-agent release notes,
  changelogs, and docs.
- Model Context Protocol spec, servers, and clients.
- Practitioner write-ups with concrete setup, prompts, or measured results.
- Simon Willison's weblog and Latent Space for context.

Selection rules:

- Name the agent, model, and version when known.
- Link release notes or docs as primary, and label workflow and opinion posts as
  discussion.
- Prefer posts with metrics, failure analysis, or reproducible setup over launch
  marketing.
- Track agent evaluation results and how they were produced.
