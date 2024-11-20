import turtle


def newturt():
    t = turtle.Turtle()
    t.shape("circle")
    return t

def getTurtle(id_: str, players, exclude=None) -> "turtle.Turtle":
    if str(exclude) == str(id_):
        return None
    if id_ not in players.keys():
        players[id_] = newturt()
    return players[id_]