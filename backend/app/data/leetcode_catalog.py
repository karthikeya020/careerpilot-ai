"""Curated LeetCode problem catalog, keyed by assessment concept slug.

This is a static, hand-picked mapping -- the same posture as the seeded
`RESOURCES` list in app/seed/assessment_taxonomy.py: no scraping, no runtime
fetch. Every entry is a canonical, well-known LeetCode problem whose slug a
reviewer can verify at https://leetcode.com/problems/<slug>/ . The
recommendation service reads a student's per-concept accuracy from their
stored assessment responses and pulls the problems for the concepts they
are weakest on.

Structure:
  CONCEPT_PROBLEMS[concept_slug] -> list[(leetcode_slug, title, difficulty)]
  CONCEPT_FOCUS[concept_slug]    -> one line on what practising these fixes
  DOMAIN_PROBLEMS[domain_slug]   -> fallback list when a weak concept has no
                                   dedicated mapping, or for the no-history
                                   profile-based recommendation path.

difficulty is LeetCode's own label: "Easy" | "Medium" | "Hard".
"""

LEETCODE_BASE_URL = "https://leetcode.com/problems/"


def problem_url(slug: str) -> str:
    return f"{LEETCODE_BASE_URL}{slug}/"


# --------------------------------------------------------------------------
# Concept -> problems
# --------------------------------------------------------------------------
CONCEPT_PROBLEMS: dict[str, list[tuple[str, str, str]]] = {
    # ---- DSA: arrays & strings ----
    "arrays_strings": [
        ("two-sum", "Two Sum", "Easy"),
        ("best-time-to-buy-and-sell-stock", "Best Time to Buy and Sell Stock", "Easy"),
        ("product-of-array-except-self", "Product of Array Except Self", "Medium"),
        ("3sum", "3Sum", "Medium"),
        ("longest-substring-without-repeating-characters", "Longest Substring Without Repeating Characters", "Medium"),
        ("container-with-most-water", "Container With Most Water", "Medium"),
        ("trapping-rain-water", "Trapping Rain Water", "Hard"),
        ("minimum-window-substring", "Minimum Window Substring", "Hard"),
    ],
    # ---- DSA: linked lists ----
    "linked_lists": [
        ("reverse-linked-list", "Reverse Linked List", "Easy"),
        ("linked-list-cycle", "Linked List Cycle", "Easy"),
        ("merge-two-sorted-lists", "Merge Two Sorted Lists", "Easy"),
        ("remove-nth-node-from-end-of-list", "Remove Nth Node From End of List", "Medium"),
        ("add-two-numbers", "Add Two Numbers", "Medium"),
        ("copy-list-with-random-pointer", "Copy List With Random Pointer", "Medium"),
        ("reverse-nodes-in-k-group", "Reverse Nodes in k-Group", "Hard"),
        ("merge-k-sorted-lists", "Merge k Sorted Lists", "Hard"),
    ],
    # ---- DSA: stacks & queues ----
    "stacks_queues": [
        ("valid-parentheses", "Valid Parentheses", "Easy"),
        ("implement-queue-using-stacks", "Implement Queue using Stacks", "Easy"),
        ("min-stack", "Min Stack", "Medium"),
        ("evaluate-reverse-polish-notation", "Evaluate Reverse Polish Notation", "Medium"),
        ("daily-temperatures", "Daily Temperatures", "Medium"),
        ("largest-rectangle-in-histogram", "Largest Rectangle in Histogram", "Hard"),
        ("basic-calculator", "Basic Calculator", "Hard"),
    ],
    # ---- DSA: trees & graphs ----
    "trees_graphs": [
        ("binary-tree-level-order-traversal", "Binary Tree Level Order Traversal", "Medium"),
        ("validate-binary-search-tree", "Validate Binary Search Tree", "Medium"),
        ("lowest-common-ancestor-of-a-binary-tree", "Lowest Common Ancestor of a Binary Tree", "Medium"),
        ("number-of-islands", "Number of Islands", "Medium"),
        ("course-schedule", "Course Schedule", "Medium"),
        ("clone-graph", "Clone Graph", "Medium"),
        ("word-ladder", "Word Ladder", "Hard"),
        ("serialize-and-deserialize-binary-tree", "Serialize and Deserialize Binary Tree", "Hard"),
        ("binary-tree-maximum-path-sum", "Binary Tree Maximum Path Sum", "Hard"),
    ],
    # ---- DSA: sorting & searching ----
    "sorting_searching": [
        ("binary-search", "Binary Search", "Easy"),
        ("sort-colors", "Sort Colors", "Medium"),
        ("search-in-rotated-sorted-array", "Search in Rotated Sorted Array", "Medium"),
        ("find-minimum-in-rotated-sorted-array", "Find Minimum in Rotated Sorted Array", "Medium"),
        ("kth-largest-element-in-an-array", "Kth Largest Element in an Array", "Medium"),
        ("merge-intervals", "Merge Intervals", "Medium"),
        ("median-of-two-sorted-arrays", "Median of Two Sorted Arrays", "Hard"),
    ],
    # ---- DSA: time & space complexity ----
    "complexity": [
        ("sqrtx", "Sqrt(x)", "Easy"),
        ("search-a-2d-matrix", "Search a 2D Matrix", "Medium"),
        ("find-peak-element", "Find Peak Element", "Medium"),
        ("koko-eating-bananas", "Koko Eating Bananas", "Medium"),
        ("split-array-largest-sum", "Split Array Largest Sum", "Hard"),
    ],
    # ---- JavaScript: fundamentals ----
    "js_fundamentals": [
        ("create-hello-world-function", "Create Hello World Function", "Easy"),
        ("counter", "Counter", "Easy"),
        ("to-be-or-not-to-be", "To Be Or Not To Be", "Easy"),
        ("apply-transform-over-each-element-in-array", "Apply Transform Over Each Element in Array", "Easy"),
    ],
    # ---- JavaScript: functions & scope (closures, currying) ----
    "js_functions": [
        ("counter-ii", "Counter II", "Easy"),
        ("allow-one-function-call", "Allow One Function Call", "Medium"),
        ("memoize", "Memoize", "Medium"),
        ("curry", "Curry", "Medium"),
        ("debounce", "Debounce", "Medium"),
        ("throttle", "Throttle", "Medium"),
    ],
    # ---- JavaScript: async (promises, event loop) ----
    "js_async": [
        ("sleep", "Sleep", "Easy"),
        ("add-two-promises", "Add Two Promises", "Easy"),
        ("promise-time-limit", "Promise Time Limit", "Medium"),
        ("promise-pool", "Promise Pool", "Medium"),
        ("cache-with-time-limit", "Cache With Time Limit", "Medium"),
        ("debounce", "Debounce", "Medium"),
    ],
    # ---- JavaScript: arrays & objects ----
    "js_arrays_objects": [
        ("array-reduce-transformation", "Array Reduce Transformation", "Easy"),
        ("array-wrapper", "Array Wrapper", "Easy"),
        ("chunk-array", "Chunk Array", "Easy"),
        ("group-by", "Group By", "Medium"),
        ("flatten-deeply-nested-array", "Flatten Deeply Nested Array", "Medium"),
        ("array-of-objects-to-matrix", "Array of Objects to Matrix", "Hard"),
    ],
    # ---- JavaScript: DOM & events ----
    "js_dom_events": [
        ("event-emitter", "Event Emitter", "Medium"),
        ("cache-with-time-limit", "Cache With Time Limit", "Medium"),
        ("debounce", "Debounce", "Medium"),
        ("throttle", "Throttle", "Medium"),
    ],
    # ---- SQL: joins family (LeetCode's SQL track) ----
    "joins": [
        ("combine-two-tables", "Combine Two Tables", "Easy"),
        ("customers-who-never-order", "Customers Who Never Order", "Easy"),
        ("employees-earning-more-than-their-managers", "Employees Earning More Than Their Managers", "Easy"),
        ("replace-employee-id-with-the-unique-identifier", "Replace Employee ID With The Unique Identifier", "Easy"),
        ("rising-temperature", "Rising Temperature", "Easy"),
        ("department-highest-salary", "Department Highest Salary", "Medium"),
    ],
    "inner_join": [
        ("employees-earning-more-than-their-managers", "Employees Earning More Than Their Managers", "Easy"),
        ("rising-temperature", "Rising Temperature", "Easy"),
        ("exchange-seats", "Exchange Seats", "Medium"),
        ("department-highest-salary", "Department Highest Salary", "Medium"),
    ],
    "outer_join": [
        ("combine-two-tables", "Combine Two Tables", "Easy"),
        ("customers-who-never-order", "Customers Who Never Order", "Easy"),
        ("students-and-examinations", "Students and Examinations", "Easy"),
        ("find-customer-referee", "Find Customer Referee", "Easy"),
    ],
    "table_relationships": [
        ("combine-two-tables", "Combine Two Tables", "Easy"),
        ("replace-employee-id-with-the-unique-identifier", "Replace Employee ID With The Unique Identifier", "Easy"),
        ("employee-bonus", "Employee Bonus", "Easy"),
        ("students-and-examinations", "Students and Examinations", "Easy"),
    ],
    "relational_model": [
        ("big-countries", "Big Countries", "Easy"),
        ("recyclable-and-low-fat-products", "Recyclable and Low Fat Products", "Easy"),
        ("article-views-i", "Article Views I", "Easy"),
        ("invalid-tweets", "Invalid Tweets", "Easy"),
    ],
    "group_by": [
        ("classes-more-than-5-students", "Classes More Than 5 Students", "Easy"),
        ("project-employees-i", "Project Employees I", "Easy"),
        ("game-play-analysis-i", "Game Play Analysis I", "Easy"),
        ("number-of-unique-subjects-taught-by-each-teacher", "Number of Unique Subjects Taught by Each Teacher", "Easy"),
        ("group-sold-products-by-the-date", "Group Sold Products By The Date", "Easy"),
    ],
    "aggregate_functions": [
        ("average-selling-price", "Average Selling Price", "Easy"),
        ("queries-quality-and-percentage", "Queries Quality and Percentage", "Easy"),
        ("percentage-of-users-attended-a-contest", "Percentage of Users Attended a Contest", "Easy"),
        ("monthly-transactions-i", "Monthly Transactions I", "Medium"),
        ("department-top-three-salaries", "Department Top Three Salaries", "Hard"),
    ],
    "where_vs_having": [
        ("classes-more-than-5-students", "Classes More Than 5 Students", "Easy"),
        ("customers-who-never-order", "Customers Who Never Order", "Easy"),
        ("find-users-with-valid-e-mails", "Find Users With Valid E-Mails", "Easy"),
        ("product-sales-analysis-iii", "Product Sales Analysis III", "Medium"),
    ],
    "subqueries": [
        ("second-highest-salary", "Second Highest Salary", "Medium"),
        ("nth-highest-salary", "Nth Highest Salary", "Medium"),
        ("employees-earning-more-than-their-managers", "Employees Earning More Than Their Managers", "Easy"),
        ("managers-with-at-least-5-direct-reports", "Managers with at Least 5 Direct Reports", "Medium"),
        ("consecutive-numbers", "Consecutive Numbers", "Medium"),
    ],
    "indexes": [
        ("rank-scores", "Rank Scores", "Medium"),
        ("consecutive-numbers", "Consecutive Numbers", "Medium"),
        ("human-traffic-of-stadium", "Human Traffic of Stadium", "Hard"),
        ("trips-and-users", "Trips and Users", "Hard"),
    ],
    "normalization": [
        ("replace-employee-id-with-the-unique-identifier", "Replace Employee ID With The Unique Identifier", "Easy"),
        ("combine-two-tables", "Combine Two Tables", "Easy"),
        ("employee-bonus", "Employee Bonus", "Easy"),
        ("triangle-judgement", "Triangle Judgement", "Easy"),
    ],
    # ---- Python core concepts (general algorithmic practice) ----
    "data_types": [
        ("valid-anagram", "Valid Anagram", "Easy"),
        ("contains-duplicate", "Contains Duplicate", "Easy"),
        ("two-sum", "Two Sum", "Easy"),
        ("group-anagrams", "Group Anagrams", "Medium"),
        ("top-k-frequent-elements", "Top K Frequent Elements", "Medium"),
    ],
    "list_comprehension": [
        ("squares-of-a-sorted-array", "Squares of a Sorted Array", "Easy"),
        ("matrix-diagonal-sum", "Matrix Diagonal Sum", "Easy"),
        ("transpose-matrix", "Transpose Matrix", "Easy"),
        ("spiral-matrix", "Spiral Matrix", "Medium"),
        ("pascals-triangle", "Pascal's Triangle", "Easy"),
    ],
    "functions": [
        ("fibonacci-number", "Fibonacci Number", "Easy"),
        ("power-of-three", "Power of Three", "Easy"),
        ("pow-x-n", "Pow(x, n)", "Medium"),
        ("permutations", "Permutations", "Medium"),
        ("subsets", "Subsets", "Medium"),
    ],
    "exceptions": [
        ("string-to-integer-atoi", "String to Integer (atoi)", "Medium"),
        ("valid-number", "Valid Number", "Hard"),
        ("basic-calculator-ii", "Basic Calculator II", "Medium"),
        ("integer-to-roman", "Integer to Roman", "Medium"),
    ],
    "dict_operations": [
        ("ransom-note", "Ransom Note", "Easy"),
        ("first-unique-character-in-a-string", "First Unique Character in a String", "Easy"),
        ("two-sum", "Two Sum", "Easy"),
        ("subarray-sum-equals-k", "Subarray Sum Equals K", "Medium"),
        ("longest-consecutive-sequence", "Longest Consecutive Sequence", "Medium"),
        ("lru-cache", "LRU Cache", "Medium"),
    ],
    # ---- OOP: design problems ----
    "oop_basics": [
        ("design-parking-system", "Design Parking System", "Easy"),
        ("design-hashmap", "Design HashMap", "Easy"),
        ("design-hashset", "Design HashSet", "Easy"),
        ("design-an-ordered-stream", "Design an Ordered Stream", "Easy"),
    ],
    "encapsulation": [
        ("min-stack", "Min Stack", "Medium"),
        ("design-browser-history", "Design Browser History", "Medium"),
        ("design-circular-queue", "Design Circular Queue", "Medium"),
        ("design-a-stack-with-increment-operation", "Design a Stack With Increment Operation", "Medium"),
    ],
    "inheritance": [
        ("design-underground-system", "Design Underground System", "Medium"),
        ("design-a-leaderboard", "Design a Leaderboard", "Medium"),
        ("design-a-food-rating-system", "Design a Food Rating System", "Medium"),
    ],
    "polymorphism": [
        ("flatten-nested-list-iterator", "Flatten Nested List Iterator", "Medium"),
        ("design-twitter", "Design Twitter", "Medium"),
        ("peeking-iterator", "Peeking Iterator", "Medium"),
        ("implement-trie-prefix-tree", "Implement Trie (Prefix Tree)", "Medium"),
    ],
    "abstraction": [
        ("lru-cache", "LRU Cache", "Medium"),
        ("lfu-cache", "LFU Cache", "Hard"),
        ("design-in-memory-file-system", "Design In-Memory File System", "Hard"),
        ("all-oone-data-structure", "All O`one Data Structure", "Hard"),
    ],
    # ---- Java: collections & concurrency ----
    "java_basics": [
        ("valid-anagram", "Valid Anagram", "Easy"),
        ("roman-to-integer", "Roman to Integer", "Easy"),
        ("string-to-integer-atoi", "String to Integer (atoi)", "Medium"),
        ("add-strings", "Add Strings", "Easy"),
    ],
    "java_collections": [
        ("design-hashmap", "Design HashMap", "Easy"),
        ("group-anagrams", "Group Anagrams", "Medium"),
        ("top-k-frequent-elements", "Top K Frequent Elements", "Medium"),
        ("lru-cache", "LRU Cache", "Medium"),
        ("insert-delete-getrandom-o1", "Insert Delete GetRandom O(1)", "Medium"),
    ],
    "java_exceptions": [
        ("string-to-integer-atoi", "String to Integer (atoi)", "Medium"),
        ("valid-number", "Valid Number", "Hard"),
        ("basic-calculator", "Basic Calculator", "Hard"),
    ],
    "java_memory": [
        ("lru-cache", "LRU Cache", "Medium"),
        ("lfu-cache", "LFU Cache", "Hard"),
        ("design-linked-list", "Design Linked List", "Medium"),
        ("copy-list-with-random-pointer", "Copy List With Random Pointer", "Medium"),
    ],
    "java_multithreading": [
        ("print-in-order", "Print in Order", "Easy"),
        ("print-foobar-alternately", "Print FooBar Alternately", "Medium"),
        ("print-zero-even-odd", "Print Zero Even Odd", "Medium"),
        ("fizz-buzz-multithreaded", "Fizz Buzz Multithreaded", "Medium"),
        ("building-h2o", "Building H2O", "Medium"),
        ("the-dining-philosophers", "The Dining Philosophers", "Medium"),
    ],
}


