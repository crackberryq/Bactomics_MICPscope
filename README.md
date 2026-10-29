# Bactomics MICPscope

**0.1.0a1 — initial alpha.** Protein characterization and traceable application evidence for MICP research, designed for future integration with HybAs, BaSIS and Bactologix.

## Available now

- Protein FASTA input, explicit validation and per-record ambiguity flags.
- Aliphatic index, theoretical pI, GRAVY, instability index, molecular weight, aromaticity and amino-acid counts.
- Optional sample-linked evidence CSV import with source attribution.
- Self-contained HTML report, machine-readable JSON and spreadsheet-readable protein TSV.
- Input checksums, software versions and UTC timestamps.
- Existing output directories are never overwritten.

## Install and try

Python 3.10 or newer is required. From Ubuntu/WSL:

```bash
mkdir -p ~/bactomics
cd ~/bactomics
git clone https://github.com/crackberryq/Bactomics_MICPscope.git
cd Bactomics_MICPscope
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
micpscope --proteins examples/demo.faa --sample demo --out results/demo
```

Open `results/demo/report.html` in a browser. The demo contains synthetic composition fixtures, not MICP proteins. On WSL, `explorer.exe "$(wslpath -w results/demo)"` opens the results directory.

For your own annotated **protein** FASTA (`.faa`), replace the input and sample name and choose a new output directory. Genome DNA must first be annotated externally; sequence alphabet alone cannot reliably distinguish DNA from proteins.

## Evidence

Copy `examples/evidence_template.csv` and retain its column order. Add one observation per row. `sample_id` must match `--sample`. `subject_id` identifies the protein, preparation, formulation or material tested. Allowed evidence types: `measured`, `predicted`, `literature-derived`, `calculated`. Property, value, source and subject are required; use a unit where applicable and notes for measurement context. Supply the file with `--evidence your_evidence.csv`.

Entries are displayed as supplied, not independently verified or converted into recommended conditions. No numeric response models are fitted in this release.

## Interpretation limits

Aliphatic index is not an optimum temperature. Theoretical pI is not an optimum pH. Instability index is not shelf life. Sequence properties do not demonstrate mineralization, material compatibility or safe deployment. Completeness and biological function remain unassessed; headers are retained but not treated as functional evidence. Operating conditions remain undetermined.

One terminal stop is removed and documented; sequences with other unsupported residues are retained as flagged records without property calculations. Duplicate IDs, empty records and malformed FASTA fail validation. Original sequence hashes and input-file hashes provide traceability. TSV text fields beginning with formula characters are prefixed with an apostrophe for spreadsheet safety; JSON preserves original text.

## Planned stages

1. Curated, versioned functional evidence catalogue and validated annotation import.
2. HybAs/BaSIS result adapters with explicit schema compatibility checks.
3. Measured material-performance and formulation comparison, with uncertainty and units.
4. Bactologix interface and batch workflow integration.

These are planned features, not implemented capabilities. This alpha does not identify pathways, rank strains, infer formulation conditions, design genetic changes or certify deployment.

## Methods and development

Biopython 1.86 `ProteinAnalysis` provides standard descriptors. Aliphatic index uses `100 × [A + 2.9V + 3.9(I + L)] / length` with residue counts.

- [ExPASy ProtParam methodology](https://web.expasy.org/protparam/protparam-doc.html)
- [Biopython 1.86 API](https://biopython.org/docs/1.86/api/Bio.SeqUtils.ProtParam.html)

```bash
python -m unittest discover -s tests -v
```

No license has yet been selected by the repository owner.
