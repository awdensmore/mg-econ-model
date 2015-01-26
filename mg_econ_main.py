#!/usr/bin env python
# Copyright 2015 Alex Densmore
# Licensed under GNU GPL v3.0 (see license.txt in repo)

from __future__ import print_function
import math
import econ

def read_file(f_open):
    output = []
    with open(f_open, mode='r') as mf:
        while True:
            x = mf.readline().rstrip()
            if not x: break
            y = float(x)
            output.append(y)
    return output

def read_files(f_prod, f_dmnd):
    prod = read_file(f_prod)
    demand = read_file(f_dmnd)
    if len(prod) != len(demand):
        exit("Number of hours in demand and production import files don't match.")
    return prod, demand

def scale(prod, sp, demand, sd):
    p, d = [a * float(sp) for a in prod], [b * float(sd) for b in demand]
    return p, d

# Battery model
class battery:
    def __init__(self, size, type, bid=0, soci=0.7, soc_min = 0.4, c_rate_d_max=0.05, c_rate_c_max=0.3, \
                 cc_cv_trans_pt=0.8, eff_c=0.9, eff_d=0.9):
        self.size = size
        self.type = type
        if type == "s" and bid == 0:
            exit("Slave batteries must have a bid > 0")
        else:
            self.bid = bid
        self.soci = soci
        self.c_rate_c_max = c_rate_c_max
        self.__c_rate_d_max = c_rate_d_max
        self.c_trans_pt = cc_cv_trans_pt
        self.soc_min = soc_min
        self.md_types = ["full", "empty", "disch", "cv", "cc", "prc", "ldshd"]

    # Note on conventions
    # Argument "w": "+" means battery could not use all energy given to it. "-" means it could not supply the neded energy.

    # Mode: battery full
    # Input: watts into the battery
    # Outputs: soc (100%), watts unused (= w since battery is full)
    def bat_full(self, soc, w):
        soc_new = min(soc, 1)
        return soc_new, w

    # Mode: battery empty
    # Input: none
    # Outputs: soc (0%), watts unused (= w since battery is empty)
    def bat_empty(self, soc, w):
        soc_new = max(soc, 0)
        return soc_new, w

    # Mode: discharge battery
    # Inputs: bat soc (%), discharge watts (negative number), bat size (whr)
    # Output: Bat soc after discharge for this hour, unmet load (calc'd using shed() so set to 0 here)
    def discharge(self, soc, w_out):
            if w_out > 0:
                exit("In discharge(): load must be negative: " + str(w_out) + " " + str(soc))
            soc_new = max(soc + (float(w_out) / self.size), 0)
            return soc_new, 0

    # Mode: constant current charging
    # Inputs: battery soc (%) at beginning of hour, watts into battery, bat size, max C rate for charging
    # Outputs: battery soc at end of hour, any excess energy not used (if w_in exceeds c_rate_c_max)
    def cc_charge(self, soc, w_in):
        c_win = (float(w_in) / self.size)
        c_rate = min(self.c_rate_c_max, c_win)
        soc_max = soc + c_rate

        if soc_max >= self.c_trans_pt:
            w = (soc_max - self.c_trans_pt) * self.size
            t = (soc_max - self.c_trans_pt) / (soc_max - soc)
            soc_new, w_unused = self.cv_charge(self.c_trans_pt, w, t)
        else:
            soc_new = soc_max
            w_unused = 0

        return soc_new, w_unused

    # Mode: constant voltage charging
    # Inputs: battery soc (%) at beginning of hour, watts into battery, bat size, charging transition point (cc -> cv)
    #         t_add is used when the cc/cv transition occurs during the hour of a cc charge
    # Outputs: battery soc at end of hour, any excess energy not used (if w_in exceeds cv_rate)
    def cv_charge(self, soc, w_in, t_add=1):
        if soc < self.c_trans_pt:
            exit("During cv charge: soc must be > cc/cv transition point")
        power = -0.5
        # During cv charging the soc is assumed to approach 100% by m/(t^p)+b, where t is the time in hrs since
        # crossing the cc/cv transition point, and p, m & b are constants. "hrs" is scaled from 1 (moment of transition)
        # to 6 (5 hrs after transition), ie, it's assumed to take 5hrs to fully charge during cv mode.
        m = (1 - self.c_trans_pt) / ((math.pow(6,power) - math.pow(1,power)))
        b = 1 - (m * math.pow(6,power))
        t = math.pow((m / (soc - b)),-1/float(power))
        soc_max = m / math.pow((t+t_add),-power) + b
        soc_win = soc + (w_in / float(self.size))
        soc_new = min(soc_max, soc_win)
        w_unused = max(0, (soc_win - soc_max) * self.size)
        return soc_new, w_unused

    # Algorithm for determining which households to load shed
    # Inputs: Load on the bat from hh's, the percent of the hh load this hour to shed,
    #         hh_lds w/% of hh load & bid (dict) ie {1: [10, .5], 2: [5, .5]}
    #         ex_ld = excess load: if a slave battery, the load demanded by the master battery
    # Output: new bat soc, total load shed, unmet load (can happen when load demanded by master bat exceeds
    #         this bat's capacity), hh's disconnected
    # Note: unlike in real life, there is no "reconnect" setpoint. Just evaluate energy debt each hr, d/c as needed
    def shed(self, soc, hh_dsctd, prod, ld_bal, ld_tot, hh_lds, ex_ld=0):
        if (ld_bal or ex_ld) > 0:
            exit("In shed(): loads must be negative (ld_bal): " + str(ld_bal))
        else:
            load = -ld_bal
        ld_shd_t =  max(0, abs(ld_bal + ex_ld) - ((soc - self.soc_min) * self.size))  # the target load to be shed

        if ld_shd_t >= ld_bal:
            hh_shd_pct = 1 # The load shedding required exceeds all hh loads, therefore disconnect all hh's
        else:
            hh_shd_pct = ld_shd_t / abs(ld_bal)

        #hh_dsctd = []
        hh_srtd = sorted(hh_lds, key=hh_lds.__getitem__) # (keys) household identifiers sorted from lowest bid to highest
        bids_srtd = sorted(hh_lds.values()) # [bid, ld%] sorted from lowest to highest bid
        ld_shd = 0
        i = 0
        if len(hh_dsctd) > 0:
            while hh_dsctd[i] == hh_srtd[i]:
                i = i + 1
                if i == len(hh_dsctd):
                    break
        while ld_shd < (ld_shd_t): #abs(ld_bal) * hh_shd_pct):  # disconnect hh's until the required shedding threshold is reached
            ld_shd = abs(ld_tot) * bids_srtd[i][1] + ld_shd
            hh_dsctd.append(hh_srtd[i])
            i = i + 1
            if i == len(hh_lds):
                break

        bat_ld_unmet = max(0, min(abs(ex_ld), ld_shd_t - ld_shd)) # the amount of master battery load that could not be met

        soc_new = soc + (float((ld_shd + prod + bat_ld_unmet + ld_bal + ex_ld)) / self.size)
        if soc >= 0.95:
            print(str(soc) + " " + str(soc_new) + " " + str(ld_shd) + " "\
                    + str(ld_bal) + " " + str(ld_tot) + " " + str(ld_shd_t))
        return soc_new, ld_shd, bat_ld_unmet, hh_dsctd

    # Shed any hh's whose bid is less than the current price of electricity
    def shed_p(self, hh_info, load, price):
        hh_dsctd = []
        ld_shed = 0
        for key in hh_info.keys():
            if hh_info[key][0] < price:
                hh_dsctd.append(key)
                ld_shed = ld_shed + hh_info[key][1] * load
        return ld_shed, hh_dsctd

    # Determine the battery operating mode for this hour
    # Inputs:  bat soc, difference b/w energy produced/consumed this hr (pos is produced), bat type (master / slave)
    # Outputs: battery operating mode (string)
    def bat_mode(self, soc, bal):
        mode = ""
        w_now = self.size * soc
        w_min = self.size * self.soc_min
        if bal > 0 and soc >= 1:
            mode = self.md_types[0] # full
        elif bal <= 0 and soc <= 0:
            mode = self.md_types[1] # empty
        elif bal <= 0 and soc > self.soc_min:
            mode = self.md_types[2] # discharge
        elif bal > 0 and soc > self.c_trans_pt:
            mode = self.md_types[3] # cv
        elif (w_now + bal) > w_min and soc <= self.c_trans_pt:
            mode = self.md_types[4] # cc
        elif (w_now + bal) <= w_min and self.type == "m":
            mode = self.md_types[5] # purchase
        elif soc <= self.soc_min and self.type == "s": # for now, disabling load shedding on slave batteries
            #if (bal / self.size) + soc > self.soc_min: # soc will be > soc_min after this hr, tf just cc charge
            mode = self.md_types[4] # cc
            #else:
            #    mode = self.md_types[6] # ldshd
        if mode == "": exit("Battery mode unassigned! (soc, bal, type): " + str(soc) + ", " \
                            + str(bal) + ", " + str(self.type))
        return mode

    bat_action = {"full": bat_full, "empty": bat_empty, "disch": discharge, "cv": cv_charge,\
                   "cc": cc_charge, "ldshd": shed}

