# v2.0.0 — GEN1+GEN2 Reproducibility Release

Draft release notes; publication is an author-controlled next step.

This major version supersedes v1.0.0 as the reproducibility package for **When Is Pooled Return-Quality Information Sufficient for Remanufacturing Capacity Choice?** The v1.0.0 tag and release remain archived for the former MDE3-era manuscript state.

The browsable package adds the final GEN1+GEN2 exact verification architecture: matched-information exchange and finite-menu checks, ordered recovery residual-capacity checks, immutable required inputs, archived expectations and release-wide integrity checks. The prepared version passes GEN1, GEN2 and full parsed JSON equivalence; actual byte equality is recorded in the migration verification report.

From the repository root, run:

```sh
python -B verify_release.py
```

The software provides exact falsification and implementation/reproducibility assurance. Analytical proofs are in the manuscript and supplement; the computations do not establish empirical prevalence or industrial validation. Python code remains MIT licensed; documentation and archived outputs remain CC BY 4.0.

No DOI for this version has been assigned in these metadata. Historical archive identifiers must not be reused as a version-2 identifier.
