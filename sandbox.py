import mg_econ_main as main

t = 2

a = main.battery(5000, "s")
b = main.battery(5000, "s")
d = main.battery(3000, "s")
c = main.battery(10000, "m")
m = main.control([a,b,c,d])

# Test 1 - charging
if t == 1:
    m.run([1000,1000,1000, 3000],[500,2000,0,2100],{1:[5,0.2],2:[10,0.1],3:[8,0.15],4:[1,0.1],5:[12,0.25],6:[3,.2]})
    print(m.soc)
    print(m.soc_w)
    print(m.bal)

# Test 2 - discharging
if t == 2:
    m.run([1000,1000,1000, 3000],[2500,3000,2000,2100],{1:[5,0.2],2:[10,0.1],3:[8,0.15],4:[1,0.1],5:[12,0.25],6:[3,.2]})
    print(m.soc)
    print(m.soc_w)
    print(m.bal)

# Test 3 - large data set
if t == 3:
    prod, demand = main.read_files("production.txt", "demand.txt")
    m.run(prod,demand,{1:[5,0.2],2:[10,0.1],3:[8,0.15],4:[1,0.1],5:[12,0.25],6:[3,.2]})
    print(m.soc)
    print(m.soc_w)
    print(m.bal)