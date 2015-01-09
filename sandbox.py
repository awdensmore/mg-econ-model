
hh = {1: [5, 0.08], 2: [20, 0.12], 3: [10, 0.15], 4: [6, 0.12], 5: [30, 0.17], 6: [22, 0.11], 7: [12, 0.16], 8: [10, 0.08], 9: [18, 0.1]}
load = 5000

def __shed(load, shd_pct, hh_lds):
    hh_dsctd = []
    hh_srtd = sorted(hh, key=hh.__getitem__) # (key) household identifiers sorted from lowest bid to highest
    bids_srtd = sorted(hh.values()) # [bid, ld%] sorted from lowest to highest bid
    ld_shd = 0
    i = 0
    while ld_shd < (load * shd_pct):  # disconnect hh's until the required shedding threshold is reached
        ld_shd = load * bids_srtd[i][1] + ld_shd
        hh_dsctd.append(hh_srtd[i])
        i = i + 1

    return hh_dsctd, 5

y, x = __shed(load, 0.3, hh)

print(y)
print(x)