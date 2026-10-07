import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'examples' / 'channelrhodopsin')]


@pytest.fixture
def pdb():
    return lambda pdb_id: ROOT / 'assets' / 'pdb' / f'{pdb_id}.cif'
