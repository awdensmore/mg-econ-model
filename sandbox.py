import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)
red_patch = mpatches.Patch(marker="o", label="The red data")
blue_patch = mpatches.Patch(color='blue', label='The blue data')
ax.legend(handler = [red_patch, blue_patch])

plt.show()