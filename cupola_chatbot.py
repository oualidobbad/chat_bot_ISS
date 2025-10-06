import google.generativeai as genai
import gradio as gr

# Your API key
API_KEY = "AIzaSyD_GPtXH_AGWHBOQ3HOjlYq3yKeawLqTT4"

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ API configured successfully with gemini-2.5-flash model!")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    exit(1)

# Topics about the ISS Cupola module
CUPOLA_TOPICS = [
    "What is the Cupola and its purpose on the ISS?",
    "The design and structure of the Cupola",
    "The seven windows and their functions",
    "How astronauts use the Cupola for robotic operations",
    "Photography and Earth observation from the Cupola",
    "The Cupola's role in spacewalk monitoring"
]

SYSTEM_PROMPT = """You are a friendly teacher helping complete beginners learn about the Cupola module 
of the International Space Station. Explain concepts in simple, clear language without jargon."""


class CupolaTeacher:
    def __init__(self):
        self.current_topic = 0
        self.chat = None
        self.in_quiz_mode = False
        self.current_quiz = None
        self.quiz_questions = []
        self.current_question_index = 0
        self.score = 0
        self.total_questions = 0
        
    def start_chat(self):
        if self.chat is None:
            self.chat = model.start_chat(history=[])
        
    def get_lesson(self):
        try:
            self.start_chat()
            
            if self.current_topic >= len(CUPOLA_TOPICS):
                final_score_pct = (self.score / self.total_questions * 100) if self.total_questions > 0 else 0
                return (
                    f"## 🎓 Course Completed!\n\n"
                    f"### Final Score: {self.score}/{self.total_questions} ({final_score_pct:.0f}%)\n\n"
                    f"**Topics Mastered:**\n" + "\n".join([f"- ✅ {topic}" for topic in CUPOLA_TOPICS])
                )
            
            topic = CUPOLA_TOPICS[self.current_topic]
            prompt = f"{SYSTEM_PROMPT}\n\nTeach about: {topic}\n\nProvide a clear, beginner-friendly explanation in 3-4 paragraphs."
            
            response = self.chat.send_message(prompt)
            
            self.in_quiz_mode = False
            self.current_question_index = 0
            return f"## Lesson {self.current_topic + 1}: {topic}\n\n{response.text}"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_quiz(self):
        try:
            self.start_chat()
            
            if self.current_topic >= len(CUPOLA_TOPICS):
                return "No more quizzes available.", ""
            
            prompt = """Create exactly 3 multiple choice questions about what we just discussed. 
            For each question:
            1. Write a clear question
            2. Provide exactly 3 options labeled A), B), and C)
            3. Indicate which option is correct
            
            Format EXACTLY like this:
            
            Question 1: [Your question]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            Correct Answer: [A/B/C]
            
            Question 2: [Your question]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            Correct Answer: [A/B/C]
            
            Question 3: [Your question]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            Correct Answer: [A/B/C]"""
            
            response = self.chat.send_message(prompt)
            
            self.current_quiz = response.text
            self.in_quiz_mode = True
            self.current_question_index = 0
            
            first_question = self._extract_question(0)
            
            return "## 📝 Quiz Time!", first_question
            
        except Exception as e:
            return f"❌ Error: {str(e)}", ""
    
    def _extract_question(self, question_number):
        if not self.current_quiz:
            return "No quiz available."
        
        lines = self.current_quiz.split('\n')
        question_text = ""
        in_question = False
        
        target = f"Question {question_number + 1}:"
        
        for i, line in enumerate(lines):
            if target in line:
                in_question = True
                question_text = f"### Question {question_number + 1} of 3\n\n"
            
            if in_question:
                question_text += line + "\n"
                
                if "Correct Answer:" in line:
                    question_text = question_text.replace(line, "").strip()
                    break
        
        if not question_text:
            return f"Question {question_number + 1} not found."
        
        return question_text
    
    def _get_correct_answer(self, question_number):
        if not self.current_quiz:
            return None
        
        lines = self.current_quiz.split('\n')
        target = f"Question {question_number + 1}:"
        found_question = False
        
        for line in lines:
            if target in line:
                found_question = True
            if found_question and "Correct Answer:" in line:
                answer = line.split("Correct Answer:")[-1].strip()
                for char in answer.upper():
                    if char in ['A', 'B', 'C']:
                        return char
        return None
    
    def check_answer(self, user_answer):
        try:
            self.start_chat()
            
            if not self.in_quiz_mode:
                return "⚠️ Please start a quiz first!", "", ""
            
            user_answer = user_answer.strip().upper()
            if not user_answer:
                return "Please enter your answer (A, B, or C)", "", ""
            
            user_letter = None
            for char in user_answer:
                if char in ['A', 'B', 'C']:
                    user_letter = char
                    break
            
            if not user_letter:
                return "Please answer with A, B, or C only", "", ""
            
            correct_answer = self._get_correct_answer(self.current_question_index)
            
            if not correct_answer:
                return "❌ Error: Could not find correct answer.", "", ""
            
            self.total_questions += 1
            
            if user_letter == correct_answer:
                self.score += 1
                feedback = f"### ✅ Correct!\n\nGreat job! The answer is **{correct_answer}**."
            else:
                explanation_prompt = f"""The student answered '{user_letter}' but the correct answer is '{correct_answer}'. 
                Briefly explain why '{correct_answer}' is correct and why '{user_letter}' is incorrect. Keep it simple and encouraging."""
                
                explanation_response = self.chat.send_message(explanation_prompt)
                
                feedback = (
                    f"### ❌ Incorrect\n\n"
                    f"**Your answer:** {user_letter}  \n"
                    f"**Correct answer:** {correct_answer}\n\n"
                    f"**Explanation:**\n\n{explanation_response.text}"
                )
            
            self.current_question_index += 1
            
            if self.current_question_index >= 3:
                self.in_quiz_mode = False
                score_pct = (self.score / self.total_questions * 100) if self.total_questions > 0 else 0
                next_question = (
                    f"## 📊 Quiz Complete!\n\n"
                    f"**Overall Score:** {self.score}/{self.total_questions} ({score_pct:.0f}%)\n\n"
                    f"Click **Next Lesson** to continue! 🚀"
                )
            else:
                next_question = self._extract_question(self.current_question_index)
            
            return feedback, next_question, self.get_progress()
            
        except Exception as e:
            return f"❌ Error: {str(e)}", "", ""
    
    def next_topic(self):
        if self.current_topic < len(CUPOLA_TOPICS):
            self.current_topic += 1
        return self.get_lesson()
    
    def ask_question(self, user_question):
        try:
            self.start_chat()
            
            if not user_question.strip():
                return "Please type a question."
            
            prompt = f"{SYSTEM_PROMPT}\n\nStudent question: {user_question}\n\nProvide a helpful, simple answer."
            
            response = self.chat.send_message(prompt)
            
            return f"**Q:** {user_question}\n\n**A:** {response.text}"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_progress(self):
        total = len(CUPOLA_TOPICS)
        current = min(self.current_topic, total)
        return f"Lesson {current}/{total} • Score: {self.score}/{self.total_questions}"


