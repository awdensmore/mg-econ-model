import mg_econ_main as main
import econ

# Inputs - Households and the grid
global hh
hh = {1:[1.15,0.2],2:[1.18,0.1],3:[1.19,0.08],4:[1.19,0.22],5:[1.2,0.27],6:[1.2,.13]}
a = main.battery(5000, "s", .0011)
b = main.battery(3000, "s", .0013)
d = main.battery(1000, "s", .0017)
e = main.battery(7000, "s", .0014)
c = main.battery(10000, "m")
mg = main.control([a,e,c,d,b])

# Inputs - Loads, production, pricing, simulation length
scale_p = 1
scale_d = 1.3
period = 31 # length of simulation in days
p_nom = 1 # Nominal price of electricity
global p_delta
p_delta = 0.2 # maximum daily price change (e.g. +/- 50%)
p_d_p = 0.2 # max change in price between periods (e.g. +/- 20%)
elast_d = 0.05 # elasticity of demand (e.g., for 1% change in price, 5% change in demand
prod, demand = main.read_files("production.txt", "demand.txt")
#prod, demand = main.scale(prod, scale_p, demand, scale_d)
out_lbls = ["soc", "soc_w", "bal", "mode", "hh_dsctd", "ul", "p"]
hourly_output = dict.fromkeys(out_lbls, [])

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

def mainsdf():
    simhrs = len(prod) # Length of each simulation sub-period
    hr = 0
    sd = 1
    while hr < simhrs:
        hr_max = min(len(prod) - hr, period*24)
        prod1 = prod[hr:hr+hr_max]
        dmnd1 = demand[hr:hr+hr_max]
        prod1, dmnd1 = main.scale(prod1, scale_p, dmnd1, sd)
        ulw, ulp = sim1(prod1, dmnd1, p_nom)
        print(ulw, ulp)

        # Assume that load needs to be reduced by same % as unmet load %
        # i.e., demand scale = ulp / elast_d
        sd = 1 - (float(ulp) / elast_d) / 100
        hr = hr + hr_max


mainsdf()


#simhrs = min(len(prod), period*24) # Length of each simulation sub-period
#prod, demand = prod[:simhrs], demand[:simhrs]

