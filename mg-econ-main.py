#!/usr/bin env python

import numpy as np
import matplotlib.pyplot as plt

# USER INPUTS
dmnd_scl = 5 # scale the hourly demand
prod_scl = 1.5 #scale the hourly production
mbat_size = 60000 # Size of the master battery
bat_slv_sizes = [20000 for x in range(0,3)] # Size of the slave batteries (provided by third-party entrepreneurs)
bat_slv_bids = [50, 80, 20, 30] # Bids to sell power to the grid. Lowest bid is taken first when extra energy is needed.
hh_dmnd_lst = [0.05 for x in range(0,20)] # Each HH's % of total load. MUST add to 100%!
hh_shd_bids = [50,20,10,90,95,15,20,35,60,45,5,85,75,25,30,65,0,95,40,45] # The min $/R value at which each HH is willing to be disconnected. Lowest is disconnected first.
hh_dmnd = {}
bats_slv = {}
i = 0
for hh in hh_dmnd_lst:
    hh_dmnd[i+1] = [hh_shd_bids[i], hh] # starts at i+1 because it's a dict key, not list index.
    i = i + 1
j = 0
for bats in bat_slv_sizes:
    bats_slv[j+1] = [bat_slv_bids[j], bats]
    j = j + 1

dmnd_hr = []
prod_hr = []

def read_file(f_open, output):
    """
    :rtype : list
    """
    with open(f_open, mode='r') as mf:
        while True:
            x = mf.readline().rstrip()
            if not x: break
            y = int(x)
            output.append(y)

read_file("demand.txt", dmnd_hr)
read_file("production.txt", prod_hr)

# Verify demand and production import files are of same length
if len(dmnd_hr) != len(prod_hr):
    exit("Number of hours in demand and production import files don't match.")

