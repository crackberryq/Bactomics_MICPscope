import json
from pathlib import Path
import tempfile
import unittest

from micpscope.analysis import characterize, read_fasta
from micpscope.cli import main, read_evidence, EVIDENCE_FIELDS


class CoreTests(unittest.TestCase):
    def test_aliphatic_and_gravy_known_composition(self):
        row = characterize("p", "p", "AVIL")
        self.assertAlmostEqual(row["aliphatic_index"], 292.5)
        self.assertAlmostEqual(row["gravy"], 3.575)

    def test_biopython_documentation_reference(self):
        seq = ("MAEGEITTFTALTEKFNLPPGNYKKPKLLYCSNGGHFLRILPDGTV DGT"
               "RDRSDQHIQLQLSAESVGEVYIKSTETGQYLAMDTSGLLYGSQTPSEEC"
               "LFLERLEENHYNTYTSKKHAEKNWFVGLKKNGSCKRGPRTHYGQKAILF"
               "LPLPV").replace(" ", "")
        row = characterize("p", "p", seq)
        self.assertAlmostEqual(row["molecular_weight_da"], 17103.16, places=2)
        self.assertAlmostEqual(row["theoretical_pi"], 7.72, places=2)
        self.assertAlmostEqual(row["instability_index"], 41.98, places=2)

    def test_invalid_and_terminal_stop(self):
        self.assertEqual(characterize("p", "p", "MXA")["status"], "not_calculated")
        self.assertEqual(characterize("p", "p", "MA*")["length"], 2)
        self.assertEqual(characterize("p", "p", "MA**")["status"], "not_calculated")

    def test_fasta_rejections(self):
        for value in ("", "MAAA", ">p\n", ">p\nMA\n>p\nAC", ">\nMA"):
            with self.assertRaises(ValueError):
                read_fasta(value)

    def test_report_escape_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            fasta = base / "test.faa"
            fasta.write_text(">p<script>\nAVIL\n>bad\nMX\n")
            args = ["--proteins", str(fasta), "--sample", "<script>", "--out", str(base / "run")]
            main(args)
            data = json.loads((base / "run/results.json").read_text())
            self.assertEqual(len(data["proteins"]), 2)
            self.assertEqual(data["operating_conditions"], "undetermined")
            report = (base / "run/report.html").read_text()
            self.assertNotIn("<script>", report)
            with self.assertRaises(SystemExit) as caught:
                main(args)
            self.assertEqual(caught.exception.code, 2)

    def test_evidence_sample_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.csv"
            path.write_text(",".join(EVIDENCE_FIELDS) + "\nother,p,measured,test,1,a,source,note\n")
            with self.assertRaises(ValueError):
                read_evidence(path, "sample")


if __name__ == "__main__":
    unittest.main()
