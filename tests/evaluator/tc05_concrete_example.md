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
information to the AI. Finally, the AI uses it to write a good answer. The
retrieved information is given to the model as context, and the model's
own settings are not changed by this process.

## How does RAG work?

1. A user asks a question.
2. The system looks through a collection of documents to find the parts
   that are related to the question. This step is called "retrieval," and
   it works by comparing the meaning of the question to the meaning of
   each stored piece of text, not just matching exact words.
3. The most related pieces of text are given to the AI model, along with
   the original question.
4. The AI reads this information and writes an answer using it.

## Where is RAG used?

For example, RAG can be used in a customer-support chatbot, so the chatbot
can answer questions using the company's own support documents.

## Quick recap

- RAG has two main steps: retrieval and generation.
- Retrieval finds information related to the question by comparing
  meaning, not exact words.
- The AI uses the retrieved information, along with the question, to
  write its answer.
