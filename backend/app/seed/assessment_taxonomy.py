"""Seed data for the assessment engine: domains, concepts (with a real
prerequisite dependency graph, mirrored into Neo4j by app/graphrag/seed.py),
a question bank, and a curated learning-resource catalog.

Concept dependency chain for SQL matches docs/04_KNOWLEDGE_GRAPH.md's
root-cause example exactly:
    relational_model -> table_relationships -> joins -> inner_join / outer_join
"""

DOMAINS = [
    {"slug": "sql", "name": "SQL", "description": "Relational database querying: joins, aggregation, and schema design."},
    {"slug": "python", "name": "Python", "description": "Core language fundamentals: data types, functions, and control flow."},
]

# (domain_slug, concept_slug, name, skill_name_or_None, description)
CONCEPTS = [
    ("sql", "relational_model", "Relational Model", "SQL", "Data organized into tables of rows and columns related by keys."),
    ("sql", "table_relationships", "Table Relationships", "SQL", "How primary and foreign keys link rows across tables."),
    ("sql", "joins", "Joins", "SQL", "Combining rows from two or more tables based on a related column."),
    ("sql", "inner_join", "Inner Join", "SQL", "Returns only rows with matching values in both joined tables."),
    ("sql", "outer_join", "Outer Join", "SQL", "Returns matched rows plus unmatched rows from one or both tables."),
    ("sql", "group_by", "Grouping", "SQL", "Collapsing rows that share a value into summary rows."),
    ("sql", "aggregate_functions", "Aggregate Functions", "SQL", "COUNT, SUM, AVG, MIN, MAX over grouped or whole result sets."),
    ("sql", "where_vs_having", "WHERE vs HAVING", "SQL", "Filtering rows before grouping versus filtering groups after."),
    ("sql", "subqueries", "Subqueries", "SQL", "A query nested inside another query's WHERE, FROM, or SELECT clause."),
    ("sql", "indexes", "Indexes", "SQL", "Data structures that speed up row lookups at the cost of write overhead."),
    ("sql", "normalization", "Normalization", "SQL", "Structuring tables to reduce redundancy and update anomalies."),
    ("python", "data_types", "Data Types", "Python", "int, float, str, bool, list, dict, tuple, set."),
    ("python", "list_comprehension", "List Comprehensions", "Python", "Concise syntax for building a list from an iterable."),
    ("python", "functions", "Functions", "Python", "Defining and calling reusable blocks of code with parameters."),
    ("python", "exceptions", "Exceptions", "Python", "try/except/finally control flow for handling runtime errors."),
    ("python", "dict_operations", "Dictionary Operations", "Python", "Key lookup, iteration, and mutation on dict objects."),
]

# (concept_slug, depends_on_slug) -- both within the same domain.
CONCEPT_DEPENDENCIES = [
    ("table_relationships", "relational_model"),
    ("joins", "table_relationships"),
    ("inner_join", "joins"),
    ("outer_join", "joins"),
    ("group_by", "relational_model"),
    ("aggregate_functions", "group_by"),
    ("where_vs_having", "group_by"),
    ("subqueries", "joins"),
    ("indexes", "relational_model"),
    ("normalization", "relational_model"),
    ("list_comprehension", "data_types"),
    ("functions", "data_types"),
    ("exceptions", "functions"),
    ("dict_operations", "data_types"),
]

