import numpy as np
import pandas as pd
import re
from pdfminer.high_level import extract_text

Country = ['United States', 'Afghanistan', 'Albania', 'Algeria', 'American Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antarctica', 'Antigua And Barbuda', 'Argentina', 'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia', 'Bosnia And Herzegowina', 'Botswana', 'Bouvet Island', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Cayman Islands', 'Central African Rep', 'Chad', 'Chile', 'China', 'Christmas Island', 'Cocos Islands', 'Colombia', 'Comoros', 'Congo', 'Cook Islands', 'Costa Rica', 'Cote D`ivoire', 'Croatia', 'Cuba', 'Cyprus', 'Czech Republic', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'East Timor', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Ethiopia', 'Falkland Islands (Malvinas)', 'Faroe Islands', 'Fiji', 'Finland', 'France', 'French Guiana', 'French Polynesia', 'French S. Territories', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guam', 'Guatemala', 'Guinea', 'Guinea-bissau', 'Guyana', 'Haiti', 'Honduras', 'Hong Kong', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Korea (North)', 'Korea (South)', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macau', 'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Martinique', 'Mauritania', 'Mauritius', 'Mayotte', 'Mexico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montserrat', 'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'Netherlands Antilles', 'New Caledonia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Norfolk Island', 'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Pitcairn', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Reunion', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts And Nevis', 'Saint Lucia', 'St Vincent/Grenadines', 'Samoa', 'San Marino', 'Sao Tome', 'Saudi Arabia', 'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'St. Helena', 'St.Pierre', 'Sudan', 'Suriname', 'Swaziland', 'Sweden', 'Switzerland', 'Syrian Arab Republic', 'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Togo', 'Tokelau', 'Tonga', 'Trinidad And Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'Uruguay', 'Uzbekistan', 'Vanuatu', 'Vatican City State', 'Venezuela', 'Viet Nam', 'Virgin Islands (British)', 'Virgin Islands (U.S.)', 'Western Sahara', 'Yemen', 'Yugoslavia', 'Zaire', 'Zambia', 'Zimbabwe']


def clean_text(text):
    # Remove CID artifacts which are common in PDFs
    text = re.sub(r'\(cid:[^\)]+\)', '', text)
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove other common PDF artifacts if needed
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]', '', text)
    return text

def split_pdf_to_cvs(file_path):
    text = extract_text(file_path)
    text = clean_text(text)
    
    # Debug: count how many headers we can find
    header_matches = re.findall(r"Applicant\s+Details\s+Report\s+For", text, flags=re.IGNORECASE)
    #print(f"Found {len(header_matches)} applicant headers in PDF.")

    # Split by more flexible delimiter
    cvs = re.split(r"\bApplicant\s+Details\s+Report\s+For\b", text, flags=re.IGNORECASE)
    # print(re.search(r"Nationality(?:\(ies\))? at Birth:\s*(\w+)", cvs[55], re.IGNORECASE))
    return [cv.strip() for cv in cvs if cv.strip()]


def extract_gender(cv_text):
    gender_match = re.search(r"Gender:\s*(Male|Female)", cv_text, re.IGNORECASE)
    return gender_match.group(1).capitalize() if gender_match else "Not Specified"

def extract_personal_info(cv_text):
    info_match = re.search(r"Personal Information\s*(.*?)\s*Applicant's", cv_text, re.DOTALL | re.IGNORECASE)
    return info_match.group(1).strip() if info_match else "Not Specified"

def extract_employment_history(cv_text):
    employment_sections = re.findall(
        r"DESCRIPTION OF YOUR DUTIES AND RELATED ACCOMPLISHMENTS(.*?)Reason for Leaving:",
        cv_text, re.DOTALL
    )
    return "\n\n".join(section.strip() for section in employment_sections) if employment_sections else "No Employment History Found"

def extract_nationality(pi_text): #personal information text
    lcv_text = pi_text.lower()
    #print(lcv_text)
    c = []

    for country in Country:
        if country.lower() in lcv_text:
            #print(f"Found country: {country.name}")
            c.append(country)
            return c
    if len(c) == 0:
        return ["Not Specified"]

def extract_details(cv_text):
    name = re.search(r"^(.*?)[\r\n]", cv_text)
    degree = re.search(r"Highest Degree:\s*(.*?)\s*Years of Experience:", cv_text)
    experience = re.search(r"Years of Experience:\s*(\d+)", cv_text)
    return (
        name.group(1).strip() if name else "Unknown",
        degree.group(1).strip() if degree else "Not Specified",
        int(experience.group(1)) if experience else 0
    )

def extract_all(cv_pdf_file):
            
        ll = []
        cv_text = split_pdf_to_cvs(cv_pdf_file)
        #print(cv_text[1])

        

        for idx, cv_text in enumerate(cv_text):
            applicant_name, highest_degree, years_experience = extract_details(cv_text)
            gender = extract_gender(cv_text)
            perinfo = extract_personal_info(cv_text)
            nation = extract_nationality(perinfo)
            employment_history = extract_employment_history(cv_text)
            ll.append((
                f"CV {idx + 1}",
                applicant_name,
                highest_degree,
                years_experience,
                gender,
                nation,
                employment_history
            ))
        
        df = pd.DataFrame(ll, columns=["CV ID", "Name", "Highest Degree", "YOE", "Gender", "Nationality", "Employment History"])
        # ddf = df.drop(columns=["Employment History"])
        # ddf.insert(0, 'Sr. No.', range(1, len(df) + 1))
        #print(df)

        #st.dataframe(df, use_container_width=True, hide_index=True)
        return df