import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons
import sys, math, os

from os import listdir
from os.path import isfile, join

def get_points(fp : str, centerpoint) -> tuple[tuple[float, float], list[float], list[float], list[tuple[float, float, float]]]:
    xvals = []
    yvals = []
    with open(fp) as f:
        channels = f.readline().split(",")
        try:
            Lat_index = next(i for i,d in enumerate(channels) if d.startswith("\"Latitude"))
            Lon_index = next(i for i,d in enumerate(channels) if d.startswith("\"Longitude"))
            ax_index = next(i for i,d in enumerate(channels) if d.startswith("\"AccelX"))
            ay_index = next(i for i,d in enumerate(channels) if d.startswith("\"AccelY"))
            az_index = next(i for i,d in enumerate(channels) if d.startswith("\"AccelZ"))
        except:
            return None, 0, 0, None 
        
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

        accel_x = []
        accel_y = []
        accel_z = []
        while(1):
            line = f.readline()
            if line == '': break
            data = line.split(",")

            if len(data) > 100:
                if data[Lat_index] != '':
                    lat_x = (float(data[Lat_index]) - centerpoint[0]) * m_per_deg_lat
                    lon_x = (float(data[Lon_index]) - centerpoint[1]) * m_per_deg_lon

                
                    yvals.append(lat_x)
                    xvals.append(lon_x)
                if data[ax_index] != '':
                    ax = float(data[ax_index])
                    ay = float(data[ay_index])
                    az = float(data[az_index])
                    
                    accel_x.append(-0.685 * ay + 0.729 * az)
                    accel_y.append(-ax)
                    accel_z.append(-0.685 * az + -0.729 * ay)
        
    return (centerpoint, xvals, yvals, (accel_x, accel_y, accel_z))


current_file = 1

if __name__ == '__main__':
    fp = sys.argv[1]
    filedat = []
    if (os.path.isfile(fp)):
        centerpoint, xp, yp, a = get_points(fp, None)
        filedat.append([fp, xp, yp, a]) 
    elif (os.path.isdir(fp)):
        # from stackoverflow lol
        logs = [f for f in listdir(fp) if (isfile(join(fp, f)) and f.endswith(".log"))]
        centerpoint = None
        for f in logs:
            print("reading " + join(fp, f))
            centerpoint, xp, yp, a = get_points(join(fp, f), centerpoint)
            if (centerpoint == None or len(xp) == 0):
                print("Error reading file " + str(f))
            else: 
                filedat.append([f, xp, yp, a]) 
    else:
        print("ERROR: NOT A VALID FILE OR DIRECTORY!")
        sys.exit(-1)
    
    fig = plt.figure()
    ax = fig.subplots()
    
    def pltcur():
        global current_file
        print(current_file)
        ax.clear()
        ax.set_title(filedat[current_file][0])
        if (len(sys.argv) > 2):
            if (sys.argv[2] == 'e'): 
                ax.scatter(filedat[current_file][3][0],filedat[current_file][3][1])
            else:
                ax.plot(filedat[current_file][1],filedat[current_file][2])
        else:
            ax.plot(filedat[current_file][1],filedat[current_file][2])
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
    
    plt.gca().set_aspect('equal')
    plt.show()