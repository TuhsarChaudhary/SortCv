import pandas as pd
import re
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
from keybert import KeyBERT

education_hierarchy = {
    "Doctorate": 1.0,
    "Masters Degree": 0.8,
    "Bachelors Degree": 0.6,
    "Diploma": 0.4,
    "High School Level": 0.2
}

eh = [
    "Any",
    "High School Level",
    "Diploma",
    "Bachelors Degree",
    "Masters Degree",
    "Doctorate",
]

def load_sbert_model(model_name):
    return SentenceTransformer(model_name)

model_name = "all-MiniLM-L12-v2"
sbert_model = load_sbert_model(model_name)

# Load heavy models once per Python process to avoid repeated loading cost
kw_model = KeyBERT(model="all-MiniLM-L6-v2")

def clean_text(text):
    # Remove CID artifacts which are common in PDFs
    text = re.sub(r'\(cid:[^\)]+\)', '', text)
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove other common PDF artifacts if needed
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]', '', text)
    return text

def extract_job_description(file):
    # Assume `file` is a string path to a PDF or text file
    if file.endswith(".pdf"):
        text = extract_text(file)
    else:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
    return clean_text(text)

def extract_relevant_job_sections(job_description_text, template_type):
    # Clean CID artifacts from the text
    cleaned_text = re.sub(r'\(cid:[^\)]+\)', '', job_description_text)
    
    if template_type == "UNV Template":
        sections = []
        patterns = [
            r"ASSIGNMENT CONTEXT(.*?)(TASK DESCRIPTION|ELIGIBILITY CRITERIA)",
            r"TASK DESCRIPTION(.*?)(ELIGIBILITY CRITERIA|SKILLS AND EXPERIENCE)",
            r"SKILLS AND EXPERIENCE(.*?)(COMPETENCIES AND VALUES|OTHER INFORMATION)",
            r"COMPETENCIES AND VALUES(.*?)(OTHER INFORMATION|LIVING CONDITIONS)"
        ]
        for pattern in patterns:
            match = re.search(pattern, cleaned_text, re.DOTALL)
            if match:
                sections.append(match.group(1).strip())
        return "\n".join(filter(None, sections))
    
    elif template_type == "SC Template":
        sections = []
        
        # Extract Functions/Key Results Expected
        functions_pattern = r"Functions\s*/\s*Key Results Expected(.*?)(?:IV\.|V\.|Institutional|Competencies)"
        functions_match = re.search(functions_pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
        if functions_match:
            sections.append("FUNCTIONS / KEY RESULTS EXPECTED:\n" + functions_match.group(1).strip())
        
        # Extract Competencies
        competencies_pattern = r"Competencies(.*?)(?:VI\.|Recruitment|Education)"
        competencies_match = re.search(competencies_pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
        if competencies_match:
            sections.append("COMPETENCIES:\n" + competencies_match.group(1).strip())
        
        # Clean up extra whitespace and weird characters
        result = "\n\n".join(filter(None, sections))
        return re.sub(r'\n{3,}', '\n\n', result)  # Replace 3+ newlines with double newlines
    
    elif template_type == "SC Manager Template":
        sections = []
        
        # Extract Functions section
        functions_pattern = r"III\.\s*Functions(.*?)(?:IV\.|Key Performance)"
        functions_match = re.search(functions_pattern, cleaned_text, re.DOTALL)
        if functions_match:
            sections.append("FUNCTIONS:\n" + functions_match.group(1).strip())
        
        # Extract Functional Competencies section
        func_competencies_pattern = r"Functional Competencies(.*?)(?:VI\.|Recruitment|\bEducation\b)"
        func_competencies_match = re.search(func_competencies_pattern, cleaned_text, re.DOTALL)
        if func_competencies_match:
            sections.append("FUNCTIONAL COMPETENCIES:\n" + func_competencies_match.group(1).strip())
        
        # Clean up extra whitespace and weird characters
        result = "\n\n".join(filter(None, sections))
        return re.sub(r'\n{3,}', '\n\n', result)  # Replace 3+ newlines with double newlines

    elif template_type == "IC Consultant Template":
        sections = []
        
        # Extract Roles and Responsibilities section (excluding deliverables and timeline)
        roles_pattern = r"III\.\s*ROLES AND RESPONSIBILITIES(.*?)(?:Deliverables and Timeline|IV\.)"
        roles_match = re.search(roles_pattern, cleaned_text, re.DOTALL)
        if roles_match:
            sections.append("ROLES AND RESPONSIBILITIES:\n" + roles_match.group(1).strip())
        
        # Extract Functional Competencies section
        func_competencies_pattern = r"Functional Competencies(.*?)(?:V\.|QUALIFICATIONS|Education)"
        func_competencies_match = re.search(func_competencies_pattern, cleaned_text, re.DOTALL)
        if func_competencies_match:
            sections.append("FUNCTIONAL COMPETENCIES:\n" + func_competencies_match.group(1).strip())
        
        # Clean up extra whitespace and weird characters
        result = "\n\n".join(filter(None, sections))
        return re.sub(r'\n{3,}', '\n\n', result)  # Replace 3+ newlines with double newlines
    
    #return cleaned_text  # Return cleaned text if no template matches
    return "" # Return empty string if no template matches

def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    return re.sub(r'\s+', ' ', text)

# def scale_experience(candidate_years, required_years):
#     if required_years == 0:
#         required_years = 1  # Avoid division by zero if no experience is required
#     return min(candidate_years / required_years, 1.0) if required_years > 0 else 0.0

def scale_experience(candidate_years, required_years, max_yoe=None, weight_experience=0):
    if weight_experience == 1.0 and max_yoe:  # Normalize only in this edge case
        return candidate_years / max_yoe if max_yoe > 0 else 0.0
    
    if required_years == 0:
        required_years = 1  # Avoid division by zero
    return min(candidate_years / required_years, 1.0)    


def scale_education(candidate_degree, required_degree):
    candidate_score = education_hierarchy.get(candidate_degree, 0.0)
    required_score = education_hierarchy.get(required_degree, 0.0)

    # Debugging output for scaled education calculation
    #print(f"Candidate Degree: {candidate_degree}, Candidate Score: {candidate_score}")
    #print(f"Required Degree: {required_degree}, Required Score: {required_score}")

    if required_score == 0:
        if candidate_score == 0:
            return 0.0  # No match for either degree
        return 1.0  # If required degree is missing, consider as fully qualified

    return candidate_score / required_score if required_score > 0 else 0.0

def rank_cvs(job_description, required_experience, required_degree, df, weight_experience, weight_qualifications, weight_skills):
    job_embedding = sbert_model.encode(preprocess_text(job_description), convert_to_tensor=True)
    
    rankings = []
    global kw_model

    #test
    max_yoe = df['YOE'].max()

    # Iterate over rows by column name instead of relying on tuple positions
    for idx, row in df.reset_index(drop=True).iterrows():
        
        # ------------------------------------------------------------------
        # Robust field extraction with sensible fall-backs
        # ------------------------------------------------------------------
        employment_history = (
            row.get("Employment History")
            or row.get("Employment_History")
            or ""
        )
        
        highest_degree = (
            row.get("Highest Degree")
            or row.get("Highest_Degree")
            or ""
        )
        
        yoe = row.get("YOE", 0)
        
        applicant_name = (
            row.get("Name")
            or row.get("Applicant Name")
            or row.get("Applicant_Name")
            or f"CV {idx + 1}"
        )
        
        age = row.get("Age")
        lang = row.get("Languages", "")
        gender = row.get("Gender", "")
        nationality = row.get("Nationality", "")

        # ------------------------------------------------------------------
        # Embedding & scoring
        # ------------------------------------------------------------------

        processed_cv = preprocess_text(str(employment_history))
        cv_embedding = sbert_model.encode(processed_cv, convert_to_tensor=True)
        similarity_score = util.cos_sim(job_embedding, cv_embedding).item()

        mkws = []
        kws = kw_model.extract_keywords(job_description, top_n=20, keyphrase_ngram_range=(1, 2), stop_words='english')
    
        for kw, _ in kws:
            kws_clean = kw.lower()
            if kws_clean in processed_cv:
                mkws.append(kws_clean)
            match_count = len(mkws)
            total_keywords = len(kws)
            score = match_count / total_keywords if total_keywords else 0       

        hybrid_score = (similarity_score *0.7) + (score * 0.3)

        # Scale experience and education
        # scaled_experience = scale_experience(yoe, required_experience)
        scaled_experience = scale_experience(yoe, required_experience, max_yoe, weight_experience)
        scaled_education = scale_education(highest_degree, required_degree)
        
        # Final score calculation
        final_score = (
            weight_experience * scaled_experience
            + weight_qualifications * scaled_education
            + weight_skills * hybrid_score
        )

        # Debugging output for final score calculation
        #print(similarity_score)

        final_score = max(0.0, min(final_score, 1.0))  # clamp 0-1
        
        rankings.append(
            (
                #f"CV {idx + 1}",
                row.get("CV ID"),
                applicant_name,
                age,
                lang,
                highest_degree,
                yoe,
                final_score,
                employment_history,
                gender,
                nationality,
            )
        )

    sort_rank = sorted(rankings, key=lambda x: x[4], reverse=True)    

    dsr = pd.DataFrame(sort_rank, columns=[
                'CV', 'Applicant Name', 'Age', 'Languages', 'Highest Degree', 'YOE', 'Final Score', 'Employment History', 'Gender', 'Nationality'
            ])
    
    dsr.insert(0, 'Rank', range(1, len(df) + 1))

    #ddsr = dsr.drop(columns=['Employment History'])

    return dsr





# #testing
# file_path = r"C:\Users\InkyPhantom\Desktop\Projects\cv sorter files\UNV Graphics Designer.pdf"
# one = extract_job_description(file_path)
# two = extract_relevant_job_sections(one, "UNV Template")
# print(two)

# print()
