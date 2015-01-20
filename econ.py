import numpy as np
import mg_econ_main as main

# Determine hourly consumption for each household
# Inputs: hh_info = disctionary of hh's {1: [bid, demand], .., hhx}
#         hh_dsctd = list of hh's (keys) disconnected each hr
# Outputs: hh_load = dictionary of the hrly load of each hh. {1: [hr1, hrx, ..., hrx], ..., hhx}
#          hh_ul = dictionary of hrly unmet load of each hh. {1: [hr1, hrx, ..., hrx], ..., hhx}
def hh_consumption(hh_info, hh_dsctd, demand):
    hh_load = dict.fromkeys(hh_info.keys()) # household load
    hh_ul = dict.fromkeys(hh_info.keys()) # unmet hh demand

    for key in hh_info.keys():
        hh_load[key] = []
        hh_ul[key] = []
        for i in range(len(demand)):
            ld = demand[i] * hh_info[key][1] # demand for this hh at this hr
            if key in hh_dsctd[i]:
                l = 0
                ul = ld # demand is unmet for this hh at this hr
            else:
                l = ld # total hr demand * % of ld for this hh
                ul = 0
            hh_load[key].append(l)
            hh_ul[key].append(ul)

    return hh_load, hh_ul

# Determine the hourly consumer price of electricity
# Inputs: p_nom - nominal price of electricity, i.e. when production and supply are equal
#         p_delta - the maximum allowable % change in the price of electricity
#         bal - a list of the net production / consumption of electricity each hr
# Method: the hrly price of electricity is determined by setting the maximum price when
#         there is the greatest debt of available power. Min price is set when the greatest
#         amount is available. It depends on knowing the net electricity production for
#         each hr of the simulation period, which is clearly not possible in a real scenario.
#         A more sophisticated or accurate modeling method would use a prediction or simple rule
#         dependent only on past behavior.
#         ALTERNATE - use bat soc. Low soc = high price, high soc = low price
# Output: A list of the hourly price of electricity
def price(p_nom, p_delta, bal):
    b_min = min(bal)
    b_avg = np.average(bal)
    p = []
    for b in bal:
        p_i = p_nom * (1 - p_delta * (float(b) - b_avg)/(b_avg - b_min))
        p.append(p_i)

    return p

# Bill each hh
# Inputs: the load from each hh. The hourly price of electricity
def hh_billing(hh_load, prices):
    hh_billing = {}
    for key in hh_load.keys():
        b = 0
        for i in range(len(prices)):
            b = b + prices[i] * hh_load[key][i]
        hh_billing[key] = b

    return hh_billing

# Determine the hourly net charging / discharging for slave batteries ("+" = charging, "-" = discharging)
# Inputs: bat_net_w = [[hr1, hr2, ..., hrx], ... [bx]]. Net charge/discharge for each slave bat (sorted from lowest bid
#                     highest.
#         sbats = list of battery objects.
#         c_rate = the billing rate for the micro-grid to recharge slave batteries (same for all)
# Output: billings = "-" means money paid to the slave battery, "+" means money billed to the slave battery
def sbat_billing(bat_net_w, sbats, c_rate):
    sb_sorted = main.sbat_sort(sbats)
    bids = [a.bid for a in sb_sorted]
    billings = []
    for i in range(len(bids)): # cycle through each battery
        billings.append([])
        for j in range(len(bat_net_w[0])): # cycle through each hr
            if bat_net_w[i][j] > 0: # bat charging, bill
                bill_hr = bat_net_w[i][j] * c_rate
            else: # bat discharging, pay out
                bill_hr = bat_net_w[i][j] * bids[i]
            billings[i].append(bill_hr)

    return billings


hh_info = {1:[5,0.2],2:[10,0.1],3:[8,0.15],4:[1,0.1],5:[12,0.25],6:[3,.2]}
hh_dsctd = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], \
            [], [], [], [4, 6, 1, 3, 2, 5], [4, 6, 1, 3, 2, 5], [4, 6, 1, 3, 2, 5], [4, 6, 1, 3, 2, 5],\
            [4, 6, 1, 3, 2, 5], [4, 6, 1, 3, 2, 5]]
demand = [50, 60, 45, 35, 32, 24, 20, 22, 25, 39, 50, 62, 70, 76, 80, 80, 80, 60, 68, 50, 50, 40, 80,\
          100, 110, 105, 95, 110, 98, 103]
bal = [20, 30, 40, 50, 60, 50, 40, 30, 20, 10, 0, -10, -20, -30, -40, -50, -40, -30, -20, -10, 0]

#a = price(100, 1, bal)

#a,b = hh_consumption(hh_info, hh_dsctd, demand)
#print(a[1][:5])
#print(a[2][:5])