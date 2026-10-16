import streamlit as st
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="JEE Assessment Student Portal", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Generate Custom Test", "Take JEE Mock Test", "Adaptive Test", "Performance History"])

if "current_test" not in st.session_state:
    st.session_state.current_test = None
if "student_answers" not in st.session_state:
    st.session_state.student_answers = {}
if "test_start_time" not in st.session_state:
    st.session_state.test_start_time = None
if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None

def render_test_ui(test_data):
    st.header(f"Test: {test_data.get('subject', 'Assessment')}")
    questions = test_data.get("questions", [])
    
    if not questions:
        st.warning("No questions found for this configuration.")
        return
        
    for idx, q in enumerate(questions):
        st.markdown(f"### Q{idx+1}: {q.get('question_text')}")
        q_id = str(q.get('id'))
        q_type = q.get('question_type', 'mcq_single')
        
        if q_type == 'mcq_single':
            options = q.get("options", {})
            opt_list = []
            for k, v in options.items():
                opt_list.append(f"{k}: {v}")
                
            choice = st.radio("Select Answer:", ["Not Attempted"] + opt_list, key=f"q_{q_id}")
            if choice != "Not Attempted":
                st.session_state.student_answers[q_id] = choice.split(":")[0]
            elif q_id in st.session_state.student_answers:
                del st.session_state.student_answers[q_id]
        else:
            choice = st.text_input("Enter Numerical Answer:", key=f"q_{q_id}")
            if choice:
                st.session_state.student_answers[q_id] = choice
            elif q_id in st.session_state.student_answers:
                del st.session_state.student_answers[q_id]
                
    if st.button("Submit Test", type="primary"):
        with st.spinner("Evaluating your responses..."):
            time_taken = (time.time() - st.session_state.test_start_time) / 60 if st.session_state.test_start_time else 0
            payload = {
                "question_ids": [q['id'] for q in questions],
                "answers": st.session_state.student_answers,
                "time_taken_minutes": time_taken
            }
            try:
                res = requests.post(f"{BASE_URL}/evaluate/", json=payload)
                if res.status_code == 200:
                    st.session_state.evaluation_result = res.json()
                    st.session_state.current_test = None
                    st.session_state.student_answers = {}
                    st.success("Test submitted successfully! View your detailed results below or under Performance History.")
                    st.rerun()
                else:
                    st.error(f"Error evaluating test: {res.text}")
            except Exception as e:
                st.error(f"Backend not reachable. Ensure Django server is running. {e}")

