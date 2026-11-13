#!/usr/bin/env python3
"""Build a review-only overlay in a temporary directory; never edit paper/."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PAPER = HERE.parents[1]
BASE_SHA = '06a39b89e579aef57d14ae51e86d74ecf9b6b768'

def main():
    baseline = {}
    patch = []
    for new in sorted((HERE/'overlay').rglob('*')):
        if not new.is_file():
            continue
        rel = new.relative_to(HERE/'overlay')
        old = PAPER/rel
        if old.exists():
            baseline[str(rel)] = hashlib.sha256(old.read_bytes()).hexdigest()
            previous = old.read_text()
        else:
            previous = ''
        patch.extend(difflib.unified_diff(previous.splitlines(True), new.read_text().splitlines(True),
                      fromfile='a/paper/'+str(rel) if old.exists() else '/dev/null',
                      tofile='b/paper/'+str(rel)))
    (HERE/'paper_rewrite_diff.patch').write_text(''.join(patch))
    (HERE/'baseline_sources.json').write_text(json.dumps({'baseline_commit':BASE_SHA,'sha256':baseline},indent=2)+'\n')
    logs = HERE/'build_logs'
    logs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='comet-manuscript-proposal-') as tmp:
        work = Path(tmp)
        for name in ('math_commands.tex','references.bib','iclr2027_conference.sty','iclr2027_conference.bst'):
            shutil.copy2(PAPER/name,work/name)
        shutil.copytree(HERE/'overlay', work, dirs_exist_ok=True)
        commands = [['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],
                    ['bibtex','main'],
                    ['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],
                    ['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex']]
        outcomes=[]
        for i,command in enumerate(commands,1):
            result=subprocess.run(command,cwd=work,capture_output=True,text=True)
            (logs/f'{i}_{command[0]}.txt').write_text(result.stdout+result.stderr)
            outcomes.append({'command':command,'exit_code':result.returncode})
            if result.returncode:
                (logs/'commands.json').write_text(json.dumps(outcomes,indent=2)+'\n')
                raise SystemExit(result.returncode)
        shutil.copy2(work/'main.pdf',HERE/'review_proposal.pdf')
        shutil.copy2(work/'main.log',logs/'final_latex.log')
        (logs/'commands.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    for rel,digest in baseline.items():
        assert hashlib.sha256((PAPER/rel).read_bytes()).hexdigest()==digest
    print('Review PDF and patch created; original paper files unchanged.')
if __name__=='__main__':
    main()
