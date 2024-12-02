from browser import document, alert
from browser.html import P, TABLE, TR, TD, DIV, STYLE, PRE
from supportfuncs import *


color_red = "#EB212E"
color_grey = "#D3D3D3"

def displayError(f):
    def do(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            alert(e)
    return do


def updatelocal(op, inp, out, varname):
    def tx_sty(result: str, col: str):
        out.text = result
        out.style = f"background-color: {col}; "
    
    try:
        gbls = {varname: eval(inp.text)}
        gbls.update(globals())
    except Exception as e:
        tx_sty(f"Unable to evaluate input: '{inp.text}'", color_red)
        return
    
    code: str = op.text
    if code.strip() == "":
        tx_sty("_", color_grey)
        return
    
    try:
        result = repr(eval(code, gbls))
        tx_sty(result, "lightgreen")
    except Exception as e:
        tx_sty(str(e), color_red)

    
def main():
    def updateall(ev):
        updatelocal(op1, priminp, out1, "a")
        updatelocal(op2, out1, out2, "b")
        updatelocal(op3, out2, out3, "c")
        updatelocal(op4, out3, out4, "d")
        finalcode.innerHTML = "a = "+ priminp.text + "<br>b = " + op1.text.strip() + "<br>c = " + op2.text.strip()+ "<br>d = " + op3.text.strip()+ "<br>e = " + op4.text.strip()

    document <= STYLE("* { font-family: monospace; font-size: 20px; }")

    priminp = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    op1 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out1 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    op2 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out2 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    op3 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out3 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    op4 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out4 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    
    document <= TABLE([
        TR([
            TD(),
            TD("Operation",style='text-align: center; min-width: 200px;'),
            TD("I/O",style='text-align: center; min-width: 200px;'),
        ]),
        TR([
            TD("a&nbsp;=&nbsp;",style='text-align: right'),
            TD(),
            TD(PRE(priminp)),
        ]),
        TR([
            TD("b&nbsp;=&nbsp;"),
            TD(PRE(op1)),
            TD(PRE(out1)),
        ]),
        TR([
            TD("c&nbsp;=&nbsp;"),
            TD(PRE(op2)),
            TD(PRE(out2)),
        ]),
        TR([
            TD("d&nbsp;=&nbsp;"),
            TD(PRE(op3)),
            TD(PRE(out3)),
        ]),
        TR([
            TD("e&nbsp;=&nbsp;"),
            TD(PRE(op4)),
            TD(PRE(out4)),
        ])
    ])

    finalcode = DIV(contenteditable=True, style="vertical-align: middle; border: 1px solid blue; margin-top: 1em;")
    document <= finalcode

    ## TODO: Make `finalcode` populate to individual ops

    priminp.onkeyup = displayError(updateall)
    op1.onkeyup = displayError(updateall)
    op2.onkeyup = displayError(updateall)
    op3.onkeyup = displayError(updateall)
    op4.onkeyup = displayError(updateall)


main()


## TODO: easier symbolic links to things like
## /venv/lib/.../more_itertools