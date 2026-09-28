# Library Classification Evolution

Three sequential classification prompt iterations for CSE 4392/5320.

Status: preparation in progress; no classification runs have been submitted yet.

Generation inputs are in `inputs/generation/`. The expert workbook is isolated in `inputs/evaluation_only/` and must never be uploaded to a generating model. Its contents have not been inspected during setup. Originals were preserved.

The project mirror contained no synced source files, so matching files were recovered from the Desktop. `SOURCE_MANIFEST.json` records paths and SHA-256 hashes.

The cached source chat contained only the latest five turns. A saved identification response was recovered from `output_classification_lib.docx`; only its `<answer>` block is used as the candidate phrase inventory. Confirmation of its identity with the original chat inventory is pending. Its analysis is not a generation input.

Each completed run will contain the exact prompt, raw model output, run metadata, and a post-generation evaluation. C2 will be authored only after C1 is evaluated; C3 only after C2 is evaluated. Fresh model conversations will isolate runs from evaluation and previous answers.
