SCHEMA = {
    "sections": [
        {
            "id": "identity",
            "legend": "Identity & Contact",
            "fields": [
                {"name": "full_name", "label": "Full Name", "type": "text"},
                {"name": "display_name", "label": "Display Name", "type": "text"},
                {"name": "email", "label": "Email", "type": "email"},
                {"name": "phone", "label": "Phone", "type": "text"},
                {"name": "timezone", "label": "Timezone", "type": "text"},
                {"name": "bio", "label": "Bio", "type": "textarea"},
                {"name": "languages", "label": "Languages", "type": "text", "placeholder": "e.g. Burmese, English"}
            ]
        },
        {
            "id": "teaching_subjects",
            "legend": "Teaching Subjects",
            "fields": [
                {
                    "name": "subjects",
                    "label": "Subjects",
                    "type": "repeater",
                    "fields": [
                        {"name": "subject_id", "label": "Subject", "type": "select", "options": [
                            {"value": "math", "label": "Mathematics"},
                            {"value": "physics", "label": "Physics"},
                            {"value": "english", "label": "English"},
                            {"value": "chemistry", "label": "Chemistry"},
                            {"value": "biology", "label": "Biology"},
                            {"value": "history", "label": "History"}
                        ]},
                        {"name": "level", "label": "Level", "type": "select", "options": [
                            {"value": "primary", "label": "Primary"},
                            {"value": "secondary", "label": "Secondary"},
                            {"value": "igcse", "label": "IGCSE"},
                            {"value": "alevel", "label": "A Level"},
                            {"value": "ib", "label": "IB"},
                            {"value": "university", "label": "University"}
                        ]},
                        {"name": "curriculum_id", "label": "Curriculum", "type": "select", "options": [
                            {"value": "myanmar", "label": "Myanmar Government"},
                            {"value": "cambridge", "label": "Cambridge"},
                            {"value": "ib", "label": "IB"},
                            {"value": "american", "label": "American"}
                        ]},
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
                    "name": "modes",
                    "label": "Modes",
                    "type": "checkboxes",
                    "options": [
                        {"value": "online", "label": "Online"},
                        {"value": "in_person", "label": "In Person"},
                        {"value": "home_tuition", "label": "Home Tuition"}
                    ]
                }
            ]
        },
        {
            "id": "teaching_styles",
            "legend": "Teaching Style",
            "fields": [
                {
                    "name": "styles",
                    "label": "Style",
                    "type": "checkboxes",
                    "options": [
                        {"value": "patient", "label": "Patient"},
                        {"value": "interactive", "label": "Interactive"},
                        {"value": "structured", "label": "Structured"},
                        {"value": "exam_focused", "label": "Exam Focused"},
                        {"value": "project_based", "label": "Project Based"}
                    ]
                }
            ]
        },
        {
            "id": "student_types",
            "legend": "Student Types",
            "fields": [
                {
                    "name": "types",
                    "label": "Comfortable with",
                    "type": "checkboxes",
                    "options": [
                        {"value": "preschool", "label": "Preschool"},
                        {"value": "primary", "label": "Primary"},
                        {"value": "middle_school", "label": "Middle School"},
                        {"value": "high_school", "label": "High School"},
                        {"value": "university", "label": "University"},
                        {"value": "adult", "label": "Adult"}
                    ]
                }
            ]
        },
        {
            "id": "certifications",
            "legend": "Certifications",
            "fields": [
                {
                    "name": "certifications",
                    "label": "Certifications",
                    "type": "repeater",
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