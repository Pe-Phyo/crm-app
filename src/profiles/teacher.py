from .base import SCHEMA as BASE_SCHEMA

# Extend the identity section from base
SCHEMA = {
    "sections": BASE_SCHEMA["sections"] + [
        {
            "id": "teaching_subjects",
            "legend": "Teaching Subjects",
            "fields": [
                {
                    "type": "repeater",
                    "name": "subjects",
                    "fields": [
                        {"name": "subject_id", "label": "Subject ID", "type": "text"},
                        {"name": "subject_name", "label": "Subject Name", "type": "text"},
                        {"name": "level", "label": "Level", "type": "text"},
                        {"name": "curriculum_id", "label": "Curriculum ID", "type": "text"},
                        {"name": "years_exp", "label": "Years Experience", "type": "number", "min": 0}
                    ]
                }
            ]
        },
        {
            "id": "teaching_modes",
            "legend": "Teaching Modes",
            "fields": [
                {
                    "type": "checkboxes",
                    "name": "modes",
                    "options": [
                        {"value": "online", "label": "Online"},
                        {"value": "home_tuition", "label": "Home Tuition"},
                        {"value": "student_home", "label": "Student's Home"},
                        {"value": "tutor_home", "label": "Tutor's Home"},
                        {"value": "learning_centre", "label": "Learning Centre"}
                    ]
                }
            ]
        },
        {
            "id": "teaching_styles",
            "legend": "Teaching Style",
            "fields": [
                {
                    "type": "checkboxes",
                    "name": "styles",
                    "options": [
                        {"value": "patient", "label": "Patient"},
                        {"value": "structured", "label": "Structured"},
                        {"value": "interactive", "label": "Interactive"},
                        {"value": "discussion_based", "label": "Discussion-based"},
                        {"value": "exam_focused", "label": "Exam-focused"},
                        {"value": "concept_focused", "label": "Concept-focused"},
                        {"value": "project_based", "label": "Project-based"},
                        {"value": "hands_on", "label": "Hands-on"},
                        {"value": "fun", "label": "Fun lessons"},
                        {"value": "fast_paced", "label": "Fast-paced"}
                    ]
                }
            ]
        },
        {
            "id": "student_types",
            "legend": "Student Types",
            "fields": [
                {
                    "type": "checkboxes",
                    "name": "types",
                    "options": [
                        {"value": "preschool", "label": "Preschool"},
                        {"value": "primary", "label": "Primary"},
                        {"value": "middle_school", "label": "Middle School"},
                        {"value": "high_school", "label": "High School"},
                        {"value": "university", "label": "University"},
                        {"value": "adult", "label": "Adult"},
                        {"value": "professionals", "label": "Professionals"},
                        {"value": "international", "label": "International Students"}
                    ]
                }
            ]
        },
        {
            "id": "curriculum_expertise",
            "legend": "Curriculum Expertise",
            "fields": [
                {
                    "type": "checkboxes",
                    "name": "curricula",
                    "options": [
                        {"value": "myanmar_gov", "label": "Myanmar Government"},
                        {"value": "cambridge_primary", "label": "Cambridge Primary"},
                        {"value": "cambridge_lower_secondary", "label": "Cambridge Lower Secondary"},
                        {"value": "igcse", "label": "IGCSE"},
                        {"value": "a_level", "label": "A Level"},
                        {"value": "ib", "label": "IB"},
                        {"value": "ged", "label": "GED"},
                        {"value": "sat", "label": "SAT"},
                        {"value": "ielts", "label": "IELTS"},
                        {"value": "toefl", "label": "TOEFL"},
                        {"value": "jplt", "label": "JLPT"},
                        {"value": "hsk", "label": "HSK"},
                        {"value": "university", "label": "University Courses"}
                    ]
                }
            ]
        },
        {
            "id": "certifications",
            "legend": "Certifications",
            "fields": [
                {
                    "type": "repeater",
                    "name": "certs",
                    "fields": [
                        {"name": "name", "label": "Name", "type": "text"},
                        {"name": "issuer", "label": "Issuer", "type": "text"},
                        {"name": "year", "label": "Year", "type": "number", "min": 1900}
                    ]
                }
            ]
        }
    ]
}