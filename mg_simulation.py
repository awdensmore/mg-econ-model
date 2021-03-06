import mg_econ_main as main
import numpy as np
import math
import econ

# Inputs - Households and the grid
global hh, mb_size, b_bid, BL_FLAG
BL_FLAG = 0
hh = {1:[1.5,0.2],2:[1.5,0.1],3:[1.5,0.08],4:[1.5,0.22],5:[1.5,0.27],6:[1.5,.13]}
a = main.battery(7000, "s", 1.5)
b = main.battery(7000, "s", 1.5)
d = main.battery(7000, "s", 1.5)
e = main.battery(7000, "s", 1.5)
sbats = [a,b,d,e]
c = main.battery(32000, "m")
mg = main.control([c,a,b,d,e])

# Inputs - Loads, production, pricing, simulation length
scale_p = 1
scale_d = 1
period = 31 # length of simulation in days
global p_start
p_start = 1 # Starting price of electricity
global p_delta
p_delta = 0.005 # maximum hourly price change (e.g. +/- 50%)
#p_d_p = 0.05 # max change in price between periods (e.g. +/- 20%)
elast_d = -0.7# elasticity of demand (e.g., for 1% increase in price, 0.5% decrease in demand
prod, demand = main.read_files("production.txt", "demand.txt")
prod, demand = main.scale(prod, scale_p, demand, scale_d)
hrly_lbls = ["soc", "soc_w", "bal", "mode", "hh_dsctd", "ul", "ulpr", "p", "b_net_w"]
hourly_output = dict.fromkeys(hrly_lbls, [])

# One simulation period
# Inputs: prod - solar production for the simulation period
#         demand - load demand for the simulation period
#         p_nom - the nominal price of electricity during the simulation period
#         co - control object
#         soci - the starting soc of the batteries
#         bl - baseline flag
# Outputs: ul_hrs - unmet load hours (Whrs) during the simulation period due to low battery status
#          prc_ul - unmet load hours as a % of total demand during simulation period
#          mg.hrs_dsctd - total hrs (hr x # hh) disconnected. Includes disconnection due to low soc OR insufficient bid.
#                         (i.e. the hh was unwilling to pay the price of electricity at that hr)
def sim1(prod, demand, p_nom, bl, soci=[]):
    # if it's not the first simulation period, populate soci with previous soc's
    l = len(soci)
    if l > 0:
        for i in range(l):
            mg.batteries[i].soci = soci[i]

    mg.run(prod, demand, hh, p_nom, p_delta, bl)

    for key in hourly_output.keys():
        hourly_output[key] = hourly_output[key] + mg.__dict__[key]

    ul_hrs = sum(mg.ul)
    d = sum(demand)
    prc_ul = float(ul_hrs) / d
    hrs_dsctd = sum(mg.hrs_dsctd.values())

    return ul_hrs, prc_ul, hrs_dsctd

