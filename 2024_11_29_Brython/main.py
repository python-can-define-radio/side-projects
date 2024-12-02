from browser import document, alert
from browser.html import P, TABLE, TR, TD, DIV, STYLE, PRE


color_red = "#EB212E"
color_grey = "#D3D3D3"

def displayError(f):
    def do(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            alert(e)
    return do


def updatelocal(proc, inp, out, varname, funcs):
    def tx_sty(result: str, col: str):
        out.text = result
        out.style = f"background-color: {col}; "
    
    try:
        gbls = {varname: eval(inp.text)}
    except Exception as e:
        tx_sty(f"Unable to evaluate input: '{inp.text}'", color_red)
        return
    
    code: str = proc.text
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
        updatelocal(primproc, priminp, primout, "a", funcs)
        updatelocal(proc2, primout, out2, "b", funcs)
        updatelocal(proc3, out2, out3, "c", funcs)
        updatelocal(proc4, out3, out4, "d", funcs)
        finalcode.innerHTML = "a = "+ priminp.text + "<br>b = " + primproc.text.strip() + "<br>c = " + proc2.text.strip()+ "<br>d = " + proc3.text.strip()+ "<br>e = " + proc4.text.strip()

    document <= STYLE("* { font-family: monospace; font-size: 20px; }")

    document <= P("Functions (doesn't work yet):")
    funcs = DIV(PRE("""
def lmap(f,x):
    return list(map(f,x))"""), style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    document <= funcs
    document <= P("Process demo:")
    priminp = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    primproc = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    primout = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    proc2 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out2 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    proc3 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out3 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    proc4 = DIV(style="vertical-align: middle; border: 1px solid blue;", contenteditable=True)
    out4 = DIV("&nbsp;", style="vertical-align: middle; border: 1px solid blue;")
    
    document <= TABLE([
        TR([
            TD(),
            TD("Process",style='text-align: center; min-width: 200px;'),
            TD("I/O",style='text-align: center; min-width: 200px;')
        ]),
        TR([
            TD("a =&nbsp;",style='text-align: right'),
            TD(),
            TD(priminp)
        ]),
        TR([
            TD("b =&nbsp;"),
            TD(primproc),
            TD(primout)
        ]),
        TR([
            TD("c =&nbsp;"),
            TD(proc2),
            TD(out2),
        ]),
        TR([
            TD("d =&nbsp;"),
            TD(proc3),
            TD(out3),
        ]),
        TR([
            TD("e =&nbsp;"),
            TD(proc4),
            TD(out4)
        ])
    ])

    finalcode = DIV(contenteditable=True, style="vertical-align: middle; border: 1px solid blue; margin-top: 1em;")
    document <= finalcode

    priminp.onkeyup = displayError(updateall)
    primproc.onkeyup = displayError(updateall)
    proc2.onkeyup = displayError(updateall)
    proc3.onkeyup = displayError(updateall)
    proc4.onkeyup = displayError(updateall)


main()


