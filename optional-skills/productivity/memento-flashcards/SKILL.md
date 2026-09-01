---
name: memento-flashcards
description: "Spaced-repetition flashcards: create, review, quiz, export."
version: 1.0.0
author: Memento AI
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [Education, Flashcards, Spaced Repetition, Learning, Quiz, YouTube]
    requires_toolsets: [terminal]
    category: productivity
---

# Memento Flashcards

role: local flashcard/spaced-repetition operator
do: classify intent; generate Q/A; store atomically; fetch due cards; grade free text; reveal answer/feedback; rate/retire; generate validated five-card YouTube quiz; import/export/stats
inputs: fact; explicit flashcard request; collection; answer; YouTube URL; CSV path; card ID; rating
outputs: card JSON; due/review sequence; brief plain-text feedback; next interval; quiz cards; CSV/stats
¬: activate for general Q&A; create implicit card without confirmation; edit JSON directly; hide answer/feedback; skip rate; invent quiz items; persist secrets

Memento is a local file-based spaced-repetition system. Card content is
agent-generated; no external API keys required. User-facing review/quiz replies:
plain text only, brief, neutral, no Markdown, extra praise, pep, or long explanation.

## When to Use

- explicit fact-to-card request or "remember this"
- due-card review with adaptive intervals and free-text grading
- five-question quiz from a YouTube transcript
- card/deck inspection, CSV import/export, statistics, deletion

Do not use for general Q&A, coding, ordinary conversation, or non-memory work.

## Quick Reference

| User intent | Action |
|---|---|
| "Remember that X" / "save this as a flashcard" | Generate Q/A, call `memento_cards.py add` |
| factual statement without flashcard wording | Ask "Want me to save this as a Memento flashcard?"; create only after yes |
| "Create a flashcard" | Ask Q, A, collection; call `memento_cards.py add` |
| "Review my cards" | Call `memento_cards.py due`, present one by one |
| "Quiz me on [YouTube URL]" | `youtube_quiz.py fetch VIDEO_ID`; generate 5; `memento_cards.py add-quiz` |
| "Export my cards" | `memento_cards.py export --output PATH` |
| "Import cards from CSV" | `memento_cards.py import --file PATH --collection NAME` |
| "Show my stats" | `memento_cards.py stats` |
| "Delete a card" | `memento_cards.py delete --id ID` |
| "Delete a collection" | `memento_cards.py delete-collection --collection NAME` |

## Prerequisites and Storage

No API key. Helpers:

- `~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py`
- `~/.hermes/skills/productivity/memento-flashcards/scripts/youtube_quiz.py`

Cards live at:

```
~/.hermes/skills/productivity/memento-flashcards/data/cards.json
```

Never edit `cards.json` directly. Always use script subcommands; atomic
temp-file-then-rename writes prevent corruption. File appears on first use.

## Procedure

### 1. Classify card activation

1. explicit intent: "memento", "flashcard", "remember this", "save this card", "add a card" → create directly
2. implicit intent: factual statement without flashcard wording → ask exactly: "Want me to save this as a Memento flashcard?"; wait for confirmation
3. no intent: coding, question, instructions, conversation, or non-memory task → do not activate

### 2. Generate/store a fact card

Turn statement into a recall Q/A pair. Internal generation contract:

```
Turn the factual statement into a front-back pair.
Return exactly two lines:
Q: <question text>
A: <answer text>

Statement: "{statement}"
```

Question tests one key fact; answer is concise/direct. Store:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add \
  --question "What year did World War 2 end?" \
  --answer "1945" \
  --collection "History"
```

Default collection: `"General"`. Script returns JSON confirmation.

For an explicit create request, ask Q, A, and optional collection, then call
`memento_cards.py add`.

### 3. Review due cards

Fetch cards where `next_review_at <= now`:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

Optional collection:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due --collection "History"
```

Interaction is binding:

1. show only question; wait
2. compare response to expected answer
3. tell grade, correct answer, and next interval before anything else
4. rate: correct→easy, partial→good, incorrect→hard
5. show next question

Grade correct if key fact right despite wording; partial if right track but core
detail missing; incorrect if wrong/off-topic. Exact feedback forms:

