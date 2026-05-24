import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons, Cursor
import math, os, sys, multiprocessing
import dearpygui.dearpygui as dpg
from scipy.signal import savgol_filter 
from os import listdir
from os.path import isfile, join
from threading import Thread



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
            return None, None, 0, 0, None, None 
        
        headers = list(map(lambda x : x.split("\"")[1], channels))
        data = f.readline().split(",")
        #print(data[Lat_index])
        while(data[Lat_index] == '' or data[Lat_index] == '0.0'):
            data = f.readline().split(",")
            if (len(data) == 1): 
                return None, None, 0, 0, None, None 
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
        gpsglast = 0
        gpstlast = 0
        otherdata["PosX"] = []
        otherdata["PosY"] = []
        otherdata['gpsG'] = []
        theta = -56.28 * math.pi / 180.0
        j = 0
        while(1):
            line = f.readline()
            if line == '': break
            data = line.split(",")
            
            j += 1
            
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
                        
                        #g2 = otherdata['Speed'] * (1.0/3.6)
                        #otherdata['gpsG'].append(((g2 - gpsglast) / ((gpstlast - interval) * 9.81 * 0.001)))
                        #gpsglast = g2
                        #gpstlast = interval
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


class plotset:
    def getposofinterval(this, xint):
        if xint < 0 or xint >= this.filedat[this.current_file][4][-1]:
            return None, None
        i = 0
        while this.filedat[this.current_file][4][i] < xint:
            i += 1
        while math.isnan(this.filedat[this.current_file][5]['PosX'][i]):
            i += 1 
        
        return (this.filedat[this.current_file][5]['PosX'][i], this.filedat[this.current_file][5]['PosY'][i]) 

    def mouse_move(this, event):
        x, y, a = event.xdata, event.ydata, event.inaxes 
        if (a == this.plot):
            xp, yp = this.getposofinterval(x)
            
            if this.mouse_hover_point is None:
                this.mouse_hover_point = this.line.scatter([0], [0], color='red')
            if xp is not None:
                this.mouse_hover_point.set_offsets([xp, yp])
            
            this.fig.canvas.draw()
            
    def pltcur(this):
        tf = this.filedat[this.current_file]
        this.plot.clear()
        this.plot.set_title(tf[0])
        
        this.line.clear() 
        this.line.plot(tf[1], tf[2])
        this.line.axis('equal')

        if (this.type != None):
            if (this.type == 'e'):
                xa, ya, inter = plottable(tf[4], tf[5]['AccelX'], tf[5]['AccelY']) 
                s = this.plot.scatter(savgol_filter(ya, window_length=20, polyorder=6), savgol_filter(xa, window_length=20, polyorder=6), c=inter)
                this.fig.colorbar(s)
            elif (this.type == 'a'):
                for a in this.args:
                    if (a not in tf[5]):
                        continue
                    p1 = plottable(tf[4], tf[4], tf[5][a])
                    filtered = this.plot.plot(p1[0], savgol_filter(x=p1[1], window_length=20, polyorder=6), label=a)
                    this.plot.scatter(p1[0], p1[1], label=a + "_raw", marker='x', color=filtered[0].get_color())
            elif (this.type == 's'):
                xa, ya, inter = plottable(tf[4], tf[5]['AccelX'], tf[5]['ShockPotLR']) 
                this.plot.scatter(xa, ya, c='blue')
                xa, ya, inter = plottable(tf[4], tf[5]['AccelX'], tf[5]['ShockPotsRR']) 
                this.plot.scatter(xa, ya, c='red')
                xa, ya, inter = plottable(tf[4], tf[5]['AccelX'], tf[5]['ShockPotLF']) 
                this.plot.scatter(xa, ya, c='red')
        this.plot.legend()
        this.fig.canvas.draw()
     
    def next(this, val):
        this.mouse_hover_point = None
        this.current_file += 1
        if this.current_file == len(this.filedat):
            this.current_file = 0
        this.pltcur()
    
    def prev(this, val):
        this.mouse_hover_point = None
        this.current_file -= 1 
        if this.current_file == -1:
            this.current_file += len(this.filedat)
        this.pltcur()


    def __init__(this, fdat, type, args):
        this.current_file = 0
        this.mouse_hover_point = None
        this.line = None
        this.plot = None
        this.filedat = fdat
        this.type = type
        this.args = args
        
        if type == 'c':
            for i in this.filedat[0][5].keys():
                print(i)
            sys.exit(0)
        
        this.fig, ax = plt.subplots(1, 2)
        
        this.line = ax[0]
        this.plot = ax[1]
        
        bnext = Button(plt.axes([0.0, 0.8, 0.1, 0.1]), 'Next')
        bprev = Button(plt.axes([0.0, 0.6, 0.1, 0.1]), 'Prev')
        if (this.type == 'a'):
            plt.connect('motion_notify_event', this.mouse_move)

        bnext.on_clicked(this.next)
        bprev.on_clicked(this.prev)
    
        this.pltcur()
        
        plt.gca().set_aspect('equal')
        plt.show()