teacher = CupolaTeacher()

def start_lesson():
    return (
        teacher.get_lesson(), 
        teacher.get_progress(), 
        "", 
        "",
        gr.update(visible=False),
        gr.update(visible=False)
    )

def start_quiz():
    quiz_intro, first_question = teacher.get_quiz()
    return (
        quiz_intro, 
        teacher.get_progress(), 
        first_question, 
        "",
        gr.update(visible=True),
        gr.update(visible=True)
    )

def submit_answer(user_answer):
    feedback, next_question, progress = teacher.check_answer(user_answer)
    show_input = "Quiz Complete" not in next_question
    return (
        feedback, 
        next_question, 
        progress, 
        "",
        gr.update(visible=show_input),
        gr.update(visible=show_input)
    )

def next_lesson():
    return (
        teacher.next_topic(), 
        teacher.get_progress(), 
        "", 
        "",
        gr.update(visible=False),
        gr.update(visible=False)
    )

def ask_question(question):
    return teacher.ask_question(question)

def reset_chatbot():
    global teacher
    teacher = CupolaTeacher()
    return (
        "🔄 Reset complete! Start your first lesson.", 
        teacher.get_progress(), 
        "", 
        "",
        gr.update(visible=False),
        gr.update(visible=False)
    )


# Professional CSS with FIXED collapsible menu
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.gradio-container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    background: #f8f9fa !important;
}

#top-nav {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 20px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 0;
}

#logo {
    color: white;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

#user-info {
    color: #e0e0e0;
    font-size: 14px;
    background: rgba(255,255,255,0.1);
    padding: 8px 16px;
    border-radius: 20px;
}

