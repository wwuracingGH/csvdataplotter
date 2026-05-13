import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons, Cursor
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
                return None 
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
        
        otherdata["PosX"] = []
        otherdata["PosY"] = []
        theta = -47.8 * math.pi / 180.0
        while(1):
            line = f.readline()
            if line == '': break
            data = line.split(",")

            for i,d in enumerate(data):
                if d == '':
                    fl = float('nan')
                else:
                    try:
                        fl = float(d)
                    except:
                        fl = float('nan')
                otherdata[headers[i]].append(fl)
             
            otherdata["PosX"].append(float('nan'))
            otherdata["PosY"].append(float('nan'))
            if len(data) > 100:
                if data[Lat_index] != '':
                    try:
                        lat_x = (float(data[Lat_index]) - centerpoint[0]) * m_per_deg_lat
                        lon_x = (float(data[Lon_index]) - centerpoint[1]) * m_per_deg_lon 
                        
                        otherdata["PosX"][-1] = lon_x
                        otherdata["PosY"][-1] = lat_x
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
mouse_hover_point = None
line = None
plot = None
filedat = []

def getposofinterval(xint):
    if xint < 0 or xint >= filedat[current_file][4][-1]:
        return None, None
    i = 0
    while filedat[current_file][4][i] < xint:
        i += 1
    while math.isnan(filedat[current_file][5]['PosX'][i]):
        i += 1 
    
    return (filedat[current_file][5]['PosX'][i], filedat[current_file][5]['PosY'][i]) 

def mouse_move(event):
    global mouse_hover_point
    x, y, a = event.xdata, event.ydata, event.inaxes 
    if (a == plot):
        xp, yp = getposofinterval(x)
        
        if mouse_hover_point is None:
            mouse_hover_point = line.scatter([0], [0], color='red')
        if xp is not None:
            mouse_hover_point.set_offsets([xp, yp])
         
        fig.canvas.draw()
        
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
    
    if sys.argv[2] == 'c':
        for i in filedat[0][5].keys():
            print(i)
        sys.exit(0)
     
    fig, ax = plt.subplots(1, 2)
     
    line = ax[0]
    plot = ax[1]
    
    def pltcur():
        global current_file
        global cb
        plot.clear()
        plot.set_title(filedat[current_file][0])
        
        line.clear() 
        line.plot(filedat[current_file][1], filedat[current_file][2])
        line.axis('equal')
        if (len(sys.argv) > 2):
            if (sys.argv[2] == 'e'):
                xa, ya, inter = plottable(filedat[current_file][4], filedat[current_file][5]['AccelX'], filedat[current_file][5]['AccelY']) 
                s = plot.scatter(ya, xa, c=inter)
                fig.colorbar(s)
            elif (sys.argv[2] == 'a'):
                for a in sys.argv[3:]:
                    if (a not in filedat[current_file][5]):
                        continue
                    p1 = plottable(filedat[current_file][4], filedat[current_file][4], filedat[current_file][5][a])
                    plot.plot(p1[0], p1[1])
            elif (sys.argv[2] == 's'):
                xa, ya, inter = plottable(filedat[current_file][4], filedat[current_file][5]['AccelX'], filedat[current_file][5]['ShockPotLR']) 
                plot.scatter(xa, ya, c='blue')
                xa, ya, inter = plottable(filedat[current_file][4], filedat[current_file][5]['AccelX'], filedat[current_file][5]['ShockPotsRR']) 
                plot.scatter(xa, ya, c='red')
                xa, ya, inter = plottable(filedat[current_file][4], filedat[current_file][5]['AccelX'], filedat[current_file][5]['ShockPotLF']) 
                plot.scatter(xa, ya, c='red')
        cursor = Cursor(plot, color='green', linewidth=2)
        fig.canvas.draw()
     
    def next(val):
        global current_file
        global mouse_hover_point
        mouse_hover_point = None
        current_file += 1
        if current_file == len(filedat):
            current_file = 0
        pltcur()
    
    def prev(val):
        global current_file
        global mouse_hover_point
        mouse_hover_point = None
        current_file -= 1 
        if current_file == -1:
            current_file += len(filedat)
        pltcur()
    
    bnext = Button(plt.axes([0.0, 0.8, 0.1, 0.1]), 'Next')
    bprev = Button(plt.axes([0.0, 0.6, 0.1, 0.1]), 'Prev')
    plt.connect('motion_notify_event', mouse_move)

    bnext.on_clicked(next)
    bprev.on_clicked(prev)
   
    pltcur()
     
    plt.gca().set_aspect('equal')
    plt.show()