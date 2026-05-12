import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons
import sys, math, os

from os import listdir
from os.path import isfile, join

def get_points(fp : str, centerpoint) -> tuple[tuple[float, float], list[int], list[float], list[float], list[tuple[float, float, float]]]:
    xvals = []
    yvals = []
    headers = []
    with open(fp) as f:
        channels = f.readline().split(",")
        try:
            int_idx = next(i for i,d in enumerate(channels) if d.startswith("\"Interval"))
            Lat_index = next(i for i,d in enumerate(channels) if d.startswith("\"Latitude"))
            Lon_index = next(i for i,d in enumerate(channels) if d.startswith("\"Longitude"))
            ax_index = next(i for i,d in enumerate(channels) if d.startswith("\"AccelX"))
            ay_index = next(i for i,d in enumerate(channels) if d.startswith("\"AccelY"))
            az_index = next(i for i,d in enumerate(channels) if d.startswith("\"AccelZ"))
        except:
            return None, None, 0, 0, None 
        
        headers = list(map(lambda x : x.split("\"")[1], channels))
        data = f.readline().split(",")
        #print(data[Lat_index])
        while(data[Lat_index] == '' or data[Lat_index] == '0.0'):
            data = f.readline().split(",")
            if (len(data) == 1): 
                return None, 0, 0, None 
            #print(data[Lat_index])

        if (centerpoint is None):
            lat = float(data[Lat_index])
            lon = float(data[Lon_index])

            centerpoint = (lat, lon)

        lat, lon = centerpoint

        lat_radians = lat * math.pi / 180.0
        m_per_deg_lat = 111132.954 - 559.822 * math.cos(2 * lat_radians) + 1.175 * math.cos(4 * lat_radians)
        m_per_deg_lon = 111412.84 * math.cos(lat_radians) - 93.5 * math.cos(3 * lat_radians) 

        interval = []
        accel_x = []
        accel_y = []
        accel_z = []
        otherdata = {}
        for head in headers:
            otherdata[head] = []
        theta = -47.8 * math.pi / 180.0
        while(1):
            line = f.readline()
            if line == '': break
            data = line.split(",")

            for i,d in enumerate(data):
                try:
                    fl = float(d)
                except:
                    fl = float('nan')
                otherdata[headers[i]].append(fl)
            
            if len(data) > 100:
                if data[Lat_index] != '':
                    try:
                        lat_x = (float(data[Lat_index]) - centerpoint[0]) * m_per_deg_lat
                        lon_x = (float(data[Lon_index]) - centerpoint[1]) * m_per_deg_lon 
                        yvals.append(lat_x)
                        xvals.append(lon_x)
                    except:
                        print("bad data: " + data[Lat_index])
                if data[ax_index] != '':
                    ax = float(data[ax_index])
                    ay = float(data[ay_index])
                    az = float(data[az_index])
                    
                    ct = math.cos(theta)
                    st = math.sin(theta) 
                    accel_x.append(ct * ax + st * az)
                    accel_y.append(ay)
                    accel_z.append(-st * ax + ct * az)
                    
                    otherdata["AccelX"][-1] = accel_x[-1]
                    otherdata["AccelY"][-1] = accel_y[-1]
                    otherdata["AccelZ"][-1] = accel_z[-1]
                    interval.append(float(data[int_idx]) / 1000.0)
        
    return (centerpoint, interval, xvals, yvals, (accel_x, accel_y, accel_z), otherdata)


current_file = 0

def plottable(interval, xvals, yvals):
    xvalspruned = []
    yvalspruned = []
    interpruned = []
    i = 0
    for xv, yv in zip(xvals,yvals):
        if not math.isnan(xv) and not math.isnan(yv):
            xvalspruned.append(xv)
            yvalspruned.append(yv)
            interpruned.append(interval[i])
        i += 1
        
    return xvalspruned, yvalspruned, interpruned

if __name__ == '__main__':
    fp = sys.argv[1]
    filedat = []
    if (os.path.isfile(fp)):
        centerpoint, interval, xp, yp, a, otherdata = get_points(fp, None)
        filedat.append([fp, xp, yp, a, interval, otherdata]) 
    elif (os.path.isdir(fp)):
        # from stackoverflow lol
        logs = [f for f in listdir(fp) if (isfile(join(fp, f)) and f.endswith(".log"))]
        centerpoint = None
        for f in logs:
            print("reading " + join(fp, f))
            centerpoint, interval, xp, yp, a, otherdata = get_points(join(fp, f), centerpoint)
            if (centerpoint == None or len(xp) == 0):
                print("Error reading file " + str(f))
            else: 
                filedat.append([f, xp, yp, a, interval, otherdata]) 
    else:
        print("ERROR: NOT A VALID FILE OR DIRECTORY!")
        sys.exit(-1)
    
    fig = plt.figure()
    ax = fig.subplots()
   
    def pltcur():
        global current_file
        global cb
        ax.clear()
        ax.set_title(filedat[current_file][0])
        if (len(sys.argv) > 2):
            if (sys.argv[2] == 'e'):
                xa, ya, inter = plottable(filedat[current_file][4], filedat[current_file][5]['AccelX'], filedat[current_file][5]['AccelY']) 
                s = ax.scatter(ya, xa, c=inter)
                fig.colorbar(s)
            elif (sys.argv[2] == 'a'):
                for a in sys.argv[3:]:
                    p1 = plottable(filedat[current_file][4], filedat[current_file][4], filedat[current_file][5][a])
                    ax.plot(p1[0], p1[1])
            else:
                ax.plot(filedat[current_file][1], filedat[current_file][2])
        else:
            xa, ya, inter = plottable(filedat[current_file][4], filedat[current_file][5]['Latitude'], filedat[current_file][5]['Longitude']) 
            s = ax.scatter(ya, xa, c=inter)
            fig.colorbar(s) 
        plt.gca().set_aspect('equal')
        fig.canvas.draw()
     
    def next(val):
        global current_file
        current_file += 1
        if current_file == len(filedat):
            current_file = 0
        pltcur()
    
    def prev(val):
        global current_file
        current_file -= 1 
        if current_file == -1:
            current_file += len(filedat)
        pltcur()
    
    bnext = Button(plt.axes([0.0, 0.8, 0.1, 0.1]), 'Next')
    bprev = Button(plt.axes([0.0, 0.6, 0.1, 0.1]), 'Prev')
    

    bnext.on_clicked(next)
    bprev.on_clicked(prev)
   
    pltcur()
     
    plt.gca().set_aspect('equal')
    plt.show()