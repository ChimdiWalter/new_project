# Scientific Decision Intelligence — InvariantCell

Decision intelligence between biological predictions and laboratory measurements. This is the shared implementation and founder demonstration for the InvariantCell program.

Part of the shared [InvariantCell program](https://github.com/ChimdiWalter/new_project). [MIT License](LICENSE).
## Mike Knoop technical discussion

The pitch/demo materials are prepared for a technical conversation with **Mike Knoop**. The proposed product is a decision layer between biological models and the laboratory: which prediction should be tested, and which measurement should happen next?

See [pitch and ask](docs/mike_knoop_pitch.md) and open [the evidence demo](demo/index.html). This names the intended audience; no endorsement, partnership, investment or contact is asserted.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
PYTHONPATH=src python -B -m unittest discover -s tests -v
PYTHONPATH=src python -B examples/check_replay.py
```

Python >=3.11. The submitted development environment uses Python3.12; pinned optional dependencies may impose a stricter interpreter requirement. Tests use explicit synthetic fixtures and are engineering checks, not biological validation.

## Current evidence

Read [the timestamped evidence snapshot](evidence/current_summary.json). Arc's official score was pending at this snapshot. Temporal rules and the verified reasoner tie138/138 on the consumed final documentary benchmark; the verifier adds replay/provenance and specific tamper rejection. Earlier verified-policy ranking experiments showed no incremental gain. Real next-measurement benefit, learned procedure transfer and an independent molecular endpoint comparison remain unproven.

The new pathology measurement panel has five patients/five fields, macro localizationF1 .35054 and Dice .45366. It is a small retrospective measurement study, not clinical validation.

## Source and reproducibility

See [release scope](RELEASE_SCOPE.md), [notices](NOTICE.md), [validation receipt](VALIDATION.json) and release_manifest.json. Shared code hashes match across the four focused repositories. Large/private assets and live credentials are excluded.

## Repositories

- [Startup and Mike Knoop proof](https://github.com/ChimdiWalter/new_project)
- [ConformaCell](https://github.com/ChimdiWalter/conformacell)
- [Arc challenge](https://github.com/ChimdiWalter/arc_challenge)
- [NIH temporal reasoning](https://github.com/ChimdiWalter/nih_challenge)
