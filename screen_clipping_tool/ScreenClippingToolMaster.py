import sys, os, signal, time, threading, PIL.Image, ctypes, datetime, gc, pytesseract, imageio, numpy, io, win32clipboard
import keyboard as kb
import json
import subprocess
import win32con
from infi.systray import SysTrayIcon 
from tkinter import *
from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter import messagebox, ttk
from tkinter.colorchooser import askcolor
from PIL import ImageGrab, Image, ImageTk
from threading import Thread, Timer
#from screeninfo import get_monitors
from ctypes import windll, Structure, c_ulong, byref
#from desktopmagic.screengrab_win32 import getDisplayRects, saveScreenToBmp, saveRectToBmp, getScreenAsImage, getRectAsImage, getDisplaysAsImages
#from pynput import keyboard
import clr
from shutil import rmtree
from GlobalHotKeys_e import GlobalHotKeys

#***************** import dll *************. 
filename = os.path.join(os.getcwd(), 'screeninfo.dll')
print(filename)


#add referance 
clr.AddReference(filename)
from screeninfo_c import ScreenInfo
get_monitors = ScreenInfo.GetMonitors
monitor_from_point = ScreenInfo.MonitorFromPoint
get_rect_as_image = ScreenInfo.GetRectAsImage



#***************** Set process DPI aware for all monitors *************. 
awareness = ctypes.c_int()
errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
success = ctypes.windll.user32.SetProcessDPIAware()

gc.enable()
print(*sys.argv) # path name to file (used for the reload script button)
print(os.getcwd())

def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)



def explore(path):                                                      # https://stackoverflow.com/a/50965628/13994936
    FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
    path = os.path.normpath(path)

    if os.path.isdir(path):
        subprocess.run([FILEBROWSER_PATH, path])
    elif os.path.isfile(path):
        subprocess.run([FILEBROWSER_PATH, '/select,', path])

class PrintLogger(): # create file like object
    DEFAULT_OUT = sys.__stdout__
    console = None
    textbox = None

    @classmethod
    def __init__(cls, textbox): # pass reference to text widget
        cls.textbox = textbox # keep ref

    @classmethod
    def write(cls, text):
        try:
            cls.textbox.insert(END, text)   # write text to textbox
            cls.textbox.yview(END)          # move view as text gets added
        except Exception as ex:
            cls.resetconsole()

    @classmethod
    def flush(cls): # needed for file like object
        pass

    @classmethod
    def resetconsole(cls):
        sys.stdout = cls.DEFAULT_OUT
        try: cls.console.destroy()
        except:pass
        cls.console = None
        cls.textbox = None
        
    @classmethod
    def consolewin(cls, parent, fontsize = 12):
        def commands(event):
            try:exec(event.widget.get('end - 1 lines linestart', 'end - 1 lines lineend'))
            except Exception as e:print(e)

        cls.resetconsole()
        cls.console = Toplevel(parent)
        cls.console.title("Console")
        cls.console.protocol("WM_DELETE_WINDOW", cls.resetconsole)
        console_output_widget = Text(cls.console,bg= "#0C0C0C", fg = "#CCCCCC", selectbackground="white", insertbackground='white', font=("consolas", fontsize, ))
        scrollb = Scrollbar(cls.console, bg = "#0C0C0C", command=console_output_widget.yview)
        console_output_widget['yscrollcommand'] = scrollb.set
        scrollb.pack(side='right', fill = Y)
        console_output_widget.pack(expand = True, fill = BOTH)
        console_output_widget.bind("<Return>", commands)
        console_output = PrintLogger(console_output_widget)
        sys.stdout = console_output