#progress-container {
    background: white;
    padding: 24px 40px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    margin-bottom: 32px;
}

#progress-bar-fill {
    background: linear-gradient(90deg, #4CAF50 0%, #81C784 100%);
    height: 8px;
    border-radius: 4px;
    transition: width 0.3s ease;
    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
}

#progress-text {
    color: #424242;
    font-size: 14px;
    font-weight: 600;
    margin-top: 12px;
    text-align: center;
}

.content-card {
    background: white;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 24px;
    border: 1px solid #e0e0e0;
}

.quiz-card {
    background: #fff8e1;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 24px;
    border: 2px solid #ffd54f;
}

.feedback-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-top: 16px;
    border-left: 4px solid #4CAF50;
}

.btn-primary {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%) !important;
    color: white !important;
    border: none !important;
    padding: 14px 32px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    text-transform: none !important;
    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3) !important;
}

.btn-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4) !important;
}

.btn-secondary {
    background: white !important;
    color: #2196F3 !important;
    border: 2px solid #2196F3 !important;
    padding: 14px 32px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    text-transform: none !important;
}

.btn-secondary:hover {
    background: #e3f2fd !important;
    transform: translateY(-2px) !important;
}

.btn-success {
    background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%) !important;
    color: white !important;
    border: none !important;
    padding: 14px 32px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3) !important;
}

.btn-success:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4) !important;
}

textarea, input {
    border: 2px solid #e0e0e0 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
    transition: all 0.2s ease !important;
    background: white !important;
}

textarea:focus, input:focus {
    border-color: #2196F3 !important;
    box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1) !important;
    outline: none !important;
}

label {
    color: #424242 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.sidebar-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 24px;
    border: 1px solid #e0e0e0;
}

.stat-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    margin-bottom: 16px;
}

.stat-box h4 {
    font-size: 32px;
    font-weight: 700;
    margin: 0;
}

.stat-box p {
    font-size: 14px;
    margin: 8px 0 0 0;
    opacity: 0.9;
}

/* FIXED Collapsible Menu Styles */
.collapsible-item {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 16px;
    border: 1px solid #e0e0e0;
    overflow: hidden;
}

.collapsible-header {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    color: white;
    padding: 16px 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    font-size: 16px;
    transition: all 0.3s ease;
    user-select: none;
}

.collapsible-header:hover {
    background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
}

.collapsible-arrow {
    font-size: 18px;
    transition: transform 0.3s ease;
    display: inline-block;
}

.collapsible-content {
    display: none;
    padding: 20px;
    background: white;
}

.collapsible-content.show {
    display: block;
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.collapsible-content ul {
    padding-left: 20px;
    color: #616161;
    line-height: 1.8;
    margin: 0;
    list-style-type: disc;
}

.collapsible-content p {
    color: #616161;
    line-height: 1.7;
    margin: 0 0 12px 0;
}

.collapsible-content li {
    margin-bottom: 10px;
}

.collapsible-content strong {
    color: #1a1a2e;
    font-weight: 600;
}

.help-section {
    background: #e3f2fd;
    border-radius: 8px;
    padding: 20px;
    margin-top: 24px;
    border-left: 4px solid #2196F3;
}

.help-section h4 {
    color: #1976D2;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
}

.help-section p {
    color: #424242;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
}

@media (max-width: 768px) {
    #top-nav {
        padding: 16px 20px;
        flex-direction: column;
        gap: 12px;
    }
    
    .content-card, .quiz-card {
        padding: 20px;
    }
}

footer {
    display: none !important;
}

html {
    scroll-behavior: smooth;
}

.markdown-text h2 {
    color: #1a1a2e;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 3px solid #2196F3;
}

.markdown-text h3 {
    color: #424242;
    font-size: 20px;
    font-weight: 600;
    margin-top: 24px;
    margin-bottom: 12px;
}

.markdown-text p {
    color: #616161;
    font-size: 16px;
    line-height: 1.7;
    margin-bottom: 16px;
}

.markdown-text ul, .markdown-text ol {
    color: #616161;
    line-height: 1.8;
    margin-bottom: 16px;
}

