"""
Name: "Trapure" -> TRAnslating to ensure functional PURity

Goal statement:
I want to be able to define functions in Python and know that the following is true:
1. It is pure (has no side effects).
2. The implementation has FP style (avoids mutation, etc).
3. (future possibility) The types are correct.

FP languages such as Elm, Haskell, Erg, and Purescript encourage 
and/or ensure these three attributes (purity, FP style, correct types).

Solution idea:
Make a program that automatically translates Python code to 
Elm (or similar) so we can use that type checker. Like pylyzer.

How?
- Translate Python to Python-AST (Abstract Syntax Tree)
- Translate Python-AST to Elm/other
"""



import ast


def listmap(f, x):
    return list(map(f, x))


def repr2(x) -> str:
    """Like python's `repr`, but modified:
    - strings: changes the outermost `'` to `"`'
    - all other types: no change (returns `repr(x)`)"""
    if type(x) == str:
        return f'"{x}"'
    else:
        return repr(x)

assert repr2(3) == '3'
assert repr2("hi") == '"hi"'


def translateExprLike(astElem) -> str:
    """Not sure whether 'Expression-Like' is correct
    terminology."""
    if type(astElem) == ast.Name:
        return astElem.id
    elif type(astElem) == ast.Constant:
        return repr2(astElem.value)
    elif type(astElem) == ast.Call:
        return translateCall(astElem)
    elif type(astElem) == ast.BinOp:
        return translateBinOp(astElem)
    else:
        raise TypeError(f"Unsupported: {astElem}")

        
def getFuncs(statementList):
    def ensureFunkiness(statement):
        if type(statement) != ast.FunctionDef:
            raise TypeError("Must all be functions")
    
    listmap(ensureFunkiness, statementList)
    return statementList
       
  
def translatePreEqualsSign(func):
    def getarg(item):
        return item.arg
    
    args = listmap(getarg, func.args.args)
    return f"{func.name} {' '.join(args)} "

  
def translateBinOp(binop):
    def translateOp(op) -> str:
        if type(op) == ast.Add:
            return "+"
        elif type(op) == ast.Sub:
            return "-"
        elif type(op) == ast.Mult:
            return "*"
        elif type(op) == ast.Div:
            return "/"
        else:
            raise TypeError(f"Unsupported op: {op}")

    return (
        f"({translateExprLike(binop.left)} "
        + f"{translateOp(binop.op)} "
        + f"{translateExprLike(binop.right)})"
    )

  
def translateCall(call) -> str:            
    def paren(x):
        return f"({x})"
    args = listmap(translateExprLike, call.args)
    parenEach = listmap(paren, args)
    return f"{call.func.id} {' '.join(parenEach)}"


def translateOneFunc(func) -> str:
    def retVal(func) -> ast.expr:
        b0 = func.body[0]
        if type(b0) != ast.Return:
            raise TypeError(
                "Body of function currently must contain "
                "exactly one return statement and nothing else"
            )
        v = b0.value 
        if v == None:
            raise TypeError("Return value must not be None.")        
        return v

    return (
        translatePreEqualsSign(func)
        + "= "
        + translateExprLike(retVal(func))
    )


def translate(code: str) -> str:
    """Given a very limited subset of valid Python code,
    return the code with syntax tranlated to Elm.
    
    Constraints:
    - All functions must return something. This is functional programming after all! :-)"""
    parsed = ast.parse(code)
    funcs = getFuncs(parsed.body)
    translatedfuncs = listmap(translateOneFunc, funcs)
    return "\n\n".join(translatedfuncs)

assert translate("""\
def dostuff(x, y):
    return (addone(x) + addone(y)) / 10
""") == """\
dostuff x y = ((addone (x) + addone (y)) / 10)"""

assert translate("""\
def dostuff(x):
    return len(bin(x))
""") == """\
dostuff x = len (bin (x))"""

assert translate("""
def dostuff(x):
    return x + 1

def other(x):
    return x + 2
    """) == """\
dostuff x = (x + 1)

other x = (x + 2)"""

# assert translate("""
# def dostuff(x):
#     y = x + 1
#     return y + 1
# """) == "this is going to fail"


# if __name__ == "__main__":
#     print()
