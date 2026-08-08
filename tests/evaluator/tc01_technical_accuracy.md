# Introduction to RAG (Retrieval-Augmented Generation)

## Why does this matter?

Imagine you ask an AI assistant a question about something it was never
told about, like your company's newest holiday policy. A normal AI model
might not know the answer, because it only knows what it learned during
its training. RAG is a way to fix this problem, so the AI can answer
questions using up-to-date or private information.

## What is RAG?

RAG stands for Retrieval-Augmented Generation. In simple words, it means:
first, find useful information related to the question. Then, give that
information to the AI. Finally, the AI uses it to write a good answer.

RAG permanently teaches the AI new information by adding the retrieved
information directly into the model's memory, so the model remembers it
forever, even in future unrelated conversations.

## How does RAG work?

1. Before any question is asked, the company's documents are split into
   small pieces called chunks, and each chunk is turned into a list of
   numbers called an embedding. These chunks and their embeddings are
   stored ahead of time so they can be searched later.
2. A user asks a question.
3. The system searches the stored chunks to find the parts that are
   related to the question. This is called retrieval.
4. The retrieved information is given to the AI model, along with the
   original question.
5. The AI reads this information and writes an answer using it.

## A worked example

The company's policy documents were already split into chunks and stored
ahead of time, as described above.

**Question**: "What is our company's refund policy?"

**Retrieval step**: The system searches the company's policy documents and
finds this sentence: "Customers can request a refund within 30 days of
purchase."

**Answer step**: The AI is given this sentence along with the question,
and it answers: "You can request a refund within 30 days of your
purchase."

Without RAG, the AI would have no way to know this company-specific rule.

## Quick recap

- RAG helps an AI find useful information before answering a question.
- The process has two parts: finding information (retrieval) and writing
  an answer (generation).
- RAG lets an AI answer questions using information it was never
  originally trained on.