- correct: "Correct. Answer: {answer}. Next review in 7 days."
- partial: "Close. Answer: {answer}. {what they missed}. Next review in 3 days."
- incorrect: "Not quite. Answer: {answer}. Next review tomorrow."

Example interaction:

> **Agent:** What year did the Berlin Wall fall?
>
> **User:** 1991
>
> **Agent:** Not quite. The Berlin Wall fell in 1989. Next review is tomorrow.
> *(agent calls: memento_cards.py rate --id ABC --rating hard --user-answer "1991")*
>
> Next question: Who was the first person to walk on the moon?

Rate command:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py rate \
  --id CARD_ID --rating easy --user-answer "what the user said"
```

Never skip answer/feedback. No due cards: "No cards due for review right now.
Check back later!" User can say "retire this card"; use `--rating retire`.

### 4. Apply intervals

| Rating | Interval | ease_streak | Status change |
|---|---|---|---|
| **hard** | +1 day | reset to 0 | stays learning |
| **good** | +3 days | reset to 0 | stays learning |
| **easy** | +7 days | +1 | if ease_streak >= 3 → retired |
| **retire** | permanent | reset to 0 | → retired |

`learning` = active rotation; `retired` = absent from review. Three consecutive
`easy` ratings auto-retire.

### 5. Generate YouTube quiz

When user supplies YouTube URL and asks quiz:

1. extract ID, e.g. `dQw4w9WgXcQ` from `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
2. fetch transcript:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/youtube_quiz.py fetch VIDEO_ID
```

Returns `{"title": "...", "transcript": "..."}` or error. If
`missing_dependency`, tell user:

```bash
pip install youtube-transcript-api
```

3. use first 15,000 transcript characters; generate five questions with exact contract:

```
You are creating a 5-question quiz for a podcast episode.
Return ONLY a JSON array with exactly 5 objects.
Each object must contain keys 'question' and 'answer'.

Selection criteria:
- Prioritize important, surprising, or foundational facts.
- Skip filler, obvious details, and facts that require heavy context.
- Never return true/false questions.
- Never ask only for a date.

Question rules:
- Each question must test exactly one discrete fact.
- Use clear, unambiguous wording.
- Prefer What, Who, How many, Which.
- Avoid open-ended Describe or Explain prompts.

Answer rules:
- Each answer must be under 240 characters.
- Lead with the answer itself, not preamble.
- Add only minimal clarifying detail if needed.
```

4. validate valid JSON, exactly 5 items, non-empty string `question`/`answer`; retry once on failure
5. store:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add-quiz \
  --video-id "VIDEO_ID" \
  --questions '[{"question":"...","answer":"..."},...]' \
  --collection "Quiz - Episode Title"
```

Script deduplicates by `video_id`; existing cards are reported, not recreated.

6. ask one by one: `Question 1/5: ...`; hide answer/hints; wait; grade with
review rules; visibly show grade/correct answer/next due; then rate and show next
question in same message. Every answer gets feedback before next question.

Rate example:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py rate \
  --id CARD_ID --rating easy --user-answer "what the user said"
```

### 6. Export/import CSV

Export:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py export \
  --output ~/flashcards.csv
```

Produces headerless three-column CSV: `question,answer,collection`.

Import:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py import \
  --file ~/flashcards.csv \
  --collection "Imported"
```

Input columns: question, answer, optional collection column 3; absent column 3
uses `--collection`.

### 7. Inspect statistics

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
```

JSON fields: `total`, `learning`, `retired`, `due_now`, and `collections`.

## Pitfalls

- never edit `cards.json`; use commands for atomic writes
- YouTube transcript may be disabled or lack English; inform user and suggest another video
- missing `youtube-transcript-api` requires the exact install command
- thousands-row imports may produce verbose JSON; summarize
- support both `youtube.com/watch?v=ID` and `youtu.be/ID`
- preserve plain-text, brief, neutral feedback and answer-before-next-card ordering

## Verification

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add --question "Capital of France?" --answer "Paris" --collection "General"
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

Repo checkout tests:

```bash
pytest tests/skills/test_memento_cards.py tests/skills/test_youtube_quiz.py -q
```

Agent verification: review feedback is plain/brief and always gives answer
before next card; YouTube quiz gives visible feedback before each next question.