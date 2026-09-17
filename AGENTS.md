# Repository guidance

This repository contains a Python report generator in code/ and published HTML
archives. Python 3.11 is the minimum runtime. Use offline tests for routine PRs:

    python3 -m unittest discover -s tests -v
    python3 -m pip install -r requirements-dev.txt
    python3 -m ruff check code scripts tests

Do not use live API keys or publish reports while testing a PR. Use explicit
mock flags and temporary output directories. A successful mock report validates
the software path, not live data, model access, or prediction accuracy.

## Code Review Rules

### Output trust
- Treat model text, external data and citation URLs as untrusted. Escape text
  in HTML and restrict clickable source links to HTTP(S). Flag changes that
  allow generated content to become executable markup.
- Do not describe mock results as verified live observations. A successful
  test or generated report does not prove a real provider call succeeded.

### Publishing and checks
- Code changes enter main through PRs. Scheduled reporting may update the
  site-content archive and publish Pages, but must not push source changes to main.
- PR jobs must not receive provider keys or publishing credentials. Required
  job failures, missing results and unexpected skips must fail ci-required.
- Changes to workflows, check policy or CODEOWNERS require a configuration
  owner's approval. Do not weaken a check merely to make a PR green.
