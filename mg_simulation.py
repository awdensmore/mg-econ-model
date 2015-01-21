import mg_econ_main as main
import numpy as np
import econ

# Inputs - Households and the grid
global hh
hh = {1:[1.15,0.2],2:[1.18,0.1],3:[1.19,0.08],4:[1.19,0.22],5:[1.2,0.27],6:[1.2,.13]}
a = main.battery(5000, "s", 1.1)
b = main.battery(3000, "s", 1.1)
d = main.battery(1000, "s", 1.1)
e = main.battery(7000, "s", 1.1)
sbats = [a,b,d,e]
c = main.battery(10000, "m")
mg = main.control([a,e,c,d,b])

# Inputs - Loads, production, pricing, simulation length
scale_p = 1
scale_d = 1.7
period = 31 # length of simulation in days
global p_start
p_start = 1 # Starting price of electricity
global p_delta
p_delta = 0.2 # maximum daily price change (e.g. +/- 50%)
p_d_p = 0.1 # max change in price between periods (e.g. +/- 20%)
elast_d = -0.5# elasticity of demand (e.g., for 1% increase in price, 0.5% decrease in demand
prod, demand = main.read_files("production.txt", "demand.txt")
prod, demand = main.scale(prod, scale_p, demand, scale_d)
hrly_lbls = ["soc", "soc_w", "bal", "mode", "hh_dsctd", "ul", "ulpr", "p", "b_net_w"]
hourly_output = dict.fromkeys(hrly_lbls, [])

# One simulation period
def sim1(prod, demand, p_nom, soci=[]):
    # if it's not the first simulation period, populate soci with previous soc's
    l = len(soci)
    if l > 0:
        for i in range(l):
            mg.batteries[i].soci = soci[i]

    mg.run(prod, demand, hh, p_nom, p_delta)

    for key in hourly_output.keys():
        hourly_output[key] = hourly_output[key] + mg.__dict__[key]

    ul_hrs = sum(mg.ul)
    d = sum(demand)
    prc_ul = float(ul_hrs) / d

    return ul_hrs, prc_ul

def simyr(eld):
    per_lbls = ["ulw", "ulp", "avg_p", "dsctd_hrs", "hh_bill", "hh_rev", "bat_bill", "bat_bill_tot"]
    per_output = dict.fromkeys(per_lbls, [])
    simhrs = len(prod) # Length of each simulation sub-period
    hr = 0
    sd = 1
    p_nom = p_start
    soci = []
    for key in per_output.keys(): # not sure why this is needed, but dict builds incorrectly w/o it
        per_output[key] = []

    while hr < simhrs:
        # Run simulation
        hr_max = min(len(prod) - hr, period*24)
        prod1 = prod[hr:hr+hr_max]
        dmnd1 = demand[hr:hr+hr_max]
        prod1, dmnd1 = main.scale(prod1, scale_p, dmnd1, sd)
        ulw, ulp = sim1(prod1, dmnd1, p_nom, soci)

        # Run economics
        p_avg = np.average(mg.p)
        hh_cons, hh_ul = econ.hh_consumption(hh, mg.hh_dsctd, dmnd1)
        hh_bill = econ.hh_billing(hh_cons, mg.p) # Billings to households
        hh_rev = sum(hh_bill.values())
        bat_bill_hr = econ.sbat_billing(mg.b_net_w[1:], sbats, p_avg) # Billings to/from bats. Charge avg price to recharge
        bat_bill = [sum(b) for b in bat_bill_hr] # list of billings for each sbat for one period
        bat_bill_tot = sum(bat_bill) # total billings to/from sbats for one period

        # Save outputs. Use "+" for integers, "append" for lists
        per_output["ulw"] = per_output["ulw"] + [ulw]
        per_output["ulp"] = per_output["ulp"] + [ulp]
        per_output["avg_p"] = per_output["avg_p"] + [p_avg]
        per_output["dsctd_hrs"].append(mg.hrs_dsctd)
        per_output["hh_bill"] = per_output["hh_bill"] + [hh_bill]
        per_output["hh_rev"].append(hh_rev)
        per_output["bat_bill"].append(bat_bill)
        per_output["bat_bill_tot"].append(bat_bill_tot)

        # Set parameters for next simulation period
        # Scale demand and price of electricity
        # Raise price of electricity by (Y * unmet load). If unmet load = 0, lower prices by 10%
        Y = 2
        if ulp > 0:
            p_new = p_nom * min((1 + Y*ulp), 1+p_d_p) # ensure price doesn't change more than allowed
        else:
            p_new = p_nom * (1 - p_d_p)

        # Assume that demand is reduced proportional to the elasticity of demand
        delta = eld * (p_new - p_nom) / p_nom
        sd = sd + delta

        p_nom = p_new
        soci = mg.soc[-1]
        hr = hr + hr_max

    yr_output = yr_outputs(per_output)

    #print("% of load unmet for each period:     {}".format(per_output["ulp"]))
    #print("Revenue from hh's for each period:   {}".format(per_output["hh_rev"]))
    #print("Billings to/from slave batteries:    " + str(per_output["bat_bill_tot"]))
    #print("Average price of electricity:        {:0.4f}".format(yr_output["avg_p"]))
    #print("Annual revenue from house holds:     {:0.0f}".format(yr_output["yr_hh_rev"]))
    print("Annual revenue/cost (+/-) from bats: {:0.0f}".format(yr_output["yr_bat_bill"]))
    print("Annual micro-grid revenue:           {:0.0f}".format(yr_output["yr_rev"]))

    return yr_output, per_output

def yr_outputs(per_output):
    yr_lbls = ["yr_hh_rev", "yr_bat_bill", "yr_rev", "avg_p"]
    yr_output = dict.fromkeys(yr_lbls, 0)

    yr_output[yr_lbls[0]] = sum(per_output["hh_rev"])
    yr_output[yr_lbls[1]] = sum(per_output["bat_bill_tot"])
    yr_output[yr_lbls[2]] = yr_output[yr_lbls[0]] + yr_output[yr_lbls[1]]
    yr_output[yr_lbls[3]] = np.average(per_output["avg_p"])

    return yr_output

#yr_output, per_output = simyr()

