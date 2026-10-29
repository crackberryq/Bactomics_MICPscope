import argparse
import csv
import hashlib
import html
import io
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import Bio
from . import __version__
from .analysis import characterize, read_fasta

LIMITS = ("Sequence descriptors do not establish temperature or pH optima, shelf life, "
          "mineralization activity, material performance, or deployment safety. "
          "Protein completeness and MICP relevance are unassessed. "
          "Evidence entries are user-supplied and are not independently verified.")
EVIDENCE_FIELDS = ["sample_id", "subject_id", "evidence_type", "property", "value", "unit", "source", "notes"]


def read_evidence(path, sample):
    if path is None:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EVIDENCE_FIELDS:
            raise ValueError("Evidence CSV columns must be: " + ",".join(EVIDENCE_FIELDS))
        rows = list(reader)
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Malformed evidence row {number}")
        if row["sample_id"] != sample:
            raise ValueError(f"Evidence row {number} belongs to a different sample")
        if row["evidence_type"] not in {"measured", "predicted", "literature-derived", "calculated"}:
            raise ValueError(f"Invalid evidence type at row {number}")
        if any(not row[key].strip() for key in ("subject_id", "property", "value", "source")):
            raise ValueError(f"Missing subject, property, value or source at row {number}")
    return rows


def table(rows, columns):
    esc = lambda value: html.escape(str(value), quote=True)
    return "<div class='scroll'><table><thead><tr>" + "".join(
        f"<th>{esc(c.replace('_', ' '))}</th>" for c in columns
    ) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f"<td>{esc(row.get(c, '—'))}</td>" for c in columns) + "</tr>"
        for row in rows
    ) + "</tbody></table></div>"


def render(result):
    sample = html.escape(result["sample_id"])
    proteins = result["proteins"]
    count = sum(p["status"] == "calculated" for p in proteins)
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MICP Scope · {sample}</title><style>
:root{{font-family:system-ui,sans-serif;color:#173443;background:#eef3f5}}
body{{max-width:1250px;margin:auto;padding:32px}}header{{background:#123c49;color:white;padding:32px;border-radius:16px}}
h1{{font-size:36px;margin:8px 0}}h2{{margin-top:30px}}.label{{letter-spacing:3px;color:#88e3ca}}
.card{{background:white;border:1px solid #ccdce2;border-radius:12px;padding:20px;margin-top:18px}}
.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid #dbe5e9;vertical-align:top}}
th{{background:#e4f1ee}}.muted{{color:#526974}}a{{color:#066e70}}@media print{{body{{padding:0}}.scroll{{overflow:visible}}}}
</style><header><div class="label">BACTOMICS / MICP Scope</div><h1>{sample}</h1>
<p>Protein characterization & application evidence · {__version__}</p></header>
<section class="card"><b>{len(proteins)} proteins</b> · {count} calculated · {len(proteins)-count} flagged
<p>{LIMITS}</p><b>Operating conditions: undetermined</b></section>
<h2>Protein properties</h2>{table(proteins, ['protein_id','length','status','aliphatic_index','theoretical_pi','gravy','instability_index','molecular_weight_da','notes'])}
<h2>Application evidence</h2><div class="card">{table(result['evidence'], EVIDENCE_FIELDS) if result['evidence'] else 'No experimental or literature evidence supplied.'}</div>
<h2>Interpretation</h2><div class="card"><p>Aliphatic index describes amino-acid composition; theoretical pI estimates the charge-neutral point. Neither is an activity optimum. GRAVY is mean hydropathy. Instability index is a sequence heuristic, not measured storage stability.</p>
<p>Compare descriptors only with appropriate protein-family and sequence-completeness context. Whole-cell behavior, enzyme activity, and material performance require distinct evidence.</p></div>
<h2>Methods & provenance</h2><div class="card"><p>Biopython {Bio.__version__} ProteinAnalysis: average molecular mass, theoretical pI, Kyte–Doolittle GRAVY, instability index and aromaticity. Aliphatic index = 100 × [A + 2.9V + 3.9(I + L)] / sequence length, using residue counts.</p>
<p>Uppercase normalization; whitespace removed; one terminal stop removed. Unsupported residues are flagged, never silently substituted. No gene annotation or pathway detection is performed.</p>
<p><a href="https://web.expasy.org/protparam/protparam-doc.html">ExPASy methods</a> · <a href="https://biopython.org/docs/1.86/api/Bio.SeqUtils.ProtParam.html">Biopython reference</a></p>
<p class="muted">Input SHA-256: {result['provenance']['input_sha256']}<br>Generated: {result['provenance']['created_utc']}</p></div></html>"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="MICP Scope protein characterization and evidence report")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--proteins", type=Path, required=True, help="Annotated protein FASTA (.faa), not genome DNA")
    parser.add_argument("--data-only", action="store_true", help="Write analysis data for the Snakemake report stage")
    parser.add_argument("--sample", required=True)
    parser.add_argument("--evidence", type=Path, help="Optional evidence CSV")
    parser.add_argument("--out", type=Path, required=True, help="New output directory; existing paths are never overwritten")
    args = parser.parse_args(argv)
    try:
        raw = args.proteins.read_bytes()
        proteins = [characterize(*record) for record in read_fasta(raw.decode("utf-8-sig"))]
        evidence = read_evidence(args.evidence, args.sample)
        result = dict(schema_version="1.0", software_version=__version__, sample_id=args.sample,
                      proteins=proteins, evidence=evidence, operating_conditions="undetermined",
                      limitations=LIMITS, provenance=dict(
                          input_sha256=hashlib.sha256(raw).hexdigest(),
                          evidence_sha256=hashlib.sha256(args.evidence.read_bytes()).hexdigest() if args.evidence else None,
                          created_utc=datetime.now(timezone.utc).isoformat(),
                          python_version=platform.python_version(), biopython_version=Bio.__version__))
        report = None if args.data_only else render(result)
        columns = ["protein_id", "description", "length", "status", "aliphatic_index", "theoretical_pi", "gravy", "instability_index", "molecular_weight_da", "aromaticity", "sequence_sha256", "evidence_type", "completeness", "notes"]
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore", delimiter="\t")
        writer.writeheader()
        # Prevent spreadsheet formula interpretation in exported text fields.
        writer.writerows({key: ("'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value)
                         for key, value in row.items()} for row in proteins)
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        (args.out / "proteins.tsv").write_text(buffer.getvalue(), encoding="utf-8")
        if report is not None:
            (args.out / "report.html").write_text(report, encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.exit(2, f"MICP Scope: {error}\n")
    print(f"Outputs: {args.out}")


if __name__ == "__main__":
    main()
