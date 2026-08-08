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

1. A user asks a question.
2. The system searches a collection of documents to find the parts that
   are related to the question. This is called retrieval.
3. The retrieved information is given to the AI model, along with the
   original question.
4. The AI reads this information and writes an answer using it.

## A worked example

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
