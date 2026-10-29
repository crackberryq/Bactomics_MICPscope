import json
import os
from pathlib import Path
import sys
import tempfile

root, source, destination = sys.argv[1:]
sys.path.insert(0, str(Path(root) / "src"))
from micpscope.cli import render

report = render(json.loads(Path(source).read_text()))
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=Path(destination).parent, delete=False) as handle:
    temporary = Path(handle.name)
    handle.write(report)
try:
    os.replace(temporary, destination)
finally:
    temporary.unlink(missing_ok=True)
print("Report generated:", destination)