QUESTIONS = [
    {
        "domain": "sql", "concept": "relational_model", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "In the relational model, what uniquely identifies a row within a table?",
        "options": [
            {"id": "a", "text": "The primary key"},
            {"id": "b", "text": "The table name"},
            {"id": "c", "text": "The column order"},
            {"id": "d", "text": "The first column"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "A primary key is a column (or set of columns) guaranteed to be unique per row.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "table_relationships", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "A `orders.customer_id` column that references `customers.id` is an example of a:",
        "options": [
            {"id": "a", "text": "Primary key"},
            {"id": "b", "text": "Foreign key"},
            {"id": "c", "text": "Unique index"},
            {"id": "d", "text": "Composite key"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A foreign key is a column that references the primary key of another table, forming the relationship.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "joins", "question_type": "multiple_selection", "difficulty": 2,
        "prompt": "Which of the following are valid SQL join types? (select all that apply)",
        "options": [
            {"id": "a", "text": "INNER JOIN"},
            {"id": "b", "text": "LEFT JOIN"},
            {"id": "c", "text": "PARALLEL JOIN"},
            {"id": "d", "text": "FULL OUTER JOIN"},
        ],
        "correct_answer": {"correct_option_ids": ["a", "b", "d"]},
        "explanation": "INNER, LEFT (OUTER), RIGHT (OUTER), and FULL OUTER are the standard SQL join types. 'PARALLEL JOIN' is not a SQL construct.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "inner_join", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": (
            "`SELECT o.id, c.name FROM orders o INNER JOIN customers c ON o.customer_id = c.id;` "
            "What happens to an order row whose `customer_id` matches no row in `customers`?"
        ),
        "options": [
            {"id": "a", "text": "It is included with c.name set to NULL"},
            {"id": "b", "text": "It is excluded from the result entirely"},
            {"id": "c", "text": "The query raises an error"},
            {"id": "d", "text": "It is included with c.name set to an empty string"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "INNER JOIN only returns rows that have a matching row in both tables; unmatched rows are dropped.",
        "target_role_relevance": ["SQL", "Data Analyst", "Backend Engineer"],
    },
    {
        "domain": "sql", "concept": "inner_join", "question_type": "concept_explanation", "difficulty": 3,
        "prompt": "In one or two sentences, explain the difference between an INNER JOIN and a LEFT JOIN.",
        "options": None,
        "correct_answer": {
            "keywords": ["inner join", "left join", "match", "unmatched", "null", "left table"],
            "sample_answer": (
                "An INNER JOIN returns only rows with a match in both tables, while a LEFT JOIN returns "
                "every row from the left table plus matching rows from the right table, filling unmatched "
                "right-table columns with NULL."
            ),
        },
        "explanation": (
            "A correct answer names both join types and states that LEFT JOIN keeps unmatched left-table "
            "rows (with NULLs on the right side) while INNER JOIN drops them."
        ),
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "outer_join", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "A LEFT OUTER JOIN between `customers` (left) and `orders` (right) returns:",
        "options": [
            {"id": "a", "text": "Only customers who have placed at least one order"},
            {"id": "b", "text": "Every customer, with order columns NULL if they have no orders"},
            {"id": "c", "text": "Only orders that have a matching customer"},
            {"id": "d", "text": "Every order, regardless of customer"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "LEFT OUTER JOIN keeps every row from the left table (customers), padding unmatched right-side columns with NULL.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "group_by", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "`SELECT department, COUNT(*) FROM employees GROUP BY department;` groups rows by:",
        "options": [
            {"id": "a", "text": "Each distinct value of department"},
            {"id": "b", "text": "Each row individually"},
            {"id": "c", "text": "The primary key of employees"},
            {"id": "d", "text": "Alphabetical order of employee name"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "GROUP BY collapses rows sharing the same value in the grouped column(s) into one summary row per distinct value.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "aggregate_functions", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "Which aggregate function returns the number of rows in a group, including rows with NULLs (when used as COUNT(*))?",
        "options": [
            {"id": "a", "text": "SUM"},
            {"id": "b", "text": "COUNT"},
            {"id": "c", "text": "AVG"},
            {"id": "d", "text": "MAX"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "COUNT(*) counts rows regardless of NULLs; COUNT(column) would skip NULLs in that column.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "where_vs_having", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "To filter out groups whose COUNT(*) is less than 5 after grouping, you should use:",
        "options": [
            {"id": "a", "text": "WHERE COUNT(*) < 5"},
            {"id": "b", "text": "HAVING COUNT(*) >= 5"},
            {"id": "c", "text": "GROUP BY COUNT(*) >= 5"},
            {"id": "d", "text": "ORDER BY COUNT(*) >= 5"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "WHERE filters rows before grouping and cannot reference aggregates; HAVING filters groups after aggregation.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "subqueries", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "`SELECT name FROM employees WHERE department_id IN (SELECT id FROM departments WHERE budget > 100000);` — the inner SELECT is a:",
        "options": [
            {"id": "a", "text": "Correlated trigger"},
            {"id": "b", "text": "Subquery"},
            {"id": "c", "text": "View"},
            {"id": "d", "text": "Stored procedure"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A query nested inside another query's clause is a subquery -- here it feeds the outer WHERE ... IN (...) filter.",
        "target_role_relevance": ["SQL", "Data Analyst", "Backend Engineer"],
    },
    {
        "domain": "sql", "concept": "indexes", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "The main tradeoff of adding an index to a frequently-queried column is:",
        "options": [
            {"id": "a", "text": "Faster reads, slower writes and extra storage"},
            {"id": "b", "text": "Slower reads, faster writes"},
            {"id": "c", "text": "No effect on performance, only readability"},
            {"id": "d", "text": "It removes the need for a primary key"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Indexes speed up lookups but must be updated on every write, and they consume additional storage.",
        "target_role_relevance": ["SQL", "Backend Engineer"],
    },
    {
        "domain": "sql", "concept": "normalization", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "Storing a customer's full address as repeated text in every order row (instead of a `customer_id` foreign key) primarily risks:",
        "options": [
            {"id": "a", "text": "Update anomalies from duplicated data"},
            {"id": "b", "text": "Faster query performance"},
            {"id": "c", "text": "Stronger referential integrity"},
            {"id": "d", "text": "Automatic indexing"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Denormalized, duplicated data can go out of sync when only some copies are updated -- exactly what normalization avoids.",
        "target_role_relevance": ["SQL", "Backend Engineer"],
    },
    {
        "domain": "sql", "concept": "joins", "question_type": "short_answer", "difficulty": 3,
        "prompt": "Name the SQL clause used to specify the condition that matches rows between two joined tables.",
        "options": None,
        "correct_answer": {"keywords": ["on", "on clause"], "sample_answer": "The ON clause."},
        "explanation": "The ON clause specifies the join condition, e.g. `ON o.customer_id = c.id`.",
        "target_role_relevance": ["SQL"],
    },
    {
        "domain": "python", "concept": "data_types", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "Which of these Python types is mutable?",
        "options": [
            {"id": "a", "text": "tuple"},
            {"id": "b", "text": "str"},
            {"id": "c", "text": "list"},
            {"id": "d", "text": "int"},
        ],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "Lists can be modified in place; tuples, strings, and ints are immutable.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "list_comprehension", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does `[x * 2 for x in range(3)]` evaluate to?",
        "options": [
            {"id": "a", "text": "[0, 2, 4]"},
            {"id": "b", "text": "[0, 1, 2]"},
            {"id": "c", "text": "[2, 4, 6]"},
            {"id": "d", "text": "[1, 2, 3]"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "range(3) yields 0, 1, 2; doubling each gives [0, 2, 4].",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "functions", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "In `def greet(name, greeting='Hello'):`, what kind of parameter is `greeting`?",
        "options": [
            {"id": "a", "text": "Positional-only"},
            {"id": "b", "text": "Keyword with a default value"},
            {"id": "c", "text": "*args"},
            {"id": "d", "text": "**kwargs"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A parameter assigned a default value in the signature can be omitted by the caller and passed by keyword.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "exceptions", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "Which block always runs, whether or not an exception was raised in the `try` block?",
        "options": [
            {"id": "a", "text": "except"},
            {"id": "b", "text": "else"},
            {"id": "c", "text": "finally"},
            {"id": "d", "text": "raise"},
        ],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "`finally` runs unconditionally, typically used for cleanup such as closing files or connections.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "exceptions", "question_type": "code_reading", "difficulty": 3,
        "prompt": (
            "What is printed by:\n```python\ntry:\n    x = 1 / 0\nexcept ZeroDivisionError:\n    print('caught')\nelse:\n    print('no error')\n```"
        ),
        "options": None,
        "correct_answer": {"keywords": ["caught"], "sample_answer": "caught"},
        "explanation": "1 / 0 raises ZeroDivisionError, so the except block runs and prints 'caught'; the else block is skipped.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "dict_operations", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does `{'a': 1, 'b': 2}.get('c', 0)` return?",
        "options": [
            {"id": "a", "text": "KeyError"},
            {"id": "b", "text": "None"},
            {"id": "c", "text": "0"},
            {"id": "d", "text": "'c'"},
        ],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "`dict.get(key, default)` returns the default (here 0) when the key is absent, instead of raising KeyError.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "dict_operations", "question_type": "multiple_selection", "difficulty": 2,
        "prompt": "Which of the following are valid ways to iterate over a dict `d`? (select all that apply)",
        "options": [
            {"id": "a", "text": "for k in d:"},
            {"id": "b", "text": "for k, v in d.items():"},
            {"id": "c", "text": "for v in d.values():"},
            {"id": "d", "text": "for d in d.keys:"},
        ],
        "correct_answer": {"correct_option_ids": ["a", "b", "c"]},
        "explanation": "Iterating a dict directly yields keys; `.items()` yields (key, value) pairs; `.values()` yields values. `.keys` without parentheses is not a call.",
        "target_role_relevance": ["Python"],
    },
]

# provider/url are illustrative "known-good" reference material, not scraped
# at runtime (Prompt 2 explicitly avoids open web scraping in the core demo).
RESOURCES = [
    {
        "title": "SQL Joins Explained", "provider": "MDN-style reference", "url": "https://example-docs.careerpilot.ai/sql/joins",
        "resource_type": "documentation", "concept": "joins", "skill": "SQL", "difficulty": 2, "duration_minutes": 12,
        "quality_score": 0.92, "cost": "free",
        "description": "A concise reference covering INNER, LEFT, RIGHT, and FULL OUTER JOIN with diagrams.",
    },
    {
        "title": "Understanding Table Relationships", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/table-relationships",
        "resource_type": "article", "concept": "table_relationships", "skill": "SQL", "difficulty": 1, "duration_minutes": 8,
        "quality_score": 0.88, "cost": "free",
        "description": "Primary keys, foreign keys, and how relational databases link rows across tables.",
    },
    {
        "title": "The Relational Model in 10 Minutes", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/relational-model",
        "resource_type": "video", "concept": "relational_model", "skill": "SQL", "difficulty": 1, "duration_minutes": 10,
        "quality_score": 0.85, "cost": "free",
        "description": "A short video walkthrough of tables, rows, columns, and keys.",
    },
    {
        "title": "INNER JOIN vs LEFT JOIN, Visually", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/inner-vs-left-join",
        "resource_type": "interactive", "concept": "inner_join", "skill": "SQL", "difficulty": 2, "duration_minutes": 15,
        "quality_score": 0.94, "cost": "free",
        "description": "An interactive query sandbox comparing INNER and LEFT JOIN result sets side by side.",
    },
    {
        "title": "Outer Joins Deep Dive", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/outer-joins",
        "resource_type": "article", "concept": "outer_join", "skill": "SQL", "difficulty": 3, "duration_minutes": 12,
        "quality_score": 0.87, "cost": "free",
        "description": "LEFT, RIGHT, and FULL OUTER JOIN semantics with worked examples.",
    },
    {
        "title": "GROUP BY and Aggregates", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/group-by",
        "resource_type": "article", "concept": "group_by", "skill": "SQL", "difficulty": 2, "duration_minutes": 10,
        "quality_score": 0.86, "cost": "free",
        "description": "How GROUP BY collapses rows and how aggregate functions summarize each group.",
    },
    {
        "title": "WHERE vs HAVING", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/where-vs-having",
        "resource_type": "article", "concept": "where_vs_having", "skill": "SQL", "difficulty": 3, "duration_minutes": 8,
        "quality_score": 0.83, "cost": "free",
        "description": "Why aggregate filters belong in HAVING, not WHERE.",
    },
    {
        "title": "Subqueries in Practice", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/subqueries",
        "resource_type": "article", "concept": "subqueries", "skill": "SQL", "difficulty": 3, "duration_minutes": 14,
        "quality_score": 0.84, "cost": "free",
        "description": "Nested SELECTs in WHERE, FROM, and SELECT clauses, with performance notes.",
    },
    {
        "title": "Database Indexing Basics", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/indexes",
        "resource_type": "article", "concept": "indexes", "skill": "SQL", "difficulty": 3, "duration_minutes": 11,
        "quality_score": 0.85, "cost": "free",
        "description": "How B-tree indexes speed up lookups and what they cost on writes.",
    },
    {
        "title": "Normal Forms Without the Jargon", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/sql/normalization",
        "resource_type": "article", "concept": "normalization", "skill": "SQL", "difficulty": 4, "duration_minutes": 16,
        "quality_score": 0.82, "cost": "free",
        "description": "1NF through 3NF explained with a running example, focused on avoiding update anomalies.",
    },
    {
        "title": "Python List Comprehensions", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/python/list-comprehensions",
        "resource_type": "article", "concept": "list_comprehension", "skill": "Python", "difficulty": 2, "duration_minutes": 9,
        "quality_score": 0.88, "cost": "free",
        "description": "Building lists concisely, with conditional and nested comprehension examples.",
    },
    {
        "title": "Python Functions and Defaults", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/python/functions",
        "resource_type": "article", "concept": "functions", "skill": "Python", "difficulty": 2, "duration_minutes": 10,
        "quality_score": 0.86, "cost": "free",
        "description": "Positional, keyword, default, *args, and **kwargs parameters.",
    },
    {
        "title": "Exception Handling in Python", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/python/exceptions",
        "resource_type": "article", "concept": "exceptions", "skill": "Python", "difficulty": 2, "duration_minutes": 11,
        "quality_score": 0.87, "cost": "free",
        "description": "try/except/else/finally control flow, with common pitfalls.",
    },
    {
        "title": "Working with Python Dictionaries", "provider": "CareerPilot Learn", "url": "https://example-docs.careerpilot.ai/python/dict-operations",
        "resource_type": "article", "concept": "dict_operations", "skill": "Python", "difficulty": 1, "duration_minutes": 8,
        "quality_score": 0.85, "cost": "free",
        "description": "Lookup, iteration, mutation, and safe access patterns for dict.",
    },
]
