# CORE-COUPLE - Reproducibility Manifest v1

## Status

**REPRODUCIBILITY LOCK: PASS**

## Authoritative core verifier

File: CORE_COUPLE_MDE3_exact_theorem_falsifier.py
SHA-256: 2f13de6019df53335b620cf9d94d0fb9d8cded533b0ebd57664c4b24692521b8

Authoritative output:

File: CORE_COUPLE_MDE3_exact_audit_results.json
SHA-256: f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4

## Clean-room audit output

File: CORE_COUPLE_cleanroom_checker_results.json
SHA-256: fca1ff6ed5057df26ac98e7752225a8f5a233f73ae9b676928a116b1982ddae8

## Execution environment used for freeze audit

Python: 3.13.5
SymPy: 1.14.0
Platform: Linux x86_64, glibc 2.41

## Authoritative numerical counts

Original MDE-3 verifier:

- recourse formula comparisons: 80,160, failures: 0;
- Result A configurations: 6,318, failures: 0;
- Result B configurations: 59,616, failures: 0;
- straddling configurations: 15,732, failures: 0.

Clean-room checker:

- Result A configurations: 8,505, failures: 0;
- Result B configurations: 27,630, failures: 0;
- straddling configurations: 15,255, failures: 0;
- sensitivity identity exact rational checks: 100, failures: 0;
- explicit equality/boundary checks: 1,404, failures: 0.

## Locked exact nonmonotone diagnostic

Delta(eta) = -(1296 eta^4 - 1120 eta^3 - 50568 eta^2 + 24696 eta - 98441) / 76832

Delta'(eta) = -3(216 eta^3 - 140 eta^2 - 4214 eta + 1029) / 9604

Endpoints on eta in [-7/8,7/8]:

- Delta(-7/8) = 16767/8192;
- Delta(0) = 41/32;
- Delta(7/8) = 12319/8192.

Interior minimum:

- eta approximately 0.24296006008558177;
- Delta approximately 1.2421570914985993.

For F=1.26:

- first decision root approximately 0.07886777800562036;
- second decision root approximately 0.4071262386134061.

## Reproduction rule

Do not edit the authoritative verifier or output in place after freeze.

Any changed verifier must receive a new filename/version and a new manifest entry.
