# Review requirements

- Flag unescaped model/data output in generated HTML and citation URLs that
  permit schemes other than HTTP(S).
- Flag changes that present mock output or a failed provider call as live,
  verified data. Offline CI does not verify live model access or accuracy.
- Source changes must use PRs. Automated reporting may publish Pages and write
  only report artifacts to site-content; it must not push source code to main.
- PR checks must not use provider keys or publishing permissions. Required
  failures, missing results and unexpected skipped jobs must block ci-required.
- Workflow, check-policy and CODEOWNERS changes require the configuration owner.
  Do not recommend suppressing failures merely to make the current PR pass.

Report consequential correctness, security and maintainability issues. Leave
mechanical lint and test checks to CI. Include the affected behavior and evidence.
