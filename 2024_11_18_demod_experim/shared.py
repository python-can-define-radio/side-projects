import turtle


def newturt():
    t = turtle.Turtle()
    t.shape("circle")
    return t

def getTurtle(id_: str, players):
    if id_ not in players.keys():
        players[id_] = newturt()
    return players[id_]