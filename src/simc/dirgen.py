import sys, os, glob

dir = sys.argv[1]

# Get list of obs in file
obs = []
for file in os.listdir(dir):
    print(file)
    # For sharad
    # ob = file.split('_')[0] + "_" + file.split('_')[1]

    # For marsis
    ob = file.split("_")[0] + "_" + file.split("_")[1] + "_" + file.split("_")[2]
    print(ob)
    if ob not in obs:
        obs.append(ob)

# Make directories
for ob in obs:
    try:
        os.mkdir(dir + "/" + ob)
    except:
        print(ob + " dir exists")

# Move files
for ob in obs:
    for file in glob.glob(dir + "/" + ob + "*.*"):
        os.rename(file, dir + "/" + ob + "/" + file.split("/")[-1])
