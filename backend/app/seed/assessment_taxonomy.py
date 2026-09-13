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

# ============================================================================
# Question-bank expansion (v2): four brand-new domains (JavaScript, DSA, OOP,
# Java) plus a handful of extra questions on the existing SQL/Python concepts.
# Loaded by alembic/versions/<rev>_expand_assessment_question_bank.py, which
# runs AFTER the original 298c98dafbbb seed migration -- these lists are
# additive, never re-declare an existing domain/concept/skill.
#
# Every question here is original and hand-written for this project (not
# scraped from a live site at runtime or at build time): a working demo
# cannot depend on a third-party site being reachable/unchanged, and
# reproducing third-party question text verbatim would be a copyright risk.
# Difficulty still uses the existing 1-5 scale; the API/UI buckets it into
# easy (1-2) / medium (3) / hard (4-5) for display.
# ============================================================================

NEW_SKILLS = [
    {"name": "Object-Oriented Programming", "category": "technical", "aliases": ["oop", "oops"]},
]

NEW_DOMAINS = [
    {"slug": "javascript", "name": "JavaScript", "description": "Core language, async programming, and DOM fundamentals."},
    {"slug": "dsa", "name": "Data Structures & Algorithms", "description": "Complexity analysis, core data structures, sorting and searching."},
    {"slug": "oop", "name": "Object-Oriented Programming", "description": "Classes, encapsulation, inheritance, polymorphism, and abstraction."},
    {"slug": "java", "name": "Java", "description": "Core language, collections, exceptions, memory, and concurrency basics."},
]

# (domain_slug, concept_slug, name, skill_name_or_None, description)
NEW_CONCEPTS = [
    ("javascript", "js_fundamentals", "JS Fundamentals", "JavaScript", "Variable declarations, primitive types, and equality checks."),
    ("javascript", "js_functions", "Functions & Scope", "JavaScript", "Closures, hoisting, and arrow functions."),
    ("javascript", "js_arrays_objects", "Arrays & Objects", "JavaScript", "Array methods, destructuring, and the spread operator."),
    ("javascript", "js_async", "Asynchronous JavaScript", "JavaScript", "Callbacks, Promises, async/await, and the event loop."),
    ("javascript", "js_dom_events", "DOM & Events", "JavaScript", "DOM manipulation and the event propagation model."),
    ("dsa", "complexity", "Time & Space Complexity", "Algorithms", "Big-O analysis of algorithm running time and memory use."),
    ("dsa", "arrays_strings", "Arrays & Strings", "Data Structures", "Contiguous data structures and common string/array techniques."),
    ("dsa", "linked_lists", "Linked Lists", "Data Structures", "Singly/doubly linked lists and pointer-based traversal."),
    ("dsa", "stacks_queues", "Stacks & Queues", "Data Structures", "LIFO and FIFO data structures and their applications."),
    ("dsa", "trees_graphs", "Trees & Graphs", "Data Structures", "Hierarchical and networked data structures and traversal."),
    ("dsa", "sorting_searching", "Sorting & Searching", "Algorithms", "Comparison sorts, binary search, and their complexity trade-offs."),
    ("oop", "oop_basics", "Classes & Objects", "Object-Oriented Programming", "The fundamental building blocks of object-oriented design."),
    ("oop", "encapsulation", "Encapsulation", "Object-Oriented Programming", "Bundling data and behavior while restricting direct access."),
    ("oop", "inheritance", "Inheritance", "Object-Oriented Programming", "Reusing and extending behavior across a class hierarchy."),
    ("oop", "polymorphism", "Polymorphism", "Object-Oriented Programming", "One interface, many implementations -- overloading and overriding."),
    ("oop", "abstraction", "Abstraction", "Object-Oriented Programming", "Hiding implementation detail behind a simpler interface."),
    ("java", "java_basics", "Java Fundamentals", "Java", "JVM/JDK/JRE, primitive types, and String comparison."),
    ("java", "java_collections", "Collections Framework", "Java", "List, Map, and Set implementations and their trade-offs."),
    ("java", "java_exceptions", "Exception Handling", "Java", "Checked vs. unchecked exceptions and try/catch/finally."),
    ("java", "java_memory", "Memory Management & GC", "Java", "The heap, the stack, and garbage collection."),
    ("java", "java_multithreading", "Multithreading Basics", "Java", "Threads, synchronization, and race conditions."),
]

# (concept_slug, depends_on_slug) -- both within the same new domain.
NEW_CONCEPT_DEPENDENCIES = [
    ("js_functions", "js_fundamentals"),
    ("js_arrays_objects", "js_fundamentals"),
    ("js_async", "js_functions"),
    ("js_dom_events", "js_arrays_objects"),
    ("arrays_strings", "complexity"),
    ("sorting_searching", "complexity"),
    ("linked_lists", "arrays_strings"),
    ("stacks_queues", "arrays_strings"),
    ("trees_graphs", "linked_lists"),
    ("encapsulation", "oop_basics"),
    ("inheritance", "oop_basics"),
    ("polymorphism", "inheritance"),
    ("abstraction", "encapsulation"),
    ("java_collections", "java_basics"),
    ("java_exceptions", "java_basics"),
    ("java_memory", "java_basics"),
    ("java_multithreading", "java_memory"),
]

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

