# Introduction to RAG (Retrieval-Augmented Generation)

## What is RAG?

RAG stands for Retrieval-Augmented Generation. In simple words, it means:
first, find useful information related to a question. Then, give that
information to an AI model. Finally, the AI uses it to write an answer.
The retrieved information is given to the model as context, and the
model's own settings are not changed by this process.

## How does RAG work?

1. Before any question is asked, the documents are split into small
   pieces called chunks, and each chunk is turned into a list of numbers
   called an embedding. These chunks and their embeddings are stored
   ahead of time so they can be searched later.
2. A user asks a question.
3. The system looks through the stored chunks to find the parts
   that are related to the question. This step is called "retrieval," and
   it works by comparing the meaning of the question to the meaning of
   each stored piece of text, not just matching exact words.
4. The most related pieces of text are given to the AI model, along with
   the original question.
5. The AI reads this information and writes an answer using it.

## A worked example

The policy document was already split into chunks and stored ahead of
time, as described above.

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
