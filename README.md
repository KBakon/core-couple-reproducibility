# CORE-COUPLE reproducibility release

Supporting **When Is Pooled Return-Quality Information Sufficient for Remanufacturing Capacity Choice?** Version 2.0.0.

This package reproduces exact computational checks for matched pooled-information exchanges, finite capacity-menu comparisons and ordered recovery residual-capacity mechanisms. Analytical proofs are in the manuscript and supplement. The computations provide falsification and implementation assurance; they do not establish empirical prevalence or industrial validation.

## Quick start

Extract the complete archive. From its root, with Python 3.10 or newer:

```sh
python -B verify_release.py
```

A fast integrity-only check is available separately:

```sh
python -B verify_release.py --checksums-only
```

No third-party packages or internet connection are required. The default command first checks every manifest file and required snapshot member, then runs both scientific verifiers from a fresh temporary working directory and compares every parsed output field to the immutable archived expectations. Temporary generated outputs are removed after comparison. The release tree is not changed. A writable system temporary directory is required; `--work-dir` can select another existing writable scratch directory. An optional `--report` path must be outside the release directory and have an existing parent.

For individual generation (an existing output directory is required):

```sh
python -B gen1/CORE_COUPLE_GEN1_exact_falsifier_v1.py --output ../results_gen1.json
python -B gen2/CORE_COUPLE_GEN2_exact_falsifier_v1.py --output ../results_gen2.json
```

Individual commands create files and therefore change the release inventory. Save outputs outside the extracted release tree when retaining checksum verification. Use the top-level command for an automatically isolated run.

## Contents

- gen1/: exact exchange/recourse/finite-menu verifier and unchanged expected output.
- gen2/: exact residual-capacity verifier and unchanged expected output.
- input_snapshot/: immutable two-member regression ZIP, subset checksums and original-container provenance receipt.
- portability/: focused path/input-plumbing diffs and their explanation.
- metadata/: software-deposit metadata; no repository identifier assigned.
- CITATION.cff, licenses, manifest and checksums: citation, rights and integrity information.

## Interpreting verification

PASS means the bounded tests execute successfully and the complete generated scientific JSON is semantically identical to the archived result. JSON_SEMANTIC_EQUIVALENCE and BYTE_EQUALITY are separate: line endings, whitespace or serialization can differ across systems even when every parsed field agrees. Any parsed field mismatch is a failure; no numerical field is excluded. Checksums alone do not execute science and are labeled as such.

The verifiers perform complete declared small domains, including intentional counterexamples to rejected sign/converse rules. Their nonempty counterexample lists are scientific evidence, not failed verification. Exact integers, Fraction and finite polynomials are used; there is no Monte Carlo. The complete release test took 67.034 seconds for GEN1 and 35.720 seconds for GEN2 on the tested Windows/Python environment. These measured times are hardware/runtime dependent, not performance guarantees; allow several minutes on other systems. The external verification report records the test environment and timings.

## Reproducibility boundaries

All computational functions are unchanged from the source verifiers. Portability changes are limited to CLI/path resolution, input-container bookkeeping and output placement. The regression input snapshot omits unused legacy manuscript/housekeeping contents from the original full archive. The original input_integrity field is retained as archived historical provenance; fresh runs verify the current subset separately. See REPRODUCIBILITY_MANIFEST.md and portability/PATCHES.md for details.

The historical standalone cleanroom verifier source is unavailable. Its archived JSON is a reference, and its checks are not advertised as independently rerun here. The analytical assumptions are finite regimes/menus, conditional multinomial composition for the exchange, and ordered positive values/integer loads for the residual mechanism. Finite checks do not extend theorem domains. The equal-load finite-menu decision construction and strict cross-load local examples retain their distinct roles.

## Citation and license

Use CITATION.cff and cite the repository record once published: **DOI assigned upon repository publication**. No DOI, repository URL, publication date or journal identifier is claimed for this release.

Python code is MIT licensed. Documentation, metadata and archived outputs are CC BY 4.0; preserve attribution and indicate changes. See LICENSE.md, LICENSE-CODE.txt and LICENSE-CONTENT.md. Author and ORCID are drawn from existing project citation metadata. No author email is included.

## Version history

The current package is v2.0.0 and supports the manuscript named above with GEN1+GEN2 exact verification. The v1.0.0 tag and release remain unchanged for the earlier MDE3-era manuscript state. Historical files are retrievable from that tag; the current root contains the current evidence package. Repository metadata carry no DOI for v2.0.0 before archival publication.
