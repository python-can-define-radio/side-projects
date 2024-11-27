from itertools import count
from visualizing_mod_demod import Slowgraph, parmap


def timestwo(x):
    return x * 2


def test_Slowgraph_make_iterators_1():
    initdat = count(5)
    iterables = Slowgraph.make_iterators(initdat, {
        "times two":    parmap(timestwo),
        "sub 1":        parmap(lambda x: x - 1),    
    })
    it0, it1, it2 = iterables
    assert next(it0) == 5
    assert next(it0) == 6
    assert next(it0) == 7
    assert next(it0) == 8
    assert next(it1) == 10
    assert next(it1) == 12
    assert next(it1) == 14
    assert next(it1) == 16
    assert next(it2) == 9
    assert next(it2) == 11
    assert next(it2) == 13
    assert next(it2) == 15
    ## Try advancing in a different order to ensure it acts as expected
    assert next(it0) == 9
    assert next(it1) == 18
    assert next(it2) == 17
    assert next(it2) == 19
    assert next(it1) == 20
    assert next(it0) == 10

def test_Slowgraph_make_iterators_2():
    initdat = [3, 9]
    iterables = Slowgraph.make_iterators(initdat, {
        "times two":    parmap(timestwo),
        "sub 1":        parmap(lambda x: x - 1),    
    })
    it0, it1, it2 = map(list, iterables)
    assert it0 == [3, 9]
    assert it1 == [6, 18]
    assert it2 == [5, 17]

