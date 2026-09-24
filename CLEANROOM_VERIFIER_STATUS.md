# Clean-room verifier status

`CORE_COUPLE_cleanroom_checker_results.json` is the frozen output of the independent clean-room verification and is preserved byte-for-byte.

Recorded SHA-256:

`fca1ff6ed5057df26ac98e7752225a8f5a233f73ae9b676928a116b1982ddae8`

A standalone clean-room verifier source was not part of the frozen releasable artifact set available for this public package. Therefore:

- the archived clean-room output can be inspected and integrity-checked;
- the package does not claim that this independent check can be rerun from the deposited files;
- no replacement implementation has been reconstructed from the output.

The main exact verifier is independently rerunnable from this package and reproduces its frozen output byte-for-byte in the recorded Python/SymPy environment.
