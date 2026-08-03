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
  -> If invalid Python syntax, report and stop
- Translate Python-AST to Elm/other
  -> If unable to translate, report specific failure and stop
- Use elm to type-check
  -> report elm's results without any changes,
     which will include specific functions and such


### How to handle imports
I want to start with the simplest approach even if it's not a good idea long-term.
Here's what I'm planning:
1. Ignore Python imports.
2. Have elm imports AND definitions specified in a multiline string (so that Python ignores it).

Example:

    '''trapure-output-only
    import List

    listmap = List.map
    '''

    def listmap(f, list_):
        # trapure-ignore
        return list(map(f, list_))

"""


import ast


def listmap(f, list_: list) -> list:
    """Apply a function `f` to each item of `list_`"""
    # trapure-ignore
    return list(map(f, list_))


def repr2(x) -> str:
    """Like python's `repr`, but modified:
    - strings: changes the outermost `'` to `"`'
    - all other types: no change (returns `repr(x)`)"""
    if type(x) == str:
        return f'"{x}"'
    else:
        return repr(x)


def translateExprLike(astElem) -> str:
    """Not sure whether 'Expression-Like' is correct
    terminology. This handles, for example, `x + 3`"""
    if type(astElem) == ast.Name:
        return astElem.id
    elif type(astElem) == ast.Constant:
        return repr2(astElem.value)
    elif type(astElem) == ast.Call:
        return translateCall(astElem)
    elif type(astElem) == ast.BinOp:
        return translateBinOp(astElem)
    elif type(astElem) == ast.List:
        return translateList(astElem)
    else:
        raise TypeError(f"Unsupported: {astElem}")

        
def getFuncs(statementList: list) -> list:
    def ensureFunkiness(statement):
        if type(statement) != ast.FunctionDef:
            raise TypeError("Must all be functions")
    
    listmap(ensureFunkiness, statementList)
    return statementList
       
   
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

  
def translateCall(call: ast.Call) -> str:            
    def paren(x):
        return f"({x})"
    args = listmap(translateExprLike, call.args)
    parenEach = listmap(paren, args)
    return f"{call.func.id} {' '.join(parenEach)}"   # type: ignore


def translateList(list_: ast.List) -> str:
    ids = listmap(translateExprLike, list_.elts)
    idsjoined = ", ".join(ids)
    return "[" + idsjoined + "]"


def translateAssign(assign: ast.Assign) -> str:
    """
    Given:
        y = 5  (ast parsed)
    Return:
        let
            y = 5
        in "
    """
    if len(assign.targets) != 1:
        raise NotImplementedError("Currently, there must be exactly one assign target -- we have not implemented `x, y = something`")
    nameObj = assign.targets[0]
    assert type(nameObj) == ast.Name
    var = nameObj.id
    con = translateExprLike(assign.value)
    return f"{var} = {con}"


def translateFuncSig(func: ast.FunctionDef):
    """translate this part of a function:
        `def doStuff(a, b, c):`
        into
        `doStuff a b c`
    Note that the parameter `func` is already ast-parsed (it's not a string).
    """
    def getarg(item):
        return item.arg
    
    args = listmap(getarg, func.args.args)
    return f"{func.name} {' '.join(args)} "


def translateFunc(func: ast.FunctionDef) -> str:
    """Example:
    Given this function:
        def add5(x):
            y = 5
            return x + y
    Returns:
        doStuff x =
            let
                y = 5
            in
                x + y
    """
    
    def retVal(func: ast.FunctionDef) -> ast.expr:
        """checks that the last item of the function's body is a return statment.
        If it is, return its value. Otherwise, raise an error.
        """
        last = func.body[-1]
        if type(last) != ast.Return:
            raise TypeError("Function currently must contain only one return statement as the last line. ")
        v = last.value 
        if v == None:
            raise TypeError("Return value must not be None.")        
        return v

    def funcbody(func: ast.FunctionDef) -> str:
        """Translate any assign statements that precede the return statement in the function body"""
        def transIfGoodType(x):
            if type(x) != ast.Assign:
                raise TypeError(f"Function bodies must contain a sequence of zero or more assign statements followed by a return statement. The following is not allowed: {type(x)}")
            else:
                return translateAssign(x)

        allButLast = func.body[:-1]
        if allButLast == []:
            return ""
        else:            
            translated = listmap(transIfGoodType, allButLast)
            combined = "\n        ".join(translated)
            return f"\n    let\n        {combined} \n    in\n        "
    
    return (
        translateFuncSig(func)
        + "= "
        + funcbody(func)
        + translateExprLike(retVal(func))
    )


def translate_ni(code: str) -> str:
    """The "ni" means "no imports" -- those are handled by the plain `translate` function."""
    parsed = ast.parse(code)
    funcs = getFuncs(parsed.body)
    translatedfuncs = listmap(translateFunc, funcs)
    newlinejoined = "\n\n".join(translatedfuncs)
    seplines = newlinejoined.splitlines()
    return "\n".join(listmap(lambda x: x.rstrip(), seplines))


def translate(code: str) -> str:
    """Given a very limited subset of valid Python code,
    return the code with syntax tranlated to Elm, and add some default imports automatically.
    
    Constraints:
    - All functions must return something. This is functional programming after all! :-)"""
    
    return "import List\n\n" + translate_ni(code)


assert translate_ni("""
def add5(x):
    y = x
    z = 5
    return y + z
""") == 'add5 x =\n    let\n        y = x\n        z = 5\n    in\n        (y + z)'

assert translate_ni("""
def add5(x):
    y = x + 1
    return y + 4
""") == 'add5 x =\n    let\n        y = (x + 1)\n    in\n        (y + 4)'

assert translate_ni("""
def add5(x):
    y = x
    return y + 5
""") == 'add5 x =\n    let\n        y = x\n    in\n        (y + 5)'

assert translate_ni("""
def add5(x):
    y = 5
    return x + y
""") == 'add5 x =\n    let\n        y = 5\n    in\n        (x + y)'

assert translate_ni("""\
def dostuff(x, y):
    return (addone(x) + addone(y)) / 10
""") == """\
dostuff x y = ((addone (x) + addone (y)) / 10)"""

assert translate_ni("""\
def dostuff(x):
    return len(bin(x))
""") == """\
dostuff x = len (bin (x))"""

assert translate_ni("""
def dostuff(x):
    return x + 1

def other(x):
    return x + 2
""") == """\
dostuff x = (x + 1)

other x = (x + 2)"""

assert translate_ni("""
def stuff(a, b):
    return [[99, a], [a, b], [b, "stuff"]]  
""") == """\
stuff a b = [[99, a], [a, b], [b, "stuff"]]"""

assert (
    translate_ni("def addone(x): return x + 1")
    == """addone x = (x + 1)"""
)

assert repr2(3) == '3'

assert repr2("hi") == '"hi"'

if __name__ == "__main__":
    print()





