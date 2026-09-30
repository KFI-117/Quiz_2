import streamlit as st
from supabase import create_client, Client

# Page configuration for the new 3-Student Quiz Platform
st.set_page_config(
    page_title="Tri-Quiz Battle: Language and GS",
    page_icon="🎓",
    layout="centered",
)

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://uyxeykhgcqubjcwgvzrl.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV5eGV5a2hnY3F1Ympjd2d2enJsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA3NzcyNzMsImV4cCI6MjEwNjM1MzI3M30.7y3FI5oVVoYMCfh8OrUXUceOXV-S9YRZxfyvheuMgL4")

# Define the 3 Students (Aap yahan inke asli naam likh sakte hain)
STUDENTS = ["Faizan", "Kaifi", "Osama"]


@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase: Client = init_supabase()


# Helper functions for Supabase Database
def load_questions():
    try:
        response = (
            supabase.table("quiz_questions")
            .select("*")
            .order("id", desc=False)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return []


def load_user_attempts(username):
    try:
        response = (
            supabase.table("quiz_attempts")
            .select("*")
            .eq("user", username)
            .execute()
        )
        return {att["question_id"]: att for att in response.data} if response.data else {}
    except Exception as e:
        return {}


def save_question_to_db(question_data):
    try:
        supabase.table("quiz_questions").insert(question_data).execute()
        return True
    except Exception as e:
        st.error(f"Error saving question: {e}")
        return False


def delete_question_from_db(q_id):
    try:
        supabase.table("quiz_questions").delete().eq("id", q_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting question: {e}")
        return False


# Main UI Title
st.title("🎓 Tri-Quiz Battle (Language and GS)")
st.write(
    "Multi-peer competitive quizzing platform for 3 candidates. (1/3 Negative Marking)"
)

# Sidebar for Student Selection
st.sidebar.header("👤 Student Profile")
current_user = st.sidebar.selectbox(
    "Select Your Name", ["Select Name"] + STUDENTS
)

if current_user == "Select Name":
    st.warning("⚠️ Please select your profile from the sidebar to begin.")
    st.stop()

# Determine remaining 2 students
other_students = [s for s in STUDENTS if s != current_user]

# Fetch questions and attempts from Supabase
questions_list = load_questions()
user_attempts = load_user_attempts(current_user)

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📝 Add Questions", "🎯 Attempt Quiz", "📊 Scoreboard & Analytics", "⚙️ Manage Questions"]
)

# --- TAB 1: ADD QUESTIONS ---
with tab1:
    st.header("Add New Question")
    st.write(
        f"Questions added here will be **automatically assigned to both** of your peers: **{other_students[0]}** and **{other_students[1]}**."
    )

    with st.form("add_question_form_3s", clear_on_submit=True):
        q_text = st.text_area("Question Statement:")
        opt_a = st.text_input("Option (a)")
        opt_b = st.text_input("Option (b)")
        opt_c = st.text_input("Option (c)")
        opt_d = st.text_input("Option (d)")

        correct_opt = st.selectbox(
            "Correct Answer Option",
            ["Option (a)", "Option (b)", "Option (c)", "Option (d)"],
        )

        explanation_text = st.text_area(
            "Explanation (Optional - Provide reasoning for the correct answer):"
        )

        submitted = st.form_submit_button("Save & Broadcast Question")

        if submitted:
            if not q_text or not opt_a or not opt_b or not opt_c or not opt_d:
                st.error("Please fill in all options (a, b, c, d) and the question text.")
            else:
                success_all = True
                # Automatically loop and save for both remaining students
                for target_student in other_students:
                    new_q = {
                        "creator": current_user,
                        "target": target_student,
                        "question": q_text,
                        "opt_a": opt_a,
                        "opt_b": opt_b,
                        "opt_c": opt_c,
                        "opt_d": opt_d,
                        "answer": correct_opt,
                        "explanation": explanation_text.strip(),
                    }
                    if not save_question_to_db(new_q):
                        success_all = False

                if success_all:
                    st.success(f"🎉 Question successfully saved and assigned to both **{other_students[0]}** and **{other_students[1]}**!")
                    st.rerun()

# --- TAB 2: TAKE QUIZ ---
with tab2:
    st.header(f"Quiz Session ({current_user}'s Test)")

    # Sirf wohi questions dikhenge jo is current user ke target hain
    pending_questions = [
        q for q in questions_list if q.get("target") == current_user
    ]

    if not pending_questions:
        st.info("No pending questions assigned to you right now. Ask your peers to add some!")
    else:
        st.write(f"Total Available Questions: {len(pending_questions)}")

        for idx, q in enumerate(pending_questions[::-1]):
            q_id = q["id"]
            q_num = questions_list.index(q) + 1  
            creator_name = q.get("creator", "Unknown")
            st.markdown(f"### Q{q_num} [Created by: {creator_name}]: {q['question']}")

            if q_id in user_attempts:
                att = user_attempts[q_id]
                st.write(f"**Your Choice:** {att['selected_answer']}")

                opt_map = {
                    "Option (a)": q["opt_a"],
                    "Option (b)": q["opt_b"],
                    "Option (c)": q["opt_c"],
                    "Option (d)": q["opt_d"],
                }
                correct_text = opt_map.get(q["answer"], "")

                if att["selected_answer"] == "Option (e) Question not attempted":
                    st.info(
                        f"ℹ️ You marked this question as **Not Attempted**. Correct"
                        f" Answer: **{correct_text}**"
                    )
                elif att["is_correct"]:
                    st.success("✅ Correct Answer! Great job.")
                else:
                    st.error(
                        f"❌ Incorrect Answer. Correct Answer was:"
                        f" **{correct_text}**"
                    )

                if q.get("explanation"):
                    st.info(f"💡 **Explanation:** {q['explanation']}")
                else:
                    st.caption("*(No explanation provided)*")

                if st.button("🔄 Retry Question", key=f"retry_3s_{q_id}"):
                    try:
                        supabase.table("quiz_attempts").delete().eq("user", current_user).eq("question_id", q_id).execute()
                        st.success("Attempt reset successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error resetting attempt: {e}")

            else:
                with st.form(key=f"q_form_3s_{q_id}"):
                    opts_list = [
                        f"(a) {q['opt_a']}",
                        f"(b) {q['opt_b']}",
                        f"(c) {q['opt_c']}",
                        f"(d) {q['opt_d']}",
                        "(e) Question not attempted",
                    ]

                    selected_choice = st.radio(
                        f"Select your response for Q{q_num}",
                        opts_list,
                        index=None,
                        key=f"ans_radio_3s_{q_id}",
                    )

                    ans_submitted = st.form_submit_button("Check Answer")

                    if ans_submitted:
                        if selected_choice is None:
                            st.warning(
                                "Please select an option or choose 'Question not attempted'."
                            )
                        else:
                            if selected_choice.startswith("(e)"):
                                formatted_choice = "Option (e) Question not attempted"
                                is_correct = False
                            else:
                                option_letter = selected_choice[1]
                                formatted_choice = f"Option ({option_letter}) {q[f'opt_{option_letter}']}"
                                is_correct = (f"Option ({option_letter})" == q["answer"])

                            attempt_payload = {
                                "user": current_user,
                                "question_id": q_id,
                                "selected_answer": formatted_choice,
                                "is_correct": is_correct
                            }

                            try:
                                supabase.table("quiz_attempts").upsert(attempt_payload, on_conflict="user,question_id").execute()
                                st.success("Answer saved successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error recording attempt: {e}")

            st.divider()

# --- TAB 3: PERFORMANCE SCOREBOARD & ANALYTICS ---
with tab3:
    st.header(f"📊 Performance Scoreboard ({current_user})")
    st.markdown("Track evaluation metrics, correct/incorrect attempts, and net scores with 1/3 negative marking (-0.33).")

    if not user_attempts:
        st.info("No attempts recorded yet. Attempt questions in the 'Attempt Quiz' tab to view analytics.")
    else:
        total_attempted = len(user_attempts)
        correct_count = sum(
            1 for att in user_attempts.values() if att["is_correct"]
        )
        skipped_count = sum(
            1
            for att in user_attempts.values()
            if "Question not attempted" in att["selected_answer"]
        )
        incorrect_count = total_attempted - correct_count - skipped_count

        raw_score = correct_count * 1.0
        negative_penalty = round(incorrect_count * 0.33, 2)
        net_score = round(raw_score - negative_penalty, 2)
        accuracy_rate = round((correct_count / total_attempted) * 100, 2) if total_attempted > 0 else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Attempted", total_attempted)
        col2.metric("Correct", correct_count)
        col3.metric("Incorrect", incorrect_count)
        col4.metric("Accuracy", f"{accuracy_rate}%")

        st.markdown("---")

        col_score1, col_score2 = st.columns(2)
        col_score1.metric("Score Without Negative Marking", f"{raw_score} / {len(user_attempts)}")
        col_score2.metric("Net Score (With 1/3 Negative)", f"{net_score} / {len(user_attempts)}")
        
        if skipped_count > 0:
            st.caption(f"Note: You skipped {skipped_count} question(s).")

# --- TAB 4: VIEW & MANAGE QUESTIONS ---
with tab4:
    st.header("📊 Database History & Management")
    st.write("Review all questions stored in the cloud database:")

    if not questions_list:
        st.write("Database is currently empty.")
    else:
        for idx, q in enumerate(questions_list[::-1]):
            q_id = q["id"]
            q_num = len(questions_list) - idx
            opt_map = {
                "Option (a)": q["opt_a"],
                "Option (b)": q["opt_b"],
                "Option (c)": q["opt_c"],
                "Option (d)": q["opt_d"],
            }
            correct_ans_text = opt_map.get(q["answer"], "")

            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(
                    f"**Q{q_num}. [Created by: {q['creator']} -> Assigned to:"
                    f" {q['target']}]** {q['question']}"
                )
                st.write(f" - Correct Answer: {q['answer']} ({correct_ans_text})")
                if q.get("explanation"):
                    st.write(f" - Explanation: {q['explanation']}")

            with col2:
                if st.button("🗑️ Delete", key=f"del_btn_3s_{q_id}"):
                    if delete_question_from_db(q_id):
                        st.success("Question deleted successfully!")
                        st.rerun()

            st.markdown("---")