# Battery model
class battery:
    def __init__(self, size, type, soc_min = 0.4, c_rate_d_max=0.05, c_rate_c_max=0.3, \
                 cc_cv_trans_pt=0.8, eff_c=0.9, eff_d=0.9):
        self.size = size
        self.type = type
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
    # Inputs: bat soc (%), discharge watts, bat size (whr)
    # Output: Bat soc after discharge for this hour, unmet load (calc'd using shed() so set to 0 here)
    def discharge(self, soc, w_out):
            soc_new = max(soc + (float(w_out) / self.size), 0)
            return soc_new, 0

    # Mode: constant current charging
    # Inputs: battery soc (%) at beginning of hour, watts into battery, bat size, max C rate for charging
    # Outputs: battery soc at end of hour, any excess energy not used (if w_in exceeds c_rate_c_max)
    def cc_charge(self, soc, w_in):
        c_max = self.c_rate_c_max * self.size
        if w_in <= c_max:  # power in is less than maximum charge rate of bat
            soc_max = soc + (float(w_in) / self.size)
            soc_new = min(soc_max, 1)
            w_unused = (max(soc_max, 1) - 1) * self.size # if 100% exceeded, determine unused energy
        else:
            soc_new = soc + self.c_rate_c_max
            w_unused = w_in - c_max

        return soc_new, w_unused

    # Mode: constant voltage charging
    # Inputs: battery soc (%) at beginning of hour, watts into battery, bat size, charging transition point (cc -> cv)
    # Outputs: battery soc at end of hour, any excess energy not used (if w_in exceeds cv_rate)
    def cv_charge(self, soc, w_in):
        cv_rate = -0.0025 + 0.0005/(soc - self.c_trans_pt) # asymptotically approach 0C rate as soc approaches 100% (hard coded assuming 80% transition point!)
        c_rate = float(w_in) / self.size # the current charging rate assuming all watts are used
        if cv_rate > c_rate: # the maximum possible charging rate (cv_rate) is > than current c rate
            soc_max = soc + c_rate
            soc_new = min(soc_max, 1)
            w_unused = (max(soc_max, 1) - 1) * self.size # if 100% soc is exceeded, determine the unused energy
        else:
            soc_new = soc + cv_rate
            w_unused = w_in - (cv_rate * self.size)

        return soc_new, w_unused

    # Algorithm for determining which households to load shed
    # Inputs: Load on the bat from hh's, the percent of the hh load this hour to shed,
    #         hh_lds w/% of hh load & bid (dict) ie {1: [10, .5], 2: [5, .5]}
    #         ex_ld = excess load: if a slave battery, the load demanded by the master battery
    # Output: new bat soc, total load shed, unmet load (can happen when load demanded by master bat exceeds
    #         this bat's capacity), hh's disconnected
    # Note: unlike in real life, there is no "reconnect" setpoint. Just evaluate energy debt each hr, d/c as needed
    def shed(self, soc, prod, hh_ld, hh_lds, ex_ld=0):
        if (hh_ld or ex_ld) > 0:
            exit("loads must be negative, otherwise bat is charging")
        else:
            load = -hh_ld
        ld_shd_t =  max(0, abs(hh_ld + ex_ld) - (prod - ((self.soc_min - soc) * self.size)))  # the target load to be shed
        print("ld_shd_t = " + str(ld_shd_t))
        if ld_shd_t >= hh_ld:
            hh_shd_pct = 1 # The load shedding required exceeds all hh loads, therefore disconnect all hh's
        else:
            hh_shd_pct = ld_shd_t / abs(hh_ld)

        hh_dsctd = []
        hh_srtd = sorted(hh_lds, key=hh_lds.__getitem__) # (keys) household identifiers sorted from lowest bid to highest
        bids_srtd = sorted(hh_lds.values()) # [bid, ld%] sorted from lowest to highest bid
        ld_shd = 0
        i = 0
        while ld_shd < (ld_shd_t): #abs(hh_ld) * hh_shd_pct):  # disconnect hh's until the required shedding threshold is reached
            ld_shd = abs(hh_ld) * bids_srtd[i][1] + ld_shd
            hh_dsctd.append(hh_srtd[i])
            i = i + 1
            if i == len(hh_lds):
                break

        bat_ld_unmet = max(0, min(abs(ex_ld), ld_shd_t - ld_shd)) # the amount of master battery load that could not be met

        soc_new = soc + (float((prod + ld_shd + bat_ld_unmet + hh_ld + ex_ld)) / self.size)
        #if soc_new < 0:
        #    ld_unmet = -(soc_new * self.size)
        #    soc_new = 0

        return soc_new, ld_shd, bat_ld_unmet, hh_dsctd

#a = battery(10000, "s")
#print(a.shed(0.3, 5000, -3000, {1:[5,0.2],2:[10,0.1],3:[8,0.15],4:[1,0.1],5:[12,0.25],6:[3,.2]},-2000))

    # Determine the battery operating mode for this hour
    # Inputs:  bat soc, difference b/w energy produced/consumed this hr (pos is produced), bat type (master / slave)
    # Outputs: battery operating mode (string)
    def bat_mode(self, soc, bal):
        if bal > 0 and soc >= 1:
            mode = self.md_types[0] # full
        elif bal <= 0 and soc <= 0:
            mode = self.md_types[1] # empty
        elif bal <= 0 and soc > self.soc_min:
            mode = self.md_types[2] # discharge
        elif bal > 0 and soc > self.c_trans_pt:
            mode = self.md_types[3] # cv
        elif bal >= 0 and soc > self.soc_min and soc <= self.c_trans_pt:
            mode = self.md_types[4] # cc
        elif soc <= self.soc_min and self.type == "m":
            mode = self.md_types[5] # purchase
        elif soc <= self.soc_min and self.type == "s":
            if (bal / self.size) + soc > self.soc_min: # soc will be > soc_min after this hr, tf just cc charge
                mode = self.md_types[4] # cc
            else:
                mode = self.md_types[6] # ldshd

        return mode

    bat_action = {"full": bat_full, "empty": bat_empty, "disch": discharge, "cv": cv_charge,\
                   "cc": cc_charge, "ldshd": shed}

