import io
import subprocess
import time



def runElmCode(code: str) -> str:
    """Opens the elm repl and returns a subset of its
    response after providing `code` for running."""
    try:
        marker = '"start"'
        markerElmTypeName = "String"
        p = subprocess.Popen(
            ["elm", "repl", "--no-colors"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        outputTuple = p.communicate(
            ( marker
            + "\n"
            + code
            + "\n"
            ),
            timeout=8
        )
        output = outputTuple[0]
        startidx = 288
        
        if output.index('> ' + marker) != startidx:
            print(output)
            raise ValueError("This only works if the spacing is JUST right. Output is above.")
        shiftedidx = (
            startidx
            + len("> ")
            + len(marker)
            + len(" : ")
            + len(markerElmTypeName)
            + len("\n")
        )
        return output[shiftedidx:]
    finally:
        p.terminate()


def checkElmCode(elmCode, expectVal, expectType):
    resultlines = runElmCode(elmCode).splitlines()
    fmt = "> " + expectVal + " : " + expectType
    return resultlines[-2] == fmt
        
assert checkElmCode("""\
times1111 x = x * 1111
times1111 3""",
    expectVal = "3333",
    expectType = "number"
)
