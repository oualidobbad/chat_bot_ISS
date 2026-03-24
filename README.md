# chat_bot_ISS

AI-powered educational chatbot built with Google Gemini and Gradio that teaches users about the ISS Cupola module through interactive lessons, quizzes with scoring, and free-form Q&A.

## Project Overview
- What it does: delivers a 6-lesson course about the ISS Cupola module with AI-generated content, 3-question quizzes per lesson, instant feedback with explanations, and cumulative scoring.
- Use cases: interactive learning platform prototype, demonstrating LLM-driven education with structured progression.
- Problem solved: combines AI content generation with pedagogical flow control (lessons → quizzes → feedback → next topic).

## Architecture & Design
- **Backend**: single Python file (`cupola_chatbot.py`) using `google.generativeai` (Gemini 2.5 Flash model).
- **UI**: Gradio Blocks layout with custom CSS (Inter font, gradient navbars, stat boxes, collapsible menus).
- **Core class**: `CupolaTeacher` manages state — `current_topic`, `chat` session, `in_quiz_mode`, `score`, `total_questions`.
- **Flow**: `get_lesson()` → AI generates lesson content → `get_quiz()` → AI generates 3 MCQs → `check_answer()` validates and provides AI-generated explanations for wrong answers.
- **Topics**: 6 predefined ISS Cupola topics (purpose, design, windows, robotic ops, photography, spacewalk monitoring).

## Core Concepts (with code)
- Quiz answer validation with AI-generated feedback:
```python
# cupola_chatbot.py — CupolaTeacher.check_answer()
correct_answer = self._get_correct_answer(self.current_question_index)
if user_letter == correct_answer:
    self.score += 1
    feedback = f"### Correct! The answer is **{correct_answer}**."
else:
    explanation_response = self.chat.send_message(
        f"Explain why '{correct_answer}' is correct and '{user_letter}' is incorrect."
    )
```
- Lesson progression with topic tracking:
```python
# cupola_chatbot.py — CupolaTeacher.get_lesson()
topic = CUPOLA_TOPICS[self.current_topic]
prompt = f"{SYSTEM_PROMPT}\nTeach about: {topic}\nProvide a clear explanation in 3-4 paragraphs."
response = self.chat.send_message(prompt)
```

## Code Walkthrough
1) Configure Gemini API with key; initialize `generativeai.GenerativeModel('gemini-2.5-flash')`.
2) `CupolaTeacher` class: manages lesson/quiz state, chat session, scoring.
3) `get_lesson()`: generates AI lesson for current topic; `get_quiz()`: requests 3 MCQs in strict format.
4) `_extract_question()` / `_get_correct_answer()`: parse quiz text by pattern matching.
5) Gradio UI: main content column (lesson + quiz + feedback) + sidebar (stats + collapsible help).
6) Custom CSS: professional design with gradient headers, animated cards, responsive layout.

## Installation & Setup
- Requires: Python 3, `google-generativeai`, `gradio`.
- Install deps: `pip install google-generativeai gradio`.
- Run: `python cupola_chatbot.py` → opens web UI.

## Usage Guide
- Click **Start Lesson** → read AI-generated content → **Take Quiz** → answer A/B/C → get feedback → **Next Lesson**.
- Use the **Ask Question** box for free-form queries about the Cupola.
- **Reset Course** restarts from lesson 1 with fresh scoring.

## Technical Deep Dive
- Chat history is maintained across lesson/quiz to give the AI context for coherent explanations.
- Quiz parsing uses string splitting to extract questions and correct answers from structured AI output.
- Gradio `gr.update(visible=...)` toggles quiz input/button visibility based on flow state.
- Custom JavaScript initializes collapsible sidebar menus after DOM load.

## Improvements & Future Work
- Replace hardcoded API key with environment variable.
- Add persistent storage for user progress across sessions.
- Expand topic list and add difficulty levels.
- Add image/media content from NASA APIs.

## Author
Oualid Obbad (@oualidobbad)