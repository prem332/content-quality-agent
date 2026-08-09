# RAG (Retrieval-Augmented Generation) — Reference Knowledge

This document is the authoritative technical reference for the content
generation system. It is written for accuracy and completeness, not for
beginners. The generator transforms this material into a beginner-friendly
lesson; the evaluator uses this material as the source of truth for
fact-checking generated content.

## 1. What RAG Is

RAG (Retrieval-Augmented Generation) is a technique for improving the
answers of a large language model (LLM) by giving it relevant external
information at the time it generates a response, instead of relying only
on what the model learned during training.

An LLM's learned knowledge is based on its training data and does not
automatically update when new information is created. It does not
automatically know about information created after training, private
company data, or niche/specific information that was not well represented
in its training data. RAG addresses this by retrieving relevant text from
an external knowledge source and inserting it into the model's prompt
before the model generates its answer.

RAG does not change the model's weights or "teach" the model permanently.
Each time a RAG system answers a question, it retrieves relevant
information from its external knowledge source and provides it as
temporary context for that response. The model's underlying parameters
are not modified.

## 2. Why RAG Matters

Without RAG, an LLM answering a question can only draw on:
- What it learned during training (which becomes outdated over time)
- What the user manually includes in the prompt

This creates two common problems:
- **Outdated or missing information**: the model doesn't know about recent
  events, updated policies, or new documents.
- **Hallucination**: when the model doesn't know an answer, it may
  generate a plausible-sounding but incorrect answer instead of admitting
  it doesn't know.

RAG can reduce the risk of outdated or unsupported answers by providing
relevant external information as context, although it does not eliminate
hallucinations. It grounds the model's answer in real, retrieved source
material relevant to the specific question, rather than relying purely on
the model's internal memory.

RAG is widely used for:
- Customer support systems answering questions from a company's own
  documentation
- Internal tools that let employees ask questions about company policies
- Search-assistant products that cite sources
- Coding assistants that retrieve relevant documentation or code

## 3. The Core RAG Pipeline

A RAG system has two main phases: an indexing (setup) phase, done once or
periodically, and a retrieval + generation phase, done for every query.

### Phase A — Indexing (done once, ahead of time)
1. Collect source documents (e.g. company policies, articles, manuals).
2. Split ("chunk") the documents into smaller pieces, typically a
   paragraph or a few sentences each. Chunking is necessary because very
   long documents are hard to search accurately and don't fit well into
   a model's context.
3. Convert each chunk into a numerical representation called an
   **embedding** (see Section 4).
4. Store the chunks and their embeddings in a **vector database** — a
   storage system designed to search by meaning/similarity rather than
   exact keyword match.

### Phase B — Retrieval + Generation (done for every user query)
1. The user asks a question.
2. The question itself is converted into an embedding, using the same
   embedding model used during indexing.
3. The system searches the vector database for the stored chunks whose
   embeddings are most similar to the question's embedding. This is
   called **semantic search** — it matches based on meaning, not just
   matching words.
4. The system selects the top few most relevant chunks (often called
   "top-k retrieval").
5. Those retrieved chunks are inserted into the prompt sent to the LLM,
   along with the original question.
6. The LLM generates an answer using both its own general knowledge and
   the specific retrieved information provided in the prompt.

## 4. Embeddings, Explained Simply

An embedding is a way of representing a piece of text (a word, sentence,
or paragraph) as a list of numbers, such that pieces of text with similar
meaning end up with numerically similar representations.

This allows a computer to compare meaning mathematically. For example,
the sentences "How do I get my money back?" and "What is your refund
policy?" use different words but have similar meaning — a good embedding
model will place them close together in this numerical space, even though
they share almost no exact words. This is what allows semantic search to
find relevant information even when the user's wording doesn't match the
source document's wording exactly.

Embeddings are produced by a trained embedding model, which is typically
a separate, smaller model from the LLM that generates the final answer.

## 5. Vector Databases / Vector Search

A vector database is a system designed to store embeddings and efficiently
search for the ones most similar to a given query embedding. "Similar" is
usually measured using a mathematical distance measure between the number
lists (embeddings), such as cosine similarity.

Vector databases exist because comparing a query against millions of
documents one at a time would be too slow; they use specialized indexing
structures to make similarity search fast even over large collections.

For a small, curated set of documents, a lightweight local vector store is
sufficient; large-scale production systems may use dedicated vector
database infrastructure to handle millions of documents with low latency.

## 6. How Retrieved Context Reaches the LLM

