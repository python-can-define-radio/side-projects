import random

import rx
from rx import operators as ops




def generate_position(_):
    return {"x": random.randint(0, 400), "y": random.randint(0, 400)}


def make_rx_send_stream():
    return (rx
        .interval(1.0)
        .pipe(ops.map(generate_position))
    )