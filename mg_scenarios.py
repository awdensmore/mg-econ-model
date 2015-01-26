import mg_simulation as sim
import mgplot as plt
import os

# Potential variables to analyze
sd = [0.25, 0.5, 0.75, 1, 1.5, 2, 3] # scale demand
elds = [-0.2, -0.4, -0.7, -0.9, -1, -1.25, -1.5] # elasticity of demand

# Choose which variable to analyze
var = sd

results = []
per_results = []
for i in range(len(var)):
    ry, rp = sim.simyr(sd=var[i])
    results.append(ry)
    per_results.append(rp)

rplot = [[] for a in results[0]]
i = 0
for key in results[0].keys():
    for j in range(len(var)):
        rplot[i].append(results[j][key])
    i = i + 1

#for i in rplot:
#    print(i)

# rplot[6] = annual revenue
# rplot[2] = total unmet load
revenue = rplot[6]
unmet_load = [ a * 100 for a in rplot[2]]
#print(sim.hourly_output["soc_w"])
print(revenue)
print(unmet_load)

# Plot
#plt.plot_pd(sim.prod, [a *2 for a in sim.demand])
#plt.plot_hd(rplot, var)
plt.plot_rev(rplot, var)
#plt.plot_socw(sim.hourly_output["soc_w"][43800:52560])
plt.show()

# Write results to file
def save_to_file():
    f = "results.txt"
    record = ""
    for i in range(len(rplot[6])):
        record = record + str("1, " + str(elds[i]) + ", " + str(revenue[i]) + ", " + str(unmet_load[i]) \
                              + ", BASELINE" + "\n")
    with open(f, mode='a') as rf:
        rf.write(record)
    print(f)

#save_to_file()


