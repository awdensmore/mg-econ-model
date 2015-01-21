import mg_simulation as sim
import mgplot as plt

elds = [-0.5, -1, -1.5, -2, -2.5, -.3]
results = []

for i in range(len(elds)):
    ry, rp = sim.simyr(elds[i])
    results.append(ry)

rplot = [[] for a in results[0]]
i = 0
for key in results[0].keys():
    for j in range(len(elds)):
        rplot[i].append(results[j][key])
    i = i + 1

print(rplot[3])


# Plot
#plt.plot_pd(sim.prod, sim.demand)
#plt.plot_price(rplot[0], elds)
plt.plot_rev(rplot, elds)


plt.show()

