# CORE-COUPLE IJPE reproducibility artifacts

This repository contains the computational verification artifacts supporting the manuscript:

**Decision Validity of Stable Return Composition in Remanufacturing Capacity Expansion: Capacity-Regime Boundaries under Volume-Conditioned Core Quality**

The package is intentionally small. It is not the manuscript source tree or the full research-development archive. It contains only the frozen computational artifacts and the documentation needed to inspect and rerun the main exact verifier.

## Contents

- `CORE_COUPLE_MDE3_exact_theorem_falsifier.py` — frozen exact finite-grid verifier.
- `CORE_COUPLE_MDE3_exact_audit_results.json` — frozen byte-level reference output of the exact verifier.
- `CORE_COUPLE_cleanroom_checker_results.json` — frozen output of the independent clean-room verification.
- `CORE_COUPLE_Reproducibility_Manifest_v1.md` — frozen project manifest containing the recorded hashes, environment, verification counts, and locked diagnostic values.
- `REPRODUCIBILITY_MANIFEST.md` — public-facing inventory and integrity record.
- `CLEANROOM_VERIFIER_STATUS.md` — scope note for the archived clean-room output.
- `requirements.txt` — Python dependency specification for the exact verifier.
- `CITATION.cff` — citation metadata. No DOI is embedded by design.
- `SHA256SUMS.txt` — checksums for the deposited files.
- `PUBLIC_RELEASE_CHECKLIST.md` — the two repository-release actions that remain outside the scientific package.

## Scientific interpretation

The computations provide exact finite-grid falsification and implementation assurance for the analytical results stated in the manuscript. They are not empirical observations, statistical samples, prevalence estimates, or a substitute for the analytical proofs.

## Frozen execution environment

The project manifest records:

- Python 3.13.5
- SymPy 1.14.0
- Linux x86_64
- glibc 2.41

The main verifier was re-executed during public-package preparation with Python 3.13.5 and SymPy 1.14.0. The regenerated JSON was byte-identical to the archived frozen output, with SHA-256:

`f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4`

## Re-running the exact verifier

The frozen script writes its output to the fixed path:

`/mnt/data/CORE_COUPLE_MDE3_exact_audit_results.json`

Run a copy in a separate writable environment so that the archived frozen output is not overwritten. One reproducible Docker workflow is:

```bash
mkdir -p run-output
docker run --rm \
  -v "$PWD":/src:ro \
  -v "$PWD/run-output":/mnt/data \
  -w /mnt/data python:3.13-slim \
  sh -lc "python -m pip install --no-cache-dir sympy==1.14.0 && cp /src/CORE_COUPLE_MDE3_exact_theorem_falsifier.py . && python CORE_COUPLE_MDE3_exact_theorem_falsifier.py"
sha256sum run-output/CORE_COUPLE_MDE3_exact_audit_results.json
```

The expected digest is:

`f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4`

## Clean-room verification

The independent clean-room output is preserved and hash-verified. Its standalone verifier source was not part of the frozen releasable artifact set available for this deposit. The package therefore does not claim that the clean-room check can be rerun from these files. See `CLEANROOM_VERIFIER_STATUS.md`.

## Integrity rule

Do not edit the four frozen project artifacts in place:

- `CORE_COUPLE_MDE3_exact_theorem_falsifier.py`
- `CORE_COUPLE_MDE3_exact_audit_results.json`
- `CORE_COUPLE_cleanroom_checker_results.json`
- `CORE_COUPLE_Reproducibility_Manifest_v1.md`

Any changed computational artifact must receive a new versioned filename and a new manifest entry.

## DOI policy

No DOI is written into this package before public release. The first public GitHub release may be archived by Zenodo, which will assign the archival DOI. That DOI can then be cited in the manuscript and repository metadata without creating a DOI/release update loop.

## License

This is a mixed research-software package:

- `CORE_COUPLE_MDE3_exact_theorem_falsifier.py` is licensed under the **MIT License**.
- Documentation, metadata, manifests, checksum files, and archived JSON outputs are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)** unless otherwise stated.

See `LICENSE.md`, `LICENSE-CODE.txt`, and `LICENSE-CONTENT.md` for scope and terms.
