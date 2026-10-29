#!/usr/bin/env bash
set -euo pipefail
python -c 'import Bio; from Bio.SeqUtils.ProtParam import ProteinAnalysis; assert Bio.__version__ == "1.86"; assert ProteinAnalysis("AVIL").molecular_weight() > 0'
