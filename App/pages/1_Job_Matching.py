import streamlit as st
import uuid
from API import AdzunaAPI
from API import NewsAPI
from datetime import datetime, timedelta

#Importing classes
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

#Gemini imports
import google.generativeai as genai
genai.configure(api_key="AIzaSyDwao9o8O9moUGK-0bLfNdpifF1mwvs3E4")


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from classes import Jobs, Candidate, CandidateResultsManager, CVMatcher, CandidateEvaluator


llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-pro-002",
    temperature=0.3,
    google_api_key="AIzaSyDwao9o8O9moUGK-0bLfNdpifF1mwvs3E4"  # 🔑 explicitly pass the key here
)
matcher = CVMatcher(llm)


# --- SESSION STATE INIT ---
if "results_manager" not in st.session_state:
    st.session_state.results_manager = CandidateResultsManager()

if "jobs_instance" not in st.session_state:
    st.session_state.jobs_instance = Jobs(
        app_id="0b31602c", 
        api_key="f3051eb4a97fb6f81ed113699ecde36b",  
        country="us",
        num_pages=1
    )

jobs_instance = st.session_state.jobs_instance
results_manager = st.session_state.results_manager


# --- STREAMLIT PAGE ---
st.title("🎯 Job Matching and Screening")

# Get jobs and build selectbox
df_jobs = jobs_instance.get_jobs_df()

if df_jobs.empty:
    st.warning("⚠️ No jobs found. Please check your API credentials or connection.")
else:
    job_options = df_jobs[["id", "title", "company"]].apply(
        lambda row: f"{row['id']} | {row['title']} at {row['company']}", axis=1
    ).tolist()

    selected_job_string = st.selectbox("Select a Job to Apply For:", job_options)
    selected_job_id = selected_job_string.split(" | ")[0]

    selected_row = df_jobs[df_jobs["id"] == selected_job_id]

    if selected_row.empty:
        st.error("❌ Selected job not found.")

    else:
        selected_job = selected_row.iloc[0].to_dict()

    # Show job info
    st.markdown(f"**Job Title:** {selected_job['title']}")
    st.markdown(f"**Company:** {selected_job['company']}")
    st.markdown(f"**Description:** {selected_job['description']}")

#After Job Selection for the NewsAPI
selected_job = selected_row.iloc[0].to_dict()


# --- CV MATCHING & SCORING ---
st.subheader("📄 Upload Your CV for Evaluation")

cv_file = st.file_uploader("Upload your CV (PDF format only)", type="pdf")

if cv_file:
    with st.spinner("🔍 Analyzing your CV with Gemini..."):
        matcher = CVMatcher(llm)
        cv_text = matcher.extract_text_from_pdf(cv_file)

        # Match CV to the selected job
        match_result = matcher.match_cv_to_job(
            cv_text,
            selected_job["title"],
            selected_job["description"]
        )

    st.success("✅ CV evaluation complete!")

    st.markdown("### 🔎 CV Evaluation Result")
    st.markdown(f"```\n{match_result}\n```")


# --- 📝 SCREENING QUESTIONS ---
st.subheader("📝 Answer Screening Questions")

# Generate screening questions with Gemini
questions = jobs_instance.generate_questions(selected_job_id, llm)
user_answers = []

# Create candidate object (customize this as needed)
candidate = Candidate(name="Anonymous")  # Replace with input if collecting user name

# Show question form
with st.form("questionnaire"):
    st.markdown("Please answer the following questions:")
    for idx, question in enumerate(questions):
        answer = st.text_area(f"{idx+1}. {question}", key=f"q_{idx}")
        user_answers.append({"question": question, "answer": answer})
    submitted = st.form_submit_button("Submit Answers")

# Once form is submitted, evaluate answers
if submitted:
    with st.spinner("🧠 Evaluating your answers..."):
        evaluator = CandidateEvaluator(llm)
        scored_answers = evaluator.score_answers(selected_job, user_answers)
        avg_score = evaluator.calculate_average_score(scored_answers)

        # Save in session state for later use (important!)
        st.session_state.scored_answers = scored_answers
        st.session_state.avg_score = avg_score
        st.session_state.candidate = candidate

        # Add answers to candidate object
        candidate.add_answers(scored_answers)
        candidate.set_average_score(avg_score)

        # Save to ranking manager
        results_manager.add_candidate_result(
            job_id=selected_job["id"],
            job_title=selected_job["title"],
            user_id=candidate.user_id,
            name=candidate.name,
            average_score=avg_score,
            answers=scored_answers
        )

    st.success(f"✅ Submission complete! Your average score is **{avg_score}/10**")

    # --- 📊 Show detailed feedback
    st.markdown("### 📊 Detailed Feedback")
    for item in scored_answers:
        st.markdown(f"- **Q:** {item['question']}")
        st.markdown(f"  - 📝 **Your Answer:** {item['answer']}")
        st.markdown(f"  - ✅ **Score:** {item['score']}/10")
        st.markdown(f"  - 💡 **Explanation:** {item['explanation']}")

# --- 💬 FOLLOW-UP FEEDBACK ---
if "scored_answers" in st.session_state:
    st.subheader("💬 Ask Gemini for Further Feedback")
    user_followup = st.text_input("Ask a follow-up question (e.g. 'How can I improve my answers?')")

    if user_followup:
        qa_context = ""
        for idx, item in enumerate(st.session_state.scored_answers, 1):
            qa_context += f"\nQuestion {idx}: {item['question']}\n"
            qa_context += f"Answer: {item['answer']}\n"
            qa_context += f"Evaluation: Score: {item['score']}\nExplanation: {item['explanation']}\n"

        prompt_template = PromptTemplate.from_template("""
        You are an AI career coach helping a candidate improve their job application responses.

        Job Title: {job_title}
        Job Description: {job_description}

        Candidate's previous answers and evaluations:
        {qa_evaluations}

        Candidate's follow-up question:
        "{user_question}"

        Please respond helpfully, constructively, and specifically.
        """)

        final_prompt = prompt_template.format(
            job_title=selected_job["title"],
            job_description=selected_job["description"],
            qa_evaluations=qa_context,
            user_question=user_followup
        )

        feedback = llm.invoke(final_prompt)
        st.markdown("### 📣 Gemini's Feedback")
        st.write(feedback.content)

# --- CANDIDATE RANKING ---
st.subheader("🏆 Candidate Ranking for This Job")
ranked = results_manager.get_ranked_candidates(selected_job["id"])

for idx, cand in enumerate(ranked, 1):
    st.write(f"{idx}. {cand['name']} ({cand['user_id']}) — Score: {cand['average_score']}/10")


# --- COMPANY NEWS ---
# Initialize NewsAPI
news_api = NewsAPI(api_key="9e47d5c4e7374f29a69f83554ed9c6b9")

# Get company name from selected job
company_name = selected_job["company"]
today = datetime.today()
from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

# Fetch news articles for this company
news_df = news_api.get_news(company=company_name, from_date=from_date)

with st.expander("📰 View recent news about this company"):
    if news_df.empty:
        st.info(f"No recent news found for **{company_name}**.")
    else:
        for idx, row in news_df.iterrows():
            st.markdown(f"**🗞️ {row['title']}**")
            st.markdown(f"{row['description']}")
            st.markdown(f"[Read more ↗]({row['url']})")
            st.markdown("---")