class CreateToolTip(object):

    def __init__(self, widget, text='widget info'):
        self.waittime = 100     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tw = Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        self.tw.attributes("-topmost", True)
        self.tw.lift()
        label = Label(self.tw, text=self.text, justify='left',background="#ffffff", relief='solid', borderwidth=1,wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()


class cooldown:
    def __init__(self, timeout):
        self.timeout = timeout
        self.calltime = time.time() - timeout
        self.func = None
        self.obj = None
    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        now = time.time()
        if now - self.calltime >= self.timeout:
            self.calltime = now
            if self.obj is None:
                return self.func.__call__(*args, **kwargs)
            else:
                return self.func.__get__(self.obj, self.objtype)(*args, **kwargs)
    def __get__(self, obj, objtype):
        self.obj = obj
        self.objtype = objtype
        return self
    @property
    def remaining(self):
        now = time.time()
        delta = now - self.calltime
        if delta >= self.timeout:
            return 0
        return self.timeout - delta
    @remaining.setter
    def remaining(self, value):
        self.calltime = time.time() - self.timeout + value




class Create_gif:
    
    def __init__(self, open_on_save, border_color, monitor, x1, y1, x2, y2):
        self.adjust_vals = {"ghost border" : 10, "title bar" : 33, "trial n err" : 3}
        self.gif = []               # Keep all the pictures taken in gif mode
        self.record_on = False      # Variable that tells the gif mode when to stop taking pictures
        self.threads = []           # Keep track of used threads to join back later
        self.open_on_save = open_on_save
        self.border_color = border_color
        self.stop_drag = 0
        self.hide_border_on_drag = IntVar(value = 1)
        self.hide_border_always = IntVar(value = 0)
        self.hide_border_never  = IntVar(value = 0)
        self.center_mouse_always = IntVar(value = 0)
        self.center_mouse_never = IntVar(value = 1)
        self.center_mouse_while_off = IntVar(value = 0)
        self.gif_bounds = [i for i in [monitor.X + x1, monitor.Y + y1, monitor.X + x2, monitor.Y + y2]]
        print(self.gif_bounds)

        self.gif_area = Toplevel(root)
        self.gif_area.overrideredirect(1)
        self.gif_area.title("GifWindow")
        self.gif_area.minsize(x2-x1, y2-y1)
        self.gif_area.resizable(0,0)
        self.gif_area.attributes("-transparent", "blue")
        self.gif_area.attributes('-topmost', 'true')
        self.gif_area.geometry("{}x{}+{}+{}".format(x2-x1+2, y2-y1+2, x1 + monitor.X, y1 + monitor.Y))

        self.canvas = Canvas(self.gif_area, bg="grey11", highlightthickness = 0)
        self.canvas.pack(expand = True, fill = BOTH)
        self.canvas.create_rectangle(0, 0, x2-x1+1, y2-y1+1, outline= self.border_color, width=1, fill="blue", tag = "gif_area")

        self.gif_area.protocol("WM_DELETE_WINDOW", self.exit_gif)
        self.gif_area.bind('<Configure>', self.moving_window)

        buttons = Toplevel(self.gif_area)
        buttons.title("GifControls")
        buttons.resizable(0,0)                                                              # Cant resize
        buttons.attributes("-topmost", True)                                                # Always on top
        mousex, mousey = root.winfo_pointerxy()                                             # Get mouse xy
        buttons.geometry(f"+{mousex - 25}+{mousey - 16}")                        # Spawn the window on your mouse

        

        buttons.protocol("WM_DELETE_WINDOW", self.exit_gif) 
        #***************** Make buttons *************. 
        record_button =      Button(buttons, text = "Start", command = self.record_thread, width = 10)
        stop_record_button = Button(buttons, text = "Stop",  command = self.stop_gif,      width = 10)
        save_record_button = Button(buttons, text = "Save",  command = self.save_gif,      width = 10)

        record_button.grid      (column = 0, row = 0,  sticky = EW)
        stop_record_button.grid (column = 1, row = 0,  sticky = EW)
        save_record_button.grid (column = 2, row = 0,  sticky = EW)


        xypos_label =           Label(buttons, text = "XY Position  ")
        hide_border_on_drag =   Label(buttons, text = "HideBorderOnDrag:")
        center_on_drag =        Label(buttons, text = "CenterMouseOnDrag:")

        xypos_label.grid         (column = 0, row = 1,  sticky = EW)
        hide_border_on_drag.grid (column = 0, row = 3,  sticky = EW)
        center_on_drag.grid      (column = 1, row = 3,  sticky = EW)



        xyposition_of_main = ttk.Combobox(buttons, width = 9, values = [(i, x//2) for i, x in enumerate(numpy.arange(0, 4096))])
        xyposition_of_main.grid (column = 0, row = 2,  sticky = EW)



        self.hide_border_on_drag_if_running = Checkbutton(buttons, text = "WhileRunning",    variable = self.hide_border_on_drag, command = self.while_on_hide_border)
        self.hide_border_on_drag_always =     Checkbutton(buttons, text = "Always"      ,    variable = self.hide_border_always, command = self.always_hide_border)
        self.hide_border_on_drag_never =      Checkbutton(buttons, text =  "Never"      ,     variable = self.hide_border_never, command = self.never_hide_border)

        self.center_mouse_while_not_running = Checkbutton(buttons, text = "WhileNotRunning", variable = self.center_mouse_while_off, command = self.while_not_on_center)
        self.center_mouse_on_box_always =     Checkbutton(buttons, text = "Always",          variable = self.center_mouse_always, command = self.always_center_mouse)
        self.center_mouse_on_box_never =      Checkbutton(buttons, text = "Never",           variable = self.center_mouse_never, command = self.never_center_mouse)
        

        self.hide_border_on_drag_if_running.grid (column = 0, row = 4,  sticky = W)
        self.hide_border_on_drag_always.grid     (column = 0, row = 5,  sticky = W)
        self.hide_border_on_drag_never.grid      (column = 0, row = 6,  sticky = W)

        self.center_mouse_while_not_running.grid (column = 1, row = 4,  sticky = W)
        self.center_mouse_on_box_always.grid     (column = 1, row = 5,  sticky = W)
        self.center_mouse_on_box_never.grid      (column = 1, row = 6,  sticky = W)
        


        drag_canvas = Canvas(buttons, width = 0, height = 0, bg = "grey")
        drag_canvas.grid(column = 1, row = 1, columnspan = 2, rowspan = 2, sticky = NSEW)

        drag_canvas.bind("<Button-1>",  lambda event, win = self.gif_area :  self.start_pos(event, win))
        drag_canvas.bind("<B1-Motion>", lambda event, win = self.gif_area :  self.move(event, win))

        xyposition_of_main.bind("<Return>", self.on_enter)
        xyposition_of_main.bind("<<ComboboxSelected>>", self.on_enter)

    def while_on_hide_border(self):  
        self.hide_border_on_drag_always.deselect()
        self.hide_border_on_drag_never.deselect()


    def always_hide_border(self):
        self.hide_border_on_drag_if_running.deselect()
        self.hide_border_on_drag_never.deselect()


    def never_hide_border(self):
        self.hide_border_on_drag_always.deselect()
        self.hide_border_on_drag_if_running.deselect()


    def while_not_on_center(self):
        self.center_mouse_on_box_always.deselect()
        self.center_mouse_on_box_never.deselect()


    def always_center_mouse(self):
        self.center_mouse_while_not_running.deselect()
        self.center_mouse_on_box_never.deselect()


    def never_center_mouse(self):
        self.center_mouse_on_box_always.deselect()
        self.center_mouse_while_not_running.deselect()


    def start_pos(self, event, win):
        self.tmpx = event.x
        self.tmpy = event.y

        if self.center_mouse_always.get() or (not self.record_on and self.center_mouse_while_off.get()) and not self.center_mouse_never.get():
            win.geometry("+%s+%s" % (root.winfo_pointerx() - win.winfo_width()//2, root.winfo_pointery() - win.winfo_height()//2))
        event.widget.focus_set()


    def move(self, event, win):
        win.geometry("+%s+%s" % (event.x - self.tmpx + win.winfo_x() , event.y - self.tmpy + win.winfo_y()))
        self.tmpx = event.x
        self.tmpy = event.y

    #***************** Run the record function in seperate thread to ensure it doesn't block main program *************. 
    def record_thread(self):
        if not self.record_on:
            if len(self.gif_bounds) == 4:
                a = Thread(target = self.record, args = ())
                self.threads.append(a)
                a.start()
    
    #***************** Take rapid screenshots of selected area and stick them into an array *************. 
    def record(self):
        self.record_on = True

        while self.record_on == True:      
            img = Image.open(get_rect_as_image(self.gif_bounds[0], self.gif_bounds[1], self.gif_bounds[2], self.gif_bounds[3], os.path.join(os.getcwd(), f'screenshots\\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")}.png'))) # take image
            #rct = (self.gif_bounds[0], self.gif_bounds[1], self.gif_bounds[2], self.gif_bounds[3])#rct = (self.gif_bounds[0] + x1, self.gif_bounds[1] + y1, self.gif_bounds[2] + x2, self.gif_bounds[3] + y2)
            #img = getRectAsImage(rct) #x1, y1, x2, y2 = self.gif_bounds[0], self.gif_bounds[1], self.gif_bounds[2], self.gif_bounds[0]
            self.gif.append(img)
            del img
            print('image taken at', self.gif_bounds[0], self.gif_bounds[1], self.gif_bounds[2], self.gif_bounds[3])
            time.sleep(0.05)
        gc.collect()

    #***************** Stop taking pictures, save the gif *************. 
    def stop_gif(self):
        self.record_on = False 

        for i in self.threads.copy():
            i.join()
            self.threads.remove(i)
        gc.collect()

    #***************** Save gif *************. 
    def save_gif(self):
        self.record_on = False
        savename = datetime.datetime.now()
        savename = savename.strftime("%Y-%m-%d_%H-%M-%S.%f")
        f = asksaveasfile(initialfile = f"{savename}", mode='w', defaultextension=".gif", parent=root)
        if f is None: return
        print(f.name)

        try:
            with imageio.get_writer(f"{f.name}", mode='I') as writer:
                for i in self.gif.copy(): 
                    writer.append_data(numpy.array(i))    
                    del self.gif[self.gif.index(i)]
            if self.open_on_save: explore(f.name)
        except KeyError:
            messagebox.showerror(title="", message="The filetype {} is most likely unsupported".format(format), parent=root)
            print(KeyError)
        except Exception as e: 
            print(e)
            messagebox.showerror(title="", message=f"There was an error that was not a problem with the filetype please tell minnowo \n{e}", parent=root)

        for i in self.threads.copy():
            i.join()                # Clean up threads
            del self.threads[self.threads.index(i)]

        del f
        self.gif.clear()
        gc.collect()


    def exit_gif(self):
            self.gif_area.destroy()
            self.record_on = False
            self.gif.clear()
            gc.collect()


    def show_border(self):
        self.stop_drag = 0
        try: self.canvas.itemconfig("gif_area", outline = self.border_color) # if the window is destroyed before the 500 ms delay it throws an error 
        except:pass


    def moving_window(self, event):
        if (not self.stop_drag and self.hide_border_always.get()) or (self.record_on and self.hide_border_on_drag.get()):
            self.canvas.itemconfig("gif_area", outline = "")

        if self.stop_drag:
            root.after_cancel(self.stop_drag)

        winx, winy = (self.gif_area.winfo_x(), self.gif_area.winfo_y())
        self.gif_bounds = [winx + 1, winy + 1, winx + self.gif_area.winfo_width() - 1, winy + self.gif_area.winfo_height() - 1] # the +- 1 make it take pictures inside the box
        self.stop_drag = root.after(500, self.show_border)


    def on_enter(self, event):
        try:
            xy = [int(i.strip()) for i in event.widget.get().split(" ")]
            self.gif_area.geometry(f"+{xy[0]-1}+{xy[1]-1}") # want to move based on the picture location not the border of the rectangle
        except:
            return

 
class Settings:
    
    def __init__(self, SnippingClass):
        self.snippingclass = SnippingClass
        self.auto_copy_image = SnippingClass.auto_copy_image
        self.auto_hide_clip = SnippingClass.auto_hide_clip
        self.snapshot = SnippingClass.snapshot
        self.delayed_clip = SnippingClass.delayed_clip
        self.multi_clip = SnippingClass.multi_clip
        self.cursor_lines = SnippingClass.cursor_lines
        self.win32clipboard = SnippingClass.win32clipboard
        self.open_on_save = SnippingClass.open_on_save
        self.hotkey_visual_in_settings = SnippingClass.hotkey_visual_in_settings
        self.border_thiccness = SnippingClass.border_thiccness
        self.scale_percent = SnippingClass.scale_percent
        self.multiplyer = SnippingClass.multiplyer
        self.default_alpha = SnippingClass.default_alpha
        self.border_color = SnippingClass.border_color
        self.clip_hotkey = SnippingClass.clip_hotkey
        self.gif_hotkey = SnippingClass.gif_hotkey

        self.save_file_name = "settings.json"

        self.settings_window_root = Toplevel(root)
        self.settings_window_root.title("Settings")
        self.settings_window_root.attributes("-topmost", True)
        self.settings_window_root.lift()
        self.settings_window_root.resizable(0,0)
        
        #***************** Buttons *************. 
        save_changes =                   Button(self.settings_window_root, text =  "Save Changes",                        command = self.save_settings)
        reset_changes =                  Button(self.settings_window_root, text =  "Reset Changes",                       )#command = self.settings_window)
        restore_deault_button =          Button(self.settings_window_root, text =  "Restore Default",                     command = self.restore_default)
        show_console_button =            Button(self.settings_window_root, text =  "ShowConsole",                         command = self.show_console)
        choose_border_color =            Button(self.settings_window_root, text =  "Border/LineColor",                    command = self.change_border)
        open_image_button =              Button(self.settings_window_root, text =  "OpenImage",                           command = self.open_image) 
        open_from_clipboard_button =     Button(self.settings_window_root, text =  "OpenFromClipboard",                   command = self.clip_from_clipboard) 
        create_save_file_button =        Button(self.settings_window_root, text =  "Create Save",                         command = self.create_save_file)

        self.auto_copy_clip_button =     Button(self.settings_window_root, text = f"AutoCopyClip {self.auto_copy_image}", command = self.change_toggle_auto_copy)
        self.auto_hide_clip_button =     Button(self.settings_window_root, text = f"AutoHideClip {self.auto_hide_clip}",  command = self.change_toggle_auto_hide)
        self.snapshot_mode_button =      Button(self.settings_window_root, text = f"SnapShotMode {self.snapshot}",        command = self.change_snapshot)
        self.delay_clip_mode_button =    Button(self.settings_window_root, text = f"DelayMode {self.delayed_clip}",       command = self.change_delay_clip)
        self.multi_clip_mode_button =    Button(self.settings_window_root, text = f"MultiMode {self.multi_clip}",         command = self.change_multi_mode)
        self.cursor_guidelines_button =  Button(self.settings_window_root, text = f"CursorLines {self.cursor_lines}",     command = self.change_lines)
        self.use_win32_clipboard_copy =  Button(self.settings_window_root, text = f"Win32clipboard {self.win32clipboard}",command = self.change_win32_clip)
        self.open_on_save_button =       Button(self.settings_window_root, text = f"AutoOpenOnSave {self.open_on_save}",  command = self.change_open_on_save)

        # row 5 is for modes
        self.snapshot_mode_button.grid       (column = 0, row = 5, sticky = EW)
        self.delay_clip_mode_button.grid     (column = 1, row = 5, sticky = EW)
        self.multi_clip_mode_button.grid     (column = 2, row = 5, sticky = EW)        
        self.use_win32_clipboard_copy.grid   (column = 3, row = 5, sticky = EW)

        # row 6 for auto features 
        self.auto_copy_clip_button.grid      (column = 0, row = 6, sticky = EW)
        self.auto_hide_clip_button.grid      (column = 1, row = 6, sticky = EW)
        self.open_on_save_button.grid        (column = 2, row = 6, sticky = EW)

        # row 7 for other
        self.cursor_guidelines_button.grid   (column = 0, row = 7, sticky = EW)
        choose_border_color.grid             (column = 1, row = 7, sticky = EW)
        open_image_button.grid               (column = 2, row = 7, sticky = EW)
        open_from_clipboard_button.grid      (column = 3, row = 7, sticky = EW)

        # row 8 for function buttons
        save_changes.grid               (column = 0, row = 8, sticky = EW)
        reset_changes.grid              (column = 1, row = 8, sticky = EW)
        restore_deault_button.grid      (column = 2, row = 8, sticky = EW)
        show_console_button.grid        (column = 3, row = 8, sticky = EW)
        create_save_file_button.grid    (column = 4, row = 8, sticky = EW)

        CreateToolTip(self.snapshot_mode_button,     "Snapshot Mode: \nFreezes your screen, allowing you to crop a current point in time")
        CreateToolTip(self.delay_clip_mode_button,   "Delayed Mode: \nTakes a screenshot and holds it in memory, upon the Clip Hotkey again display the screenshot allowing you to crop it")
        CreateToolTip(self.multi_clip_mode_button,   "Lets you clip with the same clipping window until you close it with Right Click")
        CreateToolTip(self.cursor_guidelines_button, "This toggles the visual pink lines when clipping")
        CreateToolTip(self.use_win32_clipboard_copy, "Copy clip using win32clipboard \nWhen set to 0 clip will be copied using Alt+PrntScreen and then cropped\n(win32clipboard is recommended)")
        CreateToolTip(self.auto_copy_clip_button,    "Automatically copies the clip to your clipboard")
        CreateToolTip(self.auto_hide_clip_button,    "Automatically hides the clip in your task bar to keep it out of the way")
        CreateToolTip(self.open_on_save_button,      "Automatically opens file explorer to the location of saved clips/gifs")
        CreateToolTip(choose_border_color,           "Select the color of the clip outline and the guidelines shown when making a clip")
        CreateToolTip(open_image_button,             "Open an image file and create a clip from it\n(transparent images will have the background be the border color)")
        CreateToolTip(open_from_clipboard_button,    "Create a clip from image byte data on clipboard if it exists")


        #***************** Labels *************. 
        hotkey_1_label =            Label(self.settings_window_root, text = "Clip Hotkey")
        hotkey_2_label =            Label(self.settings_window_root, text = "Gif Hotkey")
        border_thiccness_label =    Label(self.settings_window_root, text = "Clip Border Thickness")
        zoom_percent_label =        Label(self.settings_window_root, text = "Zoom Square Size")
        zoom_multiplyer_label =     Label(self.settings_window_root, text = "Zoom Multiplyer")

        hotkey_1_label.grid             (column = 0, row = 1, sticky = EW)
        hotkey_2_label.grid             (column = 0, row = 2, sticky = EW, pady = (0,10))
        border_thiccness_label.grid     (column = 0, row = 4, sticky = EW, pady = (0,10))
        zoom_percent_label.grid         (column = 0, row = 3, sticky = EW)
        zoom_multiplyer_label.grid      (column = 2, row = 3, sticky = EW)
   
        CreateToolTip(hotkey_1_label,           "Hotkey to make a clip")
        CreateToolTip(hotkey_2_label,           "Hotkey to make a gif")
        CreateToolTip(border_thiccness_label,   "Thickness of border around clip") 
        CreateToolTip(zoom_percent_label,       "Size of zoom box \nLower = Smaller \nHigher = Bigger \nAbove 1.25 can be lagy")
        CreateToolTip(zoom_multiplyer_label,    "How far in the zoom starts \nLower = More Zoomed \nHigher = Less Zoomed")


        #***************** ComboBox *************. 
        MODIFIERS = ["Windows", "Alt", "Ctrl", "Shift", "None"]
        KEYS = [chr(key_code) for key_code in (list (range(ord('A'), ord('Z') + 1)) + list(range(ord('0'), ord('9') + 1)) )] + [str(item)[3:] for item in win32con.__dict__ if item[:3] == 'VK_']  + list(GlobalHotKeys.PUNCTUATION_CHARACTERS)

        self.hotkey_1_modifyer_1 =   ttk.Combobox(self.settings_window_root,  values = MODIFIERS, width=12,  state='readonly')
        self.hotkey_1_modifyer_2 =   ttk.Combobox(self.settings_window_root,  values = MODIFIERS, width=12,  state='readonly')
        self.hotkey_1_modifyer_3 =   ttk.Combobox(self.settings_window_root,  values = MODIFIERS, width=12,  state='readonly')
        self.hotkey_1_key =          ttk.Combobox(self.settings_window_root,  values = KEYS,      width=12,  state='readonly')

        self.hotkey_2_modifyer_1 =   ttk.Combobox(self.settings_window_root,  values = MODIFIERS, width=12,  state='readonly')
        self.hotkey_2_modifyer_2 =   ttk.Combobox(self.settings_window_root,  values = MODIFIERS, width=12,  state='readonly')
        self.hotkey_2_modifyer_3 =   ttk.Combobox(self.settings_window_root,  values = MODIFIERS, width=12,  state='readonly')
        self.hotkey_2_key =          ttk.Combobox(self.settings_window_root,  values = KEYS,      width=12,  state='readonly')
        
        self.border_thiccness_combobox = ttk.Combobox(self.settings_window_root,  values = [i for i in range(0, 100)],                                        width=4,  state='readonly')
        self.zoom_percent_Combobox =     ttk.Combobox(self.settings_window_root,  values = [round(x, 3) for x in numpy.arange(0, 2, 0.01) if x >= 0.03],      width=5,  state='readonly')
        self.zoom_multiplyer_Combobox =  ttk.Combobox(self.settings_window_root,  values = [round(x, 3) for x in numpy.arange(0, 0.2, 0.01) if x >= 0.03],    width=5,  state='readonly')
        
        self.hotkey_1_modifyer_1.set         (self.hotkey_visual_in_settings["hotkey_1_modifyer_1"])
        self.hotkey_1_modifyer_2.set         (self.hotkey_visual_in_settings["hotkey_1_modifyer_2"])
        self.hotkey_1_modifyer_3.set         (self.hotkey_visual_in_settings["hotkey_1_modifyer_3"])
        self.hotkey_1_key.set                (self.hotkey_visual_in_settings["hotkey_1_key"])

        self.hotkey_2_modifyer_1.set         (self.hotkey_visual_in_settings["hotkey_2_modifyer_1"])
        self.hotkey_2_modifyer_2.set         (self.hotkey_visual_in_settings["hotkey_2_modifyer_2"])        
        self.hotkey_2_modifyer_3.set         (self.hotkey_visual_in_settings["hotkey_2_modifyer_3"])
        self.hotkey_2_key.set                (self.hotkey_visual_in_settings["hotkey_2_key"])

        self.border_thiccness_combobox.set   (self.border_thiccness)
        self.zoom_percent_Combobox.set       (self.scale_percent)
        self.zoom_multiplyer_Combobox.set    (self.multiplyer)

        self.hotkey_1_modifyer_1.grid        (column = 1, row = 1, sticky = EW)
        self.hotkey_1_modifyer_2.grid        (column = 2, row = 1, sticky = EW)
        self.hotkey_1_modifyer_3.grid        (column = 3, row = 1, sticky = EW)
        self.hotkey_1_key.grid               (column = 4, row = 1, sticky = EW)

        self.hotkey_2_modifyer_1.grid        (column = 1, row = 2, sticky = EW, pady = (0,10))
        self.hotkey_2_modifyer_2.grid        (column = 2, row = 2, sticky = EW, pady = (0,10))
        self.hotkey_2_modifyer_3.grid        (column = 3, row = 2, sticky = EW, pady = (0,10))
        self.hotkey_2_key.grid               (column = 4, row = 2, sticky = EW, pady = (0,10))

        self.zoom_percent_Combobox.grid      (column = 1, row = 3, sticky = EW)
        self.zoom_multiplyer_Combobox.grid   (column = 3, row = 3, sticky = EW)
        self.border_thiccness_combobox.grid  (column = 1, row = 4, sticky = EW, pady = (0,10))

        

        self.settings_window_root.update()
        xloc = (root.winfo_screenwidth() // 2) - (self.settings_window_root.winfo_width() // 2)  
        yloc = (root.winfo_screenheight() // 2) - (self.settings_window_root.winfo_height() // 2)
        print(xloc, yloc)
        self.settings_window_root.geometry(f"+{xloc}+{yloc}")
        

    def save_settings(self, *args):

            self.scale_percent = float(self.zoom_percent_Combobox.get())
            self.multiplyer = float(self.zoom_multiplyer_Combobox.get())
            self.border_thiccness = int(self.border_thiccness_combobox.get())

            
            #for key, value in VKS.items():
            #    print(key, value)

            hotkey1 = list( dict.fromkeys([i for i in [self.hotkey_1_modifyer_1.get(), self.hotkey_1_modifyer_2.get(), self.hotkey_1_modifyer_3.get(), self.hotkey_1_key.get()] if i != "None"]))
            hotkey2 = list( dict.fromkeys([i for i in [self.hotkey_2_modifyer_1.get(), self.hotkey_2_modifyer_2.get(), self.hotkey_2_modifyer_3.get(), self.hotkey_2_key.get()] if i != "None"]))

            

            if self.hotkey_visual_in_settings["current_hotkey_1"] != "+".join(hotkey1) or self.hotkey_visual_in_settings["current_hotkey_2"] != "+".join(hotkey2):
                self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : self.hotkey_1_modifyer_1.get(), "hotkey_1_modifyer_2" : self.hotkey_1_modifyer_2.get(), "hotkey_1_modifyer_3" : self.hotkey_1_modifyer_3.get(), "hotkey_1_key" : self.hotkey_1_key.get(), "current_hotkey_1" : "+".join(hotkey1),
                                                  "hotkey_2_modifyer_1" : self.hotkey_2_modifyer_1.get(), "hotkey_2_modifyer_2" : self.hotkey_2_modifyer_2.get(), "hotkey_2_modifyer_3" : self.hotkey_2_modifyer_3.get(), "hotkey_2_key" : self.hotkey_2_key.get(), "current_hotkey_2" : "+".join(hotkey2)}       
            
                self.save_file_name = "settings.tmp.json"
                self.create_save_file()
                self.save_file_name = "settings.json"
                if messagebox.askquestion(title = "", message = "The program requires a restart to change the hotkeys would you like to restart now?", parent = root) == "yes":
                    self.snippingclass.tray.restart_program(self.snippingclass.tray.sysTrayIcon)
                else:
                    messagebox.showinfo(title = "", message = "The settings will take place when the tool next opens", parent = root)
            else:
                self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : self.hotkey_1_modifyer_1.get(), "hotkey_1_modifyer_2" : self.hotkey_1_modifyer_2.get(), "hotkey_1_modifyer_3" : self.hotkey_1_modifyer_3.get(), "hotkey_1_key" : self.hotkey_1_key.get(), "current_hotkey_1" : "+".join(hotkey1),
                                              "hotkey_2_modifyer_1" : self.hotkey_2_modifyer_1.get(), "hotkey_2_modifyer_2" : self.hotkey_2_modifyer_2.get(), "hotkey_2_modifyer_3" : self.hotkey_2_modifyer_3.get(), "hotkey_2_key" : self.hotkey_2_key.get(), "current_hotkey_2" : "+".join(hotkey2)}       
            

            self.snippingclass.save_settings(self)

            



    def change_snapshot(self, *args):
        self.snapshot = 1 - self.snapshot # Toggle from 0 to 1 and 1 to 0
        if self.snapshot: 
            self.delayed_clip = 0
            self.default_alpha = 1
        else: self.default_alpha = 0.3
        print(f"snapshot mode set: {self.snapshot}")
        #SnippingClass.tray.update_hov_text(SnippingClass.tray.sysTrayIcon)
        self.snapshot_mode_button.config(text = f"SnapShotMode {self.snapshot}")
        self.delay_clip_mode_button.config(text = f"DelayMode {self.delayed_clip}")

    def change_delay_clip(self, *args):
        self.delayed_clip = 1 - self.delayed_clip # Toggle from 0 to 1 and 1 to 0
        if self.delayed_clip: 
            self.snapshot = 0
            self.default_alpha = 1
        else: self.default_alpha = 0.3
        print(f"delayed mode set: {self.delayed_clip}")
        #self.tray.update_hov_text(self.tray.sysTrayIcon)
        self.delay_clip_mode_button.config(text = f"DelayMode {self.delayed_clip}")
        self.snapshot_mode_button.config(text = f"SnapShotMode {self.snapshot}")

    def change_lines(self, *args):
        self.cursor_lines = 1 - self.cursor_lines # Toggle from 0 to 1 and 1 to 0
        print(f"cursor lines set: {self.cursor_lines}")
        self.cursor_guidelines_button.config(text = f"CursorLines {self.cursor_lines}")

    def ask_toggle_auto_hide(self):
        a = messagebox.askquestion(title = "", message = "would you like to enable autohide clips to keep them out of the way when clipping?", parent = root)
        if a == "yes": self.change_toggle_auto_hide()

    def change_multi_mode(self, *args):
        self.multi_clip = 1 - self.multi_clip # Toggle from 0 to 1 and 1 to 0
        print(f"multi clip mode set: {self.multi_clip}")
        #self.tray.update_hov_text(self.tray.sysTrayIcon)
        if self.multi_clip and not self.auto_hide_clip: root.after(0, self.ask_toggle_auto_hide)
        self.multi_clip_mode_button.config(text = f"MultiMode {self.multi_clip}")

    def change_win32_clip(self, *args):
        self.win32clipboard = 1 - self.win32clipboard # Toggle from 0 to 1 and 1 to 0
        print(f"win32clipboard set: {self.win32clipboard}")
        self.use_win32_clipboard_copy.config(text = f"Win32clipboard {self.win32clipboard}")
            
    def change_toggle_auto_copy(self, *args):
        self.auto_copy_image = 1 - self.auto_copy_image
        print(f"auto copy set : {self.auto_copy_image}")
        self.auto_copy_clip_button.config(text = f"AutoCopyClip {self.auto_copy_image}")

    def change_toggle_auto_hide(self, *args):
        self.auto_hide_clip = 1 - self.auto_hide_clip
        print(f"auto hide set : {self.auto_hide_clip}")
        self.auto_hide_clip_button.config(text = f"AutoHideClip {self.auto_hide_clip}")

    def change_open_on_save(self, *args):
        self.open_on_save = 1 - self.open_on_save
        print(f"open_on_save set : {self.open_on_save}")
        self.open_on_save_button.config(text = f"AutoOpenOnSave {self.open_on_save}")

    def show_console(self, *args):
        PrintLogger.consolewin(root)
        print("Created by Minnowo")
        print("Github: https://github.com/Minnowo")
        print("Discord: https://discord.gg/qznYCXz")


    def restore_default(self, *args):
        self.scale_percent = 0.35
        self.multiplyer = 0.08
        self.snapshot = 0
        self.delayed_clip = 0
        self.multi_clip = 0
        self.auto_copy_image = 0
        self.auto_hide_clip = 0
        self.zoomcycle = 0
        self.cursor_lines = 1
        self.default_alpha = 0.3
        self.win32clipboard = 1
        self.border_color = "#ff08ff"
        self.border_thiccness = 1
        self.open_on_save = 1


        if self.hotkey_visual_in_settings["current_hotkey_1"] != "Alt+Z" or self.hotkey_visual_in_settings["current_hotkey_2"] != "Alt+C":
                self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "Alt", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "Z", "current_hotkey_1" : 'Alt+Z',
                                              "hotkey_2_modifyer_1" : "Alt", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "C", "current_hotkey_2" : 'Alt+C'}
                self.save_file_name = "settings.tmp.json"
                self.create_save_file()
                self.save_file_name = "settings.json"
                if messagebox.askquestion(title = "", message = "The program requires a restart to change the hotkeys would you like to restart now?", parent = root) == "yes":
                    self.snippingclass.tray.restart_program(self.snippingclass.tray.sysTrayIcon)
                else:
                    messagebox.showinfo(title = "", message = "The settings will take place when the tool next opens", parent = root)
        else:
            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "Alt", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "Z", "current_hotkey_1" : 'Alt+Z',
                                              "hotkey_2_modifyer_1" : "Alt", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "C", "current_hotkey_2" : 'Alt+C'}

        
        self.snippingclass.save_settings(self)
        self.snippingclass.settings_window()


    def change_border(self, *args):
        a = askcolor(color = self.border_color)
        if a[1]:
            self.border_color = a[1]
            print(f"clip border color = {self.border_color}")


    def clip_from_clipboard(self, *args):
        img = ImageGrab.grabclipboard()
        print(img)
        if img:
            try:
                self.snippingclass.show_clip_window(None, True, img)
            except Exception as e:
                messagebox.showerror(title="", message=f"{e}", parent=root)
            finally:
                del img
                gc.collect()
        else:
            messagebox.showerror(title="", message="No image on clipboard", parent=root)

    def open_image(self, *args):
        img = askopenfilename(parent=root)

        if img:
            try:
                with PIL.Image.open(img) as image:
                    print(image)
                    self.snippingclass.show_clip_window(None, True, image.copy())
                image.close()
            except Exception as e:
                messagebox.showerror(title="", message=f"{e}", parent=root)
            finally:
                del image, img
                gc.collect()


    def create_save_file(self, *args):
        with open(self.save_file_name, "w") as save_file:
            settings = {"scale_percent"  : self.scale_percent,  "zoom_multiplyer" : self.multiplyer,   "snapshot_mode"      : self.snapshot,
                        "delayed_mode"   : self.delayed_clip,   "multi_clip"      : self.multi_clip,   "auto_copy_image"    : self.auto_copy_image,
                        "auto_hide_clip" : self.auto_hide_clip, "cursor_lines"    : self.cursor_lines, "default_alpha"      : self.default_alpha,
                        "win32clipboard" : self.win32clipboard, "border_color"    : self.border_color, "border_thiccness"   : self.border_thiccness,
                        "line_width"     : self.snippingclass.line_width,     "line_color"      : self.snippingclass.line_color,   "brush_scale_factor" : self.snippingclass.brush_scale_factor, 
                        "open_on_save"   : self.open_on_save,
                        "hotkeys"        : self.hotkey_visual_in_settings}
            save_file.write(json.dumps(settings,  indent=3))
            save_file.close()
            print("\n\n", json.dumps(settings,  indent=3), "\n\n")


class Drawing_Settings:

    def __init__(self, win, canvas, line_width, brush_scale_factor, line_color, update_variable_function,startx = 0, starty = 0):
        self.combo_box = []
        self.line_width = line_width
        self.brush_scale_factor = brush_scale_factor
        self.line_color = line_color
        self.draw = 1
        self.old_x = None
        self.old_y = None
        self.startx = startx
        self.starty = starty
        self.parent = win
        self.update_variable_function = update_variable_function

        self.mouse_rect = canvas.create_rectangle(0, 0, 0, 0,outline = self.get_complementary(self.line_color),tag = "mouse_cirlce")

        win.attributes('-topmost', 'false')
        win.overrideredirect(0)

        canvas.unbind("<B1-Motion>")
        win.unbind("<MouseWheel>")
        win.unbind("<Motion>")
        canvas.unbind("<Button-1>")

        canvas.bind("<Button-1>", self.change_rect_color)
        canvas.bind('<B1-Motion>', lambda event, win = canvas : self.paint(event, win))
        canvas.bind('<ButtonRelease-1>', self.reset)
        canvas.bind("<Motion>", self.follow_mouse)
        win.bind("<MouseWheel>", self.brush_size)
        win.config(cursor = "left_ptr")


        self.drawing_root = Toplevel(win)
        self.drawing_root.title("DrawingSettings")
        self.drawing_root.minsize(260, 90) 
        self.drawing_root.attributes('-topmost', 'true')
        self.drawing_root.geometry(f"+{startx}+{starty}")
        self.drawing_root.protocol("WM_DELETE_WINDOW", self.close)

        draw_color =         Button(self.drawing_root, text = "LineColor", command = self.change_line_color)
        clear =              Button(self.drawing_root, text = "Clear", command = self.clear)
        self.paint_button =  Button(self.drawing_root, text = "Draw", command = self.enable_draw, highlightbackground = "#000000")
        self.erase_button =  Button(self.drawing_root, text = "Erase", command = self.enable_erase, highlightbackground = "#000000")
        save_settings_button=Button(self.drawing_root, text = "SaveSettings", command = self.save_settings)

        draw_color.grid             (column = 0, row = 0, sticky = EW)
        clear.grid                  (column = 0, row = 1, sticky = EW, columnspan = 2)
        self.paint_button.grid      (column = 0, row = 5, sticky = EW, pady = (10,0))
        self.erase_button.grid      (column = 1, row = 5, sticky = EW, pady = (10,0))
        save_settings_button.grid   (column = 1, row = 0, sticky = EW)



        line_width_combobox = ttk.Combobox(self.drawing_root, width = 12, values = [i for i in range(1, 201)],  state='readonly')
        zoom_scale_combobox = ttk.Combobox(self.drawing_root, width = 12, values = [i for i in range(1, 21)],   state='readonly')

        self.combo_box.append(line_width_combobox)

        line_width_combobox.set(self.line_width)
        zoom_scale_combobox.set(self.brush_scale_factor)

        line_width_combobox.grid(column = 1, row = 3)
        zoom_scale_combobox.grid(column = 1, row = 4)
        


        line_thickness_label =  Label(self.drawing_root, text =  "Line Thickness")
        zoom_scale_label =      Label(self.drawing_root, text =  "Zoom Scale Factor")

        line_thickness_label.grid(column = 0, row = 3, pady = 2)
        zoom_scale_label.grid(column = 0, row = 4, pady = 2)
        

        

        line_width_combobox.bind("<<ComboboxSelected>>", self.setlinewidth)
        zoom_scale_combobox.bind("<<ComboboxSelected>>", self.setscale)

        if self.draw:
            self.enable_draw()
        else:
            self.enable_erase()

    def save_settings(self):
        self.update_variable_function(self, 1)

    def close(self):
        if self.parent["cursor"] == "arrow":
            self.drawing_root.destroy()

    def paint(self, event, win):
        self.adjust_mouse_rect(event.x, event.y, self.line_width//2, event.widget, self.mouse_rect)
        if self.draw:
            if self.old_x and self.old_y:
                win.create_line(self.old_x, self.old_y, event.x, event.y, width=self.line_width, fill=self.line_color, capstyle=ROUND, smooth=TRUE, splinesteps=36, tags = "<drawnlines>")
        else:
            coords = win.coords("mouse_cirlce")
            result = win.find_overlapping(coords[0], coords[1], coords[2], coords[3])
            for i in result:
                if  str(win.itemcget(i, "tags")).find("<drawnlines>") != -1:
                    win.delete(i)

        win.tag_raise("mouse_cirlce")
        self.old_x = event.x
        self.old_y = event.y

    def reset(self, event):
        self.old_x, self.old_y = None, None

    def brush_size(self, event):
        if (event.delta > 0):
            self.line_width += self.brush_scale_factor if self.line_width + self.brush_scale_factor <= 200 else 0
        if (event.delta < 0):
            self.line_width -= self.brush_scale_factor if self.line_width - self.brush_scale_factor >= 1 else 0

        self.adjust_mouse_rect(event.x, event.y, self.line_width//2, event.widget, self.mouse_rect)

        if len(self.combo_box) > 0:
            for i in self.combo_box:
                try:
                    i.set(self.line_width)
                except:
                    self.combo_box.remove(i)

    def change_rect_color(self, event):
            event.widget.itemconfig(self.mouse_rect, outline= self.get_complementary(self.line_color))
            event.widget.focus_set()

    def change_line_color(self):
            a = askcolor(color = self.line_color)
            if a[1]:
                self.line_color = a[1]
                print(f"line color = {self.line_color}")

    def update(self, event, canvas, color):
        try:
            canvas.config(bg = color)
        except:
            event.widget.pack_forget()

    def clear(self, *args):
        try:self.clear_menu.destroy()
        except:pass

        children = [i for i in root.winfo_children() if isinstance(i, Toplevel) if i.title() != "GifWindow"]
            
        self.clear_menu = Toplevel(self.drawing_root)
        self.clear_menu.title("ClearMenu")
        self.clear_menu.attributes("-topmost", True)
        self.clear_menu.lift()
        self.clear_menu.resizable(0,0)
        self.clear_menu.minsize(260, 20)
        self.clear_menu.geometry(f"+{self.startx}+{self.starty}")

        for i in children:
            for x in i.winfo_children():
                if isinstance(x, Canvas):
                    button = Button(self.clear_menu, text = i.title(), command = lambda canvas = x, tag = "<drawnlines>" : canvas.delete(tag))
                    button.pack()
                    button.bind("<Enter>", lambda event, canvas = x, color = self.get_complementary(x["bg"]) : self.update(event, canvas, color))
                    button.bind("<Leave>", lambda event, canvas = x, color = x["bg"] : self.update(event, canvas, color))

    def enable_draw(self, *args):
        self.draw = 1
        self.paint_button.config(relief= SUNKEN)
        self.erase_button.config(relief = RAISED)

    def enable_erase(self, *args):
        self.draw = 0
        self.paint_button.config(relief= RAISED)
        self.erase_button.config(relief = SUNKEN)

    def setlinewidth(self, event):
        self.line_width = int(event.widget.get())

    def setscale(self, event):
        self.brush_scale_factor = int(event.widget.get())

    def adjust_mouse_rect(self, x, y, width, canvas, rect):
        x1 = x + width
        y1 = y + width
        x = x - width
        y = y - width
        canvas.coords(rect, x, y, x1, y1)
        if canvas.itemcget(rect, "state") == "hidden":
            canvas.itemconfig("mouse_cirlce", state = "normal")

    def follow_mouse(self, event):
            self.adjust_mouse_rect(event.x, event.y, self.line_width//2, event.widget, self.mouse_rect)

    def get_complementary(self, color):
        color = color[1:]
        color = int(color, 16)
        comp_color = 0xFFFFFF ^ color
        comp_color = "#%06X" % comp_color
        return comp_color


class snipping_tool():

    def __init__(self):
        self.tray = None
        
        self.drag_box = None        # Used to show selected area
        self.start_x = None         # On click x
        self.start_y = None         # On click y
        self.curx = None            # After releasing x
        self.cury = None            # After releasing y
        #self.monitorid = None       # Monitor id of the monitor you started on
        self.monitor = None         # monitor that you started on
        self.zoom_image = None      # Image displayed when you zoom in 
        self.img = None             # Temporary image that is shown when you zoom in

        correct_modifyers_for_hotkey = {"Windows" : win32con.MOD_WIN, "Alt" : win32con.MOD_ALT, "Ctrl" : win32con.MOD_CONTROL, "Shift" : win32con.MOD_SHIFT, "None" : 0}

        VKS = {**{str(item)[3:] : win32con.__dict__[str(item)] for item in win32con.__dict__ if item[:3] == 'VK_'}, **{chr(key_code) : key_code for key_code in (list (range(ord('A'), ord('Z') + 1)) + list(range(ord('0'), ord('9') + 1)) )}, **GlobalHotKeys.PUNCTUATION_CHARACTERS}


        try:           
            if not os.path.exists(os.path.join(os.getcwd(), 'settings.tmp.json')):
                file = "settings.json"
            else:
                file = "settings.tmp.json"

            with open(file, "r") as settings_file:
                settings = json.load(settings_file)

                self.scale_percent = settings["scale_percent"]
                self.multiplyer = settings["zoom_multiplyer"]
                self.cursor_lines = settings["cursor_lines"]
                self.default_alpha = settings["default_alpha"]
                self.border_color = settings["border_color"]
                self.border_thiccness = settings["border_thiccness"]
                self.auto_copy_image = settings["auto_copy_image"]
                self.auto_hide_clip = settings["auto_hide_clip"]
                self.snapshot = settings["snapshot_mode"]
                self.delayed_clip = settings["delayed_mode"]
                self.multi_clip =  settings["multi_clip"]
                self.win32clipboard = settings["win32clipboard"]
                self.hotkey_visual_in_settings = settings["hotkeys"]
                self.line_width = settings["line_width"]
                self.line_color = settings["line_color"]
                self.brush_scale_factor = settings["brush_scale_factor"]
                self.open_on_save = settings["open_on_save"]
                print(f"settings imported successfully from {file}")
                    
        except FileNotFoundError:
            self.scale_percent = 0.35   # The size of the zoom box based on the width/height of the clip
            self.multiplyer = 0.08      # How far zoomed out you start
            self.cursor_lines = 1       # Is there 2 lines that follow you mouse in clipping mode 
            self.default_alpha = 0.3
            self.border_color = "#ff08ff"
            self.border_thiccness = 1
            self.auto_copy_image = 0
            self.auto_hide_clip = 0
            self.snapshot = 0       # SnapshotMode takes a screenshot of the whole screen and lets you crop it
            self.delayed_clip = 0   # Delayed Clip will save a screenshot in memory and when you press the hotkey to take another screenshot it will display the img in memory and let you crop it
            self.multi_clip = 0     # Lets you clip the same window until you cancel the clip windows 
            self.win32clipboard = 1     # Copy using win32 or prnt screen
            self.line_width = 5
            self.line_color = "#ff08ff"
            self.brush_scale_factor = 10
            self.open_on_save = 1
            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "Alt", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "Z", "current_hotkey_1" : 'Alt+Z',
                                              "hotkey_2_modifyer_1" : "Alt", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "C", "current_hotkey_2" : 'Alt+C'}
            print("no settings file found")
        except Exception as e:
            self.scale_percent = 0.35   # The size of the zoom box based on the width/height of the clip
            self.multiplyer = 0.08      # How far zoomed out you start
            self.cursor_lines = 1       # Is there 2 lines that follow you mouse in clipping mode 
            self.default_alpha = 0.3
            self.border_color = "#ff08ff"
            self.border_thiccness = 1
            self.auto_copy_image = 0
            self.auto_hide_clip = 0
            self.snapshot = 0       # SnapshotMode takes a screenshot of the whole screen and lets you crop it
            self.delayed_clip = 0   # Delayed Clip will save a screenshot in memory and when you press the hotkey to take another screenshot it will display the img in memory and let you crop it
            self.multi_clip = 0     # Lets you clip the same window until you cancel the clip windows 
            self.win32clipboard = 1     # Copy using win32 or prnt screen
            self.line_width = 5
            self.line_color = "#ff08ff"
            self.brush_scale_factor = 10
            self.open_on_save = 1
            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "Alt", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "Z", "current_hotkey_1" : 'Alt+Z',
                                              "hotkey_2_modifyer_1" : "Alt", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "C", "current_hotkey_2" : 'Alt+C'}
            print("there was an error importing the settings \n{}".format(e))
        finally:
            try:settings_file.close()
            except:pass

        self.zoomcycle = 0          # How far in you are zoomed
        self.hwnd = root.winfo_id() 
        self.save_img_data = {}     # Keep track of the img data so it can be saved, or used for OCR
        self.lines_list = {} 
        self.threads = []           # Keep track of used threads to join back later

        print("snipping tool started")

        #***************** Hide root window *************. 
        root.withdraw()
        root.attributes('-alpha', .0)
        root.attributes('-topmost', 'true')

        if not os.path.exists(os.path.join(os.getcwd(), 'screenshots')):
            os.mkdir(os.path.join(os.getcwd(), 'screenshots'))
        else:
            if messagebox.askquestion(title = "", message = "Would you like to clear the screenshot folder", parent = root) == "yes":
                try:
                    rmtree("screenshots")                   
                    os.mkdir(os.path.join(os.getcwd(), 'screenshots'))
                except:pass

        if os.path.exists(os.path.join(os.getcwd(), 'settings.tmp.json')):os.remove("settings.tmp.json")
        
        # <cmd> == WindowsKey, <alt> == AltKey, <ctrl> == CtrlKey, <shift> = shift
        #self.clip_hotkey =  Global_hotkeys.create_hotkey(self.hwnd, 0, self.hotkey_visual_in_settings["current_hotkey_1"].split("+")[:-1], self.hotkey_visual_in_settings["hotkey_1_key"], self.on_activate_i) #keyboard.GlobalHotKeys({ '<cmd>+z': self.on_activate_i})
        #self.gif_hotkey =   Global_hotkeys.create_hotkey(self.hwnd, 1, self.hotkey_visual_in_settings["current_hotkey_2"].split("+")[:-1], self.hotkey_visual_in_settings["hotkey_2_key"], self.on_activate_gif) #keyboard.GlobalHotKeys({ '<cmd>+c': self.on_activate_gif})
       
        self.clip_hotkey = GlobalHotKeys.register(VKS[self.hotkey_visual_in_settings["hotkey_1_key"]], sum([correct_modifyers_for_hotkey[key] for key in [self.hotkey_visual_in_settings["hotkey_1_modifyer_1"], self.hotkey_visual_in_settings["hotkey_1_modifyer_2"], self.hotkey_visual_in_settings["hotkey_1_modifyer_3"]]]), self.on_activate_i)
        
        self.gif_hotkey =  GlobalHotKeys.register(VKS[self.hotkey_visual_in_settings["hotkey_2_key"]], sum([correct_modifyers_for_hotkey[key] for key in [self.hotkey_visual_in_settings["hotkey_2_modifyer_1"], self.hotkey_visual_in_settings["hotkey_2_modifyer_2"], self.hotkey_visual_in_settings["hotkey_2_modifyer_3"]]]), self.on_activate_gif)
        
        self.hotkey_thread = threading.Thread(target = GlobalHotKeys.listen, daemon=True)
        self.hotkey_thread.start()

        
    #*****************                *************. 
    #***************** Call Functions *************. 
    #*****************                *************. 

    def on_activate_gif(self):
        root.after(0 , self.create_gif_window)


    def on_activate_i(self):
        root.after(0 , self.create_clip_window)







    #*****************                                *************. 
    #***************** Pictures / Recording Functions *************. 
    #*****************                                *************. 
       
       



    #***************** Take the screenshot at select location on selected monitor *************. 
    def screenshot(self, x1, y1, x2, y2):

        print(f"monitor = {self.monitor.name}, {self.monitor.bounds}, {self.monitor.hashCode}")
        monitor = self.monitor.bounds
        x1, y1, x2, y2 = int(x1 + monitor.X), int(y1 + monitor.Y), int(x2 + monitor.X), int(y2 + monitor.Y)

        try:
            time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
            img = Image.open(get_rect_as_image(x1, y1, x2, y2, os.path.join(os.getcwd(), f'screenshots\\{time}.png'))) # take image
            dispImg = ImageTk.PhotoImage(img)
        except Exception as e: 
            print(e)
            img, dispImg = None, None
        return dispImg, (monitor.X, monitor.Y), img




    #*****************                       *************. 
    #***************** Clip window Functions *************. 
    #*****************                       *************. 





    #***************** Create the clipping window for each monitor *************. 
    def create_gif_window(self):
        self.destroy_all(0)

        monitors = [i for i in get_monitors()]
        for index, monitor in enumerate(monitors): 
            bounds = monitor.bounds
            monx = int(bounds.X); mony = int(bounds.Y); width = int(bounds.Width); height = int(bounds.Height)

            master_screen = Toplevel(root)
            master_screen.title(f"clip_window_gif{index}")
            master_screen.minsize(width, height)      
            master_screen.geometry(f"+{monx}+{mony}")
            master_screen.attributes("-transparent", "blue")
            master_screen.attributes('-alpha', .3) 
            master_screen.overrideredirect(1) 
            master_screen.state('zoomed')   
            master_screen.deiconify()    
            master_screen.attributes("-topmost", True) 
            
            screen = Canvas(master_screen, bg="grey11", highlightthickness = 0)
            #self.gif_canvas.append(screen) 
            screen.pack(fill=BOTH, expand=YES)

            screen.bind("<ButtonRelease-3>", self.OnRightClick)
            screen.bind("<ButtonPress-1>", self.OnLeftClick)
            screen.bind("<B1-Motion>", self.OnDrag)
            screen.bind("<ButtonRelease-1>", self.OnReleaseGif)

            

            master_screen.lift()
            master_screen.update()

            

    #***************** Create the clipping window for each monitor *************. 
    def create_clip_window(self):
        self.destroy_all(0)

        monitors = [i for i in get_monitors()]
        if self.delayed_clip:
            if any([i for i in self.save_img_data.keys() if i.find("delay_clip") != -1]): # If there are any delay_clips in the dictionary display them
                for x, i in enumerate(monitors):
                    bounds = i.bounds
                    self.lines_list[x] = {"dims" : [bounds.Width, bounds.Height, i.name], "lines" : None}
                    delayed_clips = [i for i in self.save_img_data.keys() if i.find("delay_clip") != -1] # Get all the clips tagged with delay_clip                   
                    img = ImageTk.PhotoImage(self.save_img_data[delayed_clips[x]])
                    self.make_clip_win(i, 1, img)
                    del img
                    print(delayed_clips)

                for i in delayed_clips:
                    del self.save_img_data[i]       # Remove all the delay_clips 
            else:                                   # If there are no clips take screenshots 
                for i in monitors:  
                    bounds = i.bounds
                    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
                    img = Image.open(get_rect_as_image(bounds.X, bounds.Y, bounds.Width + bounds.X, bounds.Height + bounds.Y, os.path.join(os.getcwd(), f'screenshots\\{time}delay_clip.png'))) # take image
                    #img = getRectAsImage((bounds.X, bounds.Y, bounds.Width + bounds.X, bounds.Height + bounds.Y)) #Image.open(get_rect_as_image(x1, y1, x2, y2, os.path.join(os.getcwd(), f'screenshots\\{time}.png'))) # take image
                    date_time = str(time) + "delay_clip"         # Name the clip using the date time and mark it as a delay_clip
                    self.save_img_data[date_time] = img
                    del img
                    print("image saved")
        else:
            for x, i in enumerate(monitors): # Create clipping window for all monitors 
                bounds = i.bounds
                self.lines_list[x] = {"dims" : [bounds.Width, bounds.Height, i.name], "lines" : None}
                if self.snapshot:
                    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
                    img = ImageTk.PhotoImage(Image.open(get_rect_as_image(bounds.X, bounds.Y, bounds.Width + bounds.X, bounds.Height + bounds.Y, os.path.join(os.getcwd(), f'screenshots\\{time}.png'))))
                    self.make_clip_win(i, self.snapshot, img)
                    del img
                else:
                    self.make_clip_win(i, self.snapshot)

        gc.collect()


    #***************** Make clip window *************. 
    def make_clip_win(self, monitorobj, snapshot, img = None):
        bounds = monitorobj.bounds
        monx = int(bounds.X); mony = int(bounds.Y); width = int(bounds.Width); height = int(bounds.Height)

        master_screen = Toplevel(root)
        master_screen.title(f"clip_window_{datetime.datetime.now()}")   # Name the clip windows so they can all be destroyed later        
        master_screen.minsize(width, height)                            # make the min size of the window the size of the screen
        master_screen.geometry(f"+{monx}+{mony}")                       # Put clipping window at screen pos
        master_screen.attributes("-transparent", "blue")
        master_screen.overrideredirect(1)
        master_screen.state('zoomed')  
        master_screen.deiconify()
        master_screen.attributes("-topmost", True)
            
        screen = Canvas(master_screen, bg="grey11", highlightthickness = 0)
        screen.pack(fill=BOTH, expand=YES)

        screen.bind("<ButtonRelease-3>", self.OnRightClick)
        screen.bind("<ButtonPress-1>", self.OnLeftClick)
        screen.bind("<B1-Motion>", self.OnDrag)
        screen.bind("<ButtonRelease-1>", self.OnRelease)

        if snapshot: 
            screen.create_image(0, 0, image = img, anchor=NW)  
            screen.image = img                                          # Keep image in memory 
        else: 
            master_screen.attributes('-alpha', .3) 

        if self.cursor_lines:
            master_screen.bind("<Motion>", self.lines)
            for x, i in self.lines_list.items():
                if i["dims"][2] == monitorobj.name and type(x) == int:
                    self.lines_list[x]["lines"] = [screen.create_line(0,0,1,1,fill=self.border_color), screen.create_line(0,0,1,1,fill=self.border_color)]
                    self.lines_list[screen] = self.lines_list.pop(x)

            
        master_screen.lift()                        
        master_screen.update()



    #***************** Move the lines in the clip window that follow your mouse *************. 
    def lines(self, event):
        try:
            lines = self.lines_list[event.widget]["lines"]
            dims = self.lines_list[event.widget]["dims"]
            width, height = dims[0], dims[1]
            event.widget.coords(lines[0], 0, event.y, width, event.y)
            event.widget.coords(lines[1], event.x, 0, event.x, height)
        except:pass


        


    #***************** Destroy the clipping window *************. 
    def OnRightClick(self, event):   
        event.widget.delete(self.drag_box)
        self.drag_box = None

        if self.cursor_lines and not self.multi_clip and event.widget.master.title().find("gif") == -1:
            for i in self.lines_list[event.widget]["lines"]:
                try:event.widget.delete(i)
                except:pass

        self.destroy_all(0)


    #***************** Create the drag box *************. 
    def OnLeftClick(self, event):
        if not self.drag_box:
            self.start_x = event.widget.canvasx(event.x)
            self.start_y = event.widget.canvasy(event.y)
            self.monitorid = windll.user32.MonitorFromPoint(int(root.winfo_pointerx()), int(root.winfo_pointery()), 2)
            self.monitor =  monitor_from_point(int(root.winfo_pointerx()), int(root.winfo_pointery()))

            if self.snapshot or self.delayed_clip: 
                self.drag_box = event.widget.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=1)
            else: 
                self.drag_box = event.widget.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=1, fill="blue")
        else:print("already clicked")


    #***************** Expand the drag box *************. 
    def OnDrag(self, event):
        self.curx, self.cury = (event.x, event.y)
        event.widget.coords(self.drag_box, self.start_x, self.start_y, self.curx, self.cury)


    #***************** After selecting the area reset the hotkey and show the clip *************. 
    def OnRelease(self, event): 
        if self.cursor_lines and not self.multi_clip:
            for i in self.lines_list[event.widget]["lines"]:
                event.widget.delete(i)
            self.lines_list.clear()

        event.widget.delete(self.drag_box)
        self.drag_box = None
        root.after(70 , lambda : self.show_clip_window(event)) # Call clip window 





    #*****************                       *************. 
    #***************** Gif display Functions *************. 
    #*****************                       *************. 


    #***************** When you let go of the gif select window, get coords, create buttons to start/stop recording the video *************. 
    def OnReleaseGif(self, event):           
        self.destroy_all(0)

        
        self.curx, self.cury = (event.x, event.y)
        # format the select area so it can grab from top left to bottom right
        if self.start_x <= self.curx and self.start_y <= self.cury:   
            x1, y1, x2, y2 = (int(self.start_x), int(self.start_y), int(self.curx), int(self.cury)) # Right Down
        elif self.start_x >= self.curx and self.start_y <= self.cury:
            x1, y1, x2, y2 = (int(self.curx), int(self.start_y), int(self.start_x), int(self.cury))  # Left Down
        elif self.start_x <= self.curx and self.start_y >= self.cury:
            x1, y1, x2, y2 = (int(self.start_x), int(self.cury), int(self.curx), int(self.start_y)) # Right Up 
        elif self.start_x >= self.curx and self.start_y >= self.cury:
            x1, y1, x2, y2 = (int(self.curx), int(self.cury), int(self.start_x), int(self.start_y)) # Left Up
        print(f"({x1}, {y1}) x ({x2}, {y2}) --> {datetime.datetime.now()}")

        print(f"monitor = {self.monitor.name}, {self.monitor.bounds}, {self.monitor.hashCode}")
        monitor = self.monitor.bounds

        Create_gif(self.open_on_save, self.border_color, monitor, x1, y1, x2, y2)




    #*****************                     *************. 
    #***************** Functions for clips *************. 
    #*****************                     *************. 




        #***************** Set focus to the main window *************. 
    def SaveLastClickPos(self, event, win): # Set focus to the clip and get last clicked pos to allow dragging without title bar
            self.lastClickX = event.x
            self.lastClickY = event.y
            win.focus_set()


    #***************** Move the window when dragging *************. 
    def Dragging(self, event, win): # Allows you to drag the clip easily 
        self.x, self.y = event.x - self.lastClickX + win.winfo_x(), event.y - self.lastClickY + win.winfo_y()
        win.geometry("+%s+%s" % (self.x , self.y))


    #***************** Destroy the clip window *************. 
    def close(self, event, win): # Destroy the clip 
        try:
            del win.winfo_children()[2].image
        except:pass
        del self.img, self.save_img_data[win.title()] 
        self.zoomcycle = 0
        self.img = None
        print(f"clip {win.title()} has been destroyed")
        win.destroy()
        for i in self.threads.copy():
            if not i.is_alive():
                i.join()
                self.threads.remove(i)
        gc.collect()



    @cooldown(0.5)
    def crop_out_border(self, remove_title_bar = False):
        try:
            image = ImageGrab.grabclipboard()
            print(image)
            if remove_title_bar:
                startingpoint = (1 + (self.border_thiccness),31 + (self.border_thiccness))
                endpoint = (image.width - self.border_thiccness - 1, image.height - self.border_thiccness - 1) # -1 because there is a 1 pixel thick black outline when there is a title bar
            else:
                startingpoint = (0 + (self.border_thiccness),0 + (self.border_thiccness))
                endpoint = (image.width - self.border_thiccness, image.height - self.border_thiccness)
            image = image.crop((startingpoint[0], startingpoint[1], endpoint[0], endpoint[1]))
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            del image
            gc.collect()
        except:
            messagebox.showerror(title="", message="There was an error cropping the image, please wait at least 1 second before trying again", parent=root)

    #***************** Remove the border and send Alt+Print screen to copy the window *************. 
    @cooldown(0.7)
    def copy(self, event, win, force_win32 = False):     # On Ctrl+C remove the border using geometry and send Alt+PrntScreen to copy clip
        if (self.win32clipboard or force_win32) and win["cursor"] != "left_ptr":
            output = io.BytesIO()
            self.save_img_data[win.title()].convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
        else:
            if win["cursor"] == "left_ptr":
                children = win.winfo_children()
                children[1].itemconfig("mouse_cirlce", state = "hidden")

            kb.send("Alt+print screen") # Only copies the image at the end of function so below must use something non blocking, but still need a small delay

            if win.overrideredirect():
                timer = threading.Timer(0.05, self.crop_out_border)
            else:
                timer = threading.Timer(0.05, lambda x = True : self.crop_out_border(x))
            self.threads.append(timer)
            timer.start()


    #***************** Lets the user save the image *************. 
    def save(self, event, win):
        self.zoomcycle = 0
        self.zoomer(event = win, fake_call = 1)
        savename = datetime.datetime.strptime(win.title(), '%Y-%m-%d %H:%M:%S.%f')
        savename = savename.strftime("%Y-%m-%d_%H-%M-%S.%f")
        f = asksaveasfile(initialfile = f"{savename}", mode='w', defaultextension=".png", parent=root)
        if f is None:
            return
        print(f.name)
        format = str(f.name).split(".")[-1:][0] # Grab the file type
        if format.upper() == "JPG": format = "jpeg"
        try:
            self.save_img_data[str(win.title())].save(str(f.name), format = str(format))
            if self.open_on_save: explore(f.name)
        except KeyError:
            messagebox.showerror(title="", message="The filetype {} is most likely unsupported".format(format), parent=root)
            print(KeyError)
        except Exception as e: 
            messagebox.showerror(title="", message=f"There was an error that was not a problem with the filetype please tell minnowo \n{e}", parent=root)
        finally:
            del f 
            gc.collect()


    #***************** Toggle always on top *************. 
    def top_most(self, event, win):
        if win.attributes('-topmost'):
            win.attributes('-topmost', 'false')
            win.overrideredirect(0)
        else:
            win.attributes('-topmost', 'true')
            win.overrideredirect(1)
    

    #***************** Run OCR on the image *************. 
    def tesseract_clip(self, event, win):
        self.zoomcycle = 0
        self.zoomer(event = win, fake_call = 1)
        try:
            pytesseract.pytesseract.tesseract_cmd = resource_path("tesseract.exe")
            image_text = pytesseract.image_to_string(self.save_img_data[win.title()], lang='eng', config= "--psm 1")
            root.clipboard_clear()
            root.clipboard_append(image_text)
            messagebox.showinfo(title="OCR Output", message=image_text, parent=root)
            print(image_text)
        except Exception as e: 
            messagebox.showerror(title="", message="error with ocr:\n {}".format(e), parent=root)



    def enable_drawing(self,win):
        children = win.winfo_children() # [1] == the canvas with the image
        if win["cursor"] == "arrow": # not in drawing mode 
            Drawing_Settings(win, children[1], self.line_width, self.brush_scale_factor, self.line_color, self.save_settings, win.winfo_x(), win.winfo_y())
        else:                       # in drawing mode
            children[1].delete("mouse_cirlce")
            win.attributes('-topmost', 'true')
            win.overrideredirect(1)

            win.unbind("<MouseWheel>")
            win.unbind("<Motion>")
            children[1].unbind("<B1-Motion>")
            children[1].unbind('<ButtonRelease-1>')
            children[1].unbind("<Button-1>")

            children[1].bind("<Button-1>", lambda event, win = children[1] : self.SaveLastClickPos(event, win))
            children[1].bind("<B1-Motion>", lambda event, win = win : self.Dragging(event, win))
            win.bind("<MouseWheel>",self.zoomer)
            win.bind("<Motion>", self.crop)
            win.config(cursor = "arrow")
        
            
            


    #***************** Bring up the right click menu *************. 
    def show_popup_menu(self, event, menu):
        hotkey_visual = [self.hotkey_visual_in_settings["current_hotkey_1"], self.hotkey_visual_in_settings["current_hotkey_2"]]
        hotkey_visual = [i.replace("<", "").replace(">","").replace("cmd","win").title() for i in hotkey_visual]
        try: 
            #menu.entryconfigure(7, accelerator = self.snapshot)
            #menu.entryconfigure(8, accelerator = self.delayed_clip)
            #menu.entryconfigure(9, accelerator = self.multi_clip)
            menu.entryconfigure(7, accelerator = hotkey_visual[0])
            menu.entryconfigure(8, accelerator = hotkey_visual[1])
            menu.tk_popup(event.x_root, event.y_root) 
            
            #print(menu.entrycget())
        finally: 
            menu.grab_release() 


    #***************** Create a new toplevel window and scale it to image size, then display image *************. 
    def show_clip_window(self, event, loadfromfile = False, imgfromfile = None):
        if not loadfromfile:
            if not self.snapshot and not self.delayed_clip and not self.multi_clip: self.destroy_all(0)
            if self.multi_clip and not self.delayed_clip:
                for widget in root.winfo_children():
                    if isinstance(widget, Toplevel):
                        if str(widget.title()).find("clip_window") != -1:
                            widget.attributes('-alpha', .0) 
            self.curx, self.cury = event.x, event.y

            # format the select area so it can grab from top left to bottom right
            if self.start_x <= self.curx and self.start_y <= self.cury:   x1, y1, x2, y2 = (self.start_x, self.start_y, self.curx, self.cury) # Right Down
            elif self.start_x >= self.curx and self.start_y <= self.cury: x1, y1, x2, y2 = (self.curx, self.start_y, self.start_x, self.cury)  # Left Down
            elif self.start_x <= self.curx and self.start_y >= self.cury: x1, y1, x2, y2 = (self.start_x, self.cury, self.curx, self.start_y) # Right Up 
            elif self.start_x >= self.curx and self.start_y >= self.cury: x1, y1, x2, y2 = (self.curx, self.cury, self.start_x, self.start_y) # Left Up
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            img, monx, imgobj = self.screenshot(x1, y1, x2, y2) # Get img
            date_time = datetime.datetime.now()
            self.save_img_data[str(date_time)] = imgobj
            width = x2-x1; height = y2-y1
            print(f"({x1}, {y1}) x ({x2}, {y2}) --> {date_time}\n")
        else:
            width = int(imgfromfile.width); height = int(imgfromfile.height)
            img = ImageTk.PhotoImage(imgfromfile)

            for widget in root.winfo_children():
                if isinstance(widget, Toplevel):
                    if str(widget.title()).find("Settings") != -1:
                        monx = (widget.winfo_x(), widget.winfo_y())

            x1 = 0; y1 = 0
            imgobj = imgfromfile
            date_time = datetime.datetime.now()
            self.save_img_data[str(date_time)] = imgobj
            del imgfromfile

        if img != None:                            # Create window to display clip 
            display_screen = Toplevel(root, cursor = "arrow")#, .config(cursor="spraycan"

            display_screen.title("{}".format(date_time))
            display_screen.minsize(int(width), int(height)) 
            display_screen.attributes('-topmost', 'true')
            display_screen.overrideredirect(1)
            display_screen.resizable(0,0)
            display_screen.geometry('{}x{}+{}+{}'.format((width + self.border_thiccness), (height + self.border_thiccness),(x1 + monx[0]), (y1 + monx[1]))) # +2 gives slight outline on image 

            right_click_menu = Menu(display_screen, tearoff = 0)
            right_click_menu.add_command(label ="Copy",         accelerator="Ctrl+C",   command = lambda event = None, win= display_screen : self.copy(event, win))
            right_click_menu.add_command(label ="Save",         accelerator="Ctrl+S",   command = lambda event = None, win= display_screen : self.save(event, win))
            right_click_menu.add_command(label ="OCR",          accelerator="Ctrl+T",   command = lambda event = None, win= display_screen : self.tesseract_clip(event, win))
            right_click_menu.add_command(label ="AlwaysOnTop",  accelerator="Tab",      command = lambda event = None, win= display_screen : self.top_most(event, win))
            right_click_menu.add_command(label ="Destroy",      accelerator="Esc",      command = lambda event = None, win = display_screen : self.close(event, win))
            right_click_menu.add_command(label ="Draw",                                 command = lambda win = display_screen : self.enable_drawing( win))
            right_click_menu.add_separator() 
            #right_click_menu.add_command(label ="SnapshotMode", accelerator= self.snapshot,         command = lambda :  self.toggle_snapshot_mode())
            #right_click_menu.add_command(label ="DelayMode",    accelerator= self.delayed_clip ,    command = lambda :  self.toggle_delay_mode())
            #right_click_menu.add_command(label ="MultiClip",    accelerator= self.multi_clip ,      command = lambda :  self.toggle_multi_mode())
            #right_click_menu.add_separator() 
            right_click_menu.add_command(label ="TakeScreenshot",   accelerator= self.hotkey_visual_in_settings["current_hotkey_1"],    command = lambda :  self.on_activate_i())
            right_click_menu.add_command(label ="TakeGif",          accelerator= self.hotkey_visual_in_settings["current_hotkey_2"],    command = lambda :  self.on_activate_gif())
            right_click_menu.add_separator()
            right_click_menu.add_command(label ="DestroyAll",       command = lambda :  self.destroy_all(1))
            right_click_menu.add_command(label ="BringAllFront",    command = lambda :  self.bringallfront())
            right_click_menu.add_separator()
            right_click_menu.add_command(label ="Settings",         command = lambda :  self.settings_window())
            #right_click_menu.add_command(label ="DrawingSettings",  command = lambda win = display_screen:  Drawing_Settings(self, win, win.winfo_children()[1], win.winfo_x(), win.winfo_y()))
            #right_click_menu.add_command(label ="ClipManager",      command = lambda :  self.create_drawing_settings_win(root, (x1 + monx[0]), (y1 + monx[1])))


            img_canvas = Canvas(display_screen,  bg = self.border_color, borderwidth = self.border_thiccness, highlightthickness=0)
            img_canvas.pack(expand = True, fill = BOTH)
            img_canvas.create_image(0, 0, image = img, anchor = NW) 
            img_canvas.image = img # Keep img in memory # VERY IMPORTANT

            tmp_img = Label(display_screen) # Label that holds temp image on zoom in

            img_canvas.bind("<B1-Motion>",  lambda event, win = display_screen : self.Dragging(event, win))  # Pass current Toplevel window so it knows what window to drag/copy/destroy
            img_canvas.bind("<Button-1>",   lambda event, win = img_canvas : self.SaveLastClickPos(event, win))
            img_canvas.bind('<Escape>',     lambda event, win = display_screen : self.close(event, win))
            img_canvas.bind("<Control-c>",  lambda event, win = display_screen : self.copy(event, win))
            img_canvas.bind("<Tab>",        lambda event, win = display_screen : self.top_most(event, win))
            img_canvas.bind("<Control-s>",  lambda event, win= display_screen : self.save(event, win))
            img_canvas.bind("<Control-t>",  lambda event, win = display_screen : self.tesseract_clip(event, win))
            img_canvas.bind("<Button-3>",   lambda event, menu = right_click_menu : self.show_popup_menu(event, menu))

            tmp_img.bind("<Button-3>",           self.remove_zoom)

            display_screen.bind("<MouseWheel>", self.zoomer)
            display_screen.bind("<Motion>",     self.crop)

            display_screen.protocol("WM_DELETE_WINDOW", lambda event = None, win = display_screen : self.close(event, win)) 

            if self.auto_hide_clip:
                self.top_most(None, display_screen)
                display_screen.iconify()

            if self.auto_copy_image:
                self.copy(None, display_screen, True)

            gc.collect()

        if not loadfromfile:
            if (self.snapshot or self.delayed_clip) and not self.multi_clip: self.destroy_all(0)
            if self.multi_clip and not self.delayed_clip:
                for widget in root.winfo_children():
                    if isinstance(widget, Toplevel):
                        if str(widget.title()).find("clip_window") != -1:
                            widget.attributes('-alpha', self.default_alpha)
                            widget.lift()
    


    def remove_zoom(self, event):
        del self.img
        del event.widget.image
        self.img = None
        self.zoomcycle = 0
        event.widget.place(x = -10, y = -10, anchor = "e")  # Move the empty label off the visual window 
        gc.collect()



    def zoomer(self,event = None, fake_call = 0):
        toplev = event.widget.master if fake_call == 0 else event

        if fake_call == 0:                          # fake call is used to call the function without using the binds allowing the save function to remove zoomed images
            if (event.delta > 0):
                self.img = self.save_img_data[str(toplev.title())]
                if self.zoomcycle != int(self.multiplyer // 0.005): self.zoomcycle += 1

            elif (event.delta < 0):
                if self.zoomcycle != 0: self.zoomcycle -= 1

        if self.zoomcycle == 0: 
            del self.img
            
            array_of_children_widgets = toplev.winfo_children()
            self.img = None
            array_of_children_widgets[2].place(x = -10, y = -10, anchor = "e")  # Move the empty label off the visual window

            try:
                del array_of_children_widgets[2].image  # [2] == tmp_img (holds zoomed image)
                array_of_children_widgets[2].image = '' # [2] == tmp_img (holds zoomed image)
            except:pass
            
            gc.collect()

        self.crop(event)



    def crop(self,event = None):
        if (self.zoomcycle) != 0 and event != None:
            widget = event.widget.master
            array_of_children_widgets = widget.winfo_children()         # [2] == tmp_img (holds zoomed image)
            x = event.x_root - widget.winfo_rootx()                     # Get mouse x pos relative to window 
            y = event.y_root - widget.winfo_rooty()                     # Get mouse y pos relative to window 
            width = self.img.width if self.img.width > self.img.height else self.img.height  # Use whatever length is bigger
            size = int(width * self.scale_percent) , int(width * self.scale_percent)                 # Set the size of the zoom to 20% of the clips width
            if size[0] < 1: size = (1,1) # Cant resize if its less than 1

            multiplyer = self.multiplyer - (0.005 * self.zoomcycle) if (self.multiplyer - (0.005 * self.zoomcycle)) > 0.003 else 0.004

            width = int(width * multiplyer)
            tmp = self.img.crop((x-width,y-width,x+width,y+width))
                           
            tmp = PIL.ImageTk.PhotoImage(tmp.resize(size))
            array_of_children_widgets[2].configure(image= tmp)
            array_of_children_widgets[2].image = tmp                    # [2] == tmp_img aka the label that holds the display img, which each clip has 
            array_of_children_widgets[2].place(x = x, y = y, anchor="center")   # Adjust placement


    #*****************                           *************. 
    #***************** Other functions *************. 
    #*****************                           *************. 

    # call from the settings window class to update all the variables in the snipping class 
    def save_settings(self, val, settings_number = 0):
        if settings_number == 0:
            self.scale_percent = val.scale_percent
            self.multiplyer = val.multiplyer
            self.cursor_lines = val.cursor_lines
            self.default_alpha = val.default_alpha
            self.border_color = val.border_color
            self.border_thiccness = val.border_thiccness
            self.auto_copy_image = val.auto_copy_image
            self.auto_hide_clip = val.auto_hide_clip
            self.snapshot = val.snapshot
            self.delayed_clip = val.delayed_clip
            self.multi_clip =  val.multi_clip
            self.win32clipboard = val.win32clipboard
            self.hotkey_visual_in_settings = val.hotkey_visual_in_settings
            self.open_on_save = val.open_on_save
            self.tray.update_hov_text(self.tray.sysTrayIcon)
            self.clip_hotkey = val.clip_hotkey
            self.gif_hotkey = val.gif_hotkey
        elif settings_number:
            self.line_width = val.line_width
            self.brush_scale_factor = val.brush_scale_factor
            self.line_color = val.line_color



    #***************** Destroy all toplevel widgets or only destroy clpping windows *************.###
    def destroy_all(self, destroy = 0):
        if destroy:
            print("\nDestroying all toplevel\n")
            self.zoomcycle = 0
            for widget in root.winfo_children():
                if isinstance(widget, Toplevel):
                    if str(widget.title()).find("Settings") == -1:
                        del self.save_img_data[str(widget.title())]
                        widget.destroy()
        else:
            for widget in root.winfo_children():
                if isinstance(widget, Toplevel):
                    if str(widget.title()).find("clip_window") != -1:
                        if self.snapshot or self.delayed_clip:
                            child = widget.winfo_children()
                            try: del child[0].image
                            except:pass
                        widget.destroy()
        gc.collect()


    #***************** bring all the clips to the front *************. 
    def bringallfront(self):
        print("Lifted all clips\n")
        for widget in root.winfo_children():
            if isinstance(widget, Toplevel):
                if str(widget.title()).find("clip_window") == -1:
                    widget.deiconify()




    def settings_window(self):

        for widget in root.winfo_children():
            if isinstance(widget, Toplevel):
                tit = str(widget.title())
                if tit.find("Settings") != -1:
                    widget.destroy()
        Settings(self)


        






#******************************. 
#******************************. 
#******************************. 





class tray():
    def __init__(self, snip_class):

        #***************** Start Tray icon *************. 
        print("Tray app started")
        self.clip_app = snip_class#snipping_tool() # start clipping app 
        self.hover_text = f"ScreenCaptureTool\nSnapshotMode: {self.clip_app.snapshot}\nDelayMode: {self.clip_app.delayed_clip}\nMultiClip: {self.clip_app.multi_clip}"
        self.menu_options = (("ScreenShot", self.resource_path("pyclip_screenshot.ico"), self.call_clipwin), 
                             ("Gif", self.resource_path("pyclip_gif.ico"), self.call_gifwin), 
                             ("BringAllForward", self.resource_path("pyclip_bringforward.ico"), self.bringfront),
                             ("SnapShotMode", self.resource_path("pyclip_snapshot.ico"), self.snapshot_mode), 
                             ("DelayMode", self.resource_path("pyclip_delay.ico"), self.delay_mode), 
                             ("MultiMode", self.resource_path("pyclip_multi.ico"), self.multi_mode), 
                             ("DestroyAllClips", self.resource_path("pyclip_destroy.ico"), self.call_destroy_all),
                             ("Settings", "pyclip_settings.ico", self.call_settings_window),
                             ('Reload', self.resource_path("pyclip_reload.ico"), self.restart_program)
                             )
        
        self.sysTrayIcon = SysTrayIcon(self.resource_path("pyclip_default.ico"), self.hover_text, self.menu_options, on_quit=self.on_quit_callback, default_menu_index=1)
        self.sysTrayIcon.start()
        root.iconbitmap(default=self.resource_path("pyclip_default.ico"))
    
        #threading.Thread(target = self.update_all_thread, args = (), daemon = True).start()

    #***************** Call settings window *************. 
    def call_settings_window(self, systray):
        self.clip_app.settings_window()

    #***************** Update hovertext *************. 
    def update_hov_text(self, systray):
        self.hover_text = f"ScreenCaptureTool\nSnapshotMode: {self.clip_app.snapshot}\nDelayMode: {self.clip_app.delayed_clip}\nMultiClip: {self.clip_app.multi_clip}"
        systray.update(hover_text =self.hover_text)

    #***************** Bring all clips to front *************. 
    def bringfront(self, systray):
        self.clip_app.bringallfront()

    #***************** Call create clip window *************. 
    def call_clipwin(self, systray):
        self.clip_app.on_activate_i()

    #***************** Call create gif window *************. 
    def call_gifwin(self, systray):
        self.clip_app.on_activate_gif()


    #***************** Call destroy all toplevel *************. 
    def call_destroy_all(self, systray):
        self.clip_app.destroy_all(1)

    #***************** Path to image for exe *************. 
    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    #***************** Run the file again, and destroy the old 1 *************. 
    def restart_program(self, systray):
        quit_id = [i for i in list(systray._menu_actions_by_id.keys())  if systray._menu_actions_by_id[i] == "QUIT"]
        os.startfile(*sys.argv)
        SysTrayIcon._execute_menu_option(systray, quit_id[0])
        os.kill(os.getpid(), signal.SIGTERM)

    #***************** Set the clipping windows to be screenshot of each monitor rather than transparent window *************. 
    def snapshot_mode(self, systray):
        self.clip_app.snapshot = 1 - self.clip_app.snapshot # Toggle from 0 to 1 and 1 to 0
        if self.clip_app.snapshot: 
            self.clip_app.delayed_clip = 0
            self.clip_app.default_alpha = 1
        else: self.clip_app.default_alpha = 0.3
        self.update_hov_text(systray)

    #***************** Enable delay mode which saves monitor screenshots in memory to clip when called again *************. 
    def delay_mode(self, systray):
        self.clip_app.delayed_clip = 1 - self.clip_app.delayed_clip # Toggle from 0 to 1 and 1 to 0
        if self.clip_app.delayed_clip: 
            self.clip_app.snapshot = 0
            self.clip_app.default_alpha = 1
        else: self.clip_app.default_alpha = 0.3
        self.update_hov_text(systray)

    #***************** Enable multi mode *************. 
    def multi_mode(self, systray):
        self.clip_app.multi_clip = 1 - self.clip_app.multi_clip # Toggle from 0 to 1 and 1 to 0
        self.update_hov_text(systray)

    #***************** Kill tkinter mainloop and remove all hotkey threads *************. 
    def kill_program(self):
        try:
            GlobalHotKeys.unregisterHotkKey()        
            #kb.send(self.clip_app.hotkey_visual_in_settings["current_hotkey_1"]) # this is the dumbest thing ever but it works and i couldn't think of another way 
        except Exception as e:print(e)

        root.destroy()
        os.kill(os.getpid(), signal.SIGTERM)
        raise SystemExit

    #***************** On tray Quit button, destroy tray icon and kill process *************. 
    def on_quit_callback(self, systray):
        SysTrayIcon.shutdown
        threading.Thread(target = self.kill_program, daemon = True).start()



if __name__ == '__main__':
    root = Tk()
    snip = snipping_tool()
    tr = tray(snip)
    snip.tray = tr
    root.mainloop()