def getfdatfrompath(fp):
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
        return []
    return filedat

def selectcb(sender, app_data, user_data):
    global selected
    if app_data:
        selected.append(user_data)
    else:
        selected.remove(user_data)

def buildselector(keys):
    for tag in dpg.get_item_children('buttontab')[1]:
        dpg.delete_item(tag)
    for i, k in enumerate(keys):
        with dpg.table_row(parent='buttontab', tag=f'{k}'):
            dpg.add_checkbox(label=k, callback=selectcb, user_data=k)

def dircb(sender, app_data):
    global fdat
    global loading
    dpg.show_item(loading)
    dpg.render_dearpygui_frame()
    fdat = getfdatfrompath(app_data['file_path_name'])
    dpg.hide_item(loading)
    global selector
    selector = fdat[0][5].keys()

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        plotset(getfdatfrompath(sys.argv[1]), sys.argv[2], args=sys.argv[3:])
        sys.exit()
    
    global loading
    global selector
    global selected
    global fdat
    selector = None
    selected = []
    dpg.create_context()
    
    with dpg.font_registry():
        try:
            default_font = dpg.add_font("C:/WINDOWS/FONTS/BAHNSCHRIFT.TTF", 18)
            header_font =  dpg.add_font("C:/WINDOWS/FONTS/BAHNSCHRIFT.TTF", 25)
            title_font =   dpg.add_font("C:/WINDOWS/FONTS/BAHNSCHRIFT.TTF", 45)
        except:
            print('no banchrift')
            sys.exit(0)
    dpg.bind_font(default_font)
    
    dialog0, dialog1 = None, None
    dpg.bind_font(default_font)
    with dpg.file_dialog(directory_selector=True, show=False, callback=dircb, tag="dir_dialog_id", cancel_callback=None, width=600 ,height=400) as d0:
        dialog0 = d0
        pass
    with dpg.file_dialog(directory_selector=False, show=False, callback=dircb, tag="file_dialog_id", cancel_callback=None, width=600 ,height=400) as d1:
        dialog1 = d1
        dpg.add_file_extension(".log", color=(150, 255, 150, 255))

    with dpg.window(label="csvp") as window:
        dpg.bind_font(header_font)
        dpg.add_button(label="Directory Selector", callback=lambda: dpg.show_item("dir_dialog_id"))
        dpg.add_button(label="File Selector",      callback=lambda: dpg.show_item("file_dialog_id"))
        dpg.add_button(label='plot', callback=lambda : multiprocessing.Process(None, plotset, args=(fdat, 'a', selected)).start())
        loading = dpg.add_text('Loading...', show=False)
        
        tab = None
        with dpg.table(header_row=True, row_background=True, tag='buttontab') as _b:
            dpg.add_table_column(label='Channels')
            tab = _b
        dpg.bind_item_font(tab, default_font)
        dpg.bind_item_font(dialog0, default_font)
        dpg.bind_item_font(dialog1, default_font)
    
    dpg.create_viewport(title='csvp', max_width=700, min_height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(window, True)
    
    while dpg.is_dearpygui_running():
        if selector is not None:
            buildselector(selector)
            selector = None
        dpg.render_dearpygui_frame()
