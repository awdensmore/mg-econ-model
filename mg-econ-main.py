#!/usr/bin env python

import numpy as np
import matplotlib.pyplot as plt

# USER INPUTS
dmnd_scl = 5 # scale the hourly demand
prod_scl = 1.5 #scale the hourly production
mbat_size = 60000 # Size of the master battery
bat_slv_sizes = [20000 for x in range(0,3)] # Size of the slave batteries (provided by third-party entrepreneurs
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
    def __init__(self, size, soc_min = 0.4, c_rate_d_max=0.05, c_rate_c_max=0.3, \
                 cc_cv_trans_pt=0.8, eff_c=0.9, eff_d=0.9):
        self.size = size
        self.__c_rate_c_max = c_rate_c_max
        self.__c_rate_d_max = c_rate_d_max
        self.__c_trans_pt = cc_cv_trans_pt
        self.__soc_min = soc_min

    # Calculates the battery state of charge (soc) at every hour of the simulation period
    # Inputs: list of hourly solar production and load (watts)
    # Returns: hourly soc, charging mode, state (on/off), and the difference b/w production and load
    def bat_soc(self, prod, ld, hh_lds, soci):
        simhrs = len(prod)
        self.soc = [soci] + [0 for x in range(simhrs)] # initialize the state of charge array (%)
        self.soc_w = [soci * self.size] + [0 for x in range(simhrs)] # soc in watts
        self.c_mode = ["cc"] + ["" for x in range(simhrs)] # bool, can be 'cc' or 'cv'
        self.state = ["ON"] + ["" for x in range(simhrs)]
        self.balance = [0 for x in range(simhrs)] # list containing the hourly difference between production and load
        self.hh_lds = hh_lds
        self.hh_dsctd_hr = [[] for x in range(simhrs)]

        # Constant current charge mode
        # Inputs: battery soc (%) at beginning of hour, watts into battery
        # Returns list of battery soc at end of hour, any excess energy not used (if w_in exceeds c_rate_c_max)
        def __cc_charge(soc, w_in):
            results = [0, 0]
            if w_in <= (self.__c_rate_c_max * self.size):  # power in is less than maximum charge rate of bat
                results[0] = soc + (float(w_in) / self.size)
            else:
                results[0] = soc + self.__c_rate_c_max
                results[1] = w_in - (self.__c_rate_c_max * self.size)
            return results

        # Constant voltage charge mode
        # Inputs: battery soc (%) at beginning of hour, watts into battery
        # Returns list of battery soc at end of hour, any excess energy not used (if w_in exceeds cv_rate)
        def __cv_charge(soc, w_in):
            results = [0, 0]
            cv_rate = -0.0025 + 0.0005/(soc - self.__c_trans_pt) # asymptotically approach 0C rate as soc approaches 100% (hard coded assuming 80% transition point!)
            if cv_rate > (w_in * self.size):
                results[0] = soc + (w_in * self.size)
            else:
                results[0] = soc + cv_rate
                results[1] = w_in - (cv_rate * self.size)
            results[0] = min(results[0], 1)

            return results

        def __discharge(soc, w_out):
            result = soc + (float(w_out) / self.size)
            return result

        def __c_mode(soc):
            if soc > self.__c_trans_pt:
                c_mode = "cv"
            else:
                c_mode = "cc"
            return c_mode

        # Algorithm for determining which households to load shed
        # Inputs: Total load on the bat (int), the percent of the total load this hour to shed,
        #         hh_lds w/% of total load & bid (dict)
        # Output: households disconnected, total load disconnected
        # Note: unlike in real life, there is no "reconnect" setpoint. Just evaluate energy debt each hr, d/c as needed
        def __shed(load, shd_pct, hh_lds):
            hh_dsctd = []
            hh_srtd = sorted(hh_lds, key=hh_lds.__getitem__) # (key) household identifiers sorted from lowest bid to highest
            bids_srtd = sorted(hh_lds.values()) # [bid, ld%] sorted from lowest to highest bid
            ld_shd = 0
            i = 0
            while ld_shd < (load * shd_pct):  # disconnect hh's until the required shedding threshold is reached
                ld_shd = load * bids_srtd[i][1] + ld_shd
                hh_dsctd.append(hh_srtd[i])
                i = i + 1
                if i == len(hh_lds):
                    break

            return hh_dsctd, ld_shd

        for i in range(simhrs):
            bal = prod[i] - ld[i]
            self.balance[i] = bal
            # Battery discharging
            if bal < 0:
                if self.soc[i] <= 0: # Disconnect all hh's if battery soc drops to 0
                    self.soc[i+1] = self.soc[i]
                    self.hh_dsctd_hr = range(1, len(self.hh_lds)+1)
                if self.soc[i] <= self.__soc_min: # battery soc at or below min
                    # Try to make up for deficit by purchasing power from third-party producers
                    shd_pct = ((self.__soc_min - self.soc[i]) * self.size) / abs(bal)
                    hh_dsctd, ld_shd = __shed(abs(bal), shd_pct, self.hh_lds)
                    self.soc[i+1] = self.soc[i] + ((ld_shd + bal) / self.size)
                    self.hh_dsctd_hr[i] = hh_dsctd
                #if abs(bal) > self.__c_rate_d_max:
                    # discharge rate exceeds max allowed, therefore load shedding
                else: # discharge battery
                    rslt = __discharge(self.soc[i], bal)
                    self.soc[i+1] = rslt
            # Constant current battery charging
            elif __c_mode(self.soc[i]) == "cc":
                rslt = __cc_charge(self.soc[i], bal)
                self.soc[i+1] = rslt[0]
                self.c_mode[i+1] = "cc"
            # Constant voltage battery charging
            elif __c_mode(self.soc[i]) == "cv":
                rslt = __cv_charge(self.soc[i], bal)
                self.soc[i+1] = rslt[0]
                self.c_mode[i+1] = "cv"
            # Set battery state
            if self.soc[i] >= self.__soc_min:
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
bat1 = battery(60000)
bat1.bat_soc(prod_hr, dmnd_hr, hh_dmnd, .7)
bat2 = battery(60000)
bat2.bat_soc(prod_hr, dmnd_hr, hh_dmnd, 0.7)

batteries = [bat1, bat2]

# Text output
print(bat1.hh_dsctd_hr)
"""print("Solar production:       " + str(prod_hr))
print("Demand:                 " + str(dmnd_hr))
print("Diff bw prod/load:      " + str(bat1.balance))
print("Battery state (w):      " + str(bat1.soc_w[1:]))
print("Battery SoC (%):        " + str(bat1.soc[1:]))
print("Battery state (on/off): " + str(bat1.state[1:]))
print("Battery charge mode:    " + str(bat1.c_mode[1:]))
"""

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
ax3.plot(range(0,plt_hrs), prod_hr[:plt_hrs], range(0,plt_hrs), dmnd_hr[:plt_hrs])
ax3.set_xlabel('Time (hrs)')
ax3.set_ylabel('Power (Watts)')
plt.show()