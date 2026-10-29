"""MICPscope: protein descriptors followed by evidence reporting."""
import csv
from pathlib import Path
import re

configfile: "config.yaml"

ROOT = Path(workflow.basedir)
SHEET = Path(config["samples"]).resolve()
OUT = str(Path(config["output_dir"]).resolve())
MEMORY = config.get("memory_mb", 2048)
if isinstance(MEMORY, bool) or not isinstance(MEMORY, int) or MEMORY < 512:
    raise ValueError("memory_mb must be an integer of at least 512")
SAMPLES = {}
with SHEET.open(newline="", encoding="utf-8-sig") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    if reader.fieldnames != ["sample_id", "proteins", "evidence"]:
        raise ValueError("Sample sheet columns must be sample_id, proteins, evidence")
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed sample sheet row")
        sid = row["sample_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", sid):
            raise ValueError("Invalid sample ID: " + sid)
        if sid.casefold() in {s.casefold() for s in SAMPLES}:
            raise ValueError("Duplicate sample ID: " + sid)
        if not row["proteins"].strip():
            raise ValueError("Protein FASTA is required: " + sid)
        SAMPLES[sid] = row
if not SAMPLES:
    raise ValueError("Sample sheet contains no samples")

rule all:
    input:
        expand(OUT + "/{sample}/micpscope/report.html", sample=SAMPLES)

rule protein_properties:
    input:
        proteins=lambda w: SAMPLES[w.sample]["proteins"],
        evidence=lambda w: [SAMPLES[w.sample]["evidence"]] if SAMPLES[w.sample]["evidence"] else [],
        sheet=str(SHEET),
        code=[str(ROOT / "src/micpscope" / name) for name in ["analysis.py", "cli.py", "__init__.py"]]
    output:
        data=OUT + "/{sample}/micpscope/results.json",
        table=OUT + "/{sample}/micpscope/proteins.tsv"
    log:
        OUT + "/{sample}/micpscope/logs/properties.log"
    benchmark:
        OUT + "/{sample}/micpscope/benchmarks/properties.tsv"
    threads: 1
    resources:
        mem_mb=MEMORY
    conda: "envs/properties.yml"
    params:
        script=str(ROOT / "scripts/properties.py"), root=str(ROOT)
    shell:
        "python {params.script:q} {params.root:q} {wildcards.sample:q} {input.proteins:q} {output.data:q} {output.table:q} {input.evidence:q} > {log:q} 2>&1"

rule report:
    input:
        data=rules.protein_properties.output.data,
        table=rules.protein_properties.output.table,
        code=str(ROOT / "src/micpscope/cli.py")
    output:
        OUT + "/{sample}/micpscope/report.html"
    log:
        OUT + "/{sample}/micpscope/logs/report.log"
    benchmark:
        OUT + "/{sample}/micpscope/benchmarks/report.tsv"
    threads: 1
    resources:
        mem_mb=MEMORY
    conda: "envs/properties.yml"
    params:
        script=str(ROOT / "scripts/report.py"), root=str(ROOT)
    shell:
        "python {params.script:q} {params.root:q} {input.data:q} {output:q} > {log:q} 2>&1"
