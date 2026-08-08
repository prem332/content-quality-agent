# Introduction to RAG (Retrieval-Augmented Generation)

## Why does this matter?

AI models sometimes cannot answer questions correctly if they were never
trained on the needed information. RAG addresses this limitation.

## What is RAG?

RAG stands for Retrieval-Augmented Generation. It is a technique that
combines two components: a retrieval step and a generation step.

## How does RAG work?

The system embeds the query, performs vector similarity search across an
indexed knowledge base, retrieves the top-k most similar chunks, and
injects them into the model's context window before generation. An
embedding is a numerical representation of text that captures its
meaning, allowing the system to compare how similar two pieces of text
are, even if they use different words. The context window is the portion
of text the model reads before producing its response.

## A worked example

**Query**: "What is our company's refund policy?"

The system embeds this query, retrieves the most similar indexed chunk
("Customers can request a refund within 30 days of purchase."), injects it
into the context window, and the model generates: "You can request a
refund within 30 days of your purchase."

## Quick recap

- RAG combines retrieval and generation.
- The query is embedded and compared against indexed chunks using vector
  similarity search.
- The top-k most similar chunks are injected into the context window
  before the model generates its answer.
