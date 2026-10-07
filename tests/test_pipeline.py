import json
import re
import shutil
from types import SimpleNamespace

import pipeline


def test_discovers_the_case_study():
    s = pipeline.SHOTS['channelrhodopsin']
    assert s['script'].exists() and s['brief'].exists() and s['record'].exists()
    assert s['count'] == 504 and s['overlay']['take'] == 'labels-03'


def test_new_scaffolds_a_project(tmp_path, monkeypatch):
    pdb_dir = tmp_path / 'assets' / 'pdb'
    pdb_dir.mkdir(parents=True)
    shutil.copy(pipeline.PDB_DIR / '9GO1.cif', pdb_dir / '9GO1.cif')
    monkeypatch.setattr(pipeline, 'ROOT', tmp_path)
    monkeypatch.setattr(pipeline, 'PDB_DIR', pdb_dir)
    monkeypatch.setattr(pipeline, 'SUMS', pdb_dir / 'SHA256SUMS')
    pipeline.cmd_new(SimpleNamespace(name='retinal-test', pdb='9go1', highlight='RET', chains=None, title='Retinal',
                                     seconds=5.0, fps=24, loop=True))
    dest = tmp_path / 'projects' / 'retinal-test'
    files = {p.name for p in dest.iterdir()}
    assert {'retinal_test.py', 'shots.json', 'brief.md', 'record.md', 'sources'} <= files
    for p in dest.glob('*.*'):
        assert not re.search(r'__[A-Z]+__', p.read_text(encoding='utf-8')), p.name
    spec = json.loads((dest / 'shots.json').read_text())['shots']['retinal-test']
    assert spec['count'] == 120 and spec['render'] == '1-121' and spec['loop'] is True
    script = (dest / 'retinal_test.py').read_text(encoding='utf-8')
    compile(script, 'retinal_test.py', 'exec')
    assert "HIGHLIGHT = ['RET']" in script and 'LOOP = True' in script
    assert '9GO1.cif' in (pdb_dir / 'SHA256SUMS').read_text()
