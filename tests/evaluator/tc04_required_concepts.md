# Introduction to RAG (Retrieval-Augmented Generation)

## What is RAG?

RAG stands for Retrieval-Augmented Generation. In simple words, it means:
first, find useful information related to a question. Then, give that
information to an AI model. Finally, the AI uses it to write an answer.
The retrieved information is given to the model as context, and the
model's own settings are not changed by this process.

## How does RAG work?

1. A user asks a question.
2. The system looks through a collection of documents to find the parts
   that are related to the question. This step is called "retrieval," and
   it works by comparing the meaning of the question to the meaning of
   each stored piece of text, not just matching exact words.
3. The most related pieces of text are given to the AI model, along with
   the original question.
4. The AI reads this information and writes an answer using it.

## A worked example

**Question**: "What is our company's refund policy?"

**Retrieval step**: The system searches the company's policy documents and
finds this sentence: "Customers can request a refund within 30 days of
purchase."

**Answer step**: The AI is given this sentence along with the question,
and it answers: "You can request a refund within 30 days of your
purchase."

## Quick recap

- RAG has two main steps: retrieval and generation.
- Retrieval finds information related to the question by comparing
  meaning, not exact words.
- The AI uses the retrieved information, along with the question, to
  write its answer.
