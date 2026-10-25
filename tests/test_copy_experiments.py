"""The experiment files are copied in the experiments folder of PyMoDAQ, without overwriting the user's files"""
from pathlib import Path

import pymodaq_plugins_mockexamples as package
from pymodaq_plugins_mockexamples import utils

RESOURCES = Path(package.__file__).parent / 'resources'


def _use_folder(monkeypatch, folder: Path):
    monkeypatch.setattr('pymodaq.utils.config.get_set_experiment_path', lambda user=False: folder)


def test_copies_every_experiment(monkeypatch, tmp_path):
    _use_folder(monkeypatch, tmp_path)
    copied = utils.copy_experiments(package.config)
    names = {path.name for path in RESOURCES.glob('*.xml')}
    assert names and {path.name for path in copied} == names == {path.name for path in tmp_path.iterdir()}


def test_never_overwrites_a_file(monkeypatch, tmp_path):
    _use_folder(monkeypatch, tmp_path)
    mine = tmp_path / 'beam_steering.xml'
    mine.write_text('my changes')
    utils.copy_experiments(package.config)
    assert mine.read_text() == 'my changes'


def test_can_be_disabled(monkeypatch, tmp_path):
    _use_folder(monkeypatch, tmp_path)
    monkeypatch.setattr(package.config.__class__, '__call__', lambda self, *args: False)
    assert utils.copy_experiments(package.config) == []
    assert not list(tmp_path.iterdir())
