import mg_simulation as sim
import numpy as np
import mgplot as plt
import os

# Potential variables to analyze
sd = [0.25, 0.5, 0.75, 1, 1.5, 2, 3] # scale demand
elds = -1 #[-0.2, -0.4, -0.7, -0.9, -1, -1.25, -1.5] # elasticity of demand

# Choose which variable to analyze
var = sd

results = []
per_results = []
for i in range(len(var)):
    ry, rp = sim.simyr(eld=elds, sd=var[i])
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
# rplot[2] = total unmet load
revenue = rplot[6]
unmet_load = [ a * 100 for a in rplot[2]]
#print(sim.hourly_output["soc_w"])
print("Revenue:    " + str(revenue))
print("Unmet Load: " + str(unmet_load))

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
#plt.plot_hd(rplot, var)
#plt.plot_rev(rplot, var)
#plt.plot_socw(sim.hourly_output["soc_w"][43800:52560])
#plt.show()
