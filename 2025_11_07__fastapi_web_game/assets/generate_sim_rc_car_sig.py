import numpy as np


def rc_car_data(n):
    """n = number of data points
    goal is to have...
    - Some OOK bits (not just a sine wave)
    - some AWGN
    - some time with noise-alone (no bits) before and after the 'real message'
    - a DC spike"""
    return np.sin(np.linspace(0, 10, n))

if __name__ == "__main__":
    print(rc_car_data(50))