def simyr(eld=elast_d, sd=1, baseline=0):
    per_lbls = ["ulw", "ulp", "hd", "avg_p", "hh_bill", "hh_rev", "bat_bill", "bat_bill_tot", "bat_net_w", "p_nom", "ult",\
                "p_max_min", "socw", "demand"]
    per_output = dict.fromkeys(per_lbls, [])
    simhrs = len(prod) # Length of each simulation sub-period
    hr = 0
    p_nom = p_start
    #p_d_p = 0.035#0.025/abs(eld)
    p_maxa = sum([hh[key][0]*hh[key][1] for key in hh]) # Do not let the price exceed the weighted average of hh bids
    soci = []
    for key in per_output.keys(): # not sure why this is needed, but dict builds incorrectly w/o it
        per_output[key] = []

    while hr < simhrs:
        # Run simulation
        hr_max = min(len(prod) - hr, period*24)
        prod1 = prod[hr:hr+hr_max]
        dmnd1 = demand[hr:hr+hr_max]
        prod1, dmnd1 = main.scale(prod1, scale_p, dmnd1, sd)
        ulw, ulp, hd = sim1(prod1, dmnd1, p_nom, baseline, soci)

        # Run economics
        p_avg = np.average(mg.p)
        p_max = max(mg.p)
        p_min = min(mg.p)
        hh_cons, hh_ul = econ.hh_consumption(hh, mg.hh_dsctd, dmnd1)
        hh_bill = econ.hh_billing(hh_cons, mg.p) # Billings to households
        hh_rev = sum(hh_bill.values())
        bat_bill_hr = econ.sbat_billing(mg.b_net_w[1:], sbats, 0.75) # Billings to/from bats. Charge wholesale to recharge
        bat_bill = [sum(bt) for bt in bat_bill_hr] # list of billings for each sbat for one period
        bat_bill_tot = sum(bat_bill) # total billings to/from sbats for one period

        # Save outputs. Use "+" for integers, "append" for lists
        per_output["ulw"] = per_output["ulw"] + [ulw] # Whr of load shed due to low soc
        per_output["ult"] = per_output["ult"] + [(ulw + float(sum(mg.ulpr)))/sum(dmnd1)] # % of load shed due to low soc + high prices
        per_output["ulp"] = per_output["ulp"] + [ulp] # % of total load shed due to low soc
        per_output["hd"] = per_output["hd"] + [hd] # hh-hrs of load shed due to low soc + high prices
        per_output["avg_p"] = per_output["avg_p"] + [p_avg]
        per_output["hh_bill"] = per_output["hh_bill"] + [hh_bill]
        per_output["p_nom"] = per_output["p_nom"] + [p_nom]
        per_output["hh_rev"].append(hh_rev)
        per_output["bat_bill"].append(bat_bill)
        per_output["bat_bill_tot"].append(bat_bill_tot)
        per_output["bat_net_w"].append([sum(a) for a in mg.b_net_w[1:]]) # Net watts for each battery during the period
        per_output["p_max_min"].append([p_max, p_min])
        per_output["socw"] = per_output["socw"] + [mg.soc_w]
        per_output["demand"] = per_output["demand"] + [sum(dmnd1)]

        # Set parameters for next simulation period
        # Scale demand and price of electricity
        # Raise price of electricity by (Y * unmet load).
        if baseline ==0:
            p_nom, sd = econ.price_pd(p_nom, sd, ulp, math.ceil(365/period), eld, p_maxa)
            #print(p_nom, sd)

        #print(p_nom, p_new, ulp)

        soci = mg.soc[-1]
        hr = hr + hr_max

    #print(soci)
    yr_output = yr_outputs(per_output)
    #j = np.average(demand)
    #print(j)
    #print(j*sd)
    #print("% of load unmet for each period:     {}".format(per_output["ulp"]))
    #print("Revenue from hh's for each period:   {}".format(per_output["hh_rev"]))
    #print("Billings to/from slave batteries:    " + str(per_output["bat_bill_tot"]))
    #print("Average price of electricity:        {}".format(per_output["avg_p"]))
    #print("Nominal price of electricity:        {}".format(per_output["p_nom"]))
    #print("Annual revenue from house holds:     {:0.0f}".format(yr_output["yr_hh_rev"]))
    #print("Annual revenue/cost (+/-) from bats: {:0.0f}".format(yr_output["yr_bat_bill"]))
    #print("Annual micro-grid revenue:           {:0.0f}".format(yr_output["yr_rev"]))
    #print([per_output["ulp"]])

    if baseline ==1:
        print("Baseline is on. Dynamic pricing not considered.")

    return yr_output, per_output

def yr_outputs(per_output):
    yr_lbls = ["yr_hh_rev", "yr_bat_bill", "yr_rev", "avg_p", "ulp", "ult", "p_max_min", "bat_net_w"]
    yr_output = dict.fromkeys(yr_lbls, 0)

    yr_output[yr_lbls[0]] = sum(per_output["hh_rev"])
    yr_output[yr_lbls[1]] = sum(per_output["bat_bill_tot"])
    yr_output[yr_lbls[2]] = yr_output[yr_lbls[0]] + yr_output[yr_lbls[1]]
    yr_output[yr_lbls[3]] = np.average(per_output["avg_p"])
    yr_output[yr_lbls[4]] = np.average(per_output["ulp"])
    yr_output[yr_lbls[5]] = np.average(per_output["ult"])
    pmax = [a[0] for a in per_output["p_max_min"]]
    pmin = [a[1] for a in per_output["p_max_min"]]
    yr_output[yr_lbls[6]] = [max(pmax), min(pmin)]
    yr_output[yr_lbls[7]] = sum([sum(a) for a in per_output["bat_net_w"]])
    #print(yr_output[yr_lbls[7]])
    print(yr_output[yr_lbls[6]], yr_output[yr_lbls[3]])
    return yr_output