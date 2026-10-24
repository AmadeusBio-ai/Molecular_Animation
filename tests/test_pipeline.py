import json
import re
import shutil
from types import SimpleNamespace

import pytest

import pipeline


def test_discovers_the_case_study():
    s = pipeline.SHOTS['channelrhodopsin']
    assert s['script'].exists() and s['brief'].exists() and s['record'].exists()
    assert s['count'] == 504 and s['overlay']['take'] == 'labels-05'


def test_lint_stops_a_build_before_blender(tmp_path, capsys):
    (tmp_path / 'shot.py').write_text("import bpy\nbpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'\n")
    with pytest.raises(SystemExit) as stop:
        pipeline.lint_shot({'folder': tmp_path, 'script': tmp_path / 'shot.py'})
    assert 'API errors' in str(stop.value)
    assert ':2: error [eevee-next]' in capsys.readouterr().out


def test_build_notes_report_what_a_render_hides():
    log = '\n'.join([
        f"{pipeline.ROOT / 'molanim' / 'blender' / 'look.py'}:9: DeprecationWarning: 'Material.use_nodes' is "
        'expected to be removed in Blender 6.0',
        '  m.use_nodes = True',
        'PIPELINE_RESULT {}',
        'PIPELINE_NODE_WARNINGS [["Mol", "Atoms", "INFO", "Input geometry has unsupported type: Mesh"]]',
        'Blender 5.3.0 (hash 0123456789ab built 2027-01-01 00:00:00)'])
    notes = pipeline.build_notes(log, [])
    assert notes[0].startswith('Blender 5.3.0 ran this build')
    assert "deprecated: molanim/blender/look.py:9: 'Material.use_nodes'" in notes[1]
    assert notes[2] == 'geometry nodes info: Mol / Atoms: Input geometry has unsupported type: Mesh'
    clean = 'PIPELINE_NODE_WARNINGS []\nBlender 5.2.2 LTS (hash d13f752e3b9c built 2026-09-15 01:37:04)'
    assert pipeline.build_notes(clean, []) == []


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
