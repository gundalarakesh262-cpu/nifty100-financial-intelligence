import os
import shutil
from pathlib import Path
import json

base = Path(__file__).resolve().parent.parent
out_demo = base / 'output' / 'demo'

def _on_rm_error(func, path, exc_info):
    # Handle read-only files on Windows by making them writable.
    try:
        os.chmod(path, 0o666)
        func(path)
    except Exception:
        pass

if out_demo.exists():
    shutil.rmtree(out_demo, onerror=_on_rm_error)
out_demo.mkdir(parents=True)

# files and folders to include
items = [
    base / 'output' / 'screener_output.xlsx',
    base / 'output' / 'preset_csvs',
    base / 'output' / 'peer_comparison_percentile_formatted.xlsx',
    base / 'output' / 'peer_percentiles.sqlite',
    base / 'reports' / 'radar_charts',
    base / 'reports' / 'spotchecks',
]

included = []
for it in items:
    if it.exists():
        if it.is_dir():
            dest = out_demo / it.name
            shutil.copytree(it, dest)
            included.append(str(dest.relative_to(base)))
        else:
            shutil.copy2(it, out_demo / it.name)
            included.append(str((out_demo / it.name).relative_to(base)))

# write a small summary
summary = {
    'included': included,
}
with open(out_demo / 'demo_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

# create zip
zip_path = base / 'output' / 'demo_package'
shutil.make_archive(str(zip_path), 'zip', root_dir=out_demo)
print('Wrote demo package:', str(zip_path) + '.zip')
print('Demo contents:', included)
