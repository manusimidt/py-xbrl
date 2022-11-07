from invoke import task
from pathlib import Path

@task(default=True)
def setup(c):
    from fhopecc.winman import addpath
    p = Path(__file__).parent
    addpath(str(p), 'PYTHONPATH')