def render_performance_card(record, key_suffix=""):
    marks = record.get("marks")
    if marks is None:
        marks = record.get("total_marks", 0)
        
    total_q = record.get("total_questions", 0)
    correct = record.get("correct", 0)
    wrong = record.get("wrong", 0)
    unattempted = record.get("unattempted", total_q - (correct + wrong))
    attempted = correct + wrong
    accuracy = round((correct / attempted * 100), 1) if attempted > 0 else 0.0
    time_taken = round(record.get("time_taken_minutes", 0), 2)
    
    # 1. Summary Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Marks", f"{marks}", help="+4 for correct, -1 for wrong")
    c2.metric("Attempted", f"{attempted} / {total_q}")
    c3.metric("Accuracy", f"{accuracy}%")
    c4.metric("Correct / Wrong", f"{correct} ✅ / {wrong} ❌")
    c5.metric("Time Taken", f"{time_taken} mins")
    
    # 2. Subject Breakdown Table
    subject_results = record.get("subject_results", {})
    if subject_results:
        st.subheader("📚 Subject-wise Breakdown")
        table_data = []
        for sub, sres in subject_results.items():
            table_data.append({
                "Subject": sub,
                "Total Questions": sres.get("total", 0),
                "Attempted": sres.get("attempted", 0),
                "Correct": sres.get("correct", 0),
                "Wrong": sres.get("wrong", 0),
                "Unattempted": sres.get("unattempted", 0),
                "Marks": sres.get("marks", 0)
            })
        st.dataframe(table_data, use_container_width=True)
        
    # 3. Topic Analysis (Strong, Average, Weak)
    topic_feedback = record.get("topic_feedback", {})
    if topic_feedback:
        weak_list = []
        avg_list = []
        strong_list = []
        not_attempted_list = []
        
        for sub, topics in topic_feedback.items():
            for tname, tdata in topics.items():
                perf = tdata.get("performance")
                att = tdata.get("attempted", 0)
                corr = tdata.get("correct", 0)
                pct = round(tdata.get("percentage", 0), 1)
                item = f"**{tname}** ({sub}): {corr}/{att} correct ({pct}%)"
                
                if perf == "Needs Improvement":
                    weak_list.append(item)
                elif perf == "Average":
                    avg_list.append(item)
                elif perf == "Strong":
                    strong_list.append(item)
                else:
                    not_attempted_list.append(f"{tname} ({sub})")
                    
        st.subheader("🎯 Topic Mastery Analysis")
        col_w, col_a, col_s = st.columns(3)
        with col_w:
            st.error(f"🔴 Weak Topics ({len(weak_list)})")
            if weak_list:
                for w in weak_list:
                    st.markdown(f"- {w}")
            else:
                st.caption("No weak topics detected.")
                
        with col_a:
            st.warning(f"🟡 Average Topics ({len(avg_list)})")
            if avg_list:
                for a in avg_list:
                    st.markdown(f"- {a}")
            else:
                st.caption("No average topics detected.")
                
        with col_s:
            st.success(f"🟢 Strong Topics ({len(strong_list)})")
            if strong_list:
                for s in strong_list:
                    st.markdown(f"- {s}")
            else:
                st.caption("No strong topics detected.")

    # 4. Action Button: Adaptive Test from this Record
    if weak_list or avg_list:
        st.markdown("---")
        if st.button(f"🎯 Launch Adaptive Test on Weak Topics", key=f"btn_adapt_{key_suffix}"):
            with st.spinner("Generating adaptive test based on weak topics..."):
                try:
                    payload = {
                        "topic_feedback": topic_feedback,
                        "number": 10
                    }
                    res = requests.post(f"{BASE_URL}/adaptive-test/", json=payload)
                    if res.status_code == 200:
                        st.session_state.current_test = res.json()
                        st.session_state.student_answers = {}
                        st.session_state.test_start_time = time.time()
                        st.success("Adaptive test ready! Switch to 'Adaptive Test' tab or take it now.")
                        st.rerun()
                    else:
                        st.error("Failed to generate adaptive test.")
                except Exception as e:
                    st.error(f"Error launching adaptive test: {e}")

# Page Navigation Handling
if page == "Home":
    st.title("🎓 Student Assessment Dashboard")
    st.write("Welcome to the JEE Assessment RAG System! Prepare for JEE with intelligent RAG-driven tests and adaptive learning.")
    
    if st.session_state.evaluation_result:
        st.markdown("---")
        st.header("📋 Latest Test Result Summary")
        render_performance_card(st.session_state.evaluation_result, key_suffix="home")
    else:
        st.info("Select **'Take JEE Mock Test'** or **'Generate Custom Test'** from the sidebar to start your preparation!")

elif page == "Generate Custom Test":
    st.title("📝 Generate Custom Test")
    if st.session_state.current_test:
        render_test_ui(st.session_state.current_test)
    else:
        subject = st.selectbox("Subject", ["Physics", "Chemistry", "Mathematics", ""])
        chapter = st.text_input("Chapter (optional)")
        number = st.number_input("Number of questions", min_value=1, max_value=50, value=5)
        
        if st.button("Generate Test", type="primary"):
            with st.spinner("Retrieving questions from database..."):
                try:
                    payload = {"number": number}
                    if subject: payload["subject"] = subject
                    if chapter: payload["chapter"] = chapter
                    
                    res = requests.post(f"{BASE_URL}/generate-test/", json=payload)
                    if res.status_code == 200:
                        st.session_state.current_test = res.json()
                        st.session_state.student_answers = {}
                        st.session_state.test_start_time = time.time()
                        st.rerun()
                    else:
                        st.error("Failed to generate test.")
                except Exception as e:
                    st.error(f"Backend error: {e}")

