from annotated_types import Len
from typing_extensions import Annotated




ID = Annotated[str, Len(5, 5)]