# Sort slave batteries by bid
# Inputs: bats: list of battery objects
#         order: 0 = lowest to highest, 1 = highest to lowest
def sbat_sort(sbats, order=0):
    a = []
    sbats_ordered = []
    for b in sbats:
        a.append(b.bid)
    a.sort()
    for abid in a:
        for bat in sbats:
            if bat.bid == abid:
                sbats_ordered.append(bat)
                break
    if order == 1:
        sbats_ordered.reverse()
    return sbats_ordered

def sbat_sort2(sbats, order=0):
    a = {}
    i = 0

    for b in sbats:
        a[b.bid] = b
    bids = a.keys()
    bids.sort()
    if order == 1:
        bids.reverse()
    sbats_ordered = [a[g] for g in bids]
    return sbats_ordered


class control(battery):
    # Init with instances of all batteries in the micro-grid
    def __init__(self, batteries):
        self.batteries = batteries
        sbats = []
        m = 0
        for b in batteries:
            if b.type == "m":
                m = m+1
                self.mbat = b
            else:
                sbats.append(b)
        if m != 1:
            exit("There must be 1 and only 1 master battery")
        self.sbats = sbat_sort(sbats)

    # Run the simulation
    # Inputs: bats - list of battery class instances provided at initialization
    #         prod - array of hourly solar production (len = # of simulation hours)
    #         load - matrix of the hourly load on each bat (ie [[bat1, bat2,..., batx], ...hrx])
    #         hh_lds - dict describing hh loads (ie {1:[bid, ld %], ...hhx})
    #         price = list of the hourly price of electricity
    # Notes:  1)
    def run(self, prod, load, hh_lds, p_nom, p_delta):
        if len(prod) - len(load) != 0:
            exit("simhrs don't match")
        else:
            simhrs = len(prod)

        sizes = [self.mbat.size] + [a.size for a in self.sbats] # Size of each battery
        soc_min = [self.mbat.soc_min] + [a.soc_min for a in self.sbats]
        soc = [[self.mbat.soci] + [a.soci for a in self.sbats]] # initialize the matrix of hourly battery soc (%)
        soc_w = [[c * s for c,s in zip(sizes, soc[0])]] # initialize the matrix of hourly battery soc (watts)

        # Outputs
        self.mode = []
        self.soc = []
        self.soc_w = []
        self.hh_dsctd = []
        self.ul = [] # unmet load due to insufficient bat soc
        self.ulpr = [] # unmet load due to the price of electricity
        self.p = [] # hourly price of electricity

        # !!!THE WHOLE SHEBANG!!!
        bal = []
        w_unused_hr = []
        for i in range(simhrs):
            p = econ.price(p_nom, p_delta, soc[i][0], 1, 0.3)
            self.p.append(p)
            w_shed, hh_dsctd = self.shed_p(hh_lds, load[i], p)
            ld_new = max(0, load[i] - w_shed) # max() is to catch rounding errors
            bal.append(prod[i] - ld_new)
            self.ulpr.append(w_shed) # unmet load due to price of electricity being too high
            md = self.mbat.bat_mode(soc[i][0], bal[i])
            if md == self.mbat.md_types[6]: # load shed
                # do something
                x = 5
            elif md == self.mbat.md_types[5]: # prc, try to purchase enough energy to return to soc_min
                w_avail = [max(0, round(a) - (b * c)) for a,b,c in zip(soc_w[i][1:], soc_min[1:], sizes[1:])] # determine the watts available from slave batteries
                w_needed = ((soc_min[0] - soc[i][0]) * sizes[0]) - bal[i] # watts needed to bring mbat to soc_min
                soc_new_m = soc[i][0] # initialize the new mbat soc to current soc
                soc_new_s = soc[i][1:] # inialize new sbat soc's to current soc's
                j = 0
                for b in w_avail: # Cycle through sbats until load is met or sbats are all discharged
                    w_disch = min(b, w_needed)
                    soc_new_s[j], w_unused = self.sbats[j].discharge(soc_new_s[j], -w_disch) # discharge sbat
                    w_needed = w_needed - w_disch + w_unused
                    if w_needed <= 0:
                        break
                    j = j + 1
                if w_needed > 0: # energy purchasing was insufficient, begin load shedding
                    md = self.mbat.md_types[6]
                    soc_new_m, ld_shd, blu, hh_dsctd = self.mbat.shed(soc_new_m, hh_dsctd, prod[i], -ld_new, -load[i], hh_lds) # previously, load = w_needed
                    self.ul.append(ld_shd)
            else: # full, empty, charging and discharging
                soc_new_m, w_unused = self.mbat.bat_action[md](self.mbat, soc[i][0], bal[i])
                soc_new_s = []
                if w_unused == 0: # no change in soc for slave batteries
                    k = 0
                    for s in self.sbats:
                        soc_new_s.append(soc[i][k+1])
                else: # Cycle through slave batteries, charging them until no energy is left
                    j = 0
                    while w_unused > 1: # should be 0, but set to 1 to avoid edge-case rounding errors
                        md = self.sbats[j].bat_mode(soc[i][j+1], w_unused)
                        #if md == "ldshd":
                        #    print(str(j) + " " + str(w_unused) + " " + str(soc[i-1][j+1]) + " " + str(soc[i][j+1]))
                        soc_j, w_unused = self.sbats[j].bat_action[md](self.sbats[j], soc[i][j+1], w_unused)
                        soc_new_s.append(soc_j)
                        j = j+1
                        if j == len(self.sbats):
                            break;
                    while j < len(self.sbats):
                        soc_new_s.append(soc[i][j+1])
                        j = j +1

            #if md == "full":
            #    print(str(i) + " " + str(prod[i]) + " " + str(load[i]) + " " + str(ld_new) \
            #          + " " + str(p) + " " + str(bal[i]))
            soc_new = [soc_new_m] + soc_new_s
            soc.append(soc_new)
            soc_w.append([a * b for a,b in zip(soc_new, sizes)])
            w_unused_hr.append(w_unused)
            self.mode.append(md)
            self.hh_dsctd.append(hh_dsctd)

        # Determine net charging / discharging for each battery ("+" = charging, "-" = discharging)
        net_w = []
        for i in range(len(soc_w[0])):
            net_w.append([])
            j = 0
            while j < (len(soc_w) - 1):
                w = soc_w[j+1][i] - soc_w[j][i]
                net_w[i].append(w)
                j = j+1

        self.prod = prod
        self.load = load
        self.bal = bal
        self.soc = [[round(a,3) for a in b] for b in soc[1:]]
        self.soc_w = [[round(a) for a in b] for b in soc_w[1:]]
        self.b_net_w = net_w
        self.hrs_dsctd = hrs_dsctd(hh_lds, self.hh_dsctd)

# Determine the number of hours each hh is disconnected during the simulation period
def hrs_dsctd(hh_info, hh_dsctd):
    hrs_dsctd = dict.fromkeys(hh_info, 0)
    for hr in hh_dsctd:
        for key in hr:
            hrs_dsctd[key] = hrs_dsctd[key] + 1
    return hrs_dsctd


