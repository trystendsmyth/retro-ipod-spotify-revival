"""hardware/normalize_stl.py: facet order no longer matters, geometry is kept."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.path.dirname(__file__), "..", "hardware", "normalize_stl.py")
_spec = importlib.util.spec_from_file_location("normalize_stl", _PATH)
ns = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ns)


def _facet(n):
    return (f"facet normal 0 0 1\nouter loop\nvertex {n} 0 0\nvertex 0 {n} 0\n"
            f"vertex 0 0 {n}\nendloop\nendfacet\n")


def test_order_does_not_matter_and_is_idempotent():
    a = "solid m\n" + _facet(1) + _facet(2) + _facet(3) + "endsolid m\n"
    b = "solid m\n" + _facet(3) + _facet(1) + _facet(2) + "endsolid m\n"
    assert ns.normalize(a) == ns.normalize(b)
    assert ns.normalize(ns.normalize(a)) == ns.normalize(a)
    assert ns.normalize(a).count("endfacet") == 3


def test_committed_bracket_is_normalized():
    path = os.path.join(os.path.dirname(_PATH), "usb-c-bracket.stl")
    with open(path) as fh:
        text = fh.read()
    assert ns.normalize(text) == text


def test_rejects_binary_or_broken_files():
    with pytest.raises(ValueError):
        ns.normalize("not an stl")
    with pytest.raises(ValueError):
        ns.normalize("solid m\nfacet normal 0 0 1\nendsolid m\n")
