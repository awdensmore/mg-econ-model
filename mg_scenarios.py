import mg_simulation as sim
import mgplot as plt

# Potential variables to analyze
sd = [0.25, 0.5, 1, 1.5, 2] # scale demand
elds = [-0.2, -0.7, -1.0, -1.5, -2, -3] # elasticity of demand

# Choose which variable to analyze
var = elds

results = []
for i in range(len(var)):
    ry, rp = sim.simyr(eld=var[i], sd=0.5)
    results.append(ry)

rplot = [[] for a in results[0]]
i = 0
for key in results[0].keys():
    for j in range(len(var)):
        rplot[i].append(results[j][key])
    i = i + 1

#for i in rplot:
#    print(i)

# Plot
plt.plot_hd(rplot, var)
#plt.plot_rev(rplot, var)
plt.show()

