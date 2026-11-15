#!/usr/bin/env python3
"""Write paper/swarm-dynamics-source.zip deterministically (Python standard library only).

The archive holds everything needed to rebuild and check the report offline:
the top-level license files, every file under paper/ except regenerable build
and QA output, and the paper scripts. Entries are sorted, carry one fixed
timestamp (SOURCE_DATE_EPOCH, default 15 November 2026 00:00 UTC) and fixed
permissions, so the same inputs give the same bytes. A SHA-256 manifest of the
packed files is added as SOURCE-MANIFEST.sha256.

Extract the archive into an empty directory and run ./scripts/build_paper.sh
from it; see paper/BUILD.md.
"""
from pathlib import Path
import argparse
import hashlib
import os
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper' / 'swarm-dynamics-source.zip'
TOP_LEVEL = ['LICENSE', 'LICENSE-CONTENT.md']
SCRIPTS = ['scripts/build_paper.sh', 'scripts/build_paper_bibliography.py', 'scripts/build_paper_evidence.py',
           'scripts/build_paper_figures.py', 'scripts/build_paper_package.py', 'scripts/build_paper_qa.py']
# Regenerable output (also ignored by .gitignore) and the archive itself.
EXCLUDED_DIRS = ('paper/build', 'paper/qa', 'paper/figures/qa')
EXCLUDED_FILES = {'paper/swarm-dynamics-source.zip'}
EXECUTABLE = {'scripts/build_paper.sh', 'scripts/build_paper_qa.py'}
DEFAULT_EPOCH = 1794700800  # 2026-11-15T00:00:00Z


def packed_files():
    files = list(TOP_LEVEL) + list(SCRIPTS)
    for path in (ROOT / 'paper').rglob('*'):
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or rel in EXCLUDED_FILES:
            continue
        if any(rel == d or rel.startswith(d + '/') for d in EXCLUDED_DIRS):
            continue
        if any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(ROOT).parts):
            continue
        files.append(rel)
    missing = [rel for rel in files if not (ROOT / rel).is_file()]
    if missing:
        raise SystemExit('Missing files for the package: ' + ', '.join(missing))
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, default=OUT, help='archive path (default: paper/swarm-dynamics-source.zip)')
    args = parser.parse_args()
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', DEFAULT_EPOCH))
    stamp = time.gmtime(epoch)[:6]
    files = packed_files()
    manifest = []
    tmp = args.out.with_suffix('.zip.tmp')
    with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in files:
            data = (ROOT / rel).read_bytes()
            manifest.append(f'{hashlib.sha256(data).hexdigest()}  {rel}')
            info = zipfile.ZipInfo(rel, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = ((0o100755 if rel in EXECUTABLE else 0o100644) & 0xFFFF) << 16
            archive.writestr(info, data, compresslevel=9)
        info = zipfile.ZipInfo('SOURCE-MANIFEST.sha256', date_time=stamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = (0o100644 & 0xFFFF) << 16
        archive.writestr(info, '\n'.join(manifest) + '\n', compresslevel=9)
    tmp.replace(args.out)
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(f'Wrote {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}: '
          f'{len(files)} files plus manifest, {args.out.stat().st_size} bytes, sha256 {digest}')


if __name__ == '__main__':
    main()
