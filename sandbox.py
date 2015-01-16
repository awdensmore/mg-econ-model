import math

def cv_charge(soc, w_in, t_add=1):
    c_trans_pt = 0.8
    size = 1000
    power = -0.5
    # During cv charging the soc is assumed to approach 100% by m/(t^p)+b, where t is the time in hrs since
    # crossing the cc/cv transition point, and p, m & b are constants. "hrs" is scaled from 1 (moment of transition)
    # to 6 (5 hrs after transition), ie, it's assumed to take 5hrs to fully charge during cv mode.
    m = (1 - c_trans_pt) / ((math.pow(6,power) - math.pow(1,power)))
    b = 1 - (m * math.pow(6,power))
    t = math.pow((m / (soc - b)),-1/float(power))
    soc_max = m / math.pow((t+t_add),-power) + b
    soc_win = soc + (float(w_in) / size)
    soc_new = min(soc_max, soc_win)
    w_unused = max(0, (soc_win - soc_max) * size)

    return soc_new, w_unused

def cc_charge(soc, w_in):
    size = 1000
    c_max = 0.3
    trans = 0.8

    c_win = (float(w_in) / size)
    c_rate = min(c_max, c_win)
    soc_max = soc + c_rate
    print("c_max: " + str(c_max) + ", c_win: " + str(c_win) + ", c_rate: " + str(c_rate)\
          + ", soc_max: " + str(soc_max))

    if soc_max >= trans:
        w = (soc_max - trans) * size
        t = (soc_max - trans) / (soc_max - soc)
        print("w: " + str(w) + ", t: " + str(t))
        soc_new, w_unused = cv_charge(trans, w, t)
    else:
        soc_new = soc_max
        w_unused = 0

    return soc_new, w_unused

s, w = cc_charge(0.7, 200)
print(s)
print(w)
print(cv_charge(0.85, 100))