# One line per concept: what working these problems actually builds.
CONCEPT_FOCUS: dict[str, str] = {
    "arrays_strings": "Two-pointer and sliding-window patterns on contiguous data.",
    "linked_lists": "Pointer manipulation, cycle detection, and in-place reversal.",
    "stacks_queues": "Monotonic stacks, LIFO/FIFO modelling, and expression parsing.",
    "trees_graphs": "BFS/DFS traversal, topological sort, and recursion on trees.",
    "sorting_searching": "Binary search on the answer and divide-and-conquer.",
    "complexity": "Reasoning about time/space bounds and binary-search-on-answer.",
    "js_fundamentals": "Types, equality, and closures over primitive state.",
    "js_functions": "Closures, higher-order functions, currying, and rate-limiting.",
    "js_async": "Promises, async/await, and event-loop ordering.",
    "js_arrays_objects": "Array methods, reduce, destructuring, and deep traversal.",
    "js_dom_events": "Event subscription models and time-bounded caching.",
    "joins": "Combining rows across tables with the right join type.",
    "inner_join": "Matching rows that exist in both tables, including self-joins.",
    "outer_join": "Preserving unmatched rows with LEFT/RIGHT joins and NULL handling.",
    "table_relationships": "Following primary/foreign keys across a schema.",
    "relational_model": "Selecting and filtering rows and columns from one table.",
    "group_by": "Collapsing rows into groups and counting within them.",
    "aggregate_functions": "COUNT/SUM/AVG, window functions, and top-N-per-group.",
    "where_vs_having": "Filtering rows before grouping vs. groups after.",
    "subqueries": "Correlated and scalar subqueries, and Nth-value queries.",
    "indexes": "Query patterns where ranking and self-joins dominate cost.",
    "normalization": "Splitting and re-joining data to remove redundancy.",
    "data_types": "Hashing, sets, and frequency counting.",
    "list_comprehension": "Transforming and building sequences and matrices.",
    "functions": "Recursion, backtracking, and parameter design.",
    "exceptions": "Input validation and defensive parsing of messy strings.",
    "dict_operations": "Hash-map lookups, prefix sums, and O(1) design.",
    "oop_basics": "Modelling state and behaviour as a class API.",
    "encapsulation": "Keeping invariants valid behind a small public interface.",
    "inheritance": "Sharing behaviour across related types.",
    "polymorphism": "Iterators and one interface over many implementations.",
    "abstraction": "Designing a data structure to a spec, hiding internals.",
    "java_basics": "String handling and numeric parsing.",
    "java_collections": "Map/Set/List trade-offs and O(1) composite structures.",
    "java_exceptions": "Validating input and failing on malformed data.",
    "java_memory": "Reference wiring, node reuse, and avoiding leaks.",
    "java_multithreading": "Synchronisation, ordering, and deadlock avoidance.",
}


