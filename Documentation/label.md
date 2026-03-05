# Labels Documentation

A complete guide to using labels in the AI Auto-Issue Generator.

---

## How It Works

When you make a **push** or open/update a **Pull Request**, GitHub Actions runs `process_event.py`. The script reads the labels and decides what role the AI analyzer should take — security auditor, architect, QA engineer, etc.

```
Your action (push / PR)
        ↓
GitHub Actions runs process_event.py
        ↓
Script reads labels
        ↓
Selects role and prompt for the model
        ↓
Creates an Issue with analysis + comment in PR
```

Every Issue includes:
- **Severity** in the title (`[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`)
- **Problem section** — what exactly is wrong and where
- **Code Reference** — the specific problematic code
- **Suggested Fix** — how to resolve it
- **Permalink** — direct link to the file and line on GitHub

---

## How to Activate Labels

### In a Pull Request
Add a label via the GitHub UI — right panel of the PR → **Labels** → select the one you need.
The workflow fires on the `labeled` event.

### In a commit message (push)
Insert the label in square brackets inside the commit message:

```
git commit -m "refactor auth module [security]"
git commit -m "add stripe integration [deps][review]"
git commit -m "update service layer [arch]"
```

You can specify **multiple labels** — the first match wins, in the priority order listed below.

---

## All Labels

### 🔒 `[security]` / `[sec]` / `[audit]`

**Model role:** Strict Security Auditor

**What it analyzes:**
- OWASP Top 10 vulnerabilities
- SQL / NoSQL injections
- Insecure handling of tokens, passwords, and secrets
- Exposed endpoints without authorization
- Insecure deserialization
- Hardcoded credentials in code

**Example Issue:**
```
[HIGH] SQL Injection vulnerability in user search endpoint

## Problem
In `api/users.py`, line 47, user input is passed directly
into a SQL query without parameterization.

## Code Reference
query = f"SELECT * FROM users WHERE name = '{user_input}'"

## Suggested Fix
Use parameterized queries:
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))

## Permalink
https://github.com/org/repo/blob/abc1234/api/users.py#L47
```

---

### 👁 `[review]` / `[refactor]` / `[code-review]`

**Model role:** Strict Code Reviewer

**What it analyzes:**
- Violations of SOLID principles
- DRY violations (duplicated code)
- Overly long functions / God classes
- Poor variable and function naming
- Missing error handling
- Magic numbers and magic strings

**Example Issue:**
```
[MEDIUM] Single Responsibility Principle violation in OrderService

## Problem
The class `OrderService` in `services/order.py` (lines 12–180)
handles business logic, sends emails, and writes to the database
all at once — three separate responsibilities in one class.

## Suggested Fix
Split into OrderService, OrderNotifier, and OrderRepository.
```

---

### 🧪 `[qa]` / `[test]` / `[testing]`

**Model role:** QA Engineer

**What it analyzes:**
- Uncovered edge cases
- Missing unit / integration tests
- Functions with no test coverage
- Incorrect handling of null / None / empty values
- Boundary conditions (empty array, negative numbers, very long strings)

**Example Issue:**
```
[MEDIUM] Missing edge case tests for payment processing

## Problem
The function `calculate_total()` in `utils/cart.py` has no tests
for: empty cart, item quantity = 0, negative price.

## Suggested Fix
def test_calculate_total_empty_cart():
    assert calculate_total([]) == 0

def test_calculate_total_zero_quantity():
    ...
```

---

### ⚡ `[perf]` / `[performance]` / `[optimize]`

**Model role:** Performance Expert

**What it analyzes:**
- O(n²) or worse algorithmic complexity
- N+1 database queries
- Missing caching where it is needed
- Loading unnecessary data (SELECT * instead of specific fields)
- Blocking operations inside async code
- Memory leaks

**Example Issue:**
```
[HIGH] N+1 database query problem in product listing

## Problem
In `views/products.py`, line 34, a separate query to the categories
table is executed for every product in a loop.
With 1000 products this results in 1001 database queries.

## Suggested Fix
Use select_related() or prefetch_related():
Product.objects.prefetch_related('category').all()
```

---

### 📦 `[deps]` / `[dependencies]`

