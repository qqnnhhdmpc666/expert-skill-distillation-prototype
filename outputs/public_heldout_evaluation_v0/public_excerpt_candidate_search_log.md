# Public Excerpt Candidate Search Log

- max_candidate_repos_to_screen: `12`
- accepted_candidate_count: `1`
- excluded_candidate_count: `11`

| repo | tier | accepted | reason | rejection |
|---|---|---|---|---|
| https://github.com/hindupuravinash/the-gan-zoo | `A` | `True` | Existing immutable public excerpt with pinned requests dependency and import/use site. |  |
| https://github.com/codelucas/newspaper | `C` | `False` | Python project with requests usage; screened as possible dependency-use excerpt. | No bounded immutable vulnerable dependency/advisory binding was established in this slice. |
| https://github.com/psf/requests | `rejected` | `False` | Canonical requests repository; useful as source but not an application dependency-use excerpt. | Library source is not a downstream pinned dependency-use triage task. |
| https://github.com/pallets/flask | `C` | `False` | Popular Python repo considered for public dependency triage. | No clean pinned vulnerable package/use/advisory tuple was confirmed. |
| https://github.com/kennethreitz/httpbin | `C` | `False` | Small Python web project considered for dependency-use evidence. | Advisory binding and deterministic expected decision not cleanly established. |
| https://github.com/getsentry/responses | `C` | `False` | Requests-adjacent Python project screened for import/dependency evidence. | Could not bind a frozen vulnerable dependency decision within bounded search. |
| https://github.com/requests-cache/requests-cache | `C` | `False` | Requests-based Python project screened as possible app-like excerpt. | No A-tier immutable dependency/advisory tuple established. |
| https://github.com/locustio/locust | `C` | `False` | Python project with network-client dependencies considered for public excerpt. | Too broad for minimal frozen excerpt without more manual curation. |
| https://github.com/ytdl-org/youtube-dl | `C` | `False` | Large Python project screened for pinned dependency and use-site evidence. | Not suitable as small deterministic v0 excerpt without additional curation. |
| https://github.com/ansible/ansible | `C` | `False` | Security-relevant Python project screened for dependency-use task potential. | Repository is too large for v0 minimal frozen excerpt. |
| https://github.com/mitmproxy/mitmproxy | `C` | `False` | Network/security Python project screened for dependency-use evidence. | Needs manual narrowing before it can become a clean held-out excerpt. |
| https://github.com/home-assistant/core | `C` | `False` | Large Python project screened as future held-out candidate. | Too large for bounded v0 intake; useful only for future curated benchmark work. |
