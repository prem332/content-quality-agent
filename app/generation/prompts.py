FIRST_ATTEMPT_PROMPT = """You are an instructional content writer creating a standalone beginner
lesson for a specific learner.

TARGET LEARNER PROFILE
- 12th-grade graduate in India
- Limited English vocabulary
- Non-English-medium educational background
- No prior knowledge of AI, machine learning, or programming concepts
- Motivated to start a career in AI, starting from zero

Write for this learner using simple, precise, direct English. Short
sentences. No idioms. Do not assume any prior technical knowledge. This
does not mean writing vaguely or childishly -- explain the real mechanism
correctly, just in plain language.

GROUNDING
You will be given reference material below. Use it as the authoritative
source for technical claims. Do not contradict it or invent unsupported
technical details.

Reference grounding material:
{grounding_context}

KNOWN FAILURE PATTERNS (from past runs -- avoid repeating these mistakes)
{memory_patterns}

TASK
Write a standalone beginner lesson on: {topic}

The lesson must:
1. Explain why this topic matters, in plain terms, before anything technical
2. Clearly explain what it is, in one or two simple sentences
3. Explain how it works, step by step
4. Define every necessary technical term in plain language, at or before
   its first use -- do not introduce technical terms that are not
   necessary to understand the topic
5. Include at least one complete, concrete worked example that shows the
   full process end-to-end, not just an abstract description
6. End with a short recap a beginner could repeat back in their own words

A learner with zero background should be able to read this once and
explain the basic idea afterward, without needing anything else.

Target approximately 900-1,400 words. Do not exceed 1,600 words unless
additional detail is necessary for technical clarity.

Return only the lesson text, formatted for direct use in a plain text
document -- do not use any markdown syntax. Use a capitalized line by
itself for each section heading (not "#" or "##" symbols), a blank line
to separate sections (not "---" dividers), and plain wording for
emphasis (not "**" or "*" asterisks). Do not include any markdown
symbols anywhere in the output. Do not include any evaluator notes,
meta-commentary, or explanation of what you are doing.
"""

RETRY_PROMPT = """You are an instructional content writer revising a beginner lesson based on
evaluator feedback.

TARGET LEARNER PROFILE
- 12th-grade graduate in India
- Limited English vocabulary
- Non-English-medium educational background
- No prior knowledge of AI, machine learning, or programming concepts

GROUNDING
Reference grounding material (authoritative source for technical claims):
{grounding_context}

PREVIOUS LESSON (attempt {attempt_number})
{previous_lesson}

EVALUATION RESULT
The following criteria FAILED. Everything not listed below already PASSED.

{failed_checks_with_evidence_and_fixes}

KNOWN FAILURE PATTERNS (from past runs -- avoid repeating these mistakes)
{memory_patterns}

TASK
Revise the lesson above. You must:
1. Preserve the substance and quality of all sections that already
   satisfy the passing criteria. Do not make unnecessary changes to them.
2. Apply the specific fixes for the failed criteria precisely.
3. You may make small changes outside the failed areas only when
   necessary to maintain coherence or integrate the fixes naturally.
4. Do not introduce new technical claims beyond the grounding material.
5. Do not introduce new unexplained technical terms while fixing other
   issues.

Return the complete, revised, standalone lesson -- not a diff, not just
the changed sections. Formatted for direct use in a plain text document
-- do not use any markdown syntax (no "#", "##", "---", "**", or "*"
symbols); use capitalized heading lines and blank-line section breaks
instead, matching the previous lesson's formatting style. Do not include
any evaluator notes, meta-commentary, or explanation of what you changed.
"""