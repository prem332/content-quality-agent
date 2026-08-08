# Introduction to RAG (Retrieval-Augmented Generation)

## Why does this matter?

Imagine you ask an AI assistant a question about something it was never
told about, like your company's newest leave policy. A normal AI model
might not know the answer, because it only knows what it learned during
its training. It cannot automatically learn new things after that
training is finished, and it also does not know private information, like
your company's own documents. RAG is a way to fix this problem, so the AI
can answer questions using new or private information, without needing to
be retrained.

## What is RAG?

RAG stands for Retrieval-Augmented Generation. In simple words, it means
this: first, find useful information related to the question. Then, give
that information to the AI. Finally, the AI uses it to write a good
answer.

The information is given to the AI only for that one question. The AI
itself is not changed or retrained. Next time you ask a different
question, the AI looks for new information again.

## How does RAG work?

RAG works in two main steps.

**Step 1: Finding information.** When you ask a question, the system
searches through a collection of documents. It looks for the parts that
are related to your question. It does this by comparing the *meaning* of
your question to the *meaning* of the stored text, not just matching the
exact same words. This means it can find the right information even if
you use different words than the document does.

**Step 2: Writing the answer.** The system takes the useful information
it found and gives it to the AI, along with your original question. The
AI reads both and writes an answer based on what it just learned, plus
what it already knew.

## A worked example

Let's say a company stores its policies in a set of documents. An employee
asks a chatbot:

**Question**: "How many days of sick leave do I get?"

**Step 1 (Finding information)**: The system searches the company's
policy documents and finds this sentence: "Full-time employees are
entitled to 12 days of paid sick leave per calendar year."

**Step 2 (Writing the answer)**: The system gives this sentence to the
AI, along with the question. The AI reads both and answers: "You get 12
days of paid sick leave per calendar year, if you are a full-time
employee."

Without RAG, the AI would have no way to know this specific company rule,
because it was never part of what the AI learned during training.

## Quick recap

- An AI model's training does not automatically include new or private
  information.
- RAG fixes this by finding useful information first, then giving it to
  the AI along with the question.
- The AI is not permanently changed by this process — it looks for fresh
  information every time a new question is asked.
- RAG lets an AI answer questions using information it was never
  originally trained on, without needing to be retrained.