# "How to think to solve this" -- the canonical approach for problems of
# each concept, shown in the explain pop-up before the student even pastes
# code. A live AI review can tailor further; this is the always-available
# floor.
CONCEPT_APPROACH: dict[str, str] = {
    "arrays_strings": "Ask whether the array is sorted -- if so, two pointers from both ends or a moving window usually beats a nested loop. For subarray/substring targets, grow a window on the right and shrink from the left while a running total or character-count map stays valid. Aim for one pass and O(1) extra space.",
    "linked_lists": "You only get forward pointers, so track the nodes you care about explicitly: a dummy head to simplify edge cases, fast/slow pointers for the middle or a cycle, and a `prev` pointer to reverse in place. Draw 3 nodes and re-point arrows one at a time before coding.",
    "stacks_queues": "Reach for a stack when the answer depends on the most recent unmatched thing -- brackets, previous greater element, expression evaluation. A monotonic stack keeps candidates in sorted order so each element is pushed and popped once, giving O(n).",
    "trees_graphs": "Decide BFS vs DFS first: BFS (a queue) for shortest path in an unweighted graph or level-by-level work; DFS (recursion or a stack) for reachability, subtree aggregates, and cycle detection. Mark nodes visited on entry, and for trees think about what each node needs back from its children.",
    "sorting_searching": "If the array is (or can be) sorted, binary search the index -- or binary-search the *answer* itself when you can cheaply test 'is value X feasible?'. Watch the loop invariant and whether the bound is inclusive; off-by-one is where these break.",
    "complexity": "State the brute force and its cost out loud, then find the repeated work. Binary-searching the answer turns many 'minimise the maximum' problems from O(n^2) into O(n log range). Always check the space cost, not just time.",
    "js_fundamentals": "Be precise about value vs reference and about which `this` a call site binds. Closures capture the variable, not its value at creation -- capture per iteration if you need the old value.",
    "js_functions": "Return a function that closes over the state you need (a counter, a cache, a timer id). For rate-limiting (debounce/throttle) the closed-over timer id is the whole trick; clear it and reset on each call.",
    "js_async": "Model the timeline: synchronous code first, then the microtask queue (resolved Promise callbacks) drains fully, then one macrotask (setTimeout). `await` just schedules the rest of the function as a microtask.",
    "js_arrays_objects": "Prefer `map`/`filter`/`reduce` over manual loops, and remember spread/`Object.assign` are shallow -- nested objects are still shared. For deep transforms, recurse and rebuild.",
    "js_dom_events": "Think in subscribe/unsubscribe pairs: store listeners in a map keyed by event name, return an unsubscribe handle, and clean up timers so nothing leaks.",
    "joins": "Name each table, decide the join key, then the join type: INNER for rows that must match on both sides, LEFT to keep every row of the driving table and NULL-fill the rest. Self-join with two aliases to compare a row to another row in the same table.",
    "inner_join": "Only rows present on both sides survive. A self-join (two aliases of one table) with an inequality in the ON/WHERE clause is the standard 'compare each row to a related row' pattern.",
    "outer_join": "LEFT JOIN keeps every row of the left table; unmatched right-side columns come back NULL. Filter for `right.key IS NULL` to find left rows with no match ('customers who never ordered').",
    "table_relationships": "Follow the keys: a foreign key on one table points at a primary key on another. Join on that pair, then select the columns you actually need.",
    "relational_model": "One table, so it's SELECT the columns, WHERE the rows. Get the filter predicate exactly right (ranges, NULLs, string matches) before adding anything else.",
    "group_by": "GROUP BY collapses rows that share the grouped values into one row each; every non-grouped column in SELECT must be inside an aggregate. Count/sum happen per group.",
    "aggregate_functions": "COUNT(*) counts rows, COUNT(col) counts non-NULLs, AVG ignores NULLs. For 'top N per group' or running totals, use a window function (OVER PARTITION BY ... ORDER BY ...) so you keep every row.",
    "where_vs_having": "WHERE filters individual rows before grouping; HAVING filters whole groups after aggregation. If the condition uses COUNT/SUM/etc., it belongs in HAVING.",
    "subqueries": "A scalar subquery returns one value you can compare against (e.g. MAX salary). A correlated subquery re-runs per outer row -- powerful for 'is there a related row such that...' but think about cost.",
    "indexes": "These problems reward ranking and self-join patterns; think about which columns a query filters and orders on, since that's what an index would cover.",
    "normalization": "Spot the repeated fact, pull it into its own table keyed by what it depends on, and re-join. 3NF removes non-key-to-non-key (transitive) dependencies.",
    "data_types": "Hash it: a set for 'seen before?', a dict for counts or last-seen index. Trading O(n) space for O(1) lookups collapses most nested-loop solutions to one pass.",
    "list_comprehension": "Describe the output shape first (a flat list, a matrix, a filtered slice), then write the comprehension that builds exactly that. Nested comprehensions read outer-loop-first.",
    "functions": "For 'all combinations / arrangements', use recursion with a choose / recurse / un-choose (backtracking) skeleton. Define the base case and what one recursive call is responsible for.",
    "exceptions": "Enumerate every malformed input (empty, whitespace, sign, overflow, trailing junk) and decide the response for each before writing the happy path. Validate, then parse.",
    "dict_operations": "A hash map turns 'find the pair/subarray that sums to k' into one pass: store what you've seen (value -> index, or prefix-sum -> count) and check for the complement as you go.",
    "oop_basics": "List the operations the object must support, then the minimal state each needs. The public methods are the spec; fields are private implementation detail.",
    "encapsulation": "Keep an invariant true at all times by only mutating state through methods that re-establish it (e.g. Min Stack pushes the running min alongside each value).",
    "inheritance": "Model shared behaviour once, then vary the parts that differ. If you're reaching for inheritance just to reuse code, prefer composition -- hold a helper object instead.",
    "polymorphism": "Program to an interface (an Iterator, a Comparator) so callers don't branch on type. Each implementation fills in the one method that differs.",
    "abstraction": "Design to the stated operations and their required Big-O (e.g. LRU Cache: O(1) get and put). Pick the internal structures -- hash map + doubly linked list -- that make every operation hit that bound.",
    "java_basics": "Watch String immutability and the `==` vs `.equals()` distinction; build strings with StringBuilder, and remember Integer autoboxing caches -128..127.",
    "java_collections": "Choose by access pattern: HashMap for O(1) keyed lookup, TreeMap for ordered/range, ArrayDeque for stack/queue. Combine a HashMap with a linked list for O(1) ordered structures.",
    "java_exceptions": "Validate inputs up front and throw (or return a sentinel) on malformed data; keep the parsing logic linear and total.",
    "java_memory": "Local variables and references live on the stack; objects on the heap. Reuse nodes instead of reallocating, and drop references you no longer need so nothing is retained.",
    "java_multithreading": "Identify the ordering constraint, then enforce it with the lightest tool: a CountDownLatch or Semaphore for 'A before B', synchronized/ReentrantLock for a critical section, AtomicInteger for a lone counter. Always acquire multiple locks in a fixed global order to avoid deadlock.",
}