elif page == "Take JEE Mock Test":
    st.title("🏆 Full JEE Mock Test (Weightage Based)")
    if st.session_state.current_test:
        render_test_ui(st.session_state.current_test)
    else:
        st.write("This mock exam selects questions strictly following JEE chapter weightages and official pattern (MCQs + Numericals).")
        if st.button("Generate JEE Mock Test", type="primary"):
            with st.spinner("Extracting questions from Supabase according to JEE weightage..."):
                try:
                    payload = {"is_jee_paper": True}
                    res = requests.post(f"{BASE_URL}/generate-test/", json=payload)
                    if res.status_code == 200:
                        st.session_state.current_test = res.json()
                        st.session_state.student_answers = {}
                        st.session_state.test_start_time = time.time()
                        st.rerun()
                    else:
                        st.error("Failed to generate test.")
                except Exception as e:
                    st.error(f"Backend error: {e}")

elif page == "Adaptive Test":
    st.title("🧠 Adaptive Test")
    if st.session_state.current_test:
        render_test_ui(st.session_state.current_test)
    else:
        st.write("Adaptive tests dynamically prioritize weak and average topics based on your previous test performances.")
        
        col1, col2 = st.columns(2)
        with col1:
            test_mode = st.radio("Adaptive Basis:", ["Cumulative (Across All Past Tests)", "Most Recent Test Only"])
        with col2:
            num_q = st.number_input("Number of Questions:", min_value=3, max_value=25, value=10)
            
        if st.button("Generate Adaptive Test", type="primary"):
            with st.spinner("Analyzing historical mastery and generating questions..."):
                try:
                    payload = {"number": num_q}
                    if test_mode == "Cumulative (Across All Past Tests)":
                        payload["cumulative"] = True
                    else:
                        if st.session_state.evaluation_result:
                            payload["topic_feedback"] = st.session_state.evaluation_result.get("topic_feedback", {})
                        else:
                            payload["cumulative"] = True
                            
                    res = requests.post(f"{BASE_URL}/adaptive-test/", json=payload)
                    if res.status_code == 200:
                        test_data = res.json()
                        if test_data.get("questions"):
                            st.session_state.current_test = test_data
                            st.session_state.student_answers = {}
                            st.session_state.test_start_time = time.time()
                            st.rerun()
                        else:
                            st.warning("No questions could be matched for the current adaptive topics. Please take a mock test first.")
                    else:
                        st.error(f"Error generating test: {res.text}")
                except Exception as e:
                    st.error(f"Backend error: {e}")

elif page == "Performance History":
    st.title("📊 Detailed Performance History")
    
    col_ref, col_cum = st.columns([1, 2])
    with col_ref:
        refresh = st.button("🔄 Refresh History")
        
    try:
        res = requests.get(f"{BASE_URL}/performance-history/")
        if res.status_code == 200:
            history = res.json()
            if not history:
                st.info("No test history records found yet. Complete a test to see your analytics!")
            else:
                with col_cum:
                    if st.button("🚀 Generate Cumulative Adaptive Test (All History)", type="primary"):
                        with st.spinner("Generating adaptive test from overall history..."):
                            ad_res = requests.post(f"{BASE_URL}/adaptive-test/", json={"cumulative": True, "number": 10})
                            if ad_res.status_code == 200:
                                st.session_state.current_test = ad_res.json()
                                st.session_state.student_answers = {}
                                st.session_state.test_start_time = time.time()
                                st.success("Adaptive test ready! Switch to 'Adaptive Test' tab or start below.")
                                st.rerun()

                st.write(f"Total Tests Attempted: **{len(history)}**")
                
                # Display tests in reverse chronological order (latest first)
                for idx, record in enumerate(reversed(history)):
                    test_num = len(history) - idx
                    test_date = record.get("timestamp", record.get("test_date", "N/A"))
                    
                    with st.expander(f"📌 Test #{test_num} — {test_date[:19].replace('T', ' ')} (Marks: {record.get('marks', record.get('total_marks', 0))})", expanded=(idx == 0)):
                        render_performance_card(record, key_suffix=f"hist_{test_num}")
                        
        else:
            st.error("Failed to load history from backend.")
    except Exception as e:
        st.error(f"Backend not reachable. Ensure Django server is running. {e}")
