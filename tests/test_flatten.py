import pytest
import logging
from sys import path
path.append('..')
from export import flatten

# Disable logging of all severity level 'CRITICAL' and below
logging.disable(logging.CRITICAL)

def test_simple_nested_list():
    assert list(flatten([["a","b","c",],["d","e"],["f","g","h"]])) ==['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

def test_bigger_nested_list():
    assert list(flatten([[[['abc', 'def'], [[[[['a', 'b']]]]], ['c', 'd', 'e']], ['f', 'g']], [[[[[[[[[[[[[[[[['y','z']]]]]]]]]]]]]]]]]])) == ['abc', 'def', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'y', 'z']


def flatten():
    raise TypeError()
def test_not_iterable():
    with pytest.raises(TypeError):
        list(flatten([2,3]))