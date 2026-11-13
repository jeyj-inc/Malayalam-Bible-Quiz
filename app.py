import json
import random
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
USED_FILE = BASE_DIR / "used_questions.json"
QUIZ_SIZE = 20

st.set_page_config(page_title="മലയാളം ബൈബിൾ ക്വിസ്", page_icon="📖", layout="centered")

@st.cache_data
def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def load_history():
    if not USED_FILE.exists():
        return {"used_ids": [], "last_session_ids": []}
    try:
        with open(USED_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return {
            "used_ids": data.get("used_ids", []),
            "last_session_ids": data.get("last_session_ids", [])
        }
    except (json.JSONDecodeError, OSError):
        return {"used_ids": [], "last_session_ids": []}

def save_history(data):
    with open(USED_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def start_new_quiz():
    all_questions = load_questions()
    history = load_history()
    all_ids = {q["id"] for q in all_questions}
    used_ids = set(history["used_ids"]) & all_ids
    last_ids = set(history["last_session_ids"]) & all_ids

    unused = [q for q in all_questions if q["id"] not in used_ids]

    # Avoid repeating questions until the bank is exhausted.
    if len(unused) >= QUIZ_SIZE:
        selected = random.sample(unused, QUIZ_SIZE)
    else:
        # Finish the current cycle with unused questions, then fill the
        # remaining places while avoiding the immediately previous session.
        selected = list(unused)
        selected_ids = {q["id"] for q in selected}
        refill_pool = [
            q for q in all_questions
            if q["id"] not in selected_ids and q["id"] not in last_ids
        ]
        needed = QUIZ_SIZE - len(selected)
        if len(refill_pool) < needed:
            refill_pool = [q for q in all_questions if q["id"] not in selected_ids]
        selected.extend(random.sample(refill_pool, needed))
        used_ids = set()

    random.shuffle(selected)
    new_ids = [q["id"] for q in selected]
    used_ids.update(new_ids)
    save_history({
        "used_ids": list(used_ids),
        "last_session_ids": new_ids
    })
    st.session_state.quiz_questions = selected
    st.session_state.answers = {}
    st.session_state.submitted = False

questions = load_questions()
if len(questions) < QUIZ_SIZE:
    st.error(f"ക്വിസ് തുടങ്ങാൻ കുറഞ്ഞത് {QUIZ_SIZE} ചോദ്യങ്ങൾ വേണം.")
    st.stop()

st.title("📖 മലയാളം ബൈബിൾ ക്വിസ്")
st.caption("1 ശമൂവേൽ — അദ്ധ്യായങ്ങൾ 8, 9, 10")
st.write("ഓരോ ടെസ്റ്റിലും 20 ചോദ്യങ്ങൾ. ചോദ്യങ്ങൾ പൂർത്തിയാകുന്നതുവരെ ആവർത്തിക്കില്ല.")

if "quiz_questions" not in st.session_state:
    start_new_quiz()

if st.session_state.submitted:
    quiz = st.session_state.quiz_questions
    answers = st.session_state.answers
    score = sum(1 for q in quiz if answers.get(q["id"]) == q["answer"])
    st.subheader("നിങ്ങളുടെ ഫലം")
    st.metric("സ്കോർ", f"{score} / {QUIZ_SIZE}")
    st.progress(score / QUIZ_SIZE)

    for index, q in enumerate(quiz, start=1):
        chosen = answers.get(q["id"])
        correct = chosen == q["answer"]
        with st.expander(f"{index}. {q['question']} — {'ശരി' if correct else 'തെറ്റ്'}"):
            st.write(f"**നിങ്ങളുടെ ഉത്തരം:** {chosen if chosen else 'ഉത്തരം നൽകിയില്ല'}")
            st.write(f"**ശരിയുത്തരം:** {q['answer']}")
            st.write(f"**വചനഭാഗം:** {q['reference']}")
            st.write(q["explanation"])

    if st.button("പുതിയ ടെസ്റ്റ് ആരംഭിക്കുക", type="primary", use_container_width=True):
        start_new_quiz()
        st.rerun()
else:
    st.caption(f"ചോദ്യങ്ങൾ: {len(st.session_state.quiz_questions)}")
    with st.form("bible_quiz_form"):
        for index, q in enumerate(st.session_state.quiz_questions, start=1):
            st.markdown(f"### {index}. {q['question']}")
            st.caption(f"{q['chapter']} · {q['reference']}")
            selected = st.radio(
                "ഒരു ഉത്തരം തിരഞ്ഞെടുക്കുക",
                q["options"],
                index=None,
                key=f"answer_{q['id']}",
                label_visibility="collapsed"
            )
            if selected:
                st.session_state.answers[q["id"]] = selected
            else:
                st.session_state.answers.pop(q["id"], None)
            st.divider()

        submitted = st.form_submit_button("ഉത്തരങ്ങൾ സമർപ്പിക്കുക", type="primary", use_container_width=True)

    if submitted:
        if len(st.session_state.answers) != QUIZ_SIZE:
            st.warning("ദയവായി എല്ലാ 20 ചോദ്യങ്ങൾക്കും ഉത്തരം തിരഞ്ഞെടുക്കുക.")
        else:
            st.session_state.submitted = True
            st.rerun()

with st.sidebar:
    st.header("ക്വിസ് വിവരങ്ങൾ")
    st.write(f"ആകെ ചോദ്യങ്ങൾ: {len(questions)}")
    st.write("ഉൾപ്പെടുത്തിയ അദ്ധ്യായങ്ങൾ: 8, 9, 10")
    st.write("ഡാറ്റാബേസ് ആവശ്യമില്ല. ചോദ്യങ്ങളും ഉപയോഗിച്ച ചോദ്യങ്ങളുടെ വിവരവും JSON ഫയലുകളിൽ സൂക്ഷിക്കുന്നു.")
