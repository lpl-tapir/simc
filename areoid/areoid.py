# Code to use GMM-3B spherical harmonic coefficents to calculate an areoid radius
# Data - https://pds-geosciences.wustl.edu/mro/mro-m-rss-5-sdp-v1/mrors_1xxx/data/shadr/gmm3_120_sha.tab
# Label - https://pds-geosciences.wustl.edu/mro/mro-m-rss-5-sdp-v1/mrors_1xxx/data/shadr/gmm3_120_sha.lbl
import numpy as np
import pandas as pd

mfile = "./gmm3_120_sha.tab"
cols = ["deg", "ord", "c", "s", "cu", "su"]

model = open(mfile, "r")
hdr = model.readline().split(",")
model.close()

df = pd.read_csv(mfile, names=cols, skiprows=[0])
print(df)

w = 1.0 / (
    24.6229 * 60 * 60
)  # angular velocity in 1/s - https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html
a = float(hdr[0]) * 1000  # semi-major axis for GMM-3B model in m
b = float(hdr[0]) * 1000  # semi-minor axis for GMM-3B model in m
GM = float(hdr[1]) * (1000 ** 3)  # gravity mass constant in m^3/s^2

f = (a - b) / a  # flattening
E = np.sqrt(a ** 2 - b ** 2)  # linear eccentricity
e = E / a  # first numerical eccentricity
ep = E / b  # second numerical eccentricity
m = ((w ** 2) * (a ** 2) * b) / GM
ga = (GM / (a * b)) * (1 - (1.5 * m) - ((3 / 14) * ep * m))
gb = (GM / (a ** 2)) * (1 + m + ((3 / 7) * ep * m))


def normGrav(phi, a, b, ya, yb, e):
    # Calculate normal gravity at geocentric latitude phi
    k = ((b * yb) - (a * ya)) / (a * ya)
    num = 1 + (k * (np.sin(phi) ** 2))
    denom = np.sqrt(1 - ((e ** 2) * (np.sin(phi) ** 2)))

    return num / denom


#    e = 1 # GMM3B ref sphere
# def undulation(lam, phi):
# Calculate undulation at geocentric longitude lam
# and latitude phi