The retrieved chunks are not fed to the model as raw numbers (embeddings).
The original text of the retrieved chunks is inserted directly into the
text prompt sent to the LLM, typically with an instruction such as "using
the following information, answer the question." The LLM then reads this
provided text the same way it reads any other part of its prompt, and
generates a response that draws on it.

This means the quality of a RAG system's answer depends heavily on
whether the retrieval step found genuinely relevant chunks. If retrieval
returns irrelevant or missing information, the LLM's answer quality
suffers, even if the LLM itself is capable.

## 7. Complete Worked Example

**Scenario**: An employee asks an internal HR chatbot, "How many days of
sick leave do I get?"

1. **Indexing (done earlier)**: The company's HR policy document was
   split into chunks and stored with embeddings. One chunk contains:
   "Full-time employees are entitled to 12 days of paid sick leave per
   calendar year."

2. **Query**: The employee asks: "How many days of sick leave do I get?"

3. **Retrieval**: The system converts the question into an embedding and
   searches the vector database. The chunk about sick leave is the most
   similar match and is retrieved, even though the employee's wording
   ("How many days...do I get") differs from the document's wording
   ("entitled to 12 days...per calendar year").

4. **Augmented prompt**: The system builds a prompt like: "Using the
   following information, answer the employee's question. Information:
   'Full-time employees are entitled to 12 days of paid sick leave per
   calendar year.' Question: 'How many days of sick leave do I get?'"

5. **Generation**: The LLM answers: "You get 12 days of paid sick leave
   per calendar year, if you are a full-time employee."

Without RAG, the LLM would have no way to know this company-specific
policy and could only guess or say it doesn't know.

## 8. Benefits

- Can reduce hallucination risk by grounding answers in relevant source
  material
- Allows answers to reflect information created after the model's
  training cutoff
- Allows use of private/internal information the model was never trained
  on, without retraining the model itself
- Cheaper and faster to update than retraining or fine-tuning a model —
  updating the knowledge source is enough
- Can provide source citations, since the system knows which chunks were
  retrieved

## 9. Limitations

- Answer quality depends on retrieval quality — if the relevant
  information isn't retrieved, the model cannot use it
- Poorly written or outdated source documents lead to poorly grounded
  answers, even with a good retrieval system
- Retrieval adds latency compared to asking the LLM directly
- RAG reduces hallucination but does not eliminate it — the LLM can still
  misinterpret or misstate retrieved information
- Chunking strategy matters: chunks that are too large may bury the
  relevant detail; chunks that are too small may lose necessary context

## 10. Common Misconceptions (for accuracy checking)

- **Misconception**: RAG permanently teaches the model new information.
  **Correction**: RAG provides information temporarily, within a single
  prompt/response. It does not modify the model's trained parameters.
- **Misconception**: RAG is a type of model.
  **Correction**: RAG is a technique/architecture that combines a
  retrieval system with an existing LLM. It is not itself a model.
- **Misconception**: RAG requires retraining the LLM.
  **Correction**: RAG works with an existing, unmodified LLM. Only the
  external knowledge source needs to be updated to change what
  information is available for retrieval.
- **Misconception**: Semantic search is the same as keyword search.
  **Correction**: Keyword search matches exact words; semantic search
  matches meaning, and can retrieve relevant content even when wording
  differs completely.

## 11. Scope of This Reference

This document describes RAG as a technical concept because the generated
lesson is about teaching RAG to beginners.

The content-generation system itself does not need to be a production RAG
application. This reference document is used as a small curated knowledge
source so that generated lessons can be grounded in verified information.

The retrieval step retrieves relevant sections from this reference
material for the generator and evaluator. This is separate from the RAG
architecture being taught in the lesson — RAG is the subject matter, not
necessarily a description of how this content-generation system itself
must be built, beyond the small grounding layer it uses for accuracy.

## 12. Accuracy Rules

When explaining or checking claims about RAG:

- RAG does not modify an LLM's parameters or weights.
- Retrieved information is provided as text context to the LLM, not as
  raw numerical embeddings.
- Embeddings represent text numerically and enable similarity-based
  (semantic) search.
- The query is embedded using the same embedding model used to embed the
  indexed content.
- Retrieval quality directly affects the quality of the generated answer.
- RAG can reduce hallucination risk but cannot guarantee factual answers.
- RAG does not require retraining the LLM when the external knowledge
  source changes — only the knowledge source needs to be updated.
- RAG is an architecture/technique that combines retrieval with an LLM,
  not a standalone language model itself.