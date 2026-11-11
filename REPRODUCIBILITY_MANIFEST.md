# Reproducibility manifest

Version 2.0.0. Sources are actual repository artifacts, not a Controller draft. Paths below are repository-relative or release-relative. This manifest maps evidence; it is not an analytical proof.

| Repository source | Release artifact | Evidence role | Transfer | Original SHA-256 | Release SHA-256 |
|---|---|---|---|---|---|
| development_gen1/CORE_COUPLE_GEN1_exact_results_v1.json | gen1/expected/CORE_COUPLE_GEN1_exact_results_v1.json | Archived scientific expected output and, for GEN1, GEN2 regression input | byte-identical | e72e9ccdd5652ed16e2d991c63a73447baf374b99b38e5a332988816f6d73a0c | e72e9ccdd5652ed16e2d991c63a73447baf374b99b38e5a332988816f6d73a0c |
| development_gen2/CORE_COUPLE_GEN2_exact_results_v1.json | gen2/expected/CORE_COUPLE_GEN2_exact_results_v1.json | Archived scientific expected output and, for GEN1, GEN2 regression input | byte-identical | 9c0a732d9772b965dd6d09118b0fb6090d864951cb28740d8e33382732455388 | 9c0a732d9772b965dd6d09118b0fb6090d864951cb28740d8e33382732455388 |
| development_manuscript_v2/provenance/frozen_reproducibility/CORE_COUPLE_MDE3_exact_audit_results.json | input_snapshot/required_frozen_inputs_v1.zip!frozen_reproducibility/CORE_COUPLE_MDE3_exact_audit_results.json | Required binary regression input | member bytes identical; new subset container | f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4 | f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4 |
| development_manuscript_v2/provenance/frozen_reproducibility/CORE_COUPLE_cleanroom_checker_results.json | input_snapshot/required_frozen_inputs_v1.zip!frozen_reproducibility/CORE_COUPLE_cleanroom_checker_results.json | Required binary regression input | member bytes identical; new subset container | fca1ff6ed5057df26ac98e7752225a8f5a233f73ae9b676928a116b1982ddae8 | fca1ff6ed5057df26ac98e7752225a8f5a233f73ae9b676928a116b1982ddae8 |
| development_gen1/CORE_COUPLE_GEN1_exact_falsifier_v1.py | gen1/CORE_COUPLE_GEN1_exact_falsifier_v1.py | Exact scientific verifier; all non-main function ASTs unchanged | portable CLI/input-container plumbing only | 4260abc2b67979de5720b9de02f17c9e6816ac38da4ec4f67637de489087460a | 15cd0fe3ab2301b49f660b6c1e9d38b34b40236e1b3dad24d65bf8e40666dc22 |
| development_gen2/CORE_COUPLE_GEN2_exact_falsifier_v1.py | gen2/CORE_COUPLE_GEN2_exact_falsifier_v1.py | Exact scientific verifier; all non-main function ASTs unchanged | portable CLI/input-container plumbing only | e8f3130761063cb23583b8539310d0a9b2b3fb0261a27cc3e759f89492de6b41 | 3318bab74316b03a341f1495c80d48ec11c52becda40592e26e6cd55ffaf5446 |

## Input-container provenance

The subset ZIP contains only the two required frozen regression outputs, with original member bytes and names. Its checksum manifest verifies both members and the new subset container. The original GEN1 archive included 38 files, including legacy manuscript and release-housekeeping material; none of those unused contents is needed to compute the scientific checks. Those contents are excluded from this public release.

source_input_receipt_v1.json is extracted from the original GEN1 expected output's input_integrity object. It retains the original full-container digest and member digests as historical source provenance. It is not evidence that omitted members have been freshly checked. The legacy provenance field is retained in generated JSON for exact comparison; the current subset is verified separately. No numerical/scientific output field is ignored in comparison.

The GEN1 archived expected output is also the immutable GEN2 input; reading the newly generated GEN1 serialization instead could change GEN2's byte-digest provenance across platforms. Full parsed GEN1 equivalence is checked before GEN2 is run.

## Computational domains and expected results

GEN1 reproduces 11,016 exchange identities, 3,672 three-capacity cocycles, 108,000 equal-load sign checks and 3,640 independent three-grade recourse comparisons, plus the original binary regression and exact finite-menu construction. GEN2 reproduces 982,800 cross-load and 655,200 equal-load capacity pairs, 273,000 gain identities, 546,000 prefix checks, 2,912 independent subset comparisons, residual transitions, strict/rational cases and exact examples. Complete domains are recorded in the unchanged expected JSON; domains overlap and are not independent samples.

Verification compares every parsed JSON field, including all scientific values and counts. Byte hashes are separately reported. Intended counterexamples to rejected candidate rules are expected findings, not failures of proved conditions. The finite-menu choices are 3, 1, 2 at the three supplied compositions; the two strict cross-load local effects are -1 and +1. These are distinct constructive demonstrations.

## Exclusions

Manuscript PDFs/source, administrative declarations, reviewer correspondence, Controller/protocol/audit documents, old submission files, development hashes containing local paths, caches and build products are excluded. Analytical proofs remain in the named manuscript and supplement, not asserted to be recreated by these scripts. The historical independent cleanroom source is unavailable; its archived output is a regression reference, not a claim to rerun that source. Original integrity helpers snapshot entire local workspaces and are not required by the scientific calculations; verify_release.py replaces their release-integrity role without changing the numerical verifiers.

License sources: CORE_COUPLE_IJPE_Reproducibility_v1.0.0/LICENSE-CODE.txt and LICENSE-CONTENT.md. Author identity/ORCID: its CITATION.cff, consistent with the original title page. New release code uses only Python standard-library components. See LICENSE.md for inherited versus newly assigned release scope.

The release support files (wrapper, README, citation/metadata, licenses and subset manifests) are release infrastructure, not new science. SHA256SUMS.txt enumerates all files except itself; the outer ZIP digest is recorded in the accompanying verification report. See portability/PATCHES.md and focused diffs for all input/path modifications.

## Derived receipt and completed source-directory test

The source-input receipt is the input_integrity object extracted from development_gen1/CORE_COUPLE_GEN1_exact_results_v1.json. The source file SHA-256 is e72e9ccdd5652ed16e2d991c63a73447baf374b99b38e5a332988816f6d73a0c, and receipt SHA-256 is 061c2ec2745286420f6d3e1f4199eaf5cee2eb9adfaa3cad46f1734cb675e94a. This is a metadata extraction, not a copied full input container. The subset checksum file is new integrity metadata generated from the two unchanged source members.

The full source-directory release run passed: GEN1 and GEN2 each have JSON_SEMANTIC_EQUIVALENCE = PASS and BYTE_EQUALITY = PASS. This claim concerns those measured runs, not future cross-platform serialization. The fresh extraction is independently tested and recorded in the accompanying release report.

## GitHub major-version preparation

The original verified assembly had packaging version 1.0.0; this repository prepares v2.0.0 to distinguish its expanded GEN1+GEN2 scientific scope from the historical MDE3 v1.0.0 tag. Current citation/deposit/README/license-attribution version metadata are updated only. Scientific verifier scripts, archived expected outputs, required input snapshot and receipts are byte-identical to the verified assembly. The top-level wrapper additionally excludes only the Git object/ref database (.git/) from its release inventory and checks the current CFF version 2.0.0; scientific comparisons and computation are unchanged. The root .zenodo.json duplicates metadata/zenodo_metadata.json consistently; draft release notes are included in the checksum manifest. The Git-specific .gitattributes disables automatic text conversion so archived bytes and their checksums survive checkout on different platforms.