def concept_for_slug(slug: str) -> str | None:
    """First concept whose curated list contains this problem slug."""
    for concept, rows in CONCEPT_PROBLEMS.items():
        if any(entry[0] == slug for entry in rows):
            return concept
    return None


def similar_problems(
    slug: str, concept_slug: str | None, domain_slug: str | None = None, limit: int = 4
) -> list[tuple[str, str, str]]:
    """Other canonical problems for the same concept (then the same domain),
    excluding `slug`. Deterministic -- no AI involved."""
    concept = concept_slug or concept_for_slug(slug)
    seen: set[str] = {slug}
    pool: list[tuple[str, str, str]] = []
    sources: list[list[tuple[str, str, str]]] = []
    if concept:
        sources.append(CONCEPT_PROBLEMS.get(concept, []))
    if domain_slug:
        sources.append(DOMAIN_PROBLEMS.get(domain_slug, []))
    for rows in sources:
        for entry in rows:
            if entry[0] not in seen:
                seen.add(entry[0])
                pool.append(entry)
            if len(pool) >= limit:
                return pool[:limit]
    return pool[:limit]


# Fallback per domain -- used when a weak concept has no dedicated list, and
# for the no-assessment-history profile-based path.
DOMAIN_PROBLEMS: dict[str, list[tuple[str, str, str]]] = {
    "dsa": [
        ("two-sum", "Two Sum", "Easy"),
        ("valid-parentheses", "Valid Parentheses", "Easy"),
        ("merge-two-sorted-lists", "Merge Two Sorted Lists", "Easy"),
        ("best-time-to-buy-and-sell-stock", "Best Time to Buy and Sell Stock", "Easy"),
        ("number-of-islands", "Number of Islands", "Medium"),
        ("course-schedule", "Course Schedule", "Medium"),
        ("lru-cache", "LRU Cache", "Medium"),
        ("median-of-two-sorted-arrays", "Median of Two Sorted Arrays", "Hard"),
    ],
    "javascript": [
        ("counter", "Counter", "Easy"),
        ("sleep", "Sleep", "Easy"),
        ("array-reduce-transformation", "Array Reduce Transformation", "Easy"),
        ("memoize", "Memoize", "Medium"),
        ("curry", "Curry", "Medium"),
        ("debounce", "Debounce", "Medium"),
        ("promise-pool", "Promise Pool", "Medium"),
        ("event-emitter", "Event Emitter", "Medium"),
    ],
    "sql": [
        ("combine-two-tables", "Combine Two Tables", "Easy"),
        ("second-highest-salary", "Second Highest Salary", "Medium"),
        ("customers-who-never-order", "Customers Who Never Order", "Easy"),
        ("classes-more-than-5-students", "Classes More Than 5 Students", "Easy"),
        ("department-highest-salary", "Department Highest Salary", "Medium"),
        ("rank-scores", "Rank Scores", "Medium"),
        ("consecutive-numbers", "Consecutive Numbers", "Medium"),
        ("department-top-three-salaries", "Department Top Three Salaries", "Hard"),
    ],
    "oop": [
        ("design-parking-system", "Design Parking System", "Easy"),
        ("design-hashmap", "Design HashMap", "Easy"),
        ("min-stack", "Min Stack", "Medium"),
        ("design-browser-history", "Design Browser History", "Medium"),
        ("design-underground-system", "Design Underground System", "Medium"),
        ("lru-cache", "LRU Cache", "Medium"),
        ("design-twitter", "Design Twitter", "Medium"),
        ("lfu-cache", "LFU Cache", "Hard"),
    ],
    "java": [
        ("design-hashmap", "Design HashMap", "Easy"),
        ("group-anagrams", "Group Anagrams", "Medium"),
        ("top-k-frequent-elements", "Top K Frequent Elements", "Medium"),
        ("lru-cache", "LRU Cache", "Medium"),
        ("print-in-order", "Print in Order", "Easy"),
        ("print-foobar-alternately", "Print FooBar Alternately", "Medium"),
        ("fizz-buzz-multithreaded", "Fizz Buzz Multithreaded", "Medium"),
        ("building-h2o", "Building H2O", "Medium"),
    ],
    "python": [
        ("valid-anagram", "Valid Anagram", "Easy"),
        ("contains-duplicate", "Contains Duplicate", "Easy"),
        ("group-anagrams", "Group Anagrams", "Medium"),
        ("top-k-frequent-elements", "Top K Frequent Elements", "Medium"),
        ("subarray-sum-equals-k", "Subarray Sum Equals K", "Medium"),
        ("permutations", "Permutations", "Medium"),
        ("lru-cache", "LRU Cache", "Medium"),
        ("longest-consecutive-sequence", "Longest Consecutive Sequence", "Medium"),
    ],
}
