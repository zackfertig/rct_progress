Contributing to rct_progress
===========================

Thank you for your interest in contributing to rct_progress. This file explains
how to report issues, propose changes, and run tests locally.

Please follow these small, clear steps to make contributions smooth:

1. Report a bug or request a feature
   - Open an issue with a clear title and description.
   - Include steps to reproduce, expected vs actual behavior, and minimal
     test data when possible (for example, small sample bytes or offsets).

2. Fork and branch
   - Fork the repository and create a topic branch using a short, descriptive
     name, e.g. `fix/rle-decode-boundary` or `feat/add-ci`.

3. Code style
   - Keep changes small and focused.
   - Use the existing `src/` layout and keep logic in `src/rct_progress`.
   - Use type hints for public functions where helpful.
   - Add or update unit tests for any bug fixes or new features.

4. Commit messages
   - Write meaningful, short commit messages. Prefer the Conventional Commits
     style for easier changelog generation, e.g. `fix(core): handle short buffer`.

5. Pull request
   - Open a PR against the `main` branch.
   - Describe what you changed and why, reference related issues.
   - CI (tests/lint) will run on the PR; please address any failures.

6. Review
   - Be responsive to review comments. Keep iterative changes small.

Maintainers
-----------
The project is maintained by the repository owner. If you need publish access
or help with releases, create an issue and mention the owner/maintainers.

Code of Conduct
---------------
Please follow common open source community standards: be respectful, helpful
and constructive. If you'd like, we can add a formal `CODE_OF_CONDUCT.md`.

License
-------
By contributing, you agree that your contributions will be licensed under the
project's MIT license.
