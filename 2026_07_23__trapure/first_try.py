"""
Name: "Trapure" -> TRAnslating to ensure functional PURity

Problem statement:
1. I want to know that a function is pure (has no side effects).
2. I want a function's implementation to be FP style (avoid mutation, etc).
3. I want to know that a function's types are correct.

FP languages such as Elm, Haskell, Erg, and Purescript encourage and/or ensure these three attributes (purity, FP style, correct types).

Solution idea:
Make a program that automatically translates Python code to Elm (or similar) so we can use that type checker. Like pylyzer.

How?
- Translate Python to Python-AST (Abstract Syntax Tree)
- Translate Python-AST to Elm/other
"""



import ast


def listmap(f, x):
		return list(map(f, x))
  

def oneLayerDeeper(astElem) -> str:
    if type(astElem) == ast.Name:
        return astElem.id
    elif type(astElem) == ast.Constant:
        return astElem.value
    elif type(astElem) == ast.Call:
      	return unparseCall(astElem)
    elif type(astElem) == ast.BinOp:
        return unparseBinOp(astElem)
    else:
        raise TypeError(f"Unsupported: {astElem}")
        

def stringifyBinOp(op) -> str:		
    # https://docs.python.org/3/library/ast.html
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

        
def getFunc(body):
    b0 = body[0]
    if type(b0) == ast.FunctionDef:
        return b0
    else:
        raise TypeError("This currently assumes that the first item in the body is a function def.")

        
def getArgs(func) -> list[str]:
    def getarg(item): return item.arg
    return listmap(getarg, func.args.args)
        
  
def unparsePreEqualsSign(func):
    args = getArgs(func)
    return f"{func.name} {' '.join(args)} "

  
def unparseBinOp(binop):
  	return (
        f"({oneLayerDeeper(binop.left)} "
				+ f"{stringifyBinOp(binop.op)} "
		    + f"{oneLayerDeeper(binop.right)})"
  	)

  
def unparseCall(call):            
    def paren(x):
      	return f"({x})"
    args = listmap(oneLayerDeeper, call.args)
    parenEach = listmap(paren, args)
    return f"{call.func.id} {' '.join(parenEach)}"


def unparseBinOpOrCall(expr):
    """I believe `one layer deeper` does this. Verify."""
    if type(expr) == ast.BinOp:
        return unparseBinOp(expr)
    elif type(expr) == ast.Call:
      	return unparseCall(expr)

    
def translate(code: str) -> str:
    parsed = ast.parse(code)
    func = getFunc(parsed.body)
    return (
      unparsePreEqualsSign(func)
      + "= "
      + unparseBinOpOrCall(func.body[0].value)
    )

  
if __name__ == "__main__":
    translate(
      "def dostuff(x, y):\n"
      "    return (addone(x) + addone(y)) / 5"
    )
