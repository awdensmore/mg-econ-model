#!/usr/bin env python

#import numpy as np

#dmnd_day = [[] for hr in range(0,24)]
SIMHRS = 12
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
    exit("Number of hours in demand and production import file don't match.")

# Battery model
class battery:
    def __init__(self, size, soci=0.5, soc_min = 0.3, c_rate_d_max=0.05, c_rate_c_max=0.3, \
                 cc_cv_trans_pt=0.8, eff_c=0.9, eff_d=0.9):
        self.size = size
        self.soc = [0 for x in range(SIMHRS)] # initialize the state of charge array
        self.soc_w = [0 for x in range(SIMHRS)]
        self.c_mode = ["" for x in range(SIMHRS)] # bool, can be 'cc' or 'cv'
        self.state = {"c_mode":"cc"} #"on" # bool, can be 'on' or 'off'
        self.balance = [0 for x in range(SIMHRS)] # list containing the hourly difference between production and load
        self.__c_rate_c_max = c_rate_c_max
        self.__c_rate_d_max = c_rate_d_max
        self.__c_trans_pt = cc_cv_trans_pt
        self.__soc_min = soc_min

    # Calculates the battery state of charge (soc) at every hour of the simulation period
    # Inputs: list of hourly solar production and load (watts)
    # Returns:
    def bat_soc(self, prod, ld):
        # Constant current charge mode
        # Inputs: battery soc (%) at beginning of hour, watts into battery
        # Returns list of battery soc at end of hour, any excess energy not used (if w_in exceeds c_rate_c_max)
        def __cc_charge(soc, w_in):
            results = [0, 0]
            if w_in <= (self.__c_rate_c_max * self.size):
                results[0] = soc + (float(w_in) / self.size)
            else:
                results[0] = soc + self.__c_rate_c_max
                results[1] = w_in - (self.__c_rate_c_max * size)
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

        for i in range(SIMHRS-1):
            bal = prod[i] - ld[i]
            self.balance[i] = bal
            # Battery discharging
            if bal < 0:
                if self.soc[i] <= self.__soc_min: # battery soc at or below min, disconnect battery
                    self.state = "OFF"
                    self.soc[i+1] = self.soc[i]
                #if abs(bal) > self.__c_rate_d_max:
                    # discharge rate exceeds max allowed, therefore load shedding
                else: # discharge battery
                    rslt = __discharge(self.soc[i], bal)
                    self.soc[i+1] = rslt
            # Battery charging
            elif __c_mode(self.soc[i]) == "cc":
                rslt = __cc_charge(self.soc[i], bal)
                self.soc[i+1] = rslt[0]
            elif __c_mode(self.soc[i]) == "cv":
                rslt = __cv_charge(self.soc[i], bal)
                self.soc[i+1] = rslt[0]
            self.soc_w[i+1] = self.soc[i+1] * self.size


li_ion = battery(800)
li_ion.bat_soc(prod_hr, dmnd_hr)
print(prod_hr)
print(dmnd_hr)
print(li_ion.balance)
print(li_ion.soc_w)
print(li_ion.soc)



