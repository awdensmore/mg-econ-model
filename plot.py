__author__ = 'adensmore'

import matplotlib.pyplot as plt
import numpy as np

fig, ax1 = plt.subplots()
t = np.arange(0.01, 10, 0.01)
s1 = np.exp(t)
ax1.plot(t, s1, 'b-')
ax1.set_xlabel('time (s)')
ax1.set_ylabel('exp', color='b')
for t1 in ax1.get_yticklabels():
    t1.set_color('b')

ax2 = ax1.twinx()
s2 = np.sin(2*np.pi*t)
ax2.plot(t,s2,'r-')

plt.show()