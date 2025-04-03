#Importing the necessary libraries
import os
import re
import uuid
import fitz  # PyMuPDF to read PDFs
import pandas as pd
from typing import List, Dict
from API import AdzunaAPI, NewsAPI
from langchain.prompts import PromptTemplate

#LLM import
class CVMatcher:
    def __init__(self, llm):  
        self.llm = llm

import pandas as pd
import re
from API import AdzunaAPI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate


#class that assures everything related to jobs
#getting the jobs, ids and questions

class Jobs:

    #app_id = 0b31602c
    #api_key = f3051eb4a97fb6f81ed113699ecde36b

    def __init__(self, app_id: str, api_key: str, country: str = "us", num_pages: int = 20):
        self.app_id = app_id
        self.api_key = api_key
        self.country = country
        self.num_pages = num_pages
        self.df = self._load_jobs()

    def _load_jobs(self) -> pd.DataFrame:
        api = AdzunaAPI(app_id=self.app_id, api_key=self.api_key, country=self.country)
        all_jobs = api.fetch_jobs(num_pages=self.num_pages)

        def extract_job_id(url):
            match = re.search(r"/details/(\d+)", url)
            return match.group(1) if match else None

        df = pd.DataFrame([{
            "id": extract_job_id(job["redirect_url"]),
            "title": job["title"],
            "location": job["location"]["display_name"],
            "category": job.get("category", {}).get("label", ""),
            "description": job["description"],
            "company": job.get("company", {}).get("display_name", ""),
            "url": job["redirect_url"],
            "questions": None
        } for job in all_jobs])

        return df

    #does not invoke the API again, just return what was already requested
    def get_jobs_df(self) -> pd.DataFrame:
        return self.df

    def generate_questions(self, job_id: str, llm: ChatGoogleGenerativeAI) -> list[str]:
        """
        Ensures a job has questions. If not, generates and attaches them using Gemini.
        Returns the final list of questions.
        """
        idx = self.df[self.df["id"] == job_id].index

        if not len(idx):
            raise ValueError(f"Job with ID {job_id} not found.")

        job = self.df.loc[idx[0]]

        if job["questions"] is not None and isinstance(job["questions"], list):
            print("Using existing questions.")
            return job["questions"]

        print("No questions found, generating with Gemini...")

        # Generate using Gemini
        prompt = PromptTemplate.from_template("""
        You are helping a hiring manager prepare for candidate screening.

        Job Title: {job_title}
        Job Description: {job_description}

        Generate 3 screening questions. Only return the questions as a numbered list.
        """)

        response = llm.invoke(prompt.format(
            job_title=job["title"],
            job_description=job["description"]
        ))

        questions = self._clean_questions(response.content)
        self.df.at[idx[0], "questions"] = questions

        return questions

    #lists the questions and removes any number or unwanted space from the questions
    def _clean_questions(self, raw: str) -> list[str]:
        lines = raw.strip().split("\\n")
        return [re.sub(r"^\\s*\\d+[\\.)]\\s*", "", line).strip() for line in lines if line.strip()]

#class that creates the candidate/user of the app

class Candidate:
    def __init__(self, name: str):
        self.user_id = str(uuid.uuid4())  # e.g. '3f9f53de-e1b3-4556-90ad-7d32e8c5164a'
        self.name = name
        self.answers = []
        self.average_score = 0.0

    def add_answers(self, answers: list):
        self.answers = answers

    def set_average_score(self, score: float):
        self.average_score = score

    def to_dict(self, job_id: str, job_title: str) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "job_id": job_id,
            "job_title": job_title,
            "average_score": self.average_score,
            "answers": self.answers
        }


#class that evaluates answers from different candidates

class CandidateEvaluator:
    def __init__(self, llm):
        self.llm = llm

    def score_answers(self, job: dict, user_answers: List[Dict[str, str]]) -> List[Dict]:
        scored_answers = []
        for qa in user_answers:
            result = self.score_each_answer(
                job["title"],
                job["description"],
                qa["question"],
                qa["answer"]
            )

            score = self.extract_score(result)
            explanation = self.extract_explanation(result)

            scored_answers.append({
                "question": qa["question"],
                "answer": qa["answer"],
                "score": score,
                "explanation": explanation
            })
        return scored_answers

    def score_each_answer(self, job_title, job_description, question, answer):
        prompt = f"""
        You are an AI recruiter evaluating a candidate's response.

        Job Title: {job_title}
        Job Description: {job_description}

        Question: {question}
        Candidate's Answer: {answer}

        Give a score from 0 to 10 and explain your reasoning.
        Format:
        Score: X
        Explanation: ...
        """
        return self.llm.invoke(prompt).content

    @staticmethod
    def extract_score(text):
        match = re.search(r"Score:\s*(\d+)", text)
        return int(match.group(1)) if match else 0

    @staticmethod
    def extract_explanation(text):
        return text.split("Explanation:", 1)[-1].strip()

    def calculate_average_score(self, scored_answers: List[Dict]) -> float:
        scores = [ans["score"] for ans in scored_answers]
        return round(sum(scores) / len(scores), 2) if scores else 0.0

#class that creates the candidate results per job

class CandidateResultsManager:
    def __init__(self):
        self.results: List[Dict] = []

    def add_candidate_result(
        self,
        job_id: str,
        job_title: str,
        user_id: str,
        name: str,
        average_score: float,
        answers: List[Dict]
    ):
        self.results.append({
            "job_id": job_id,
            "job_title": job_title,
            "user_id": user_id,
            "name": name,
            "average_score": average_score,
            "answers": answers
        })

    def get_all_results(self) -> List[Dict]:
        return self.results

    def get_results_for_job(self, job_id: str) -> List[Dict]:
        return [r for r in self.results if r["job_id"] == job_id]

    def get_ranked_candidates(self, job_id: str) -> List[Dict]:
        job_results = self.get_results_for_job(job_id)
        return sorted(job_results, key=lambda c: c["average_score"], reverse=True)

    def get_candidate_result(self, user_id: str, job_id: str) -> Dict:
        for result in self.results:
            if result["user_id"] == user_id and result["job_id"] == job_id:
                return result
        return {}
    
#class that reads the cv and checks if it relates with the job

class CVMatcher:
    def __init__(self, llm):
        self.llm = llm

    def extract_text_from_pdf(self, file) -> str:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()

    def match_cv_to_job(self, cv_text, job_title, job_description) -> str:
        prompt = f"""
        You are a career advisor.

        Here is a candidate's CV:
        {cv_text}

        They are applying for:
        Title: {job_title}
        Description: {job_description}

        Evaluate their fit. Score from 0–10 and explain your reasoning.
        Format:
        Score: X
        Explanation: ...
        """
        return self.llm.invoke(prompt).content