.markdown-text strong {
    color: #1a1a2e;
    font-weight: 600;
}
"""

# Create the interface
with gr.Blocks(css=custom_css, title="ISS Cupola Learning Platform", theme=gr.themes.Soft(), head="""
<script>
function initCollapsible() {
    setTimeout(function() {
        const headers = document.querySelectorAll('.collapsible-header');
        
        headers.forEach(function(header) {
            header.onclick = function() {
                const content = this.nextElementSibling;
                const arrow = this.querySelector('.collapsible-arrow');
                
                // Toggle content visibility
                if (content.classList.contains('show')) {
                    content.classList.remove('show');
                    arrow.style.transform = 'rotate(0deg)';
                } else {
                    content.classList.add('show');
                    arrow.style.transform = 'rotate(180deg)';
                }
            };
        });
    }, 1000);
}

// Initialize on page load
window.addEventListener('load', initCollapsible);

// Also initialize after a delay to catch dynamically loaded content
setTimeout(initCollapsible, 2000);
</script>
""") as demo:
    
    # Top Navigation
    gr.HTML("""
    <div id="top-nav">
        <div id="logo">🛰️ ISS Cupola Learning Platform</div>
        <div id="user-info">👤 oualidobbad • 2025-10-05 11:57:07 UTC</div>
    </div>
    """)
    
    # Progress Bar
    gr.HTML("""
    <div id="progress-container">
        <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
            <div id="progress-bar-fill" style="width: 0%;"></div>
        </div>
        <div id="progress-text">Lesson 0/6 • Score: 0/0</div>
    </div>
    """)
    
    progress_display = gr.Textbox(value="Lesson 0/6 • Score: 0/0", visible=False)
    
    # Main Layout
    with gr.Row():
        # Main Content Column
        with gr.Column(scale=7):
            # Lesson Content
            gr.HTML("<div class='content-card'>")
            lesson_output = gr.Markdown(
                value="## 👋 Welcome to ISS Cupola Learning\n\nReady to explore one of the most fascinating modules on the International Space Station?\n\nThe Cupola is famous for its seven windows and breathtaking views of Earth and space.\n\n**Click 'Start Lesson' to begin your journey!**",
                elem_classes=["markdown-text"]
            )
            
            with gr.Row():
                lesson_btn = gr.Button("📚 Start Lesson", elem_classes=["btn-primary"], size="lg")
            gr.HTML("</div>")
            
            # Quiz Section
            gr.HTML("<div class='quiz-card'>")
            quiz_output = gr.Markdown(
                value="### Quiz questions will appear here\n\nComplete a lesson first, then click **Take Quiz** to test your knowledge!",
                elem_classes=["markdown-text"]
            )
            
            answer_input = gr.Textbox(
                label="Your Answer",
                placeholder="Type A, B, or C",
                lines=1,
                max_lines=1,
                visible=False
            )
            
            submit_btn = gr.Button(
                "✓ Submit Answer", 
                elem_classes=["btn-success"], 
                size="lg",
                visible=False
            )
            gr.HTML("</div>")
            
            # Feedback Section
            gr.HTML("<div class='feedback-card'>")
            feedback_output = gr.Markdown(
                value="### Your feedback will appear here\n\nAnswer the quiz questions to get instant feedback and explanations!",
                elem_classes=["markdown-text"]
            )
            gr.HTML("</div>")
            
            # Navigation Buttons
            with gr.Row():
                quiz_btn = gr.Button("📝 Take Quiz", elem_classes=["btn-secondary"], size="lg")
                next_btn = gr.Button("→ Next Lesson", elem_classes=["btn-primary"], size="lg")
                reset_btn = gr.Button("↺ Reset Course", elem_classes=["btn-secondary"], size="lg")
        
        # Sidebar Column
        with gr.Column(scale=3):
            # Course Stats
            gr.HTML("""
            <div class='sidebar-card'>
                <div class='stat-box'>
                    <h4>6</h4>
                    <p>Total Lessons</p>
                </div>
                <div class='stat-box' style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);'>
                    <h4>18</h4>
                    <p>Quiz Questions</p>
                </div>
            </div>
            """)
            
            # FIXED Collapsible Menu: How to Use
            gr.HTML("""
            <div class='collapsible-item'>
                <div class='collapsible-header'>
                    <span>📖 How to Use</span>
                    <span class='collapsible-arrow'>▼</span>
                </div>
                <div class='collapsible-content'>
                    <ul>
                        <li><strong>Start Lesson</strong> - Learn about the Cupola module</li>
                        <li><strong>Take Quiz</strong> - Test your understanding with 3 questions</li>
                        <li><strong>Submit Answer</strong> - Get instant feedback on your answers</li>
                        <li><strong>Next Lesson</strong> - Continue to the next topic</li>
                        <li><strong>Ask Question</strong> - Get help anytime you need it</li>
                    </ul>
                </div>
            </div>
            """)
            
            # FIXED Collapsible Menu: Did You Know?
            gr.HTML("""
            <div class='collapsible-item'>
                <div class='collapsible-header'>
                    <span>🌟 Did You Know?</span>
                    <span class='collapsible-arrow'>▼</span>
                </div>
                <div class='collapsible-content'>
                    <p><strong>Seven Windows:</strong> The Cupola has six side windows and one top window, providing a 360-degree view of Earth and space.</p>
                    <p><strong>Robotic Operations:</strong> Astronauts use the Cupola to control the International Space Station's robotic arm for capturing spacecraft and moving equipment.</p>
                    <p><strong>Photography Hub:</strong> Many of the stunning Earth photos you see from space are taken from the Cupola! 📸</p>
                    <p><strong>Observation Deck:</strong> It's like the ISS's "control tower" and the best spot for Earth observation!</p>
                </div>
            </div>
            """)
            
            # Ask Question Section
            gr.HTML("""
            <div class='sidebar-card'>
                <h3 style='color: #1a1a2e; font-size: 18px; font-weight: 700; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e0e0e0;'>💬 Ask a Question</h3>
            """)
            question_input = gr.Textbox(
                label="",
                placeholder="Type your question here...",
                lines=3
            )
            ask_btn = gr.Button("Ask", elem_classes=["btn-primary"])
            question_output = gr.Markdown(value="", elem_classes=["markdown-text"])
            gr.HTML("</div>")
            
            # Help Section
            gr.HTML("""
            <div class='help-section'>
                <h4>💡 Need Help?</h4>
                <p>If you're stuck, use the "Ask a Question" feature to get personalized help about any topic!</p>
            </div>
            """)
    
    # JavaScript for progress bar
    demo.load(None, None, None, js="""
    function updateProgress(text) {
        const match = text.match(/Lesson (\\d+)\\/(\\d+)/);
        if (match) {
            const current = parseInt(match[1]);
            const total = parseInt(match[2]);
            const percentage = (current / total) * 100;
            const bar = document.getElementById('progress-bar-fill');
            const textEl = document.getElementById('progress-text');
            if (bar) bar.style.width = percentage + '%';
            if (textEl) textEl.textContent = text;
        }
    }
    """)
    
    # Connect buttons
    lesson_btn.click(
        fn=start_lesson,
        outputs=[lesson_output, progress_display, quiz_output, feedback_output, answer_input, submit_btn]
    ).then(
        fn=None,
        inputs=[progress_display],
        outputs=None,
        js="(text) => updateProgress(text)"
    )
    
    quiz_btn.click(
        fn=start_quiz,
        outputs=[lesson_output, progress_display, quiz_output, feedback_output, answer_input, submit_btn]
    ).then(
        fn=None,
        inputs=[progress_display],
        outputs=None,
        js="(text) => updateProgress(text)"
    )
    
    submit_btn.click(
        fn=submit_answer,
        inputs=[answer_input],
        outputs=[feedback_output, quiz_output, progress_display, answer_input, answer_input, submit_btn]
    ).then(
        fn=None,
        inputs=[progress_display],
        outputs=None,
        js="(text) => updateProgress(text)"
    )
    
    next_btn.click(
        fn=next_lesson,
        outputs=[lesson_output, progress_display, quiz_output, feedback_output, answer_input, submit_btn]
    ).then(
        fn=None,
        inputs=[progress_display],
        outputs=None,
        js="(text) => updateProgress(text)"
    )
    
    reset_btn.click(
        fn=reset_chatbot,
        outputs=[lesson_output, progress_display, quiz_output, feedback_output, answer_input, submit_btn]
    ).then(
        fn=None,
        inputs=[progress_display],
        outputs=None,
        js="(text) => updateProgress(text)"
    )
    
    ask_btn.click(
        fn=ask_question,
        inputs=question_input,
        outputs=question_output
    )

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 ISS CUPOLA LEARNING PLATFORM - FIXED COLLAPSIBLE MENU")
    print("=" * 70)
    print("✨ Fixed: Collapsible menu now works properly!")
    print("👤 User: oualidobbad")
    print("📅 Date: 2025-10-05 11:57:07 UTC")
    print("=" * 70)
    demo.launch(share=False, server_port=7860)