#a = battery(10000, "s")
#print(a.bat_mode(0.85, 1000))

"""class test(battery):
    a = 5

    def yo(self, soc, bal):
        t = self.bat_mode(soc, bal)
        return t

t = test(10000, "s")
print(t.yo(0.85,100))"""

class control(battery):
    # Init with instances of all batteries in the micro-grid
    #def __init__(self, batteries):
    #    self.bats = batteries

    # Returns the battery state of charge for this hour
    def bat_soc(self, soc, prod, hh_ld, hh_lds=None, ex_ld=0):
        bal = prod + hh_ld + ex_ld
        md = self.bat_mode(soc, bal)
        print(md)

        if md == self.md_types[6]: # load shed
            soc_new, ld_shd, bat_ld_unmet, hh_dsctd = self.bat_action[md](self, soc, prod, hh_ld, hh_lds=None, ex_ld=0)
            return soc_new, ld_shd, hh_dsctd
        else:
            soc_new, w_unused = self.bat_action[md](self, soc, bal)
            return soc_new, w_unused

#b = battery(10000, "s")
#c = control(10000, "s")
#print(c.bat_soc(0.85, 5000, -1000, {1:[5,0.2],2:[10,0.1],3:[8,0.15],4:[1,0.1],5:[12,0.25],6:[3,.2]},-2000))

    # Run the simulation
    # Inputs: soci - array of the initial state of charge for all batteries (len = # of bats)
    #         prod - array of hourly solar production (len = # of simulation hours)
    #         load - matrix of the hourly load on each bat (ie [[bat1, bat2,..., batx], ...hrx])
    #         hh_lds - dict describing hh loads (ie {1:[bid, ld %], ...hhx})
    def run(self, soci, prod, load, hh_lds):
        if len(prod) - len(load) != 0:
            exit("simhrs don't match")
        else:
            simhrs = len(prod)

