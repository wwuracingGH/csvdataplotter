import sys
import numpy as np

lines = [""]
dat2 = []
sample_ms = 10

if len(sys.argv) == 3:
    sample_ms = int(sys.argv[2])

def float_or_null(a):
    if len(a) == 0:
        return None
    try:
        return float(a)
    except:
        return None

channelnames = []    

with open(sys.argv[1]) as f:
    header = f.readline()

    channels = header.split(",")
    
    for c in channels:
        dat = c.replace("\"", "").split("|")
    
        channelnames.append(dat[0])    
        lines[0] += dat[0] + " [" + dat[1] + "],"
    
    f.readline()
    i = 0
    lv = f.readline()
    while (len(lv) > 10):
        dat2.append([float_or_null(d) for d in lv.replace('\n', '').split(',')])
        lv = f.readline()
        i += 1
        
dat = np.transpose(dat2)
start = dat[0][0]
end = dat[0][-1]
datinterp = []
    
newspace = np.linspace(start, end, int((end-start)/sample_ms) + 1)
# intervals are correct
for d in dat:
    oldtime = [v for i,v in enumerate(dat[0]) if d[i] is not None]
    olddat = [v for i,v in enumerate(d) if d[i] is not None]
    newdat = np.interp(x=newspace,xp=oldtime,fp=olddat)
    
    datinterp.append(newdat)

datinterp[0] = [d/1000 for d in datinterp[0]]
dat3 = np.transpose(datinterp)

with open("test.txt", "w") as f2:
    f2.write('time [s],')
    for c in lines[0].split(',')[1:]:
        f2.write(c + ',')
    f2.write('\n')
    
    for l in dat3:
        for i,c in enumerate(l):
            if (channelnames[i] != 'Latitude' and channelnames[i] != 'Longitude'):
                f2.write(f'{c:.3f},')
            else:
                f2.write(f'{c},')
        f2.write('\n')