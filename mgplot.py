__author__ = 'adensmore'

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

global mk
mk = ['b-', 'r-', 'g-', 'y-', 'm-', 'c-', 'k-']

def plot_pd(prod, demand, ul=[]):
    hrs = range(len(prod))
    fig, ax = plt.subplots()
    p1 = ax.plot(hrs, prod, 'b-')
    p2 = ax.plot(hrs, demand, 'm-')
    if len(ul) > 0:
        ax.plot(hrs, ul, 'r-')
    ax.set_xlabel("Hours of the year")
    ax.set_ylabel("Hourly Production or Load (Whr)")
    ax.legend( (p1[0], p2[0]), ('Production', 'Load') )

def plot_socw(socw, bal=[]):
    hrs = range(len(socw))
    #mk = ['b-', 'r-', 'g-', 'y-', 'm-', 'c-', 'k-']
    fig, ax = plt.subplots()
    ax.set_xlabel("Hours of the year")
    ax.set_ylabel("Hourly Battery State of Charge (Whr)")
    b = []
    for i in range(len(socw[0])):
        y = []
        for j in range(len(socw)):
            y.append(socw[j][i])
        b.append(y)
    for i in range(len(b)):
        ax.plot(hrs, b[i], mk[i])
    if len(bal) > 0:
        ax2 = ax.twinx()
        ax2.plot(hrs, bal, 'k--')

def plot_soc(soc):
    hrs = range(len(soc))
    plt.xlabel("Simulation Hours")
    plt.ylabel("Battery State of Charge (%)")
    plt.plot(hrs, soc)

def plot_prices(prc, bal=[]):
    hrs = range(len(prc))
    fig, ax = plt.subplots()
    ax.plot(hrs, prc, 'r-')
    ax.set_xlabel("Hours of the year")
    ax.set_ylabel("Hourly price of electricity ($/Whr)")
    if bal>0:
        ax2 = ax.twinx()
        ax2.plot(hrs, bal, 'k-')

def plot_price(results, labels):
    ind = np.arange(len(results))
    width_bar = 0.25
    #width_cat = width_bar *
    plt.bar(ind, results, width_bar)
    plt.xticks(ind+width_bar/2, labels)
    plt.xlabel("Elasticity of demand (% change in demand / % change in price)")
    plt.ylabel("Cost of electricity (Currency / Whr)")
    plt.title("Change in nominal electricity price with elasticity of demand")

def plot_rev(results, labels, ttl):
    ind = np.arange(len(results[6]))
    width_bar = 0.25
    plt.bar(ind, results[6], width_bar)
    plt.xticks(ind+width_bar/2, labels)
    # FOR USE WITH CHANGING ELASTICITY
    #plt.xlabel("Elasticity of demand (% change in demand / % change in price)")
    #plt.title("Change in revenue with elasticity of demand, 1*d")

    # FOR USE WITH CHANGING DEMAND
    plt.xlabel("Actual demand as a ratio of expected")
    plt.title("Change in annual revenue with demand, e= " + str(ttl))

    # FOR USE WITH BASELINE
    #plt.title("Baseline Annual Revenue")

    plt.ylabel("Annual Revenue")

def plot_hd(results, labels, ttl):
    ul_soc = [a * 100 for a in results[1]] # % unmet load due to low soc
    ul_p = [(a - b)*100 for a,b in zip(results[2], results[1])] # % unmet load due to high prices
    ind = np.arange(len(results[1]))
    width_bar = 0.25

    p1 = plt.bar(ind, ul_soc, width_bar, color='r')
    p2 = plt.bar(ind, ul_p, width_bar, color='b', bottom=ul_soc)
    plt.xticks(ind+width_bar/2, labels)
    # FOR USE WITH CHANGING ELASTICITY
    #plt.xlabel("Elasticity of demand (% change in demand / % change in price)")
    #plt.title("Change in unmet load with elasticity of demand, 0.5*d")

    # FOR USE WITH CHANGING DEMAND
    plt.xlabel("Actual demand as a ratio of expected")
    plt.title("Change in unmet load with demand, e= " + str(ttl))

    # FOR USE WITH BASELINE
    #plt.title("Baseline unmet load")

    plt.ylabel("% of total load unmet due to disconnection")
    plt.legend( (p1[0], p2[0]), ('Due to low SOC', 'Due to high prices'), loc=2 )

def import_data(file):
    results = []
    delim = ","
    with open(file, 'r') as f:
        while True:
            rx = []
            l = f.readline().rstrip()
            if not l: break
            b = False
            while True:
                n = l.find(delim)
                if n > 0:
                    a = l[0:n]
                else:
                    a = l[0:]
                    b = True
                rx.append(a)
                l = l.lstrip(a + delim)
                l = l.lstrip()
                if b == True: break
            results.append(rx)

    return results

def results_diff(results):
    out = []
    lines = len(results)
    for i in range(lines):
        if len(results[i]) == 5:
            j = 1
            while (i + j*7) < lines:
                rp = float(results[i+j*7][2])
                rb = float(results[i][2])
                r_diff = 100 * (rp / rb - 1)
                u_diff = float(results[i+j*7][3]) - float(results[i][3])
                line = [r_diff] + [u_diff] + results[i+j*7]
                j = j + 1
                out.append(line)
        else:
            break

    return out

def plot_scatter(results):
    x = [a[1] for a in results]
    y = [b[0] for b in results]
    m = ["o", "v", "s", "*", "+", "D", "x"]
    c = ["r", "b", "g", "y", "0", "0.5", "0.75"]
    p = []
    for i in range(0,7):
        for j in range(0,7):
            a = plt.scatter(x[i*7+j],y[i*7+j], marker=m[i], c=c[j], s=64)
            p.append(a)

    plt.xlabel("% change in unmet load vs. baseline")
    plt.ylabel("% change in revenue vs. baseline")
    plt.legend([p[0], p[7], p[14], p[21], p[28], p[35], p[42],\
                p[0], p[1], p[2], p[3], p[4], p[5], p[6]],\
               ['-0.2e', '-0.4e','-0.7e', '-0.9e', '-1e', '-1.25e', '-1.5e', \
                '1/4d', '1/2d', '3/4d', 'd', '1.5d', '2d', '3d'], loc=(1.005,0.05))
    plt.axis([-7,7,-5,20])
    plt.show()

a = import_data("results.txt")
b = results_diff(a)
print(b)
plot_scatter(b)

def show():
    plt.show()