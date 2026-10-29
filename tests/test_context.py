import hashlib
from pathlib import Path
import tempfile
import unittest
from micpscope.analysis import characterize
from micpscope.context import add_context, neighborhood


class ContextTests(unittest.TestCase):
    def test_coordinates_exact_ids_and_multisegment(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sample.gff'
            path.write_text('##gff-version 3\nc\tt\tCDS\t1\t12\t.\t+\t0\tID=p\n'
                            'c\tt\tCDS\t20\t31\t.\t-\t0\tID=other\n##FASTA\n>c\nACGT\n')
            p=characterize('p','p','AVIL')
            c=add_context([p],path)
            self.assertEqual(len(neighborhood(p,c)),2)
            self.assertEqual(p['coordinates'][0]['start'],1)
            path.write_text(path.read_text().split('##FASTA')[0]+'c\tt\tCDS\t40\t51\t.\t+\t0\tID=p\n')
            c=add_context([p],path)
            self.assertEqual(neighborhood(p,c),[])
            self.assertIn('multiple CDS',p['coordinate_status'])

    def test_domains_require_sequence_identity_and_valid_coordinates(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sample.interpro.tsv'
            p=characterize('p','p','AVIL')
            md5=hashlib.md5(b'AVIL').hexdigest()
            row=f'p\t{md5}\t4\tFixture\tTEST\tSynthetic\t2\t3\t-\tT\tdate\n'
            path.write_text(row+row)
            add_context([p],interpro=path)
            self.assertEqual(len(p['domains']),1)
            for bad in [row.replace(md5,'0'*32),row.replace('\t2\t3\t','\t2\t5\t')]:
                path.write_text(bad)
                with self.assertRaises(ValueError):add_context([p],interpro=path)

    def test_missing_rows_are_not_absence_and_duplicates_retained(self):
        p=characterize('p','p','AVIL');q=characterize('q','q','AVIL')
        add_context([p,q])
        self.assertEqual(p['domain_status'],'not assessed')
        self.assertEqual(p['identical_sequence_records'],['p','q'])
        self.assertIn('internal stop character',characterize('x','x','MA*AV')['quality_flags'])

    def test_unknown_identifiers_and_invalid_gff(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data.tsv'
            path.write_text('other\t'+'0'*32+'\t4\tFixture\tTEST\tSynthetic\t1\t4\t-\tT\tdate\n')
            p=characterize('p','p','AVIL')
            c=add_context([p],interpro=path)
            self.assertTrue(c['warnings'])
            self.assertIn('coverage unknown',p['domain_status'])
            path.write_text('c\tt\tCDS\t9\t1\t.\t+\t0\tID=p\n')
            with self.assertRaises(ValueError):add_context([p],gff=path)
