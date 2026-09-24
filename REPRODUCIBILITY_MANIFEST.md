# Public reproducibility manifest

## Frozen scientific artifacts

| File | Purpose | SHA-256 | Status |
|---|---|---|---|
| `CORE_COUPLE_MDE3_exact_theorem_falsifier.py` | Exact finite-grid verifier | `2f13de6019df53335b620cf9d94d0fb9d8cded533b0ebd57664c4b24692521b8` | Frozen; byte-identical to the scientific-freeze artifact |
| `CORE_COUPLE_MDE3_exact_audit_results.json` | Exact-verifier reference output | `f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4` | Frozen; byte-identical to the scientific-freeze artifact |
| `CORE_COUPLE_cleanroom_checker_results.json` | Independent clean-room output | `fca1ff6ed5057df26ac98e7752225a8f5a233f73ae9b676928a116b1982ddae8` | Frozen output; source not deposited |
| `CORE_COUPLE_Reproducibility_Manifest_v1.md` | Frozen project provenance and verification record | `2879fd2de6125d894198d34d035802c1ff11fb0ae0532eb6ae46351b06263c3c` | Frozen; byte-identical to the scientific-freeze artifact |

## Recorded verification counts

The frozen manifest reports:

- exact recourse comparisons: 80,160; failures: 0;
- aligned capacity-scarce configurations: 6,318; failures: 0;
- aligned all-high-capable configurations: 59,616; failures: 0;
- aligned straddling configurations: 15,732; failures: 0;
- clean-room capacity-scarce configurations: 8,505; failures: 0;
- clean-room all-high-capable configurations: 27,630; failures: 0;
- clean-room straddling configurations: 15,255; failures: 0;
- clean-room equality/boundary configurations: 1,404; failures: 0;
- exact rational sensitivity-identity checks: 100; failures: 0.

## Re-execution check performed for this public package

The main exact verifier was rerun with Python 3.13.5 and SymPy 1.14.0. Its regenerated output was byte-identical to the frozen JSON and reproduced SHA-256:

`f841c6a6260573ea2f9ff27d8a907d2467e71ac1b6f7aca0878cf5e0f4120ba4`

## Interpretation

These computations provide falsification and implementation assurance for the analytical model. They are not empirical samples or estimates of real-world prevalence.

## Change rule

The four frozen project artifacts above must not be edited in place. Any modified implementation or output requires a new versioned filename and a new manifest entry.
