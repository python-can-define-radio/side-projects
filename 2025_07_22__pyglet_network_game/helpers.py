import random
import string
from typing import Tuple

import deal

from projtypes import ID



@deal.has("random")
@deal.post(lambda x: len(x) == 5)
def make_id() -> ID:
    """Random letters"""
    return "".join(random.sample(string.ascii_letters, 5))


@deal.pure
def id_to_color(i: ID) -> Tuple[int, int, int]:
    """Some arbitrary math to producde an RGB color"""
    return ord(i[0]) % 256, ord(i[1]) % 256, ord(i[2]) % 256