**Model role:** Security & Dependency Auditor

**What it analyzes:**
- Known CVE vulnerabilities in new dependencies
- License compatibility (MIT / Apache / GPL — GPL can be a legal risk)
- Package maintenance activity (last commit, open issues)
- Bundle size impact of the added package
- Risky transitive dependencies
- Duplicate dependencies (a similar package already exists in the project)

**Example Issue:**
```
[HIGH] Dependency risk: lodash@3.10.1 has known prototype pollution CVE

## Problem
`some-lib==1.2.0` added in `requirements.txt` pulls in
lodash@3.10.1, which has CVE-2019-10744 (prototype pollution).

## Suggested Fix
Upgrade to lodash@4.17.21 or replace with native JS methods.
```

---

### 🏛 `[arch]` / `[architecture]`

**Model role:** Software Architect

**What it analyzes:**
- Layer separation violations (e.g. business logic inside a controller)
- Tight coupling between modules
- Dependency Inversion violations (depending on concrete classes, not abstractions)
- Anti-patterns: God Object, Spaghetti Logic, Shotgun Surgery
- Magic numbers and global mutable state
- Code in the wrong place (utility logic in a service, model logic in a controller)

**Example Issue:**
```
[MEDIUM] Business logic leaking into controller layer

## Problem
`controllers/checkout.py`, lines 67–102, contains discount
and tax calculation — this is business logic that belongs
in `services/pricing.py`.

## Suggested Fix
Extract to PricingService.calculate_final_price(cart, user)
and call it from the controller in a single line.
```

---

### 📋 `[pm]` / `[release]` / `[product]`

**Model role:** Product Manager

**What it analyzes:**
- Describes changes from the user's perspective, not the code's
- Generates Release Notes
- Highlights what changed, what improved, and what broke (breaking changes)
- Written to be understood by a non-technical audience

**Example Issue:**
```
[LOW] Release Notes: User authentication improvements

## What's New
Users can now sign in via Google OAuth.
Session duration has been extended from 1 hour to 24 hours.

## Improvements
The login page loads 40% faster.

## Breaking Changes
Legacy v1 API tokens are no longer supported.
Please re-issue tokens via /api/v2/auth.
```

---

### 📝 No label (default)

**Model role:** General Analyst

**What it analyzes:**
- Standard change documentation
- A general description of what was changed and why
- Used when no label matches any of the above

---

## Severity Levels

Every Issue is automatically assigned a severity based on the analysis:

| Level | Meaning | Examples |
|-------|---------|---------|
| `[CRITICAL]` | Requires immediate fix | RCE, data leak, production outage |
| `[HIGH]` | Fix within the current sprint | SQL injection, N+1 on a key page |
| `[MEDIUM]` | Schedule for a future sprint | SOLID violation, missing tests |
| `[LOW]` | Technical debt | Naming, code style, minor refactor |

Severity is automatically added as a GitHub label: `severity: critical`, `severity: high`, etc.

---

## Duplicate Protection

The script automatically:

1. **Skips creation** of a new Issue if an open Issue for the same commit or PR already exists
2. **Does not reopen** an Issue if a similar Issue was already found and closed
3. **Ignores merge commits** — a commit with 2+ parents (automatically created on PR merge) is skipped

---

## PR Comment

When analyzing a Pull Request, in addition to the Issue, the script automatically posts a **brief summary comment directly in the PR**:

```
🤖 AI Analysis Summary

A potential SQL injection was found in the authentication module.
Input data is not sanitized before being passed into the query.
Parameterized queries are recommended.

Severity: HIGH

📋 Full details: #42
```

---

## Quick Reference

| Label | Aliases | Role |
|-------|---------|------|
| `security` | `sec`, `audit` | Security Auditor (OWASP) |
| `review` | `refactor`, `code-review` | Code Reviewer (SOLID/DRY) |
| `qa` | `test`, `testing` | QA Engineer |
| `perf` | `performance`, `optimize` | Performance Expert |
| `deps` | `dependencies` | Dependency Auditor |
| `arch` | `architecture` | Software Architect |
| `pm` | `release`, `product` | Product Manager |
| _(none)_ | — | General Documentation |
