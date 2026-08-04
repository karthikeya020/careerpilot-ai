"""Baseline skill taxonomy used for deterministic resume/JD keyword matching.

This is reference data (like the role catalog), not demo-specific data, so it
ships via an Alembic data migration rather than the demo seed command --
registration and resume parsing must work in any freshly migrated environment.
"""

SKILLS: list[dict] = [
    # Languages
    {"name": "Python", "category": "technical", "aliases": ["py"]},
    {"name": "Java", "category": "technical", "aliases": []},
    {"name": "JavaScript", "category": "technical", "aliases": ["js", "ecmascript"]},
    {"name": "TypeScript", "category": "technical", "aliases": ["ts"]},
    {"name": "C++", "category": "technical", "aliases": ["cpp"]},
    {"name": "C", "category": "technical", "aliases": []},
    {"name": "C#", "category": "technical", "aliases": ["csharp"]},
    {"name": "Go", "category": "technical", "aliases": ["golang"]},
    {"name": "SQL", "category": "technical", "aliases": []},
    {"name": "Swift", "category": "technical", "aliases": []},
    {"name": "Kotlin", "category": "technical", "aliases": []},
    # Web / frameworks
    {"name": "React", "category": "technical", "aliases": ["react.js", "reactjs"]},
    {"name": "Next.js", "category": "technical", "aliases": ["nextjs"]},
    {"name": "Node.js", "category": "technical", "aliases": ["nodejs", "node"]},
    {"name": "FastAPI", "category": "technical", "aliases": []},
    {"name": "Django", "category": "technical", "aliases": []},
    {"name": "Flask", "category": "technical", "aliases": []},
    {"name": "HTML", "category": "technical", "aliases": ["html5"]},
    {"name": "CSS", "category": "technical", "aliases": ["css3"]},
    {"name": "Tailwind CSS", "category": "technical", "aliases": ["tailwind"]},
    {"name": "REST APIs", "category": "technical", "aliases": ["rest api", "restful"]},
    {"name": "GraphQL", "category": "technical", "aliases": []},
    # Data / ML
    {"name": "Machine Learning", "category": "technical", "aliases": ["ml"]},
    {"name": "Deep Learning", "category": "technical", "aliases": []},
    {"name": "TensorFlow", "category": "technical", "aliases": []},
    {"name": "PyTorch", "category": "technical", "aliases": []},
    {"name": "Data Analysis", "category": "technical", "aliases": []},
    {"name": "Pandas", "category": "technical", "aliases": []},
    {"name": "NumPy", "category": "technical", "aliases": []},
    {"name": "Natural Language Processing", "category": "technical", "aliases": ["nlp"]},
    {"name": "Computer Vision", "category": "technical", "aliases": []},
    {"name": "Data Structures", "category": "technical", "aliases": ["dsa"]},
    {"name": "Algorithms", "category": "technical", "aliases": []},
    {"name": "System Design", "category": "technical", "aliases": []},
    # Data stores / infra
    {"name": "PostgreSQL", "category": "tools", "aliases": ["postgres"]},
    {"name": "MongoDB", "category": "tools", "aliases": ["mongo"]},
    {"name": "Redis", "category": "tools", "aliases": []},
    {"name": "Neo4j", "category": "tools", "aliases": []},
    {"name": "Docker", "category": "tools", "aliases": []},
    {"name": "Kubernetes", "category": "tools", "aliases": ["k8s"]},
    {"name": "AWS", "category": "tools", "aliases": ["amazon web services"]},
    {"name": "Azure", "category": "tools", "aliases": []},
    {"name": "Google Cloud Platform", "category": "tools", "aliases": ["gcp"]},
    {"name": "Git", "category": "tools", "aliases": ["github", "version control"]},
    {"name": "Linux", "category": "tools", "aliases": []},
    {"name": "CI/CD", "category": "tools", "aliases": ["continuous integration"]},
    {"name": "Testing", "category": "tools", "aliases": ["unit testing", "pytest", "jest"]},
    # Soft skills / communication
    {"name": "Communication", "category": "communication", "aliases": []},
    {"name": "Teamwork", "category": "soft_skill", "aliases": ["collaboration"]},
    {"name": "Leadership", "category": "soft_skill", "aliases": []},
    {"name": "Problem Solving", "category": "soft_skill", "aliases": []},
    {"name": "Public Speaking", "category": "communication", "aliases": ["presentation"]},
    {"name": "Technical Writing", "category": "communication", "aliases": ["documentation"]},
    {"name": "Agile/Scrum", "category": "soft_skill", "aliases": ["agile", "scrum"]},
    {"name": "Project Management", "category": "soft_skill", "aliases": []},
]
