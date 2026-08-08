# Introduction to RAG (Retrieval-Augmented Generation)

## Why does this matter?

Language models acquire a substantial body of knowledge during their
training process; however, that knowledge does not automatically
incorporate information generated after training was completed, nor does
it include private or organization-specific information that was never
part of the training data in the first place. Consequently, when a
question depends on such information, the model requires some additional
mechanism by which the necessary information can be made available to it
at the moment the question is asked.

## What is RAG?

RAG, an abbreviation denoting Retrieval-Augmented Generation, refers to
precisely such a mechanism. It functions according to two sequential
steps: first, information relevant to the question is located; second,
that located information is provided to the model together with the
question itself, so that the model's response draws upon both the
question and the information it has just been given. It should be noted
that this provided information does not become a permanent part of the
model; it is made available only for the purpose of answering that
particular question.

## How does RAG work?

The two steps described above occur in the following order. First, when a
question is asked, the system searches through a collection of stored
information in order to locate the portions most relevant to that
question, a determination made on the basis of meaning rather than exact
wording, so that relevant information can be found even if it is phrased
differently from the question itself. Second, the portions of information
identified as most relevant are combined with the original question and
given to the model, which then uses both together to produce its
response.

## A worked example

**Question**: "What is our company's refund policy?"

**Information located**: Searching the company's policy documents, the
system finds the following relevant sentence: "Customers can request a
refund within 30 days of purchase."

**Response produced**: Given this sentence together with the original
question, the model produces the response: "You can request a refund
within 30 days of your purchase."

Without this mechanism, the model would have had no way of knowing this
company-specific rule, since it was never part of the model's training.

## Quick recap

- A language model's training does not automatically include new or
  private information, so an additional mechanism is needed to supply
  such information when it is required to answer a question.
- This mechanism works in two steps: first locating relevant information,
  then providing that information to the model together with the
  question.
- The model itself is not permanently changed; the located information is
  used only for that specific question.
