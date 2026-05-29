# Coding Principles

These principles govern how code is written on the Vibe Coding platform. They apply to all applications regardless of archetype or tech stack. When using speckit, this file serves as input for `speckit.constitution`.

## I. No Secrets in Code

Never hardcode secrets, API keys, credentials, or sensitive configuration in source code. Secrets belong in environment variables, credential files (gitignored), or secret management systems — never in the repository. Service account keys, connection strings, and tokens must be excluded from version control via `.gitignore`. If a secret is accidentally committed, treat it as compromised and rotate it immediately.

## II. Reusable Code

Do not duplicate logic. Extract shared behavior into functions, utilities, or modules that can be reused across the application. Before writing new code, check if similar functionality already exists. Prefer composing small, focused functions over writing monolithic blocks. When a pattern appears three or more times, it must be abstracted.

## III. Simplicity First

Write the simplest code that solves the problem. Avoid premature abstraction, over-engineering, and speculative generality. Do not build for hypothetical future requirements — solve what is needed now. Prefer explicit code over clever code. A straightforward solution that is easy to read is better than an elegant one that requires explanation.

## IV. Fail Fast and Loud

Applications must detect errors early and report them clearly. Validate inputs at system boundaries. If required configuration is missing, crash at startup with a descriptive error — do not silently fall back to defaults that mask problems. Use meaningful error messages that help diagnose the issue. Never swallow exceptions silently.

## V. Clear Naming

Names must communicate intent. Variables, functions, classes, and files should be named so that their purpose is obvious without reading the implementation. Avoid abbreviations, single-letter variables (except loop counters), and generic names like `data`, `result`, or `handler` without context. Consistency matters — use the same term for the same concept throughout the codebase.

## VI. Small, Focused Units

Functions should do one thing. Modules should have a single responsibility. Keep files short enough to understand without scrolling extensively. When a function grows beyond a clear single purpose, split it. When a file accumulates unrelated concerns, refactor into separate modules. Prefer many small files over few large ones.

## VII. Defensive at Boundaries, Trusting Inside

Validate rigorously at system boundaries: user input, API request bodies, external service responses, environment variables. Once data has crossed the boundary and been validated, trust it internally — do not re-validate the same data at every layer. Use Pydantic models to enforce contracts at entry points.

## VIII. Minimal Dependencies

Only add dependencies that provide clear, significant value. Every dependency is a maintenance and security liability. Before adding a library, consider whether the functionality can be achieved with the standard library or a few lines of code. Pin dependency versions to avoid unexpected breakage.

## IX. Test-Driven Development

Test-driven development is a fundamental principle of software development. Write tests before writing code, and write tests that fail before writing code. Write tests that cover all code paths, including edge cases. Automate tests to run on every commit.