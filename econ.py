import mg_econ_main as main

# Determine hourly consumption for each household
def hh_consumption(hh_info, hh_dsctd, demand):
    hh_load = [] # household load
    hh_ul = [] # unmet hh demand
    #hh_load = [[ld1, ld2, ..., ldx], [ld1, ld2, ..., ldx], ..., hrx]
    #dsctd_hr = [{hh1: ld1, hh2: ld2, ..., hhx: ldx}, ..., {hrx}] # loads disconnected on an hrly basis

    for i in range(len(demand)):
        hh_load.append([])
        hh_ul.append([])
        for key in hh_info.keys():
            ld = demand[i] * hh_info[key][1] # demand for this hh at this hr
            if key in hh_dsctd[i]:
                l = 0
                ul = ld # demand is unmet for this hh at this hr
            else:
                l = ld # total hr demand * % of ld for this hh
                ul = 0
            hh_load[i].append(l)
            hh_ul[i].append(ul)

    return hh_load, hh_ul

def hh_billing(hh_load)

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
        for j in range(len(bat_net_w[0])): #cycle through each hr
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

a,b = hh_consumption(hh_info, hh_dsctd, demand)
#print(a)
#print(b)