NEW_QUESTIONS = [
    # ---- JavaScript ----
    {
        "domain": "javascript", "concept": "js_fundamentals", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "Which keyword declares a variable that CANNOT be reassigned after its initial value is set?",
        "options": [{"id": "a", "text": "var"}, {"id": "b", "text": "let"}, {"id": "c", "text": "const"}, {"id": "d", "text": "static"}],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "`const` creates a binding that cannot be reassigned (the value itself can still be mutated if it's an object/array).",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_fundamentals", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What does `===` check in JavaScript that `==` does not?",
        "options": [
            {"id": "a", "text": "It also checks that the types match, without coercing either operand"},
            {"id": "b", "text": "It checks object identity (same memory reference) for all types"},
            {"id": "c", "text": "It is faster but functionally identical to =="},
            {"id": "d", "text": "It only works on numbers"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "`===` is strict equality: no type coercion happens, so `1 === '1'` is false while `1 == '1'` is true.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_fundamentals", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "What does `typeof null` evaluate to in JavaScript, and why is this considered a long-standing language bug?",
        "options": None,
        "correct_answer": {
            "keywords": ["object", "bug", "legacy", "type tag"],
            "sample_answer": "`typeof null` returns 'object', which is a bug dating back to JavaScript's original type-tagging "
            "implementation; null is not actually an object, but the behavior can't be fixed now without breaking "
            "existing code on the web.",
        },
        "explanation": "A correct answer names the actual 'object' result and explains it's a historical implementation quirk, not a logical object.",
        "target_role_relevance": ["JavaScript"],
    },
    {
        "domain": "javascript", "concept": "js_functions", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is a closure in JavaScript?",
        "options": [
            {"id": "a", "text": "A function that has no parameters"},
            {"id": "b", "text": "A function that remembers and can access variables from its outer scope even after that scope has returned"},
            {"id": "c", "text": "A syntax error caused by an unclosed bracket"},
            {"id": "d", "text": "A method that closes a database connection"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A closure is formed when an inner function retains access to its enclosing function's variables after the outer function has finished executing.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_functions", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "With `var`, a variable declared anywhere in a function is accessible (as `undefined`) even before its declaration line runs. What is this behavior called?",
        "options": [{"id": "a", "text": "Currying"}, {"id": "b", "text": "Hoisting"}, {"id": "c", "text": "Memoization"}, {"id": "d", "text": "Binding"}],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "Hoisting moves variable (and function) declarations to the top of their scope during compilation; `var` declarations are initialized to `undefined`, while `let`/`const` are hoisted but left in a 'temporal dead zone'.",
        "target_role_relevance": ["JavaScript"],
    },
    {
        "domain": "javascript", "concept": "js_functions", "question_type": "code_reading", "difficulty": 4,
        "prompt": "In a `for (var i = 0; i < 3; i++) { setTimeout(() => console.log(i), 0); }` loop, what gets logged, and why would changing `var` to `let` fix it to log 0, 1, 2?",
        "options": None,
        "correct_answer": {
            "keywords": ["3", "3 3 3", "let", "block scope", "new binding"],
            "sample_answer": "With var it logs 3, 3, 3 because var is function-scoped and all callbacks share the same final i; "
            "let creates a new block-scoped binding of i for each loop iteration, so each callback captures its own i.",
        },
        "explanation": "This is the classic var-in-a-loop closure pitfall, fixed by let's per-iteration scoping.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_arrays_objects", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "Which array method returns a NEW array by applying a function to every element, without modifying the original array?",
        "options": [{"id": "a", "text": "forEach"}, {"id": "b", "text": "map"}, {"id": "c", "text": "push"}, {"id": "d", "text": "sort"}],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "`map` returns a new array of the same length with each element transformed; `forEach` returns undefined.",
        "target_role_relevance": ["JavaScript"],
    },
    {
        "domain": "javascript", "concept": "js_arrays_objects", "question_type": "short_answer", "difficulty": 3,
        "prompt": "What does `[1, 2, 3].reduce((acc, cur) => acc + cur, 0)` evaluate to?",
        "options": None,
        "correct_answer": {"keywords": ["6"], "sample_answer": "6"},
        "explanation": "reduce accumulates: 0+1=1, 1+2=3, 3+3=6.",
        "target_role_relevance": ["JavaScript"],
    },
    {
        "domain": "javascript", "concept": "js_arrays_objects", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What does the spread operator do in `const copy = [...original];`?",
        "options": [
            {"id": "a", "text": "Creates a shallow copy of the original array's elements into a new array"},
            {"id": "b", "text": "Makes `copy` a reference to the same array as `original`"},
            {"id": "c", "text": "Sorts the array before copying"},
            {"id": "d", "text": "Throws an error unless original is an object"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Spread expands the iterable's elements into a new array literal, producing a shallow copy.",
        "target_role_relevance": ["JavaScript"],
    },
    {
        "domain": "javascript", "concept": "js_async", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does a JavaScript Promise represent?",
        "options": [
            {"id": "a", "text": "A value that is always immediately available"},
            {"id": "b", "text": "An eventual result (success or failure) of an asynchronous operation"},
            {"id": "c", "text": "A synchronous loop construct"},
            {"id": "d", "text": "A type of array"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A Promise is an object representing the eventual completion or failure of an async operation and its resulting value.",
        "target_role_relevance": ["JavaScript", "Backend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_async", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the main practical difference between chaining `.then()` calls and using `async/await` for the same Promise-based logic?",
        "options": [
            {"id": "a", "text": "async/await is just syntactic sugar over Promises that reads more like synchronous code"},
            {"id": "b", "text": "async/await runs code synchronously on a separate thread"},
            {"id": "c", "text": ".then() cannot handle errors at all"},
            {"id": "d", "text": "They cannot be mixed in the same codebase"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "async/await is built on Promises -- it doesn't change the underlying async model, just how the control flow reads and how errors are caught (try/catch instead of .catch()).",
        "target_role_relevance": ["JavaScript", "Backend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_async", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Explain the JavaScript event loop: how do the call stack, the task (macrotask) queue, and the microtask queue interact?",
        "options": None,
        "correct_answer": {
            "keywords": ["call stack", "microtask", "macrotask", "queue", "event loop"],
            "sample_answer": "JavaScript runs on a single thread with a call stack; synchronous code runs immediately. Async callbacks "
            "(from Promises) go into the microtask queue, while things like setTimeout go into the macrotask queue. "
            "The event loop only pulls a new task from either queue once the call stack is empty, and it drains "
            "the entire microtask queue before running the next macrotask.",
        },
        "explanation": "This distinguishes JS's cooperative single-threaded concurrency model from true parallelism.",
        "target_role_relevance": ["JavaScript", "Backend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_dom_events", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does `document.querySelector('.missing')` return if no element matches the selector?",
        "options": [{"id": "a", "text": "null"}, {"id": "b", "text": "undefined"}, {"id": "c", "text": "An empty array"}, {"id": "d", "text": "It throws an error"}],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "querySelector returns null when nothing matches, so callers should always null-check before using the result.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_dom_events", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is 'event bubbling' in the DOM?",
        "options": [
            {"id": "a", "text": "An event fired on a child element also propagates upward and fires on its ancestor elements"},
            {"id": "b", "text": "Multiple events firing simultaneously and colliding"},
            {"id": "c", "text": "A performance optimization that batches DOM updates"},
            {"id": "d", "text": "A CSS animation technique"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "By default, most DOM events bubble from the target element up through its ancestors, which is why event delegation on a parent works.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_dom_events", "question_type": "short_answer", "difficulty": 4,
        "prompt": "What is the difference between `event.stopPropagation()` and `event.preventDefault()`?",
        "options": None,
        "correct_answer": {
            "keywords": ["stop propagation", "bubbling", "default action", "prevent default"],
            "sample_answer": "stopPropagation() stops the event from bubbling further up (or capturing down) the DOM tree, while "
            "preventDefault() stops the browser's default action for that event (like a link navigating or a form submitting) without affecting propagation.",
        },
        "explanation": "These solve two different problems and are often confused.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },

    # ---- DSA ----
    {
        "domain": "dsa", "concept": "complexity", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "What is the time complexity of accessing an element in an array by its index?",
        "options": [{"id": "a", "text": "O(1)"}, {"id": "b", "text": "O(log n)"}, {"id": "c", "text": "O(n)"}, {"id": "d", "text": "O(n^2)"}],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Arrays store elements contiguously, so the address of any index can be computed directly -- constant time.",
        "target_role_relevance": ["Data Structures", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "complexity", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the time complexity of binary search on a sorted array of size n?",
        "options": [{"id": "a", "text": "O(1)"}, {"id": "b", "text": "O(log n)"}, {"id": "c", "text": "O(n)"}, {"id": "d", "text": "O(n log n)"}],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "Binary search halves the search space on each comparison, giving logarithmic time complexity.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "complexity", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "Quicksort's average-case time complexity is O(n log n), but its worst case is O(n^2). Why?",
        "options": None,
        "correct_answer": {
            "keywords": ["pivot", "unbalanced", "already sorted", "partition"],
            "sample_answer": "Quicksort's performance depends on how balanced the partitions are around the chosen pivot. On average, "
            "a random pivot splits the array roughly in half each time, giving O(n log n). In the worst case (e.g. "
            "always picking the smallest or largest element as pivot, such as on an already-sorted array with a naive "
            "pivot choice), each partition only removes one element, degrading to O(n^2).",
        },
        "explanation": "Tests understanding of average vs. worst-case analysis, not just memorized complexities.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "arrays_strings", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "What is the amortized time complexity of inserting an element at the end of a dynamic array (e.g. Python list, Java ArrayList)?",
        "options": [{"id": "a", "text": "O(1) amortized"}, {"id": "b", "text": "O(n) always"}, {"id": "c", "text": "O(log n)"}, {"id": "d", "text": "O(n^2)"}],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Occasional resizing costs O(n), but because resizes double the capacity, the average (amortized) cost per insertion is O(1).",
        "target_role_relevance": ["Data Structures", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "arrays_strings", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "Given a SORTED array, which technique finds a pair of numbers summing to a target value in O(n) time and O(1) extra space?",
        "options": [
            {"id": "a", "text": "Two-pointer technique (one pointer from each end, moving inward)"},
            {"id": "b", "text": "Sorting the array again"},
            {"id": "c", "text": "Checking every pair with a nested loop"},
            {"id": "d", "text": "Using recursion with memoized subsets"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "On a sorted array, moving two pointers inward based on whether the current sum is too high or too low finds the pair in a single O(n) pass.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "arrays_strings", "question_type": "short_answer", "difficulty": 3,
        "prompt": "Name one way to check if a string is a palindrome in O(n) time.",
        "options": None,
        "correct_answer": {
            "keywords": ["two pointer", "reverse", "compare", "start end"],
            "sample_answer": "Use two pointers starting at the beginning and end of the string, moving inward and comparing "
            "characters at each step; if all pairs match, it's a palindrome. (Reversing the string and comparing to the original also works.)",
        },
        "explanation": "A classic warm-up interview question.",
        "target_role_relevance": ["Algorithms"],
    },
    {
        "domain": "dsa", "concept": "linked_lists", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is the main advantage of a linked list over an array for frequent insertions and deletions in the MIDDLE of the collection?",
        "options": [
            {"id": "a", "text": "Insertion/deletion is O(1) once you have a reference to the node, with no shifting of other elements"},
            {"id": "b", "text": "Linked lists use less memory per element"},
            {"id": "c", "text": "Linked lists support O(1) random access by index"},
            {"id": "d", "text": "Linked lists are always faster to iterate than arrays"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Arrays require shifting subsequent elements on insert/delete; linked lists just re-point a few pointers, at the cost of losing O(1) indexed access.",
        "target_role_relevance": ["Data Structures", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "linked_lists", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the standard technique to detect a cycle in a linked list using O(1) extra space?",
        "options": [
            {"id": "a", "text": "Floyd's cycle detection (slow/fast 'tortoise and hare' pointers)"},
            {"id": "b", "text": "Storing every visited node in a hash set"},
            {"id": "c", "text": "Reversing the list and checking if it changes"},
            {"id": "d", "text": "Sorting the node values"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "A slow pointer moves one step and a fast pointer moves two steps; if there's a cycle, they eventually meet -- using O(1) extra space instead of a hash set's O(n).",
        "target_role_relevance": ["Data Structures", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "linked_lists", "question_type": "short_answer", "difficulty": 4,
        "prompt": "What is the time complexity of accessing the k-th element in a singly linked list, and why?",
        "options": None,
        "correct_answer": {
            "keywords": ["O(n)", "traverse", "no random access", "sequential"],
            "sample_answer": "O(n), because a linked list has no random access -- you must traverse from the head, following "
            "next pointers one node at a time, until you reach the k-th node.",
        },
        "explanation": "Contrasts directly with an array's O(1) indexed access.",
        "target_role_relevance": ["Data Structures"],
    },
    {
        "domain": "dsa", "concept": "stacks_queues", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "Which data structure follows Last-In-First-Out (LIFO) ordering?",
        "options": [{"id": "a", "text": "Queue"}, {"id": "b", "text": "Stack"}, {"id": "c", "text": "Linked list"}, {"id": "d", "text": "Hash map"}],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A stack's push/pop both happen at the same end, so the most recently added item is removed first.",
        "target_role_relevance": ["Data Structures"],
    },
    {
        "domain": "dsa", "concept": "stacks_queues", "question_type": "concept_explanation", "difficulty": 3,
        "prompt": "How can you implement a queue (FIFO) using two stacks (LIFO)?",
        "options": None,
        "correct_answer": {
            "keywords": ["two stacks", "reverse", "in stack", "out stack"],
            "sample_answer": "Use an 'in' stack for enqueue operations. For dequeue, if the 'out' stack is empty, pop everything from "
            "'in' and push it onto 'out' (which reverses the order), then pop from 'out'. This amortizes to O(1) per operation.",
        },
        "explanation": "A well-known interview question testing whether a candidate understands both structures' semantics.",
        "target_role_relevance": ["Data Structures", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "stacks_queues", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "Which of these is a classic real-world use case for a stack?",
        "options": [
            {"id": "a", "text": "A print job spooler processing jobs in the order they were submitted"},
            {"id": "b", "text": "The 'undo' feature in a text editor"},
            {"id": "c", "text": "A round-robin CPU scheduler"},
            {"id": "d", "text": "A breadth-first search of a graph"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "Undo history is LIFO -- the most recent action is the first one undone; the other options are all FIFO/queue-based.",
        "target_role_relevance": ["Data Structures"],
    },
    {
        "domain": "dsa", "concept": "trees_graphs", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "In a BINARY tree, what is the maximum number of children a single node can have?",
        "options": [{"id": "a", "text": "1"}, {"id": "b", "text": "2"}, {"id": "c", "text": "3"}, {"id": "d", "text": "Unlimited"}],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "By definition, a binary tree node has at most a left child and a right child.",
        "target_role_relevance": ["Data Structures"],
    },
    {
        "domain": "dsa", "concept": "trees_graphs", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the key difference between Breadth-First Search (BFS) and Depth-First Search (DFS) on a graph?",
        "options": [
            {"id": "a", "text": "BFS explores level by level using a queue; DFS explores as deep as possible first using a stack/recursion"},
            {"id": "b", "text": "BFS only works on trees, DFS only works on graphs"},
            {"id": "c", "text": "DFS always finds the shortest path; BFS does not"},
            {"id": "d", "text": "They always visit nodes in the exact same order"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "BFS's queue naturally explores nearer nodes first (useful for shortest paths in unweighted graphs); DFS's stack/recursion dives deep before backtracking.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "trees_graphs", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "What is the time complexity of BFS on a graph with V vertices and E edges (using an adjacency list)?",
        "options": [{"id": "a", "text": "O(V)"}, {"id": "b", "text": "O(E)"}, {"id": "c", "text": "O(V + E)"}, {"id": "d", "text": "O(V * E)"}],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "Every vertex is visited once and every edge is examined once, giving O(V + E).",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "trees_graphs", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Explain how a Binary Search Tree (BST) achieves O(log n) search time, and what causes that to degrade to O(n).",
        "options": None,
        "correct_answer": {
            "keywords": ["balanced", "unbalanced", "skewed", "left right", "height"],
            "sample_answer": "A BST keeps left-subtree values smaller and right-subtree values larger than each node, so each "
            "comparison eliminates half the remaining nodes -- O(log n) when the tree is roughly balanced (height "
            "~log n). If elements are inserted in sorted order with no rebalancing, the tree degenerates into a "
            "linked list (height ~n), making search O(n). Self-balancing trees (AVL, Red-Black) fix this.",
        },
        "explanation": "Tests whether the student understands the balance assumption behind the usual O(log n) claim.",
        "target_role_relevance": ["Data Structures", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "sorting_searching", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "Which of these sorting algorithms has the best WORST-CASE time complexity?",
        "options": [{"id": "a", "text": "Bubble sort -- O(n^2)"}, {"id": "b", "text": "Selection sort -- O(n^2)"}, {"id": "c", "text": "Merge sort -- O(n log n)"}, {"id": "d", "text": "Insertion sort -- O(n^2)"}],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "Merge sort guarantees O(n log n) in every case because it always splits the array in half and merges, regardless of input order.",
        "target_role_relevance": ["Algorithms"],
    },
    {
        "domain": "dsa", "concept": "sorting_searching", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the space complexity of the standard (non-in-place) merge sort implementation?",
        "options": [{"id": "a", "text": "O(1)"}, {"id": "b", "text": "O(log n)"}, {"id": "c", "text": "O(n)"}, {"id": "d", "text": "O(n^2)"}],
        "correct_answer": {"correct_option_ids": ["c"]},
        "explanation": "Merge sort needs an auxiliary array of size n to merge the sorted halves.",
        "target_role_relevance": ["Algorithms"],
    },
    {
        "domain": "dsa", "concept": "sorting_searching", "question_type": "short_answer", "difficulty": 4,
        "prompt": "Why can't binary search be used directly on an unsorted array?",
        "options": None,
        "correct_answer": {
            "keywords": ["sorted", "assumption", "eliminate half", "order"],
            "sample_answer": "Binary search relies on the array being sorted so that comparing the target to the middle element "
            "tells you which half to discard; on unsorted data that assumption breaks and you can't safely eliminate either half.",
        },
        "explanation": "Tests understanding of WHY the algorithm works, not just its complexity.",
        "target_role_relevance": ["Algorithms"],
    },

    # ---- OOP ----
    {
        "domain": "oop", "concept": "oop_basics", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "What is the difference between a class and an object?",
        "options": [
            {"id": "a", "text": "A class is a blueprint/template; an object is a specific instance created from that blueprint"},
            {"id": "b", "text": "They are exactly the same thing with different names"},
            {"id": "c", "text": "A class can only exist inside an object"},
            {"id": "d", "text": "An object is a blueprint; a class is an instance of it"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "A class defines the structure and behavior; an object is a concrete instance of that class in memory.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "oop_basics", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is a constructor used for in object-oriented programming?",
        "options": [
            {"id": "a", "text": "To destroy an object when it's no longer needed"},
            {"id": "b", "text": "To initialize a newly created object's state"},
            {"id": "c", "text": "To convert one class into another"},
            {"id": "d", "text": "To define which methods are private"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "A constructor runs automatically when an object is created, setting up its initial fields/state.",
        "target_role_relevance": ["Object-Oriented Programming"],
    },
    {
        "domain": "oop", "concept": "oop_basics", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does the `this` (Java/JS/C++) or `self` (Python) keyword refer to inside an instance method?",
        "options": [
            {"id": "a", "text": "The class itself, not any particular instance"},
            {"id": "b", "text": "The specific object instance the method was called on"},
            {"id": "c", "text": "A random object of the same type"},
            {"id": "d", "text": "The parent class"},
        ],
        "correct_answer": {"correct_option_ids": ["b"]},
        "explanation": "`this`/`self` is a reference to the specific instance on which the method is currently executing.",
        "target_role_relevance": ["Object-Oriented Programming"],
    },
    {
        "domain": "oop", "concept": "encapsulation", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is encapsulation in object-oriented programming?",
        "options": [
            {"id": "a", "text": "Bundling data and the methods that operate on it together, while restricting direct outside access to that data"},
            {"id": "b", "text": "Creating multiple classes that inherit from one base class"},
            {"id": "c", "text": "Writing a function that calls itself"},
            {"id": "d", "text": "Converting an object to a string"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Encapsulation hides an object's internal state and only exposes a controlled interface for interacting with it.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "encapsulation", "question_type": "concept_explanation", "difficulty": 3,
        "prompt": "Why do we make class fields private and expose getters/setters instead of just making the fields public?",
        "options": None,
        "correct_answer": {
            "keywords": ["validation", "control", "invariant", "internal representation"],
            "sample_answer": "Private fields with getters/setters let the class validate changes, enforce invariants, and change its "
            "internal representation later without breaking code that uses the class -- public fields give up all of that control.",
        },
        "explanation": "Tests the practical motivation behind encapsulation, not just its definition.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "encapsulation", "question_type": "short_answer", "difficulty": 4,
        "prompt": "What is the difference between the `private` and `protected` access modifiers?",
        "options": None,
        "correct_answer": {
            "keywords": ["subclass", "same class", "inherit", "accessible"],
            "sample_answer": "private members are only accessible within the class that declares them; protected members are "
            "additionally accessible from subclasses (and often the same package/module), letting inherited classes reuse internal state.",
        },
        "explanation": "A common confusion point for beginners.",
        "target_role_relevance": ["Object-Oriented Programming"],
    },
    {
        "domain": "oop", "concept": "inheritance", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does it mean for class `Dog` to 'inherit' from class `Animal`?",
        "options": [
            {"id": "a", "text": "Dog automatically gets Animal's fields and methods, and can add or override its own"},
            {"id": "b", "text": "Animal is deleted once Dog is created"},
            {"id": "c", "text": "Dog and Animal must have identical method implementations"},
            {"id": "d", "text": "Animal can now access Dog's private fields"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Inheritance lets a subclass reuse and extend a superclass's behavior, modeling an 'is-a' relationship.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "inheritance", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the key difference between single and multiple inheritance?",
        "options": [
            {"id": "a", "text": "Single inheritance means a class extends exactly one parent; multiple inheritance means it can extend more than one"},
            {"id": "b", "text": "Multiple inheritance means a class can only have one method"},
            {"id": "c", "text": "They are the same in every programming language"},
            {"id": "d", "text": "Single inheritance is only used in interfaces"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Some languages (like Java for classes) restrict inheritance to a single parent specifically to avoid ambiguity from multiple inheritance.",
        "target_role_relevance": ["Object-Oriented Programming", "Java"],
    },
    {
        "domain": "oop", "concept": "inheritance", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "What is the 'diamond problem' in multiple inheritance, and how does Java avoid it for classes?",
        "options": None,
        "correct_answer": {
            "keywords": ["ambiguous", "two parents", "common ancestor", "interfaces", "single inheritance"],
            "sample_answer": "The diamond problem occurs when a class inherits from two classes that both inherit from a common "
            "ancestor, creating ambiguity about which inherited method/field version to use. Java avoids it for classes by only "
            "allowing single inheritance (`extends` one class), while still allowing multiple interface implementation, where "
            "conflicts must be resolved explicitly.",
        },
        "explanation": "A classic OOP design-tradeoff question.",
        "target_role_relevance": ["Object-Oriented Programming", "Java"],
    },
    {
        "domain": "oop", "concept": "polymorphism", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is polymorphism in object-oriented programming?",
        "options": [
            {"id": "a", "text": "The ability for objects of different classes to be treated through a common interface, with each responding in its own way"},
            {"id": "b", "text": "The practice of having only one class in an application"},
            {"id": "c", "text": "A way to permanently delete unused classes"},
            {"id": "d", "text": "A synonym for encapsulation"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Polymorphism means 'many forms' -- the same method call can produce different behavior depending on the actual object's type.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "polymorphism", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the difference between method OVERLOADING and method OVERRIDING?",
        "options": [
            {"id": "a", "text": "Overloading defines multiple methods with the same name but different parameters in the same class; overriding redefines a parent method's behavior in a subclass"},
            {"id": "b", "text": "They are two names for exactly the same feature"},
            {"id": "c", "text": "Overriding can only happen within the same class"},
            {"id": "d", "text": "Overloading requires inheritance; overriding does not"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Overloading is compile-time (same class, different signatures); overriding is runtime (subclass replaces inherited behavior).",
        "target_role_relevance": ["Object-Oriented Programming", "Java"],
    },
    {
        "domain": "oop", "concept": "polymorphism", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "What is the difference between compile-time (static) polymorphism and run-time (dynamic) polymorphism?",
        "options": None,
        "correct_answer": {
            "keywords": ["overloading", "overriding", "compile time", "runtime", "virtual"],
            "sample_answer": "Compile-time polymorphism (method overloading) is resolved by the compiler based on the method "
            "signature at compile time. Run-time polymorphism (method overriding) is resolved at runtime based on the "
            "actual object type, typically via virtual method dispatch -- which concrete method runs depends on what the object actually is, not its declared type.",
        },
        "explanation": "Tests whether the student understands WHEN each kind of polymorphism is resolved.",
        "target_role_relevance": ["Object-Oriented Programming", "Java"],
    },
    {
        "domain": "oop", "concept": "abstraction", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is an abstract class, and why can't it be instantiated directly?",
        "options": [
            {"id": "a", "text": "It defines a partial blueprint (possibly with unimplemented methods) meant to be completed by a subclass, so instantiating it directly wouldn't make sense"},
            {"id": "b", "text": "It's a class that has been deleted from memory"},
            {"id": "c", "text": "It's just a regular class with a different naming convention"},
            {"id": "d", "text": "It can actually be instantiated directly like any other class"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Abstract classes may declare methods without implementations, so the language forbids creating an instance until a concrete subclass fills in the gaps.",
        "target_role_relevance": ["Object-Oriented Programming"],
    },
    {
        "domain": "oop", "concept": "abstraction", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the key difference between an abstract class and an interface (in languages that distinguish them)?",
        "options": [
            {"id": "a", "text": "An abstract class can have some concrete (implemented) methods and shared state; a traditional interface only declares a contract with no shared state"},
            {"id": "b", "text": "Interfaces can be instantiated directly, abstract classes cannot"},
            {"id": "c", "text": "There is no meaningful difference in any language"},
            {"id": "d", "text": "A class can implement multiple abstract classes but only one interface"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Abstract classes support partial implementation and instance fields; interfaces (classically) are pure contracts, and a class can implement several of them.",
        "target_role_relevance": ["Object-Oriented Programming", "Java"],
    },
    {
        "domain": "oop", "concept": "abstraction", "question_type": "short_answer", "difficulty": 4,
        "prompt": "Why is abstraction considered important for managing complexity in large codebases?",
        "options": None,
        "correct_answer": {
            "keywords": ["hide detail", "interface", "complexity", "implementation"],
            "sample_answer": "Abstraction lets callers depend on a simple, stable interface without needing to understand (or being "
            "affected by changes to) the implementation details behind it, which keeps large systems easier to reason about and change safely.",
        },
        "explanation": "Connects the OOP concept to real software-engineering motivation.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },

    # ---- Java ----
    {
        "domain": "java", "concept": "java_basics", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "What is the relationship between the JDK, the JRE, and the JVM?",
        "options": [
            {"id": "a", "text": "JVM runs bytecode; JRE bundles the JVM plus core libraries to RUN Java programs; JDK adds development tools (compiler, etc.) on top of the JRE"},
            {"id": "b", "text": "They are three unrelated, independent products"},
            {"id": "c", "text": "JDK is only for running programs; JRE is only for compiling them"},
            {"id": "d", "text": "JVM is a text editor for writing Java code"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "JVM executes bytecode, JRE = JVM + standard libraries needed to run apps, JDK = JRE + compiler/tools needed to build apps.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
    {
        "domain": "java", "concept": "java_basics", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "Is Java 'pass by value' or 'pass by reference' when you pass an object to a method?",
        "options": [
            {"id": "a", "text": "Pass by value -- but the value being copied is the object reference itself, so the method can still mutate the object's fields"},
            {"id": "b", "text": "Pass by reference -- reassigning the parameter inside the method changes the caller's variable"},
            {"id": "c", "text": "It depends on whether the object is a String"},
            {"id": "d", "text": "Java doesn't allow passing objects to methods"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Java is strictly pass-by-value; for objects, the 'value' passed is a copy of the reference, which is why mutating fields works but reassigning the parameter doesn't affect the caller.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_basics", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the difference between `==` and `.equals()` when comparing two Java String objects?",
        "options": [
            {"id": "a", "text": "== compares object references (identity); .equals() compares the actual character content"},
            {"id": "b", "text": "They always behave identically for Strings"},
            {"id": "c", "text": ".equals() compares references; == compares content"},
            {"id": "d", "text": "== only works on primitive types and never compiles for Strings"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "== checks if two references point to the same object in memory; .equals() (when properly overridden, as String does) checks logical/content equality.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_collections", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is the key practical difference between an `ArrayList` and a `LinkedList` in Java?",
        "options": [
            {"id": "a", "text": "ArrayList gives O(1) indexed access but O(n) middle insertion; LinkedList gives O(1) insertion at a known node but O(n) indexed access"},
            {"id": "b", "text": "LinkedList is always faster for every operation"},
            {"id": "c", "text": "ArrayList cannot store objects, only primitives"},
            {"id": "d", "text": "There is no practical difference"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "This mirrors the general array-vs-linked-list trade-off (see the DSA domain) applied to Java's standard library.",
        "target_role_relevance": ["Java", "Data Structures"],
    },
    {
        "domain": "java", "concept": "java_collections", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the main difference between a `HashMap` and a `TreeMap` in Java?",
        "options": [
            {"id": "a", "text": "HashMap offers average O(1) lookup with no ordering guarantee; TreeMap keeps keys sorted at the cost of O(log n) operations"},
            {"id": "b", "text": "TreeMap cannot store more than one entry"},
            {"id": "c", "text": "HashMap always iterates in insertion order"},
            {"id": "d", "text": "They have identical performance characteristics"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "HashMap is backed by a hash table (fast, unordered); TreeMap is backed by a red-black tree (sorted, logarithmic).",
        "target_role_relevance": ["Java", "Data Structures"],
    },
    {
        "domain": "java", "concept": "java_collections", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "Why must an object used as a `HashMap` key correctly override BOTH `hashCode()` and `equals()`?",
        "options": None,
        "correct_answer": {
            "keywords": ["hashcode", "equals", "bucket", "contract", "consistent"],
            "sample_answer": "HashMap uses hashCode() to pick a bucket and equals() to confirm a match within that bucket. If two "
            "'equal' objects return different hashCode() values, HashMap may look in the wrong bucket and fail to find an entry that's "
            "actually there -- violating the required hashCode/equals contract.",
        },
        "explanation": "A very common Java interview question that tests real understanding of hash-table internals.",
        "target_role_relevance": ["Java", "Data Structures"],
    },
    {
        "domain": "java", "concept": "java_exceptions", "question_type": "multiple_choice", "difficulty": 1,
        "prompt": "What is the difference between a CHECKED and an UNCHECKED exception in Java?",
        "options": [
            {"id": "a", "text": "Checked exceptions must be declared or caught at compile time; unchecked exceptions (RuntimeException and subclasses) are not enforced by the compiler"},
            {"id": "b", "text": "Unchecked exceptions can only occur in checked methods"},
            {"id": "c", "text": "They are identical; 'checked' is just older terminology"},
            {"id": "d", "text": "Checked exceptions can never be caught"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "The compiler forces callers to handle or declare checked exceptions (e.g. IOException); unchecked exceptions (e.g. NullPointerException) are not enforced.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_exceptions", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the purpose of the `finally` block in Java exception handling?",
        "options": [
            {"id": "a", "text": "It runs regardless of whether an exception was thrown or caught, typically used for cleanup like closing resources"},
            {"id": "b", "text": "It only runs if no exception occurred"},
            {"id": "c", "text": "It replaces the need for a catch block entirely"},
            {"id": "d", "text": "It runs before the try block"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "finally guarantees cleanup code (closing files, releasing locks) runs whether the try block succeeded, failed, or even returned early.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_exceptions", "question_type": "short_answer", "difficulty": 3,
        "prompt": "Why is catching the generic `Exception` class considered bad practice in most situations?",
        "options": None,
        "correct_answer": {
            "keywords": ["swallow", "specific", "hide bugs", "unrelated errors"],
            "sample_answer": "Catching Exception broadly swallows unrelated error types you didn't anticipate (including real bugs), "
            "hiding problems instead of handling them meaningfully -- catching specific exception types lets you respond appropriately to each failure mode.",
        },
        "explanation": "Common code-review feedback in real engineering teams.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
    {
        "domain": "java", "concept": "java_memory", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "In Java, where are local primitive variables and method call frames typically stored, versus where objects themselves live?",
        "options": [
            {"id": "a", "text": "Local variables/call frames live on the stack; objects (created with `new`) live on the heap"},
            {"id": "b", "text": "Everything is stored on the stack"},
            {"id": "c", "text": "Everything is stored on the heap"},
            {"id": "d", "text": "Objects live on the stack; primitives live on the heap"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "The stack holds per-call local variables and references; the actual objects those references point to are allocated on the heap.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_memory", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What makes an object eligible for garbage collection in Java?",
        "options": [
            {"id": "a", "text": "It is no longer reachable from any live thread or static reference"},
            {"id": "b", "text": "It has existed for more than 60 seconds"},
            {"id": "c", "text": "The programmer calls `delete` on it"},
            {"id": "d", "text": "It has more than one field"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Java's garbage collector reclaims objects once nothing in the program can reach them anymore -- there's no manual `delete`.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_memory", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "What is a 'memory leak' in Java, and how can one still happen despite automatic garbage collection?",
        "options": None,
        "correct_answer": {
            "keywords": ["reachable", "unused reference", "static", "cache", "listener"],
            "sample_answer": "A memory leak happens when objects are no longer actually needed by the program but are still "
            "reachable (e.g. held in a static collection, an unremoved event listener, or a growing cache), so the garbage collector "
            "can never reclaim them, and memory usage keeps growing.",
        },
        "explanation": "Tests understanding that GC only frees UNREACHABLE memory, not unused memory.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
    {
        "domain": "java", "concept": "java_multithreading", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What is the key difference between a process and a thread?",
        "options": [
            {"id": "a", "text": "A process has its own isolated memory space; threads within the same process share that memory space"},
            {"id": "b", "text": "A thread always runs in its own memory space, isolated from other threads"},
            {"id": "c", "text": "Processes and threads are the same thing in Java"},
            {"id": "d", "text": "A process can only ever have one thread"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Threads are lighter-weight units of execution that share their parent process's memory, which is why they can communicate easily but also risk race conditions.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
    {
        "domain": "java", "concept": "java_multithreading", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What does the `synchronized` keyword do in Java?",
        "options": [
            {"id": "a", "text": "Ensures only one thread at a time can execute the guarded block/method for a given lock, preventing concurrent access to shared state"},
            {"id": "b", "text": "Makes a method run faster by parallelizing it automatically"},
            {"id": "c", "text": "Deletes a thread once it finishes"},
            {"id": "d", "text": "Converts a method into a static method"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "synchronized acquires a monitor lock so that only one thread can be inside the critical section for that lock at a time.",
        "target_role_relevance": ["Java"],
    },
    {
        "domain": "java", "concept": "java_multithreading", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "What is a race condition, and how does synchronization prevent it?",
        "options": None,
        "correct_answer": {
            "keywords": ["concurrent", "shared state", "unpredictable", "lock", "interleave"],
            "sample_answer": "A race condition occurs when two or more threads access and modify shared state concurrently, and the "
            "final result depends unpredictably on the exact timing/interleaving of their operations. Synchronization prevents this by "
            "ensuring only one thread can execute the critical section at a time, making the shared-state updates atomic from other threads' perspective.",
        },
        "explanation": "One of the most commonly asked concurrency questions in technical interviews.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
]

# Extra questions on EXISTING sql/python concepts (from the original
# 298c98dafbbb migration) -- referenced by (domain_slug, concept_slug) so the
# follow-up migration can look up their already-existing concept_id in the DB
# rather than creating new concepts.
EXTRA_QUESTIONS_EXISTING = [
    {
        "domain": "sql", "concept": "joins", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "What does a SELF JOIN let you do that a regular join cannot?",
        "options": [
            {"id": "a", "text": "Join a table to itself, e.g. to compare rows within the same table (like an employee to their manager, stored in the same employees table)"},
            {"id": "b", "text": "Join more than two tables at once"},
            {"id": "c", "text": "Join without specifying an ON condition"},
            {"id": "d", "text": "Avoid using a WHERE clause"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "A self join treats one table as two logical copies (via aliases) to relate rows to other rows in the same table.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "indexes", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "Which SQL clause's columns should you typically consider indexing first for a performance win?",
        "options": [
            {"id": "a", "text": "Columns frequently used in WHERE filters and JOIN conditions"},
            {"id": "b", "text": "Columns that are never queried"},
            {"id": "c", "text": "Every column in the table, without exception"},
            {"id": "d", "text": "Only columns storing large text blobs"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Indexes speed up lookups on the columns actually used to filter or join rows; indexing rarely-queried columns wastes write performance and storage for no benefit.",
        "target_role_relevance": ["SQL", "Backend Engineer"],
    },
    {
        "domain": "sql", "concept": "normalization", "question_type": "short_answer", "difficulty": 3,
        "prompt": "What does '3rd Normal Form' (3NF) additionally require beyond 2NF?",
        "options": None,
        "correct_answer": {
            "keywords": ["transitive dependency", "non-key", "depends on"],
            "sample_answer": "3NF removes transitive dependencies: every non-key column must depend only on the primary key, not on another non-key column.",
        },
        "explanation": "Tests whether the student knows the specific rule added at each normal form, not just 'normalization is good'.",
        "target_role_relevance": ["SQL"],
    },
    {
        "domain": "sql", "concept": "aggregate_functions", "question_type": "multiple_choice", "difficulty": 2,
        "prompt": "What does `AVG(column)` ignore that could otherwise skew the result?",
        "options": [
            {"id": "a", "text": "NULL values -- they are excluded from both the sum and the count used to compute the average"},
            {"id": "b", "text": "Negative numbers"},
            {"id": "c", "text": "Duplicate rows"},
            {"id": "d", "text": "Nothing -- it always includes every row"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Like most aggregate functions, AVG ignores NULLs -- they don't count toward the sum or the divisor.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "python", "concept": "functions", "question_type": "short_answer", "difficulty": 4,
        "prompt": "What is the difference between `*args` and `**kwargs` in a Python function signature?",
        "options": None,
        "correct_answer": {
            "keywords": ["positional", "keyword", "tuple", "dict"],
            "sample_answer": "*args collects any extra positional arguments into a tuple; **kwargs collects any extra keyword "
            "arguments into a dict, letting a function accept a variable number of arguments of either kind.",
        },
        "explanation": "A frequently misunderstood but very common Python interview topic.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "data_types", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "Why can a `tuple` be used as a dictionary key in Python, but a `list` cannot?",
        "options": [
            {"id": "a", "text": "Tuples are immutable and hashable; lists are mutable and therefore unhashable"},
            {"id": "b", "text": "Tuples are faster to create than lists"},
            {"id": "c", "text": "Lists can only hold one type of data"},
            {"id": "d", "text": "There is no actual restriction -- both work identically"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Dictionary keys must be hashable; Python won't let mutable types like list be hashable because their hash would change if mutated, breaking the hash table.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "list_comprehension", "question_type": "short_answer", "difficulty": 3,
        "prompt": "Write (or describe) a list comprehension that produces only the EVEN numbers from 0 to 9.",
        "options": None,
        "correct_answer": {
            "keywords": ["if", "% 2", "even", "range"],
            "sample_answer": "[x for x in range(10) if x % 2 == 0] -- iterates 0-9 and keeps only values where the remainder after dividing by 2 is 0.",
        },
        "explanation": "Tests the conditional-filter form of a comprehension, not just the basic transform form.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "exceptions", "question_type": "multiple_choice", "difficulty": 3,
        "prompt": "What is the main risk of writing a bare `except:` (with no exception type specified) in Python?",
        "options": [
            {"id": "a", "text": "It catches EVERYTHING, including KeyboardInterrupt and SystemExit, silently hiding bugs and making the program hard to stop or debug"},
            {"id": "b", "text": "It only catches ValueError"},
            {"id": "c", "text": "Python doesn't allow this syntax at all"},
            {"id": "d", "text": "It automatically logs the error to a file"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "A bare except catches every exception, including ones you almost never want to swallow silently -- catching specific exception types is safer practice.",
        "target_role_relevance": ["Python", "Software Engineer"],
    },
]

# ============================================================================
# BANK V3 -- hard, concept- and implementation-level questions (difficulty 4-5)
# on the ALREADY-SEEDED domains/concepts (sql, python, javascript, dsa, oop,
# java). Referenced by (domain_slug, concept_slug); the follow-up migration
# looks the concept_id up in the DB, exactly like EXTRA_QUESTIONS_EXISTING.
# Purely additive -- never edits a row from an earlier migration.
# ============================================================================
BANK_V3_QUESTIONS = [
    # ------------------------------------------------------------------ SQL
    {
        "domain": "sql", "concept": "subqueries", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Why can `WHERE col NOT IN (SELECT other_col FROM t)` return zero rows unexpectedly, and what should you use instead?",
        "options": None,
        "correct_answer": {
            "keywords": ["NULL", "NOT IN", "three-valued logic", "unknown", "NOT EXISTS"],
            "sample_answer": "If the subquery returns even one NULL, `NOT IN` evaluates to UNKNOWN for every outer row "
            "(x <> NULL is never TRUE under three-valued logic), so the whole predicate filters everything out. Use "
            "`NOT EXISTS` with a correlated subquery, or add `WHERE other_col IS NOT NULL` to the inner query.",
        },
        "explanation": "A correct answer identifies the NULL-in-subquery + three-valued-logic cause and recommends NOT EXISTS.",
        "target_role_relevance": ["SQL", "Data Engineer"],
    },
    {
        "domain": "sql", "concept": "aggregate_functions", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "You need a running total per customer ordered by date, WITHOUT collapsing the individual order rows. What do you use?",
        "options": [
            {"id": "a", "text": "A window function: SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date)"},
            {"id": "b", "text": "GROUP BY customer_id with SUM(amount)"},
            {"id": "c", "text": "A correlated subquery in the WHERE clause"},
            {"id": "d", "text": "DISTINCT with ORDER BY"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Window functions compute an aggregate over a frame of rows while keeping every row; GROUP BY would collapse them.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "indexes", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "A composite index on (last_name, first_name) exists. Explain which of these it helps and why: (1) WHERE last_name = ?, (2) WHERE first_name = ?, (3) WHERE last_name = ? ORDER BY first_name.",
        "options": None,
        "correct_answer": {
            "keywords": ["leftmost prefix", "leftmost", "first_name alone", "sorted", "ORDER BY"],
            "sample_answer": "The index is sorted by last_name, then first_name, so it serves the leftmost-prefix queries: "
            "(1) is a direct range/seek on last_name; (3) is a seek on last_name plus the ORDER BY first_name comes free "
            "because within one last_name the entries are already ordered by first_name. (2) filtering by first_name alone "
            "cannot use the index for a seek because first_name is not a prefix -- it would need a full scan.",
        },
        "explanation": "A correct answer invokes the leftmost-prefix rule and notes the ordered second column serves ORDER BY.",
        "target_role_relevance": ["SQL", "Backend Engineer"],
    },
    {
        "domain": "sql", "concept": "aggregate_functions", "question_type": "code_reading", "difficulty": 4,
        "prompt": "A table `reviews(product_id, rating)` has some rows where `rating IS NULL`. Explain the difference between `COUNT(*)`, `COUNT(rating)`, and `AVG(rating)` for a given product.",
        "options": None,
        "correct_answer": {
            "keywords": ["COUNT(*)", "all rows", "COUNT(rating)", "non-null", "AVG", "ignores NULL"],
            "sample_answer": "`COUNT(*)` counts every row including NULL-rating rows. `COUNT(rating)` counts only rows where "
            "rating is not NULL. `AVG(rating)` sums the non-NULL ratings and divides by `COUNT(rating)` -- it ignores "
            "NULLs entirely rather than treating them as zero.",
        },
        "explanation": "A correct answer distinguishes row count vs non-null count and states AVG divides by the non-null count.",
        "target_role_relevance": ["SQL", "Data Analyst"],
    },
    {
        "domain": "sql", "concept": "normalization", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "A table has columns (student_id, student_dept, dept_head). `dept_head` depends on `student_dept`, which depends on `student_id`. Which normal form does this violate, and what fixes it?",
        "options": [
            {"id": "a", "text": "3NF -- a transitive dependency (non-key -> non-key); split dept into its own table keyed by student_dept"},
            {"id": "b", "text": "1NF -- there is a repeating group; add more rows"},
            {"id": "c", "text": "2NF -- a partial dependency on part of a composite key; there is no composite key here so it's fine"},
            {"id": "d", "text": "BCNF only -- no lower form is violated"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "dept_head is transitively dependent on the key via student_dept -- the textbook 3NF violation, fixed by extracting a Department table.",
        "target_role_relevance": ["SQL", "Backend Engineer"],
    },
    # --------------------------------------------------------------- Python
    {
        "domain": "python", "concept": "functions", "question_type": "code_reading", "difficulty": 5,
        "prompt": "What does this print, and why?\n\n    def append_to(x, target=[]):\n        target.append(x)\n        return target\n\n    print(append_to(1))\n    print(append_to(2))",
        "options": None,
        "correct_answer": {
            "keywords": ["mutable default", "evaluated once", "def", "[1]", "[1, 2]", "shared"],
            "sample_answer": "It prints `[1]` then `[1, 2]`. The default `[]` is evaluated once when the function is "
            "defined, not on each call, so every call that omits `target` mutates the same shared list. The fix is "
            "`target=None` then `if target is None: target = []` inside the body.",
        },
        "explanation": "A correct answer names the mutable-default-argument trap and the None sentinel fix.",
        "target_role_relevance": ["Python", "Software Engineer"],
    },
    {
        "domain": "python", "concept": "functions", "question_type": "code_reading", "difficulty": 5,
        "prompt": "What list does this produce and why?\n\n    funcs = [lambda: i for i in range(3)]\n    print([f() for f in funcs])",
        "options": None,
        "correct_answer": {
            "keywords": ["late binding", "closure", "[2, 2, 2]", "i", "default argument", "loop variable"],
            "sample_answer": "It prints `[2, 2, 2]`. Each lambda closes over the variable `i`, not its value at "
            "creation time; by the time the lambdas are called the loop has finished and `i == 2`. Capture per-iteration "
            "with `lambda i=i: i`.",
        },
        "explanation": "A correct answer explains Python closures capture the variable (late binding) and gives the default-arg capture fix.",
        "target_role_relevance": ["Python", "Software Engineer"],
    },
    {
        "domain": "python", "concept": "data_types", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "Explain when `a == b` is True but `a is b` is False, and when `a is b` can be surprisingly True for two separately written literals.",
        "options": None,
        "correct_answer": {
            "keywords": ["equality", "identity", "value", "same object", "small int cache", "interning"],
            "sample_answer": "`==` compares value; `is` compares identity (same object in memory). Two lists `[1,2] == [1,2]` "
            "is True but `is` is False -- different objects. `is` can be surprisingly True for small integers (CPython "
            "caches roughly -5..256) and some interned strings, so `256 is 256` is True while `257 is 257` may be False "
            "depending on context. Never use `is` for value comparison; use it only for `None`/sentinels.",
        },
        "explanation": "A correct answer separates value vs identity and cites the small-int / string interning caching.",
        "target_role_relevance": ["Python"],
    },
    {
        "domain": "python", "concept": "functions", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "Why should a decorator use `functools.wraps`, and what breaks if it doesn't?",
        "options": None,
        "correct_answer": {
            "keywords": ["__name__", "__doc__", "metadata", "wrapper", "introspection", "functools.wraps"],
            "sample_answer": "Without `@functools.wraps(func)` on the inner wrapper, the decorated function takes on the "
            "wrapper's identity: `__name__` becomes 'wrapper', `__doc__` and `__wrapped__` are lost, and signature "
            "introspection, help(), and some frameworks that dispatch on function name break. `wraps` copies that "
            "metadata from the original onto the wrapper.",
        },
        "explanation": "A correct answer names the lost dunder metadata (__name__/__doc__) and the introspection breakage.",
        "target_role_relevance": ["Python", "Software Engineer"],
    },
    {
        "domain": "python", "concept": "exceptions", "question_type": "code_reading", "difficulty": 5,
        "prompt": "What does this return, and what is the danger of the pattern?\n\n    def f():\n        try:\n            return 1\n        finally:\n            return 2",
        "options": None,
        "correct_answer": {
            "keywords": ["finally", "2", "overrides", "return", "swallow", "exception"],
            "sample_answer": "It returns `2`. A `return` (or `break`/`continue`) in a `finally` block overrides any "
            "return or in-flight exception from the `try` block. That means a `finally: return` silently swallows "
            "exceptions raised in `try`, which is why returning from `finally` is considered a bug.",
        },
        "explanation": "A correct answer states the result is 2 and that finally's return suppresses exceptions from try.",
        "target_role_relevance": ["Python", "Software Engineer"],
    },
    {
        "domain": "python", "concept": "dict_operations", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "Compare `d.setdefault(k, expensive())` with `collections.defaultdict(expensive)` -- what is the subtle cost of each?",
        "options": None,
        "correct_answer": {
            "keywords": ["setdefault", "always evaluated", "default factory", "missing key", "eager", "side effect"],
            "sample_answer": "`d.setdefault(k, expensive())` always evaluates `expensive()` even when `k` is already "
            "present -- the argument is computed before the call -- so it can waste work or trigger side effects. "
            "`defaultdict(expensive)` only calls the factory on a genuinely missing key, but it also inserts that key on "
            "any read via `d[k]`, so merely checking `d[missing]` mutates the dict.",
        },
        "explanation": "A correct answer notes setdefault's eager argument evaluation and defaultdict's insert-on-read.",
        "target_role_relevance": ["Python", "Software Engineer"],
    },
    # ----------------------------------------------------------- JavaScript
    {
        "domain": "javascript", "concept": "js_async", "question_type": "code_reading", "difficulty": 5,
        "prompt": "In what order do the numbers print?\n\n    console.log(1);\n    setTimeout(() => console.log(2), 0);\n    Promise.resolve().then(() => console.log(3));\n    console.log(4);",
        "options": None,
        "correct_answer": {
            "keywords": ["1", "4", "3", "2", "microtask", "macrotask", "event loop"],
            "sample_answer": "1, 4, 3, 2. Synchronous code runs first (1, 4). Then the microtask queue drains before "
            "any macrotask, so the resolved Promise's `.then` callback (3) runs. `setTimeout` schedules a macrotask, so "
            "2 runs last, after the microtask queue is empty.",
        },
        "explanation": "A correct answer gives 1,4,3,2 and explains microtasks (Promise jobs) drain before macrotasks (setTimeout).",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_functions", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "State the rules that determine the value of `this` in a regular function call, and how an arrow function differs.",
        "options": None,
        "correct_answer": {
            "keywords": ["call site", "method", "new", "call/apply/bind", "arrow", "lexical", "undefined", "strict"],
            "sample_answer": "For a regular function `this` is set by the call site: `new` -> the new instance; explicit "
            "`call`/`apply`/`bind` -> the given object; method call `obj.fn()` -> `obj`; otherwise (plain call) -> the "
            "global object, or `undefined` in strict mode / modules. An arrow function has no own `this`; it captures "
            "`this` lexically from the enclosing scope at definition time and cannot be rebound.",
        },
        "explanation": "A correct answer lists new/explicit/implicit/default binding and that arrows bind this lexically.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_fundamentals", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Explain the Temporal Dead Zone. How do `let`/`const` differ from `var` with respect to hoisting?",
        "options": None,
        "correct_answer": {
            "keywords": ["hoisted", "Temporal Dead Zone", "TDZ", "ReferenceError", "var", "undefined", "initialized"],
            "sample_answer": "`var` declarations are hoisted and initialized to `undefined`, so reading one before its line "
            "gives `undefined`. `let` and `const` are also hoisted but NOT initialized -- from the start of the block "
            "until the declaration line they are in the Temporal Dead Zone, and any access throws a ReferenceError. "
            "`const` additionally requires an initializer and forbids reassignment.",
        },
        "explanation": "A correct answer says let/const are hoisted-but-uninitialised (TDZ -> ReferenceError) vs var -> undefined.",
        "target_role_relevance": ["JavaScript"],
    },
    {
        "domain": "javascript", "concept": "js_fundamentals", "question_type": "multiple_selection", "difficulty": 4,
        "prompt": "Which of these evaluate to `true`? (Select all that apply.)",
        "options": [
            {"id": "a", "text": "typeof NaN === 'number'"},
            {"id": "b", "text": "NaN === NaN"},
            {"id": "c", "text": "[] == false"},
            {"id": "d", "text": "0.1 + 0.2 === 0.3"},
            {"id": "e", "text": "typeof [] === 'object'"},
        ],
        "correct_answer": {"correct_option_ids": ["a", "c", "e"]},
        "explanation": "NaN is a number and is never equal to itself. `[] == false` is true via coercion ([] -> '' -> 0). "
        "0.1 + 0.2 is 0.30000000000000004. Arrays report typeof 'object'.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_arrays_objects", "question_type": "code_reading", "difficulty": 5,
        "prompt": "What is logged, and why?\n\n    const a = { x: 1, nested: { y: 2 } };\n    const b = { ...a };\n    b.x = 9;\n    b.nested.y = 99;\n    console.log(a.x, a.nested.y);",
        "options": None,
        "correct_answer": {
            "keywords": ["shallow copy", "spread", "1", "99", "reference", "nested", "shared"],
            "sample_answer": "It logs `1 99`. The spread `{ ...a }` makes a shallow copy: top-level primitives like `x` "
            "are copied by value, so `a.x` stays 1. But `nested` is copied by reference -- `a.nested` and `b.nested` are "
            "the same object -- so `b.nested.y = 99` is visible through `a`. A deep copy (structuredClone) avoids this.",
        },
        "explanation": "A correct answer gives `1 99` and explains spread is a shallow copy sharing nested object references.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    {
        "domain": "javascript", "concept": "js_async", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "You fire 5 network requests and want ALL results, but must not fail the whole batch if one rejects. Which API?",
        "options": [
            {"id": "a", "text": "Promise.allSettled -- resolves once every promise settles, each result tagged {status, value|reason}"},
            {"id": "b", "text": "Promise.all -- rejects as soon as any input rejects"},
            {"id": "c", "text": "Promise.race -- settles with the first promise to settle"},
            {"id": "d", "text": "Promise.any -- rejects only if every promise rejects"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Promise.allSettled never short-circuits; Promise.all rejects on the first rejection, losing the other results.",
        "target_role_relevance": ["JavaScript", "Frontend Engineer"],
    },
    # ------------------------------------------------------------------ DSA
    {
        "domain": "dsa", "concept": "complexity", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "A dynamic array doubles its capacity when full, which is an O(n) copy. Explain why appending is still O(1) amortized.",
        "options": None,
        "correct_answer": {
            "keywords": ["amortized", "doubling", "geometric series", "n + n/2 + n/4", "2n", "total work", "per operation"],
            "sample_answer": "Over n appends the resize copies happen at sizes 1, 2, 4, ..., n, and 1 + 2 + 4 + ... + n < "
            "2n total element copies (a geometric series). Adding the n cheap writes, total work is O(n), so the "
            "amortized cost per append is O(1). Any single append can still be O(n), but that cost is 'paid off' by the "
            "many O(1) appends around it.",
        },
        "explanation": "A correct answer uses the geometric-series bound (total copies < 2n) to get O(1) amortized.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "sorting_searching", "question_type": "multiple_selection", "difficulty": 5,
        "prompt": "Select every statement that is TRUE.",
        "options": [
            {"id": "a", "text": "Merge sort is stable but not in-place (O(n) extra space in the standard array version)"},
            {"id": "b", "text": "Quicksort is in-place (O(log n) stack) but not stable"},
            {"id": "c", "text": "Heapsort is in-place but not stable"},
            {"id": "d", "text": "Comparison sorts can beat O(n log n) worst case"},
            {"id": "e", "text": "Counting sort can be O(n + k) because it does not compare elements"},
        ],
        "correct_answer": {"correct_option_ids": ["a", "b", "c", "e"]},
        "explanation": "Only (d) is false: the comparison-sort lower bound is Omega(n log n). Non-comparison sorts like counting/radix sidestep it.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "trees_graphs", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Why does plain BFS fail to find shortest paths on a weighted graph, and what do you use for (a) non-negative weights and (b) possibly-negative weights?",
        "options": None,
        "correct_answer": {
            "keywords": ["BFS", "unit weight", "edges", "Dijkstra", "priority queue", "Bellman-Ford", "negative", "relax"],
            "sample_answer": "BFS assumes every edge costs the same (1), so it explores in order of edge count, not path "
            "weight -- a 3-edge path of weight 3 can beat a 1-edge path of weight 10, which BFS would wrongly pick. For "
            "non-negative weights use Dijkstra (greedy with a min-priority-queue, settle the closest unfinished node). "
            "For possibly-negative weights use Bellman-Ford (relax all edges V-1 times, and one more pass detects a "
            "negative cycle).",
        },
        "explanation": "A correct answer ties BFS to uniform edge cost and names Dijkstra (non-negative) vs Bellman-Ford (negative).",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "trees_graphs", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "How do you detect a cycle in a DIRECTED graph with DFS?",
        "options": [
            {"id": "a", "text": "Track three states (unvisited / in-progress / done); a cycle exists if DFS reaches a node currently 'in-progress' (on the recursion stack)"},
            {"id": "b", "text": "A cycle exists if DFS ever reaches an already-visited node"},
            {"id": "c", "text": "Count edges; a cycle exists iff edges >= vertices"},
            {"id": "d", "text": "Run BFS and check for any cross edge"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "In a directed graph, revisiting a 'done' node is fine (a DAG has many). Only a back edge to a node still on the recursion stack means a cycle.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "stacks_queues", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Explain how a monotonic stack solves 'next greater element' for every array position in O(n) total.",
        "options": None,
        "correct_answer": {
            "keywords": ["monotonic", "decreasing", "pop", "each element pushed and popped once", "amortized", "O(n)"],
            "sample_answer": "Iterate left to right keeping a stack of indices whose values are strictly decreasing. For "
            "each new element, pop every stack entry smaller than it -- the current element is their 'next greater' -- "
            "then push the current index. Each index is pushed once and popped at most once, so the total work across "
            "all n steps is O(n) even though a single step can pop many entries.",
        },
        "explanation": "A correct answer describes the decreasing stack and the each-element-pushed/popped-once amortized argument.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "complexity", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "By the Master Theorem, what is the solution to T(n) = 2T(n/2) + O(n)?",
        "options": [
            {"id": "a", "text": "O(n log n)"},
            {"id": "b", "text": "O(n)"},
            {"id": "c", "text": "O(n^2)"},
            {"id": "d", "text": "O(log n)"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "n^(log_2 2) = n^1 matches the O(n) combine term (case 2), giving an extra log factor: O(n log n). This is merge sort.",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    {
        "domain": "dsa", "concept": "arrays_strings", "question_type": "code_reading", "difficulty": 5,
        "prompt": "This is meant to return the length of the longest substring without repeating characters. What bug makes it overcount, and how do you fix it?\n\n    def length_of_longest(s):\n        seen = {}\n        left = 0\n        best = 0\n        for right, ch in enumerate(s):\n            if ch in seen:\n                left = seen[ch] + 1\n            seen[ch] = right\n            best = max(best, right - left + 1)\n        return best",
        "options": None,
        "correct_answer": {
            "keywords": ["left", "move backwards", "max(left, seen[ch] + 1)", "duplicate outside window", "abba"],
            "sample_answer": "When a repeated character was last seen BEFORE the current window's left edge, `left = "
            "seen[ch] + 1` moves `left` backwards, growing the window past a real duplicate (e.g. 'abba' reports 3). Fix: "
            "`left = max(left, seen[ch] + 1)` so the left edge never retreats.",
        },
        "explanation": "A correct answer spots that left can move backwards and fixes it with max(left, seen[ch] + 1).",
        "target_role_relevance": ["Algorithms", "Software Engineer"],
    },
    # ------------------------------------------------------------------ OOP
    {
        "domain": "oop", "concept": "polymorphism", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "State the Liskov Substitution Principle and give the classic Rectangle/Square example of violating it.",
        "options": None,
        "correct_answer": {
            "keywords": ["subtype", "substitutable", "behavioral", "invariant", "Square", "setWidth", "setHeight", "postcondition"],
            "sample_answer": "LSP: objects of a subtype must be usable anywhere the supertype is expected without breaking "
            "the program's correctness -- subclasses must honor the base type's contracts (preconditions no stronger, "
            "postconditions no weaker, invariants preserved). Square extends Rectangle but overrides setWidth to also "
            "change height (to keep sides equal). Code that relies on Rectangle's contract -- 'setWidth leaves height "
            "unchanged' -- breaks when handed a Square, so Square is not a valid subtype of Rectangle.",
        },
        "explanation": "A correct answer states behavioral substitutability + contract rules and the Square.setWidth side effect.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "inheritance", "question_type": "multiple_choice", "difficulty": 5,
        "prompt": "Why do languages like Java forbid multiple class inheritance, and what is the usual recommended alternative?",
        "options": [
            {"id": "a", "text": "The diamond problem -- ambiguous method/state resolution when two parents share a base; prefer composition and interfaces"},
            {"id": "b", "text": "It makes compilation slower; prefer marking classes final"},
            {"id": "c", "text": "It breaks encapsulation entirely; prefer making all fields public"},
            {"id": "d", "text": "There is no real reason; other languages allow it with no downside"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "The diamond problem creates ambiguity in which inherited implementation/state wins. 'Favor composition over inheritance' plus interfaces is the standard answer.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "abstraction", "question_type": "concept_explanation", "difficulty": 4,
        "prompt": "When would you choose an abstract class over an interface, and vice versa?",
        "options": None,
        "correct_answer": {
            "keywords": ["shared implementation", "state", "single inheritance", "interface", "multiple", "contract", "capability"],
            "sample_answer": "Use an abstract class when subclasses share real implementation code or mutable state and "
            "form a genuine 'is-a' hierarchy -- but you spend the one inheritance slot. Use an interface to declare a "
            "capability/contract that unrelated types can implement, to allow a type to satisfy many contracts, and when "
            "you have no shared implementation (or only defaults). Modern practice: interface for the type, optional "
            "abstract base for convenience.",
        },
        "explanation": "A correct answer contrasts shared state/impl + single inheritance (abstract class) vs multiple capability contracts (interface).",
        "target_role_relevance": ["Object-Oriented Programming"],
    },
    {
        "domain": "oop", "concept": "encapsulation", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "Adding a public getter and setter for every private field is often criticized because...",
        "options": [
            {"id": "a", "text": "It exposes the internal representation as effectively public, so invariants aren't protected -- expose behavior/intent, not raw state"},
            {"id": "b", "text": "Getters and setters are slower than direct field access and hurt performance"},
            {"id": "c", "text": "It is a compile error in most languages"},
            {"id": "d", "text": "It prevents the class from being subclassed"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Blanket accessors give the same coupling as public fields and let callers put the object in invalid states; good encapsulation exposes operations that keep invariants.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    {
        "domain": "oop", "concept": "polymorphism", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "Distinguish method overloading from overriding, and explain which is resolved at compile time vs run time.",
        "options": None,
        "correct_answer": {
            "keywords": ["overloading", "compile-time", "static", "signature", "overriding", "runtime", "dynamic dispatch", "actual type"],
            "sample_answer": "Overloading: same method name, different parameter lists in the same type; the compiler picks "
            "which one based on the static (declared) argument types -- compile-time / static dispatch. Overriding: a "
            "subclass replaces a superclass method with the same signature; the call dispatches on the object's actual "
            "runtime type -- run-time / dynamic dispatch. This is why calling an overridden method through a base-type "
            "reference still runs the subclass version.",
        },
        "explanation": "A correct answer maps overloading -> compile-time/static and overriding -> runtime/dynamic dispatch on actual type.",
        "target_role_relevance": ["Object-Oriented Programming", "Software Engineer"],
    },
    # ----------------------------------------------------------------- Java
    {
        "domain": "java", "concept": "java_multithreading", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "What does `volatile` guarantee and what does it NOT guarantee? Why is `volatile int count; count++;` still not thread-safe?",
        "options": None,
        "correct_answer": {
            "keywords": ["visibility", "happens-before", "no caching", "atomicity", "read-modify-write", "count++", "AtomicInteger", "synchronized"],
            "sample_answer": "`volatile` guarantees visibility and ordering: a write is flushed so other threads see the "
            "latest value (no stale cached copy), and it establishes happens-before between the write and subsequent "
            "reads. It does NOT provide atomicity for compound actions. `count++` is a read-modify-write: two threads "
            "can both read the same value, increment, and write back, losing an update. Use `AtomicInteger` "
            "(incrementAndGet) or a `synchronized` block.",
        },
        "explanation": "A correct answer separates visibility/ordering (volatile does) from atomicity of read-modify-write (it doesn't).",
        "target_role_relevance": ["Java", "Backend Engineer"],
    },
    {
        "domain": "java", "concept": "java_collections", "question_type": "concept_explanation", "difficulty": 5,
        "prompt": "State the equals()/hashCode() contract. What goes wrong if you put an object in a HashSet and then mutate a field used by hashCode()?",
        "options": None,
        "correct_answer": {
            "keywords": ["equal objects", "same hashCode", "consistent", "bucket", "mutate", "lost", "not found", "contains"],
            "sample_answer": "Contract: if a.equals(b) then a.hashCode() == b.hashCode(); equal objects must have equal "
            "hash codes, and hashCode must stay consistent while the object is in a hash structure. If you mutate a "
            "field that feeds hashCode() after inserting into a HashSet/HashMap, the object now hashes to a different "
            "bucket than the one it's stored in, so contains()/get()/remove() fail to find it -- it's effectively lost, "
            "and the collection can even report size 1 while contains() returns false.",
        },
        "explanation": "A correct answer states equal => same hashCode + consistency, and that mutation strands the entry in the wrong bucket.",
        "target_role_relevance": ["Java", "Backend Engineer"],
    },
    {
        "domain": "java", "concept": "java_memory", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "For `void m() { int x = 5; Point p = new Point(1, 2); }`, where do `x`, the `Point` object, and the reference `p` live?",
        "options": [
            {"id": "a", "text": "x and the reference p are on the thread's stack frame; the Point object is on the heap"},
            {"id": "b", "text": "All three are on the heap"},
            {"id": "c", "text": "All three are on the stack"},
            {"id": "d", "text": "x is on the heap, p and the Point are on the stack"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "Local primitives and local reference variables live in the stack frame; the object they point to is allocated on the heap.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
    {
        "domain": "java", "concept": "java_multithreading", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "You need a shared integer counter incremented by many threads, nothing else. Lowest-overhead correct choice?",
        "options": [
            {"id": "a", "text": "AtomicInteger with incrementAndGet() -- lock-free CAS, purpose-built for this"},
            {"id": "b", "text": "A plain int marked volatile"},
            {"id": "c", "text": "Wrap every access in synchronized on a shared lock -- always the only correct option"},
            {"id": "d", "text": "A plain int -- the JVM makes ++ atomic"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "volatile doesn't make ++ atomic; a plain int is a data race. AtomicInteger uses CAS and is lighter than a lock for a single counter.",
        "target_role_relevance": ["Java", "Backend Engineer"],
    },
    {
        "domain": "java", "concept": "java_basics", "question_type": "code_reading", "difficulty": 5,
        "prompt": "What does this print and why?\n\n    Integer a = 127, b = 127;\n    Integer c = 128, d = 128;\n    System.out.println((a == b) + \" \" + (c == d));",
        "options": None,
        "correct_answer": {
            "keywords": ["Integer cache", "-128", "127", "autoboxing", "same object", "== compares references", "equals"],
            "sample_answer": "It prints `true false`. Autoboxing via Integer.valueOf caches boxed values from -128 to 127, "
            "so `a` and `b` are the same cached object and `a == b` (reference comparison) is true. 128 is outside the "
            "cache, so `c` and `d` are distinct objects and `c == d` is false. Comparing boxed values should use "
            "`equals()` or unbox to `int`.",
        },
        "explanation": "A correct answer cites the -128..127 Integer cache and that == compares references for boxed types.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
    {
        "domain": "java", "concept": "java_exceptions", "question_type": "multiple_choice", "difficulty": 4,
        "prompt": "Which statement about checked vs unchecked exceptions in Java is correct?",
        "options": [
            {"id": "a", "text": "Checked exceptions (subclasses of Exception but not RuntimeException) must be declared or caught; unchecked (RuntimeException/Error) need not be"},
            {"id": "b", "text": "Unchecked exceptions must always be declared in a throws clause"},
            {"id": "c", "text": "Checked exceptions cannot be caught, only logged"},
            {"id": "d", "text": "There is no compiler difference; the distinction is only a naming convention"},
        ],
        "correct_answer": {"correct_option_ids": ["a"]},
        "explanation": "The compiler enforces handle-or-declare for checked exceptions; RuntimeException and Error are exempt.",
        "target_role_relevance": ["Java", "Software Engineer"],
    },
]

