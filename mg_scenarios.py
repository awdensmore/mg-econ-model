import mg_simulation as sim
import numpy as np
import mgplot as plt
import os

# Potential variables to analyze
sd = [0.25, 0.5, 0.75, 1, 1.5, 2, 3] # scale demand
elds = -0.7 #[-0.2, -0.4, -0.7, -0.9, -1, -1.25, -1.5] # elasticity of demand

# Choose which variable to analyze
var = sd

results = []
per_results = []
for i in range(len(var)):
    ry, rp = sim.simyr(sd=var[i], eld=elds)
    results.append(ry)
    per_results.append(rp)

rplot = [[] for a in results[0]]
i = 0
for key in results[0].keys():
    for j in range(len(var)):
        rplot[i].append(results[j][key])
    i = i + 1

#print(rp["demand"])
#print(rp["hh_rev"])
#print(rp["avg_p"])
#print(rp["p_nom"])
#print(np.average(sim.hourly_output["soc"]))
#for i in rplot:
#    print(i)

# rplot[6] = annual revenue
# rplot[1] = unmet load due to pricing
# rplot[2] = total unmet load
# rplot[5] = bat charges
# rplot[7] = bat net watts
revenue = rplot[6]
unmet_load = [ a * 100 for a in rplot[2]]
#bat_charges
#print(sim.hourly_output["soc_w"])
print("Revenue:       " + str(revenue))
print("Unmet Load:    " + str(unmet_load))
print("Bat charges:   " + str(rplot[5]))
print("Bat net watts: " + str(rplot[7]))

# Write results to file
def save_to_file():
    f = "results.txt"
    record = ""
    for i in range(len(rplot[6])):
        record = record + str(str(sd[i]) + ", " + str(elds) + ", " + str(revenue[i]) + ", " + str(unmet_load[i]) \
                              + "\n")
    with open(f, mode='a') as rf:
        rf.write(record)

#save_to_file()

# Plot
#plt.plot_pd(sim.prod, [a *2 for a in sim.demand])
#plt.plot_hd(rplot, sd, elds)
#plt.plot_rev(rplot, sd, elds)
#plt.plot_socw(sim.hourly_output["soc_w"][43800:52560])
#plt.show()
