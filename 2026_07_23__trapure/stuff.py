from dataclasses import dataclass
from typing import Union, TypeVar

# T = TypeVar("T")
# U = TypeVar("U")


# @dataclass
# class Success:
#     val: T
# @dataclass
# class Failure:
#     val: U
# Result = Union[Success, Failure]


# @dataclass
# class Just:
#     val: T
# @dataclass
# class Nothing:
#     pass
# Maybe = Union[Just, Nothing]




# def listhead(list_: list) -> Maybe:
#     # trapure-ignore
#     if list_ == []:
#         return Nothing()
#     else:
#         return Just(list_[0])


# def headtail(list_: list[T]) -> Maybe[(T, list[T])]:
#     # trapure-ignore
#     if list_ == []:
#         return Nothing()
#     else:
#         return Just((list_[0], list_[1:]))


# def errorOrWrappedSuccess(list_: list[T]) -> Result:
#     """Given a list of Successes and Errors, return either
#     - a list, wrapped in `Success`, if all individual items are success,
#     or
#     - the first error, if any item is an error
#     Note: an empty list is considered to be all success.
#     """
#     # htmaybe = headtail(list_)
#     # if type(htmaybe) == Nothing:
#     #     return Success([])
#     # elif type(htmaybe) == Just:
#     #     ht = htmaybe.val
#     #     h, t = ht
#     #     if h
        

#     # listhead(list_):
#     #     case Nothing():
#     #         return Success([])
#     #     case Just(head):
#     #         match head:
#     #             case Success(val):
#     #                 return val
#     #             case Failure(msg):
#     #                 return Failure(msg)
        
    

# def keepListIfAllLessThan10(accumulator, newvalue):
#     print("a is ", accumulator, "b is ", newvalue)
#     if newvalue < 10:
#         return accumulator + [newvalue]
#     else:
#         return None
# print("result of reduce is", list(itertools.accumulate([7, 9, 2, 11, 5], keepListIfAllLessThan10, initial=[])))


def lessThan10(x):
    return x < 10

def reduceET(f, initial, list_):
    """reduce Early Termination"""
    # trapure-ignore
    for item in list_:
        acc, keepGoing = f(acc, item)
        if not keepGoing:
            break
    return result

# print(reduceET())

# assert errorOrWrappedSuccess(
#     [Success(3), Success(5), Success(22)]
# ) == Success([3, 5, 22])

# assert errorOrWrappedSuccess(
#     [Success(3), Error("Bad stuff happened"), Success(22)]
# ) == Error("Bad stuff happened")

# assert errorOrWrappedSuccess([]) == Success([])



