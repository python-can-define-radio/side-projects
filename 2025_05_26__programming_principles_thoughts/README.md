## Simplicity
1. In general, don't add extra to the code for the sake of making testing easier. (However, an example exception to this rule is the "instructor_data")

## General
2. Use classes (For now, pydantic's dataclasses) to make types more specific. For example, instead of using simply a Path object, use a StudentSubmission or similar.
3. {To discuss; I don't know whether this constraint is helpful} -- Only define methods for pure computations; use functions for everything else.

## FP principles
4. Avoid for-loops and while-loops as much as possible. Any function that must contain one of these should have a very short loop body (less than 4 lines). Favor `map`, `filter`, etc
5. Avoid mutation and reassignment unless it is necessary to keep track of state.
6. Prefer the pipeline style (my term, not standard AFAIK), in which line of the function depends only on the previous line and the function arguments.
7. UI should be a declarative function of state. I'm not aware of any Python libraries that do this well other than Marimo, so I'm hoping we can migrate all UI to Marimo.
8. Use pydash specifically when possible, because it uses eager evaluation.

 
