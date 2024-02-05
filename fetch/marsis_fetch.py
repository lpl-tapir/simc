import requests
import os
import sys

base = "https://pds-geosciences.wustl.edu/mex/"
bounds = {
    (0, 2418): base + "mex-m-marsis-2-edr-v2/mexme_1001/",
    (2419, 4918): base + "mex-m-marsis-2-edr-ext1-v2/mexme_1002/",
    (4919, 6836): base + "mex-m-marsis-2-edr-ext2-v1/mexme_1003/",
    (6837, 11453): base + "mex-m-marsis-2-edr-ext3-v1/mexme_1004/",
    (11455, 13960): base + "mex-m-marsis-2-edr-ext4-v1/mexme_1005/",
    (13961, 16468): base + "mex-m-marsis-2-edr-ext5-v1/mexme_1006/",
    (16470, 18974): base + "mex-m-marsis-2-edr-ext6-v1/mexme_1007/",
    (18976, 20228): base + "mex-m-marsis-2-edr-ext7-v1/mexme_1008/",
}

track = int(sys.argv[1])

fail = True
for k, v in bounds.items():
    if track >= k[0] and track <= k[1]:
        url = v
        fail = False
        break

if fail:
    print("Entry corresponding to MARSIS track %05d not found in local dictionary" % track)
    exit()

url += "data/edr%04dx/e_%05d_ss3_trk_cmp_m_g.dat" % (int(track / 10), track)

os.system("mkdir -p ../nav")

r = requests.get(url, allow_redirects=True)
if r.status_code == 404:
    print("No nav file found for MARSIS track %05d" % track)
    exit()
with open("../nav/e_%05d_ss3_trk_cmp_m_g.dat" % track, "wb") as fd:
    fd.write(r.content)
