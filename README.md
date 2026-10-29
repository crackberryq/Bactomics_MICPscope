# Bactomics MICP Scope

**0.1.0a2 — initial alpha.** Protein characterization and traceable application evidence for MICP research, designed for future integration with HybAs, BaSIS and Bactologix.

## Available now

- Protein FASTA input, explicit validation and per-record ambiguity flags.
- Aliphatic index, theoretical pI, GRAVY, instability index, molecular weight, aromaticity and amino-acid counts.
- Optional sample-linked evidence CSV import with source attribution.
- Self-contained HTML report, machine-readable JSON and spreadsheet-readable protein TSV.
- Input checksums, software versions and UTC timestamps.
- Existing output directories are never overwritten.

## Run through Bactologix

Select MICP Scope in **Install & update**, install the recommended source and runner, then prepare its protein-properties environment. Register a sample folder containing `annotation/<sample_id>.faa`; optionally include `annotation/<sample_id>.evidence.csv`. Create a MICP Scope draft, validate, prepare missing environments and run. Reports appear under Results & downloads.

## Snakemake structure

- `MICPscope.smk`: native DAG, separate properties and report rules.
- `environment.yml`: Python 3.11 / Snakemake 9.6.2 runner.
- `envs/properties.yml`: rule-local Python / Biopython environment and post-deploy check.
- `config.yaml` and `examples/samples.tsv`: configuration and batch inputs.
- `scripts/`: workflow entry points; `src/micpscope/`: reusable analysis code.
- Outputs: `<output_dir>/<sample_id>/micpscope/`, including JSON, TSV, HTML, logs and benchmarks.

For standalone development, create the Conda runner from `environment.yml`, then use:

```bash
snakemake --snakefile MICPscope.smk --cores 1 --use-conda --dry-run
snakemake --snakefile MICPscope.smk --cores 1 --use-conda --conda-create-envs-only
snakemake --snakefile MICPscope.smk --cores 1 --use-conda
```

The default configuration runs synthetic fixtures only. Sample-sheet paths resolve relative to the workflow working directory; absolute paths are recommended. Supply annotated protein FASTA, not genome DNA. The previous `micpscope` Python CLI remains available for developer use. Snakemake manages resumability and reruns; the standalone CLI still refuses existing output directories.

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
4. Expand application-specific evidence views.

These are planned features, not implemented capabilities. This alpha does not identify pathways, rank strains, infer formulation conditions, design genetic changes or certify deployment.

## Methods and development

Biopython 1.86 `ProteinAnalysis` provides standard descriptors. Aliphatic index uses `100 × [A + 2.9V + 3.9(I + L)] / length` with residue counts.

- [ExPASy ProtParam methodology](https://web.expasy.org/protparam/protparam-doc.html)
- [Biopython 1.86 API](https://biopython.org/docs/1.86/api/Bio.SeqUtils.ProtParam.html)

```bash
python -m unittest discover -s tests -v
```

No license has yet been selected by the repository owner.
