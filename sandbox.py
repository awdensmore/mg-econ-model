import math

def cv_charge(soc, c_trans_pt, w_in, t_add=1):
    power = -0.5
    size = 1000
    # During cv charging the soc is assumed to approach 100% by m/(t^p)+b, where t is the time in hrs since
    # crossing the cc/cv transition point, and p, m & b are constants. "hrs" is scaled from 1 (moment of transition)
    # to 6 (5 hrs after transition), ie, it's assumed to take 5hrs to fully charge during cv mode.
    m = (1 - c_trans_pt) / ((math.pow(6,power) - math.pow(1,power)))
    b = 1 - (m * math.pow(6,power))
    t = math.pow((m / (soc - b)),-1/float(power))
    soc_max = m / math.pow((t+t_add),-power) + b
    soc_win = soc + (w_in / float(size))
    soc_new = min(soc_max, soc_win)
    w_unused = max(0, (soc_win - soc_max) * size)
    print(t)
    print(soc_max)
    print(soc_win)
    print(w_unused)

cv_charge(.899, 0.8, 200)