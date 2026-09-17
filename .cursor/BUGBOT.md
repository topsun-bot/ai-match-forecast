# PR review requirements

- Model text and external data must be escaped in HTML; source links accept
  only HTTP(S), never executable URL schemes.
- Mock reports and failed provider calls must not be labeled verified live data.
- Source changes enter main through PRs. Automatic reports write only to the
  site-content archive and Pages, not to source main.
- PR checks receive no provider or publishing secrets. Required failures,
  missing evidence and unexpected skipped jobs must fail ci-required.
- Check workflows, gate policy and CODEOWNERS need configuration-owner review;
  weakening a check to pass the current PR is not a valid repair.

Prioritize meaningful defects with evidence. CI handles mechanical checks.
