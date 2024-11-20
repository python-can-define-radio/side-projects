import turtle


def newturt():
    t = turtle.Turtle()
    t.shape("circle")
    t.penup()
    return t


def getTurtle(id_: str, players: dict) -> "turtle.Turtle":
    """Note: this mutates `players`!"""
    if id_ not in players.keys():
        print(f"New id: {id_}")
        players[id_] = newturt()
    return players[id_]
