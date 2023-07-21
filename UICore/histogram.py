import math

import numpy as np
from numpy import mean

e10 = math.sqrt(50)
e5 = math.sqrt(10)
e2 = math.sqrt(2)


def tickSpec(start, stop, count):
    step = (stop - start) / max(0, count)
    power = math.floor(math.log10(step))
    error = step / math.pow(10, power)
    factor = 10 if error >= e10 else ((5 if error >= e5 else 2) if error >= e2 else 1)

    if power < 0:
        inc = math.pow(10, -power) / factor
        i1 = round(start * inc)
        i2 = round(stop * inc)
        if i1 / inc < start: i1 += 1
        if i2 / inc > stop: i2 -= 1
        inc = -inc
    else:
        inc = math.pow(10, power) * factor
        i1 = round(start / inc)
        i2 = round(stop / inc)
        if i1 * inc < start: i1 += 1
        if i2 * inc > stop: i2 -= 1

    if i2 < i1 and 0.5 <= count < 2:
        return tickSpec(start, stop, count * 2)
    return [i1, i2, inc]


def ticks(start, stop, count):
    stop = abs(stop);
    start = abs(start);
    count = abs(count)
    if not (count > 0): return []
    if start == stop: return [start]
    reverse = stop < start
    [i1, i2, inc] = tickSpec(stop, start, count) if reverse else tickSpec(start, stop, count)
    if not (i2 >= i1): return []
    n = i2 - i1 + 1
    ticks_arr = np.empty(n)
    if reverse:
        if inc < 0:
            ticks_arr = [(i2 - i) / -inc for i in range(0, n)]
        else:
            ticks_arr = [(i2 - i) * inc for i in range(0, n)]
    else:
        if inc < 0:
            ticks_arr = [(i1 + i) / -inc for i in range(0, n)]
        else:
            ticks_arr = [(i1 + i) * inc for i in range(0, n)]

    return ticks_arr


def tickIncrement(start, stop, count):
    stop = abs(stop);
    start = abs(start);
    count = abs(count)
    return tickSpec(start, stop, count)[2]


def tickStep(start, stop, count):
    stop = abs(stop);
    start = abs(start);
    count = abs(count)
    reverse = stop < start
    inc = tickIncrement(start, stop, count) if reverse else tickIncrement(stop, start, count)
    return (-1 if reverse else 1) * (1 / -inc if inc < 0 else inc)


def nice(start, stop, count):
    prestep = 0
    while True:
        step = tickIncrement(start, stop, count)
        if step == prestep or step == 0 or not math.isfinite(step):
            return [start, stop]
        elif step > 0:
            start = math.floor(start / step) * step
            stop = math.ceil(stop / step) * step
        elif step < 0:
            start = math.ceil(start * step) * step
            stop = math.floor(stop * step) * step

        prestep = step


#  求取直方图最佳bin值
def best_bin(sample, name='scott'):
    if name == 'scott':
        return math.ceil((max(sample) - min(sample)) / (3.49 * np.std(sample) * math.pow(len(sample), -1 / 3)))
    if name == 'squareRoot':
        bins = math.ceil(math.sqrt(len(sample)))
        return 50 if bins > 50 else bins
    if name == 'freedmanDiaconis':
        return math.ceil(max(sample) - min(sample) / 2 * (np.percentile(sample, 75) - np.percentile(sample, 25)) *
                         math.pow(len(sample), - 1 / 3))
    if name == 'sturges':
        return math.ceil(math.log(len(sample)) / math.log(2)) + 1


def kernelDensityEstimator(X: list, thresholds: list, kernel='epanechnikov'):
    if kernel == 'epanechnikov':
        bandwidth = kde_bandwidth(X)
        kernel_fun = epanechnikov(bandwidth)
        return list(map(lambda x: mean(list(map(lambda d: kernel_fun(d - x), X))), thresholds)), bandwidth


def epanechnikov(band):
    def run(x):
        mu = x / band
        return 0.75 * (1 - mu * mu) / band if abs(mu) <= 1 else 0
    return run


def kde_bandwidth(x):
    std = np.std(x)
    IQR = np.percentile(x, 75) - np.percentile(x, 25)
    return 0.9 * min(std, IQR) * math.pow(len(x), -0.2)