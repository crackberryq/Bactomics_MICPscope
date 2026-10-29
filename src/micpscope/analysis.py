"""Descriptive sequence properties; no activity or formulation predictions."""
from Bio.SeqUtils.ProtParam import ProteinAnalysis
import hashlib

STANDARD = set("ACDEFGHIKLMNPQRSTVWY")


def read_fasta(text):
    records, identifier, description, parts, seen = [], None, None, [], set()

    def finish():
        if identifier is not None:
            sequence = "".join(parts).upper()
            if not sequence:
                raise ValueError(f"Empty sequence: {identifier}")
            records.append((identifier, description, sequence))

    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            finish()
            description = line[1:].strip()
            if not description:
                raise ValueError(f"Missing FASTA identifier at line {number}")
            identifier = description.split()[0]
            if identifier in seen:
                raise ValueError(f"Duplicate FASTA identifier: {identifier}")
            seen.add(identifier)
            parts = []
        else:
            if identifier is None:
                raise ValueError("Expected a protein FASTA header before sequence")
            parts.append("".join(line.split()))
    finish()
    if not records:
        raise ValueError("No protein records found")
    return records


def characterize(identifier, description, raw_sequence):
    sequence = raw_sequence.removesuffix("*")
    row = dict(protein_id=identifier, description=description, length=len(sequence),
               sequence_sha256=hashlib.sha256(sequence.encode()).hexdigest(),
               sequence_md5=hashlib.md5(sequence.encode()).hexdigest(),
               quality_flags=[],
               evidence_type="calculated", completeness="unassessed",
               status="calculated", notes="")
    if raw_sequence.endswith("*"):
        row["notes"] = "One terminal stop removed. "
        row['quality_flags'].append('terminal stop removed')
    if '*' in sequence:
        row['quality_flags'].append('internal stop character')
    invalid = sorted(set(sequence) - STANDARD)
    if invalid or not sequence:
        row['quality_flags'].append('unsupported residues or empty normalized sequence')
        row.update(status="not_calculated", notes=row["notes"] +
                   "Unsupported/ambiguous residues or empty sequence: " + ",".join(invalid))
        return row
    analysis = ProteinAnalysis(sequence)
    counts = analysis.count_amino_acids()
    row.update(
        molecular_weight_da=round(analysis.molecular_weight(), 4),
        theoretical_pi=round(analysis.isoelectric_point(), 4),
        gravy=round(analysis.gravy(), 4),
        instability_index=round(analysis.instability_index(), 4),
        aliphatic_index=round(100 * (counts["A"] + 2.9 * counts["V"] +
                                   3.9 * (counts["I"] + counts["L"])) / len(sequence), 4),
        aromaticity=round(analysis.aromaticity(), 4),
        amino_acid_counts=counts,
    )
    return row