"""

    def bat_soc(self, prod, ld, hh_lds, soci):
        simhrs = len(prod)
        bat_actions = {self.__md_types[0]:}
        self.soc = [soci] + [0 for x in range(simhrs)] # initialize the state of charge array (%)
        self.soc_w = [soci * self.size] + [0 for x in range(simhrs)] # soc in watts
        self.c_mode_hr = ["cc"] + ["" for x in range(simhrs)] # bool, can be 'cc' or 'cv'
        self.state = ["ON"] + ["" for x in range(simhrs)]
        self.balance = [0 for x in range(simhrs)] # list containing the hourly difference between production and load
        self.hh_lds = hh_lds
        self.hh_dsctd_hr = [[] for x in range(simhrs)]
        self.ld_shd_hr = [0 for x in range(simhrs)]

        for i in range(simhrs):
            bal = prod - ld
            self.balance[i] = bal
            mode = self.__bat_mode(self.soc[i], bal, self.type)




# Master battery class. Used for defining the attributes and behavior of the master battery
class mbat(battery):

    # Calculates the battery state of charge (soc) at every hour of the simulation period
    # Inputs: list of hourly solar production and load (watts)
    # Returns: hourly soc, charging mode, state (on/off), and the difference b/w production and load
    def bat_soc(self, prod, ld, hh_lds, soci):
        simhrs = len(prod)
        self.soc = [soci] + [0 for x in range(simhrs)] # initialize the state of charge array (%)
        self.soc_w = [soci * self.size] + [0 for x in range(simhrs)] # soc in watts
        self.c_mode_hr = ["cc"] + ["" for x in range(simhrs)] # bool, can be 'cc' or 'cv'
        self.state = ["ON"] + ["" for x in range(simhrs)]
        self.balance = [0 for x in range(simhrs)] # list containing the hourly difference between production and load
        self.hh_lds = hh_lds
        self.hh_dsctd_hr = [[] for x in range(simhrs)]
        self.ld_shd_hr = [0 for x in range(simhrs)]

        for i in range(simhrs):
            bal = prod[i] - ld[i]
            self.balance[i] = bal
            # Battery discharging
            if bal < 0:
                if self.soc[i] <= 0: # Disconnect all hh's if battery soc drops to 0
                    self.soc[i+1] = self.soc[i]
                    self.hh_dsctd_hr = range(1, len(hh_lds)+1)
                if self.soc[i] <= self.soc_min: # battery soc at or below min
                    # Try to make up for deficit by purchasing power from third-party producers


                    shd_pct = ((self.soc_min - self.soc[i]) * self.size) / abs(bal)
                    hh_dsctd, ld_shd = self.shed(abs(bal), shd_pct, hh_lds)
                    self.soc[i+1] = self.soc[i] + ((ld_shd + bal) / self.size)
                    self.hh_dsctd_hr[i] = hh_dsctd
                    self.ld_shd_hr[i] = ld_shd
                #if abs(bal) > self.__c_rate_d_max:
                    # discharge rate exceeds max allowed, therefore load shedding
                else: # discharge battery
                    rslt = self.discharge(self.soc[i], bal, self.size)
                    self.soc[i+1] = rslt
            # Constant current battery charging
            elif self.c_mode(self.soc[i], self.c_trans_pt) == "cc":
                rslt = self.cc_charge(self.soc[i], bal, self.size, self.c_rate_c_max)
                self.soc[i+1] = rslt[0]
                self.c_mode_hr[i+1] = "cc"
            # Constant voltage battery charging
            elif self.c_mode(self.soc[i], self.c_trans_pt) == "cv":
                rslt = self.cv_charge(self.soc[i], bal, self.size, self.c_trans_pt)
                self.soc[i+1] = rslt[0]
                self.c_mode_hr[i+1] = "cv"
            # Set battery state
            if self.soc[i] >= self.soc_min:
                self.state[i+1] = "ON"
            else:
                self.state[i+1] = "OFF"
            self.soc_w[i+1] = self.soc[i+1] * self.size

# Scale demand and production
for i in range(0,len(dmnd_hr)):
    dmnd_hr[i] = dmnd_hr[i] * dmnd_scl

for i in range(0,len(prod_hr)):
    prod_hr[i] = prod_hr[i] * prod_scl

# Create batteries
bat1 = mbat(60000)
bat1.bat_soc(prod_hr, dmnd_hr, hh_dmnd, .7)
#bat2 = battery(60000)
#bat2.bat_soc(prod_hr, dmnd_hr, hh_dmnd, 0.7)

#batteries = [bat1, bat2]

# Text output
print(bat1.hh_dsctd_hr)
print("Solar production:       " + str(prod_hr))
print("Demand:                 " + str(dmnd_hr))
print("Diff bw prod/load:      " + str(bat1.balance))
print("Battery state (w):      " + str(bat1.soc_w[1:]))
print("Battery SoC (%):        " + str(bat1.soc[1:]))
print("Battery state (on/off): " + str(bat1.state[1:]))
print("Battery charge mode:    " + str(bat1.c_mode[1:]))


# PLOTTING
plt_hrs = 167
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(range(0,plt_hrs), bat1.soc_w[1:plt_hrs+1], 'r-', label = "Energy Available")
ax1.legend()
ax1.set_xlabel('Time (hrs)')
ax1.set_ylabel('Bat Energy Available (Whrs)')
#ax2.legend(['SoC'])
ax2.plot(range(0,plt_hrs), bat1.soc[1:plt_hrs+1])
ax2.set_ylabel('Battery state of charge (%)')

fig2, ax3 = plt.subplots()
ax3.plot(range(0,plt_hrs), prod_hr[:plt_hrs], range(0,plt_hrs), dmnd_hr[:plt_hrs],\
         range(0,plt_hrs), bat1.ld_shd_hr)
ax3.set_xlabel('Time (hrs)')
ax3.set_ylabel('Power (Watts)')
plt.show()
"""