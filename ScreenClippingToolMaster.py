import sys, os, signal, time, threading, PIL.Image, ctypes, datetime, gc, pytesseract, imageio, numpy, io, win32clipboard
import keyboard as kb
import json
from infi.systray import SysTrayIcon 
from tkinter import *
from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter import messagebox, ttk
from tkinter.colorchooser import askcolor
from PIL import ImageGrab, Image, ImageTk
from threading import Thread, Timer
from screeninfo import get_monitors
from ctypes import windll, Structure, c_ulong, byref
from desktopmagic.screengrab_win32 import getDisplayRects, saveScreenToBmp, saveRectToBmp, getScreenAsImage, getRectAsImage, getDisplaysAsImages
from pynput import keyboard



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

    

class Global_hotkeys:
    import ctypes
    import pynput.keyboard
    MODIFIER_KEYS_INT = {"<cmd>" : 0x0008,  "<shift>" : 0x0004,    "<alt>" : 0x0001,  "<ctrl>" : 0x0002, "" : 0x0000}
    PYNPUT_TO_VK = {'<scroll_lock>' : 0x91,'<num_lock>' : 0x90,'<menu>' : 0xa5,'<page_up>' : 0x21,'<page_down>' : 0x22,'0' : 0x30,'1' : 0x31,'2' : 0x32,'3' : 0x33,'4' : 0x34,'5' : 0x35,'6' : 0x36,'7' : 0x37,'8' : 0x38,'9' : 0x39,'a' : 0x41,'b' : 0x42,'c' : 0x43,'d' : 0x44,'e' : 0x45,'f' : 0x46,'g' : 0x47,'h' : 0x48,'i' : 0x49,'j' : 0x4a,'k' : 0x4b,'l' : 0x4c,'m' : 0x4d,'n' : 0x4e,'o' : 0x4f,'p' : 0x50,'q' : 0x51,'r' : 0x52,'s' : 0x53,'t' : 0x54,'u' : 0x55,'v' : 0x56,'w' : 0x57,'x' : 0x58,'y' : 0x59,'z' : 0x5a,'<backspace>' : 0x8,'<tab>' : 0x9,'<clear>' : 0xc,'<enter>' : 0xd,'<shift>' : 0x10,'<control>' : 0x11,'<alt>' : 0x12,'<pause>' : 0x13,'<caps_lock>' : 0x14,'<esc>' : 0x1b,'<space>' : 0x20,'<end>' : 0x23,'<home>' : 0x24,'<left>' : 0x25,'<up>' : 0x26,'<right>' : 0x27,'<down>' : 0x28,'<select>' : 0x29,'<print>' : 0x2a,'<execute>' : 0x2b,'<print_screen>' : 0x2c,'<insert>' : 0x2d,'<delete>' : 0x2e,'<help>' : 0x2f,'<f1>' : 0x70,'<f2>' : 0x71,'<f3>' : 0x72,'<f4>' : 0x73,'<f5>' : 0x74,'<f6>' : 0x75,'<f7>' : 0x76,'<f8>' : 0x77,'<f9>' : 0x78,'<f10>' : 0x79,'<f11>' : 0x7a,'<f12>' : 0x7b,'<f13>' : 0x7c,'<f14>' : 0x7d,'<f15>' : 0x7e,'<f16>' : 0x7f,'<f17>' : 0x80,'<f18>' : 0x81,'<f19>' : 0x82,'<f20>' : 0x83}
    REGISTER_HOTKEY_WINDLL = ctypes.windll.user32.RegisterHotKey
    UNREGISTER_HOTKEY_WINDLL = ctypes.windll.user32.UnregisterHotKey
    REGISTER_HOTKEY_PYNPUT =  pynput.keyboard.GlobalHotKeys
    UNREGISTER_HOTKEY_PYNPUT = pynput.keyboard.GlobalHotKeys.stop


    @classmethod
    def create_hotkey(cls, hwnd : int, hotkey_id : int, modifier_keys : list, activate_key : int, callback, *args):
        """creates a blocking hotkey (Windows key modifier not blocked)\nhotkey_id must be int \nmodifier_keys should be any in ["<cmd>", "<shift>", "<alt>", "<ctrl>", ""] \nactivate_key should be string"""
        activate_key = activate_key.lower()
        if cls.PYNPUT_TO_VK[activate_key]:
            modifier_int = 0; modifier_str = []
            for x, i in enumerate(modifier_keys):
                if i in cls.MODIFIER_KEYS_INT.keys():
                    modifier_int += cls.MODIFIER_KEYS_INT[i]
                    modifier_str.append(i) #if x != len(modifier_keys) -1 else i
                else: raise Exception(f"{i} is not in the modifier_key dictionary {cls.MODIFIER_KEYS_INT.keys()}")
            modifier_str = "+".join(modifier_str) + "+" if "+".join(modifier_str) != "" else ""
            windll_hotkey = cls.REGISTER_HOTKEY_WINDLL(hwnd, int(hotkey_id), modifier_int, cls.PYNPUT_TO_VK[activate_key])
            pynput_hotkey = cls.REGISTER_HOTKEY_PYNPUT({f"{modifier_str}{activate_key}" : lambda args = args: callback(args)}) if args != () else cls.REGISTER_HOTKEY_PYNPUT({f"{modifier_str}{activate_key}" : callback}); pynput_hotkey.start()
            return (pynput_hotkey, windll_hotkey, f"{modifier_str}{activate_key}", hotkey_id)

    @classmethod
    def remove_hotkey(cls, hwnd : int, hotkey_id : int, create_hotkey_return_object : object):
        """remove the hotkeys made"""
        windll_hotkey=cls.UNREGISTER_HOTKEY_WINDLL(hwnd, hotkey_id)
        pynput_hotkey = cls.UNREGISTER_HOTKEY_PYNPUT(create_hotkey_return_object)

        
    @classmethod
    def return_vk_detail(cls):
        data = b"VK_OEM_CLEAR : 0xFE, Clear key\\nVK_PA1 : 0xFD, PA1 key\\nVK_NONAME : 0xFC, Reserved\\nVK_ZOOM : 0xFB, Zoom key\\nVK_PLAY : 0xFA, Play key\\nVK_EREOF : 0xF9, Erase EOF key\\nVK_EXSEL : 0xF8, ExSel key\\nVK_CRSEL : 0xF7, CrSel key\\nVK_ATTN : 0xF6, Attn key\\n0xE9-F5 : OEM, specific\\n- : 0xE8, Unassigned\\nVK_PACKET : 0xE7, Used to pass Unicode characters as if they were keystrokes. The VK_PACKET key is the low word of a 32-bit Virtual Key value used for non-keyboard input methods. For more information, see Remark in KEYBDINPUT, SendInput, WM_KEYDOWN, and WM_KEYUP\\n0xE6 : OEM, specific\\nVK_PROCESSKEY : 0xE5, IME PROCESS key\\n0xE3-E4 : OEM, specific\\nVK_OEM_102 : 0xE2, Either the angle bracket key or the backslash key on the RT 102-key keyboard\\n0xE1 : OEM, specific\\n- : 0xE0, Reserved\\nVK_OEM_8 : 0xDF, Used for miscellaneous characters; it can vary by keyboard.\\nVK_OEM_7 : 0xDE,  For the US standard keyboard, the 'single-quote/double-quote' key\\nVK_OEM_6 : 0xDD, Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the ']}' key\\nVK_OEM_5 : 0xDC, Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '\\\\|' key\\nVK_OEM_4 : 0xDB, Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '[{' key\\n- : 0xD8-DA, Unassigned\\n- : 0xC1-D7, Reserved\\nVK_OEM_3 : 0xC0, Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '`~' key\\nVK_OEM_2 : 0xBF, Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '/?' key\\nVK_OEM_PERIOD : 0xBE, For any country/region, the '.' key\\nVK_OEM_MINUS : 0xBD, For any country/region, the '-' key\\nVK_OEM_COMMA : 0xBC, For any country/region, the ',' key\\nVK_OEM_PLUS : 0xBB, For any country/region, the '+' key\\nVK_OEM_1 : 0xBA, Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the ';:' key\\n- : 0xB8-B9, Reserved\\nVK_LAUNCH_APP2 : 0xB7, Start Application 2 key\\nVK_LAUNCH_APP1 : 0xB6, Start Application 1 key\\nVK_LAUNCH_MEDIA_SELECT : 0xB5, Select Media key\\nVK_LAUNCH_MAIL : 0xB4, Start Mail key\\nVK_MEDIA_PLAY_PAUSE : 0xB3, Play/Pause Media key\\nVK_MEDIA_STOP : 0xB2, Stop Media key\\nVK_MEDIA_PREV_TRACK : 0xB1, Previous Track key\\nVK_MEDIA_NEXT_TRACK : 0xB0, Next Track key\\nVK_VOLUME_UP : 0xAF, Volume Up key\\nVK_VOLUME_DOWN : 0xAE, Volume Down key\\nVK_VOLUME_MUTE : 0xAD, Volume Mute key\\nVK_BROWSER_HOME : 0xAC, Browser Start and Home key\\nVK_BROWSER_FAVORITES : 0xAB, Browser Favorites key\\nVK_BROWSER_SEARCH : 0xAA, Browser Search key\\nVK_BROWSER_STOP : 0xA9, Browser Stop key\\nVK_BROWSER_REFRESH : 0xA8, Browser Refresh key\\nVK_BROWSER_FORWARD : 0xA7, Browser Forward key\\nVK_BROWSER_BACK : 0xA6, Browser Back key\\nVK_RMENU : 0xA5, Right MENU key\\nVK_LMENU : 0xA4, Left MENU key\\nVK_RCONTROL : 0xA3, Right CONTROL key\\nVK_LCONTROL : 0xA2, Left CONTROL key\\nVK_RSHIFT : 0xA1, Right SHIFT key\\nVK_LSHIFT : 0xA0, Left SHIFT key\\n0x97-9F : Unassigned, \\n0x92-96 : OEM, specific -\\nVK_SCROLL : 0x91, SCROLL LOCK key\\nVK_NUMLOCK : 0x90, NUM LOCK key\\n- : 0x88-8F, Unassigned\\nVK_F24 : 0x87, F24 key\\nVK_F230x86 : F23, key\\nVK_F22 : 0x85, F22 key\\nVK_F21 : 0x84, F21 key\\nVK_F20 : 0x83, F20 key\\nVK_F19 : 0x82, F19 key\\nVK_F18 : 0x81, F18 key\\nVK_F17 : 0x80, F17 key\\nVK_F16 : 0x7F, F16 key\\nVK_F15 : 0x7E, F15 key\\nVK_F14 : 0x7D, F14 key\\nVK_F13 : 0x7C, F13 key\\nVK_F12 : 0x7B, F12 key\\nVK_F11 : 0x7A, F11 key\\nVK_F10 : 0x79, F10 key\\nVK_F9 : 0x78, F9 key\\nVK_F8 : 0x77, F8 key\\nVK_F7 : 0x76, F7 key\\nVK_F6 : 0x75, F6 key\\nVK_F5 : 0x74, F5 key\\nVK_F4 : 0x73, F4 key\\nVK_F3 : 0x72, F3 key\\nVK_F2 : 0x71, F2 key\\nVK_F1 : 0x70, F1 key\\nVK_DIVIDE : 0x6F, Divide key\\nVK_DECIMAL : 0x6E, Decimal key\\nVK_SUBTRACT : 0x6D, Subtract key\\nVK_SEPARATOR : 0x6C, Separator key\\nVK_ADD : 0x6B, Add key\\nVK_MULTIPLY : 0x6A, Multiply key\\nVK_NUMPAD9 : 0x69, Numeric keypad 9 key\\nVK_NUMPAD8 : 0x68, Numeric keypad 8 key\\nVK_NUMPAD7 : 0x67, Numeric keypad 7 key\\nVK_NUMPAD6 : 0x66, Numeric keypad 6 key\\nVK_NUMPAD5 : 0x65, Numeric keypad 5 key\\nVK_NUMPAD4 : 0x64, Numeric keypad 4 key\\nVK_NUMPAD3 : 0x63, Numeric keypad 3 key\\nVK_NUMPAD2 : 0x62, Numeric keypad 2 key\\nVK_NUMPAD1 : 0x61, Numeric keypad 1 key\\nVK_NUMPAD0 : 0x60, Numeric keypad 0 key\\nVK_SLEEP : 0x5F, Computer Sleep key\\n- : 0x5E, Reserved\\nVK_APPS : 0x5D, Applications key (Natural keyboard)\\nVK_RWIN : 0x5C, Right Windows key (Natural keyboard)\\nVK_LWIN : 0x5B, Left Windows key (Natural keyboard)\\n0x5A : Z, key\\n0x59 : Y, key\\n0x58 : X, key\\n0x57 : W, key\\n0x56 : V, key\\n0x55 : U, key\\n0x54 : T, key\\n0x53 : S, key\\n0x52 : R, key\\n0x51 : Q, key\\n0x50 : P, key\\n0x4F : O, key\\n0x4E : N, key\\n0x4D : M, key\\n0x4C : L, key\\n0x4B : K, key\\n0x4A : J, key\\n0x49 : I, key\\n0x48 : H, key\\n0x47 : G, key\\n0x46 : F, key\\n0x45 : E, key\\n0x44 : D, key\\n0x43 : C, key\\n0x42 : B, key\\n0x41 : A, key\\n- : 0x3A-40, Undefined\\n0x39 : 9, key\\n0x38 : 8, key\\n0x37 : 7, key\\n0x36 : 6, key\\n0x35 : 5, key\\n0x34 : 4, key\\n0x33 : 3, key\\n0x32 : 2, key\\n0x31 : 1, key\\n0x30 : 0, key\\nVK_HELP : 0x2F, HELP key\\nVK_DELETE : 0x2E, DEL key\\nVK_INSERT : 0x2D, INS key\\nVK_SNAPSHOT : 0x2C, PRINT SCREEN key\\nVK_EXECUTE : 0x2B, EXECUTE key\\nVK_PRINT : 0x2A, PRINT key\\nVK_SELECT : 0x29, SELECT key\\nVK_DOWN : 0x28, DOWN ARROW key\\nVK_RIGHT : 0x27, RIGHT ARROW key\\nVK_UP : 0x26, UP ARROW key\\nVK_LEFT : 0x25, LEFT ARROW key\\nVK_HOME : 0x24, HOME key\\nVK_END : 0x23, END key\\nVK_NEXT : 0x22, PAGE DOWN key\\nVK_PRIOR : 0x21, PAGE UP key\\nVK_SPACE : 0x20, SPACEBAR\\nVK_MODECHANGE : 0x1F, IME mode change request\\nVK_ACCEPT : 0x1E, IME accept\\nVK_NONCONVERT : 0x1D, IME nonconvert\\nVK_CONVERT : 0x1C, IME convert\\nVK_ESCAPE : 0x1B, ESC key\\nVK_IME_OFF : 0x1A, IME Off\\nVK_KANJI : 0x19, IME Kanji mode\\nVK_HANJA : 0x19, IME Hanja mode\\nVK_FINAL : 0x18, IME final mode\\nVK_JUNJA : 0x17, IME Junja mode\\nVK_IME_ON : 0x16, IME On\\nVK_HANGUL : 0x15, IME Hangul mode\\nVK_HANGUEL : 0x15, IME Hanguel mode (maintained for compatibility; use VK_HANGUL)\\nVK_KANA : 0x15, IME Kana mode\\nVK_CAPITAL : 0x14, CAPS LOCK key\\nVK_PAUSE : 0x13, PAUSE key\\nVK_MENU : 0x12, ALT key\\nVK_CONTROL : 0x11, CTRL key\\nVK_SHIFT : 0x10, SHIFT key\\n- : 0x0E-0F, Undefined\\nVK_RETURN : 0x0D, ENTER key\\nVK_CLEAR : 0x0C, CLEAR key\\n- : 0x0A-0B, Reserved\\nVK_TAB : 0x09, TAB key\\nVK_BACK : 0x08, BACKSPACE key\\n- : 0x07, Undefined\\nVK_XBUTTON2 : 0x06, X2 mouse button\\nVK_XBUTTON1 : 0x05, X1 mouse button\\nVK_MBUTTON : 0x04, Middle mouse button (three-button mouse)\\nVK_CANCEL : 0x03, Control-break processing\\nVK_RBUTTON : 0x02, Right mouse button\\nVK_LBUTTON : 0x01, Left mouse button"
        return data.decode("unicode-escape")



class snipping_tool():

    def __init__(self):
        self.tray = None
        
        self.drag_box = None        # Used to show selected area
        self.start_x = None         # On click x
        self.start_y = None         # On click y
        self.curx = None            # After releasing x
        self.cury = None            # After releasing y
        self.monitorid = None       # Monitor id of the monitor you started on
        #self.end_monitorid = None   # Monitor id of the monitor you ended on
        self.zoom_image = None      # Image displayed when you zoom in 
        self.img = None             # Temporary image that is shown when you zoom in
        self.old_x = None
        self.old_y = None

        try:
            with open(resource_path("settings.json"), "r") as settings_file:
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
                settings_file.close()
                print("settings imported successfully")

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
            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "WindowsKey", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "z", "current_hotkey_1" : '<cmd>+z', "id_1" : 0,
                                              "hotkey_2_modifyer_1" : "WindowsKey", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "c", "current_hotkey_2" : '<cmd>+c', "id_2" : 1}       
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
            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "WindowsKey", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "z", "current_hotkey_1" : '<cmd>+z', "id_1" : 0,
                                              "hotkey_2_modifyer_1" : "WindowsKey", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "c", "current_hotkey_2" : '<cmd>+c', "id_2" : 1}
            print("there was an error importing the settings \n{}".format(e))
        
        self.zoomcycle = 0          # How far in you are zoomed
        self.hwnd = root.winfo_id()
        self.record_on = False      # Variable that tells the gif mode when to stop taking pictures

        self.save_img_data = {}     # Keep track of the img data so it can be saved, or used for OCR
        self.lines_list = {}
        self.gif = []               # Keep all the pictures taken in gif mode
        self.threads = []           # Keep track of used threads to join back later
        self.gif_canvas = []     # Keep track of gif screens to disable binds
        
        print("snipping tool started")

        #***************** Hide root window *************. 
        root.withdraw()
        root.attributes('-alpha', .0)
        root.attributes('-topmost', 'true')

        # <cmd> == WindowsKey, <alt> == AltKey, <ctrl> == CtrlKey, <shift> = shift
        self.clip_hotkey =  Global_hotkeys.create_hotkey(self.hwnd, 0, self.hotkey_visual_in_settings["current_hotkey_1"].split("+")[:-1], self.hotkey_visual_in_settings["hotkey_1_key"], self.on_activate_i) #keyboard.GlobalHotKeys({ '<cmd>+z': self.on_activate_i})
        self.gif_hotkey =  Global_hotkeys.create_hotkey(self.hwnd, 1, self.hotkey_visual_in_settings["current_hotkey_2"].split("+")[:-1], self.hotkey_visual_in_settings["hotkey_2_key"], self.on_activate_gif) #keyboard.GlobalHotKeys({ '<cmd>+c': self.on_activate_gif})



    #*****************                *************. 
    #***************** Call Functions *************. 
    #*****************                *************. 

    def block_hotkeys(self, hotkey : list, script : list, hotkey_name :list, number_of_hotkeys : int):
        if self.block_hotkeys:
            ahk_blocking_hotkeys.create_blocking_hotkeys(hotkey, script, hotkey_name, number_of_hotkeys)


    def on_activate_gif(self):
        root.after(0 , lambda : self.create_gif_window())


    def on_activate_i(self):
        root.after(0 , lambda : self.create_clip_window())


    def call_create_clip_window(self):
        root.after(0 , lambda : self.create_clip_window())


    #***************** Run the record function in seperate thread to ensure it doesn't block main program *************. 
    def record_thread(self, x1, y1, x2, y2):
        for widget in root.winfo_children():
            if isinstance(widget, Toplevel):
                if str(widget.title()).find("clip_window") != -1:
                    widget.attributes('-alpha', .0)  
        a = Thread(target = self.record, args = (x1, y1, x2, y2))
        self.threads.append(a)
        a.start()






    #*****************                                *************. 
    #***************** Pictures / Recording Functions *************. 
    #*****************                                *************. 
       
       



    #***************** Take the screenshot at select location on selected monitor *************. 
    def screenshot(self, x1, y1, x2, y2):
        monitor_ids = {} 
        for i in get_monitors():
            monitor_ids[windll.user32.MonitorFromPoint(i.x, i.y, 2)] = i # param_1 = monitor_x + 1,  param_2 = monitor_y,  param_3 [0], [1], [3] = monitor_default to null, monitor_default to primary, monitor_default to nearest 
        print(f"\nstart monitor  = {self.monitorid}")
        if self.monitorid in list(monitor_ids.keys()):# and self.end_monitorid in list(monitor_ids.keys()): 
            #print('monitor is in')
            #if self.monitorid == self.end_monitorid:
            monitor = monitor_ids[self.monitorid] 
            x1, y1, x2, y2 = int(x1 + monitor.x), int(y1 + monitor.y), int(x2 + monitor.x), int(y2 + monitor.y)
            try:
                img = getRectAsImage((x1, y1, x2, y2)) # take image
                dispImg = ImageTk.PhotoImage(img)
            except Exception as e: 
                print(e)
                img, dispImg = None, None
            return dispImg, (monitor.x, monitor.y), img
        return None, 0, None


    
        

    #***************** Take rapid screenshots of selected area and stick them into an array *************. 
    def record(self, x1, y1, x2, y2):
        self.record_on = True
        monitor_ids = {} 
        for i in get_monitors():
            monitor_ids[windll.user32.MonitorFromPoint(i.x, i.y, 2)] = i # param_1 = monitor_x + 1,  param_2 = monitor_y,  param_3 [0], [1], [3] = monitor_default to null, monitor_default to primary, monitor_default to nearest 
        
        print(f"\nstart monitor = [{self.monitorid}")
        if self.monitorid in list(monitor_ids.keys()):# and self.end_monitorid in list(monitor_ids.keys()): 
            #if self.monitorid == self.end_monitorid:
            monitor = monitor_ids[self.monitorid]
            x1, y1, x2, y2 = int(x1 + monitor.x), int(y1 + monitor.y), int(x2 + monitor.x), int(y2 + monitor.y)
            while self.record_on == True:
                img = getRectAsImage((x1, y1, x2, y2))
                self.gif.append(img)
                del img
                print('image taken')
                time.sleep(0.05)
            gc.collect()






    #*****************                       *************. 
    #***************** Clip window Functions *************. 
    #*****************                       *************. 





    #***************** Create the clipping window for each monitor *************. 
    @cooldown(1.5)
    def create_gif_window(self):
        self.destroy_all(0)

        monitors = get_monitors()
        for index, monitor in enumerate(monitors): 
            monx = int(monitor.x); mony = int(monitor.y); width = int(monitor.width); height = int(monitor.height)

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
            screen.pack(fill=BOTH, expand=YES)

            screen.bind("<ButtonRelease-3>", self.OnRightClick)
            screen.bind("<ButtonPress-1>", self.OnLeftClick)
            screen.bind("<B1-Motion>", self.OnDrag)
            screen.bind("<ButtonRelease-1>", self.OnReleaseGif)

            self.gif_canvas.append(screen) 

            master_screen.lift()
            master_screen.update()

            

    #***************** Create the clipping window for each monitor *************. 
    @cooldown(1.5)
    def create_clip_window(self):
        self.destroy_all(0)

        monitors = get_monitors()
        if self.delayed_clip:
            if any([i for i in self.save_img_data.keys() if i.find("delay_clip") != -1]): # If there are any delay_clips in the dictionary display them
                for x, i in enumerate(monitors): 
                    self.lines_list[x] = {"dims" : [i.width, i.height, i.name], "lines" : None}
                    delayed_clips = [i for i in self.save_img_data.keys() if i.find("delay_clip") != -1] # Get all the clips tagged with delay_clip                   
                    img = ImageTk.PhotoImage(self.save_img_data[delayed_clips[x]])
                    self.make_clip_win(i, 1, img)
                    del img
                    print(delayed_clips)

                for i in delayed_clips:
                    del self.save_img_data[i]       # Remove all the delay_clips 
            else:                                   # If there are no clips take screenshots 
                for i in monitors:  
                    img = getRectAsImage((i.x, i.y, i.width + i.x, i.height + i.y))
                    date_time = str(datetime.datetime.now()) + "delay_clip"         # Name the clip using the date time and mark it as a delay_clip
                    self.save_img_data[date_time] = img
                    del img
                    print("image saved")
        else:
            for x, i in enumerate(monitors): # Create clipping window for all monitors 
                self.lines_list[x] = {"dims" : [i.width, i.height, i.name], "lines" : None}
                if self.snapshot:
                    img = ImageTk.PhotoImage(getRectAsImage((i.x, i.y, i.width + i.x, i.height + i.y)))
                    self.make_clip_win(i, self.snapshot, img)
                    del img
                else:
                    self.make_clip_win(i, self.snapshot)

        gc.collect()


    #***************** Make clip window *************. 
    def make_clip_win(self, monitorobj, snapshot, img = None):
        monx = int(monitorobj.x); mony = int(monitorobj.y); width = int(monitorobj.width); height = int(monitorobj.height)

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
        self.start_x = event.widget.canvasx(event.x)
        self.start_y = event.widget.canvasy(event.y)
        self.monitorid = windll.user32.MonitorFromPoint(int(root.winfo_pointerx()), int(root.winfo_pointery()), 2)

        if self.snapshot or self.delayed_clip: 
            self.drag_box = event.widget.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=1)
        else: 
            self.drag_box = event.widget.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=1, fill="blue")


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




    #***************** Stop taking pictures, save the gif *************. 
    def stop_gif(self):
        self.record_on = False

        for widget in root.winfo_children():
            if isinstance(widget, Toplevel):
                if str(widget.title()).find("clip_window") != -1:
                    widget.attributes('-alpha', .3)  

        for i in self.threads.copy():
            i.join()
            self.threads.remove(i)
        gc.collect()


        
    #***************** Save gif *************. 
    def save_gif(self):
        self.record_on = False

        for widget in root.winfo_children():
            if isinstance(widget, Toplevel):
                if str(widget.title()).find("clip_window") != -1: # Set all clip windows back to regular transparency 
                    widget.attributes('-alpha', .3)  
        
        for i in self.threads.copy():
            i.join()                # Clean up threads
            del self.threads[self.threads.index(i)]

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
        except KeyError:
            messagebox.showerror(title="", message="The filetype {} is most likely unsupported".format(format), parent=root)
            print(KeyError)
        except Exception as e: 
            print(e)
            messagebox.showerror(title="", message=f"There was an error that was not a problem with the filetype please tell minnowo \n{e}", parent=root)
        del f
        self.gif.clear()
        self.destroy_all()
        gc.collect()



    #***************** When you let go of the gif select window, get coords, create buttons to start/stop recording the video *************. 
    def OnReleaseGif(self, event): 
        def top(event, widget):
            widget.lift()
        def on_unmap(event, widget): 
            widget.deiconify()


        #self.end_monitorid = windll.user32.MonitorFromPoint(int(root.winfo_pointerx()), int(root.winfo_pointery()), 2) # Set finsih monitor id
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

        buttons = Toplevel(event.widget)
        buttons.protocol("WM_DELETE_WINDOW", self.destroy_all)                              # If you hit the X on the button window destroy the clip windows 
        buttons.lift()                                                                      # Bring in front of clipping windows 
        buttons.resizable(0,0)                                                              # Cant resize
        buttons.attributes("-topmost", True)                                                # Always on top
        mousex, mousey = root.winfo_pointerxy()                                             # Get mouse xy
        buttons.geometry(f"{250}x{50}+{mousex - 115}+{mousey - 10}")                        # Spawn the window on your mouse
        buttons.bind("<Unmap>", lambda event, widget = buttons : on_unmap(event, widget))   # Bind the minamize button to a function that maximizes the window 

        #***************** Make buttons *************. 
        record_button = Button(buttons, text = "Start", command = lambda *args : self.record_thread(x1, y1, x2, y2))
        record_button.pack(side = LEFT,expand = True, fill = BOTH)

        stop_record_button = Button(buttons, text = "Stop", command = self.stop_gif)
        stop_record_button.pack(side = LEFT, expand = True, fill = BOTH)

        save_record_button = Button(buttons, text = "Save", command = self.save_gif)
        save_record_button.pack(side = LEFT, expand = True, fill = BOTH)

        for canvas in self.gif_canvas:
            for bind in ["<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>"]:canvas.unbind(bind)
            canvas.bind("<ButtonPress-1>", lambda event, widget = buttons : top(event, widget))

        self.gif_canvas.clear()


    






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
        if (self.win32clipboard or force_win32) and win["cursor"] != "pencil":
            output = io.BytesIO()
            self.save_img_data[win.title()].convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
        else:

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
            pytesseract.pytesseract.tesseract_cmd = '{}\\tess_folder\\tesseract.exe'.format(os.getcwd())
            image_text = pytesseract.image_to_string(self.save_img_data[win.title()], lang='eng', config= "--psm 1")
            root.clipboard_clear()
            root.clipboard_append(image_text)
            messagebox.showinfo(title="OCR Output", message=image_text, parent=root)
            print(image_text)
        except Exception as e: 
            messagebox.showerror(title="", message="error with ocr:\n {}".format(e), parent=root)


    def paint(self, event, win):
        if self.old_x and self.old_y:
            win.create_line(self.old_x, self.old_y, event.x, event.y,
                               width=self.line_width, fill=self.line_color,
                               capstyle=ROUND, smooth=TRUE, splinesteps=36)
        self.old_x = event.x
        self.old_y = event.y

    def reset(self, event):
        self.old_x, self.old_y = None, None

    def brush_size(self, event):
        if (event.delta > 0):
            self.line_width += 1 if self.line_width + 1 <= 200 else 0
        if (event.delta < 0):
            self.line_width -= 1 if self.line_width - 1 >= 1 else 0

    def create_drawing_settings_win(self, win):
        def change_line_color(*args):
            a = askcolor(color = self.line_color)
            if a[1]:
                self.line_color = a[1]
                print(f"line color = {self.line_color}")

        drawing_root = Toplevel(win)
        drawing_root.title("DrawingSettings")
        drawing_root.geometry(f"+{win.winfo_x()}+{win.winfo_y()}")
        drawing_root.minsize(260, 90) 
        drawing_root.attributes('-topmost', 'true')

        draw_color = Button(drawing_root, text = "LineColor", command = change_line_color)
        line_width_combobox = ttk.Combobox(drawing_root, values = [i for i in range(1, 200)])
        line_width_combobox.set(self.line_width)

        draw_color.grid(column = 0, row = 0, sticky = EW)
        line_width_combobox.grid(column = 0, row = 1)

    def enable_drawing(self,win):
        children = win.winfo_children() # [1] == the canvas with the image
        if win["cursor"] == "arrow": # not in drawing mode
            win.attributes('-topmost', 'false')
            win.overrideredirect(0)
            children[1].unbind("<B1-Motion>")
            win.unbind("<MouseWheel>")
            win.unbind("<Motion>")
            children[1].bind('<B1-Motion>', lambda event, win = children[1] : self.paint(event, win))
            children[1].bind('<ButtonRelease-1>', self.reset)
            win.bind("<MouseWheel>", self.brush_size)
            win.config(cursor = "pencil")
            self.create_drawing_settings_win(win)
            
        else:                       # in drawing mode
            for i in children: 
                if isinstance(i, Toplevel): i.destroy()
            win.attributes('-topmost', 'true')
            win.overrideredirect(1)
            win.unbind("<MouseWheel>")
            win.unbind("<Motion>")
            children[1].unbind("<B1-Motion>")
            children[1].unbind('<ButtonRelease-1>')
            children[1].bind("<B1-Motion>", lambda event, win = win : self.Dragging(event, win))
            win.bind("<MouseWheel>",self.zoomer)
            win.bind("<Motion>", self.crop)
            win.config(cursor = "arrow")
        
            
            


    #***************** Bring up the right click menu *************. 
    def show_popup_menu(self, event, menu):
        hotkey_visual = [self.hotkey_visual_in_settings["current_hotkey_1"], self.hotkey_visual_in_settings["current_hotkey_2"]]
        hotkey_visual = [i.replace("<", "").replace(">","").replace("cmd","win").title() for i in hotkey_visual]
        try: 
            menu.entryconfigure(7, accelerator = self.snapshot)
            menu.entryconfigure(8, accelerator = self.delayed_clip)
            menu.entryconfigure(9, accelerator = self.multi_clip)
            menu.entryconfigure(11, accelerator = hotkey_visual[0])
            menu.entryconfigure(12, accelerator = hotkey_visual[1])
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
            self.curx, self.cury = (event.x, event.y)

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
            mons = get_monitors()
            monx = (mons[0].x, mons[0].y)
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
            right_click_menu.add_command(label ="Copy", accelerator="Ctrl+C", command = lambda event = None, win= display_screen : self.copy(event, win))
            right_click_menu.add_command(label ="Save", accelerator="Ctrl+S", command = lambda event = None, win= display_screen : self.save(event, win))
            right_click_menu.add_command(label ="OCR", accelerator="Ctrl+T", command = lambda event = None, win= display_screen : self.tesseract_clip(event, win))
            right_click_menu.add_command(label ="AlwaysOnTop", accelerator="Tab", command = lambda event = None, win= display_screen : self.top_most(event, win))
            right_click_menu.add_command(label ="Destroy", accelerator="Esc", command = lambda event = None, win = display_screen : self.close(event, win))
            right_click_menu.add_command(label ="Draw", command = lambda win = display_screen : self.enable_drawing( win))
            right_click_menu.add_separator() 
            right_click_menu.add_command(label ="SnapshotMode", accelerator= self.snapshot, command = lambda :  self.toggle_snapshot_mode())
            right_click_menu.add_command(label ="DelayMode", accelerator= self.delayed_clip , command = lambda :  self.toggle_delay_mode())
            right_click_menu.add_command(label ="MultiClip", accelerator= self.multi_clip , command = lambda :  self.toggle_multi_mode())
            right_click_menu.add_separator() 
            right_click_menu.add_command(label ="TakeScreenshot", accelerator= self.hotkey_visual_in_settings["current_hotkey_1"], command = lambda :  self.call_create_clip_window())
            right_click_menu.add_command(label ="TakeGif", accelerator= self.hotkey_visual_in_settings["current_hotkey_2"], command = lambda :  self.on_activate_gif())
            right_click_menu.add_separator()
            right_click_menu.add_command(label ="DestroyAll", command = lambda :  self.destroy_all(1))
            right_click_menu.add_command(label ="BringAllFront", command = lambda :  self.bringallfront())
            right_click_menu.add_separator()
            right_click_menu.add_command(label ="Settings", command = lambda :  self.settings_window())

            label1 = Canvas(display_screen,  bg = self.border_color, borderwidth = self.border_thiccness, highlightthickness=0)#, width = width, height = height) # border color
            label1.pack(expand = True, fill = BOTH)
            label1.create_image(0, 0, image = img, anchor = NW)#image = img # Keep img in memory # VERY IMPORTANT 
            label1.image = img

            label2 = Label(display_screen) # Label that holds temp image on zoom in

            label1.bind("<B1-Motion>", lambda event, win = display_screen : self.Dragging(event, win))  # Pass current Toplevel window so it knows what window to drag/copy/destroy
            label1.bind("<Button-1>", lambda event, win = label1 : self.SaveLastClickPos(event, win))
            label1.bind('<Escape>', lambda event, win = display_screen : self.close(event, win))
            label1.bind("<Control-c>", lambda event, win = display_screen : self.copy(event, win))
            label1.bind("<Tab>", lambda event, win = display_screen : self.top_most(event, win))
            label1.bind("<Control-s>", lambda event, win= display_screen : self.save(event, win))
            label1.bind("<Control-t>", lambda event, win = display_screen : self.tesseract_clip(event, win))
            label1.bind("<Button-3>", lambda event, menu = right_click_menu : self.show_popup_menu(event, menu))

            label2.bind("<Button-3>", self.remove_zoom)
            display_screen.bind("<MouseWheel>",self.zoomer)
            display_screen.bind("<Motion>", self.crop)

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
        if fake_call == 0:                          # fake call is used to call the function without using the binds allowing the save function to remove zoomed images
            if (event.delta > 0):
                toplev = event.widget.master if fake_call == 0 else event
                self.img = self.save_img_data[str(toplev.title())]

                if self.zoomcycle != int(self.multiplyer // 0.005): 
                    self.zoomcycle += 1

            elif (event.delta < 0):

                if self.zoomcycle != 0: 
                    self.zoomcycle -= 1

        if self.zoomcycle == 0: 
            del self.img
            toplev = event.widget.master if fake_call == 0 else event
            array_of_children_widgets = toplev.winfo_children()
            self.img = None
            array_of_children_widgets[2].place(x = -10, y = -10, anchor = "e")  # Move the empty label off the visual window

            try:
                del array_of_children_widgets[2].image  # [2] == self.label2 (holds zoomed image)
                array_of_children_widgets[2].image = '' # [2] == self.label2 (holds zoomed image)
            except:pass
            
            gc.collect()

        self.crop(event)



    def crop(self,event = None):
        if (self.zoomcycle) != 0 and event != None:
            widget = event.widget.master
            array_of_children_widgets = widget.winfo_children()         # [2] == self.label2 (holds zoomed image)
            x = event.x_root - widget.winfo_rootx()                     # Get mouse x pos relative to window 
            y = event.y_root - widget.winfo_rooty()                     # Get mouse y pos relative to window 
            width = self.img.width if self.img.width > self.img.height else self.img.height  # Use whatever length is bigger
            size = int(width * self.scale_percent) , int(width * self.scale_percent)                 # Set the size of the zoom to 20% of the clips width

            multiplyer = self.multiplyer - (0.005 * self.zoomcycle)
            
            if (multiplyer) < 0.003: multiplyer = 0.004
            width = int(width * multiplyer)
            tmp = self.img.crop((x-width,y-width,x+width,y+width))

            if size[0] < 1: size = (1,1)                                # Cant resize if its less than 1
            tmp = PIL.ImageTk.PhotoImage(tmp.resize(size))
            array_of_children_widgets[2].configure(image= tmp)
            array_of_children_widgets[2].image = tmp                    # [2] == self.label2 aka the label that holds the display img, which each clip has 
            array_of_children_widgets[2].place(x = x, y = y, anchor="center")   # Adjust placement


    #*****************                           *************. 
    #***************** Other functions *************. 
    #*****************                           *************. 


    #***************** Toggle snapshot mode *************. 
    def toggle_snapshot_mode(self):
        self.snapshot = 1 - self.snapshot # Toggle from 0 to 1 and 1 to 0
        if self.snapshot: 
            self.delayed_clip = 0
            self.default_alpha = 1
        else: self.default_alpha = 0.3
        print(f"snapshot mode set: {self.snapshot}")
        self.tray.update_hov_text(self.tray.sysTrayIcon)


    #***************** Toggle delay mode *************. 
    def toggle_delay_mode(self):
        self.delayed_clip = 1 - self.delayed_clip # Toggle from 0 to 1 and 1 to 0
        if self.delayed_clip: 
            self.snapshot = 0
            self.default_alpha = 1
        else: self.default_alpha = 0.3
        print(f"delayed mode set: {self.delayed_clip}")
        self.tray.update_hov_text(self.tray.sysTrayIcon)

    def ask_toggle_auto_hide(self):
        a = messagebox.askquestion(title = "", message = "would you like to enable autohide clips to keep them out of the way when clipping?", parent = root)
        if a == "yes": self.toggle_auto_hide()

    #***************** Toggle multi mode *************. 
    def toggle_multi_mode(self):
        self.multi_clip = 1 - self.multi_clip # Toggle from 0 to 1 and 1 to 0
        print(f"multi clip mode set: {self.multi_clip}")
        self.tray.update_hov_text(self.tray.sysTrayIcon)
        if self.multi_clip and not self.auto_hide_clip: root.after(0, self.ask_toggle_auto_hide)


    #***************** Toggle lines *************. 
    def toggle_cursor_lines(self):
        self.cursor_lines = 1 - self.cursor_lines # Toggle from 0 to 1 and 1 to 0
        print(f"cursor lines set: {self.cursor_lines}")

    #***************** Toggle copymode *************. 
    def toggle_win32_clipboard(self):
        self.win32clipboard = 1 - self.win32clipboard # Toggle from 0 to 1 and 1 to 0
        print(f"win32clipboard set: {self.win32clipboard}")


    #***************** Toggle auto copy *************. 
    def toggle_auto_copy(self):
        self.auto_copy_image = 1 - self.auto_copy_image
        print(f"auto copy set : {self.auto_copy_image}")

    #***************** Toggle auto hide *************. 
    def toggle_auto_hide(self):
        self.auto_hide_clip = 1 - self.auto_hide_clip
        print(f"auto hide set : {self.auto_hide_clip}")


    #***************** Destroy all toplevel widgets or only destroy clpping windows *************.###
    def destroy_all(self, destroy = 0):
        del self.gif
        self.gif = []
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
                if str(widget.title()).find("Settings") != -1:
                    widget.destroy()



        def save_settings(*args):
            save_changes.focus()
            check_float()
            self.scale_percent = float(zoom_percent_Combobox.get())
            self.multiplyer = float(zoom_multiplyer_Combobox.get())
            self.border_thiccness = int(border_thiccness_combobox.get())

            

            if any(i not in ["WindowsKey", "Alt", "Ctrl", "Shift", "None"] for i in [hotkey_1_modifyer_1.get(), hotkey_1_modifyer_2.get(), hotkey_1_modifyer_3.get()]): 
                messagebox.showerror(title="", message="Hotkey 1 modifier was not any of the values given", parent=root)
                return
            if any(i not in ["WindowsKey", "Alt", "Ctrl", "Shift", "None"] for i in [hotkey_2_modifyer_1.get(), hotkey_2_modifyer_2.get(), hotkey_2_modifyer_3.get()]): 
                messagebox.showerror(title="", message="Hotkey 2 modifier was not any of the values given", parent=root)
                return


            correct_modifyers_for_hotkey = {"WindowsKey" : "<cmd>", "Alt" : "<alt>", "Ctrl" : "<ctrl>", "Shift" : "<shift>"}

            hotkey1 = list( dict.fromkeys([i for i in [hotkey_1_modifyer_1.get(), hotkey_1_modifyer_2.get(), hotkey_1_modifyer_3.get(), hotkey_1_key.get()] if i != "None"]))
            hotkey2 = list( dict.fromkeys([i for i in [hotkey_2_modifyer_1.get(), hotkey_2_modifyer_2.get(), hotkey_2_modifyer_3.get(), hotkey_2_key.get()] if i != "None"]))

            hotkey1_formated = [correct_modifyers_for_hotkey[i] for i in hotkey1 if i in ["WindowsKey", "Alt", "Ctrl", "Shift"]]
            hotkey2_formated = [correct_modifyers_for_hotkey[i] for i in hotkey2 if i in ["WindowsKey", "Alt", "Ctrl", "Shift"]]

            hotkey1_formated.append(hotkey1[-1].lower())
            hotkey2_formated.append(hotkey2[-1].lower())

            final_hotkey1 = "+".join(hotkey1_formated)
            final_hotkey2 = "+".join(hotkey2_formated)

            print(final_hotkey1)
            print(final_hotkey2)

            if final_hotkey1 != self.hotkey_visual_in_settings["current_hotkey_1"]:
                del hotkey1_formated[-1]
                try:
                    Global_hotkeys.remove_hotkey(self.hwnd, self.clip_hotkey[3], self.clip_hotkey[0]) #keyboard.GlobalHotKeys.stop(self.clip_hotkey)
                    self.clip_hotkey =  Global_hotkeys.create_hotkey(self.hwnd, 0, hotkey1_formated, hotkey1[-1].lower(), self.on_activate_i) #keyboard.GlobalHotKeys({ final_hotkey1 : self.on_activate_i})
                    #self.clip_hotkey.start()
                    print(f"New hotkey set for Standard mode, {final_hotkey1}")
                except Exception as e:print(e)

            if final_hotkey2 != self.hotkey_visual_in_settings["current_hotkey_2"]:
                del hotkey2_formated[-1]
                try:
                    Global_hotkeys.remove_hotkey(self.hwnd, self.gif_hotkey[3], self.gif_hotkey[0]) #keyboard.GlobalHotKeys.stop(self.gif_hotkey)
                    self.gif_hotkey =  Global_hotkeys.create_hotkey(self.hwnd, 1, hotkey2_formated, hotkey2[-1].lower(), self.on_activate_gif) #keyboard.GlobalHotKeys({ final_hotkey2 : self.on_activate_gif})
                    #self.gif_hotkey.start()
                    print(f"New hotkey set for Gif mode, {final_hotkey2}")
                except Exception as e:print(e)

            

            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : hotkey_1_modifyer_1.get(), "hotkey_1_modifyer_2" : hotkey_1_modifyer_2.get(), "hotkey_1_modifyer_3" : hotkey_1_modifyer_3.get(), "hotkey_1_key" : hotkey_1_key.get(), "current_hotkey_1" : final_hotkey1,
                                                  "hotkey_2_modifyer_1" : hotkey_2_modifyer_1.get(), "hotkey_2_modifyer_2" : hotkey_2_modifyer_2.get(), "hotkey_2_modifyer_3" : hotkey_2_modifyer_3.get(), "hotkey_2_key" : hotkey_2_key.get(), "current_hotkey_2" : final_hotkey2}
           

            self.settings_window()


        def reset_settings(*args):
            self.settings_window()

        def callbc(event):
            if event.char != "":
                try:
                    int(event.char)
                except:
                    if event.char != ".":
                        event.widget.set("")

        def force_int(event):
            if event.char != "":
                try:
                    int(event.char)
                except:
                    event.widget.set(self.border_thiccness)

        def check_float(event=None):
            try:
                numbs = [round(x, 3) for x in numpy.arange(0, 2, 0.01) if x >= 0.03]
                val = round(float(zoom_percent_Combobox.get()), 3)
                print(val)
                if val not in numbs:
                    val= min(numbs, key=lambda x:abs(x-val))
                zoom_percent_Combobox.set(val)
            except:
                zoom_percent_Combobox.set(self.scale_percent)

        def check_float_zoom_multiplyer_Combobox(event=None):
            try:
                numbs = [round(x, 3) for x in numpy.arange(0, 0.2, 0.01) if x >= 0.03]
                val = round(float(zoom_multiplyer_Combobox.get()), 3)
                print(val)
                if val not in numbs:
                    val= min(numbs, key=lambda x:abs(x-val))
                zoom_multiplyer_Combobox.set(val)
            except:
                zoom_multiplyer_Combobox.set(self.multiplyer)

        def check_modifyer_key(event):
            print(event.widget.get())
            if str(event.widget.get()) not in ["WindowsKey", "Alt", "Ctrl", "Shift", "None"]:
                event.widget.set("None")

        def prevent_multi_keys(event):
            if event.char != "":
                event.widget.set(event.char)
            else:
                print(event.widget['values'])
                event.widget.set(event.widget['values'][0])

        def change_snapshot(*args):
            self.toggle_snapshot_mode()
            snapshot_mode_button.config(text = f"SnapShotMode {self.snapshot}")
            delay_clip_mode_button.config(text = f"DelayMode {self.delayed_clip}")

        def change_delay_clip(*args):
            self.toggle_delay_mode()
            delay_clip_mode_button.config(text = f"DelayMode {self.delayed_clip}")
            snapshot_mode_button.config(text = f"SnapShotMode {self.snapshot}")

        def change_lines(*args):
            self.toggle_cursor_lines()
            cursor_guidelines_button.config(text = f"CursorLines {self.cursor_lines}")

        def change_multi_mode(*args):
            self.toggle_multi_mode()
            multi_clip_mode_button.config(text = f"MultiMode {self.multi_clip}")

        def change_win32_clip(*args):
            self.toggle_win32_clipboard()
            use_win32_clipboard_copy.config(text = f"Win32clipboard {self.win32clipboard}")
            
        def call_toggle_auto_copy(*args):
            self.toggle_auto_copy()
            auto_copy_clip_button.config(text = f"AutoCopyClip {self.auto_copy_image}")

        def call_toggle_auto_hide(*args):
            self.toggle_auto_hide()
            auto_hide_clip_button.config(text = f"AutoHideClip {self.auto_hide_clip}")

        def show_console(*args):
            PrintLogger.consolewin(root)


        def restore_default(*args):
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


            if self.hotkey_visual_in_settings["current_hotkey_1"] != '<cmd>+z':
                try:
                    Global_hotkeys.remove_hotkey(self.hwnd, self.clip_hotkey[3], self.clip_hotkey[0])
                except Exception as e:print(e)

                try:
                    self.clip_hotkey = Global_hotkeys.create_hotkey(self.hwnd, 0, ["<cmd>"], "z", self.on_activate_i) 
                    print("Hotkey 1 has been reset")
                except Exception as e:print(e)


            if self.hotkey_visual_in_settings["current_hotkey_2"] != '<cmd>+c':
                try:
                    Global_hotkeys.remove_hotkey(self.hwnd, self.gif_hotkey[3], self.gif_hotkey[0]) 
                except Exception as e:print(e)

                try:
                    self.gif_hotkey =  Global_hotkeys.create_hotkey(self.hwnd, 1, ["<cmd>"], "c", self.on_activate_gif) 
                    print("Hotkey 2 has been reset")
                except Exception as e:print(e)


            self.hotkey_visual_in_settings = {"hotkey_1_modifyer_1" : "WindowsKey", "hotkey_1_modifyer_2" : "None", "hotkey_1_modifyer_3" : "None", "hotkey_1_key" : "z", "current_hotkey_1" : '<cmd>+z', "id_1" : 0,
                                              "hotkey_2_modifyer_1" : "WindowsKey", "hotkey_2_modifyer_2" : "None", "hotkey_2_modifyer_3" : "None", "hotkey_2_key" : "c", "current_hotkey_2" : '<cmd>+c', "id_2" : 1,}
            self.settings_window()


        def change_border(*args):
            a = askcolor(color = self.border_color)
            if a[1]:
                self.border_color = a[1]
                print(f"clip border color = {self.border_color}")


        def call_open_img(*args):
            root.after(0, open_image)


        def open_image(*args):
            img = askopenfilename(parent=root)

            if img:
                try:
                    with PIL.Image.open(img) as image:
                        print(image)
                        self.show_clip_window(None, True, image)
                    image.close()
                except Exception as e:
                    messagebox.showerror(title="", message=f"{e}", parent=root)
                finally:
                    del image, img
                    gc.collect()


        def create_save_file(*args):
            with open(resource_path("settings.json"), "w") as save_file:
                settings = {"scale_percent" : self.scale_percent, "zoom_multiplyer" : self.multiplyer, "snapshot_mode" : self.snapshot,
                            "delayed_mode" : self.delayed_clip, "multi_clip" : self.multi_clip, "auto_copy_image" : self.auto_copy_image,
                            "auto_hide_clip" : self.auto_hide_clip, "cursor_lines" : self.cursor_lines, "default_alpha" : self.default_alpha,
                            "win32clipboard" : self.win32clipboard, "border_color" : self.border_color, "border_thiccness" : self.border_thiccness,
                            "line_width" : self.line_width, "line_color" : self.line_color, "hotkeys" : self.hotkey_visual_in_settings}
                save_file.write(json.dumps(settings,  indent=3))
                save_file.close()



        settings_window_root = Toplevel(root)
        settings_window_root.title("Settings")
        settings_window_root.attributes("-topmost", True)
        settings_window_root.lift()
        settings_window_root.resizable(0,0)
        
        save_changes = Button(settings_window_root, text = "Save Changes", command = save_settings)
        reset_changes = Button(settings_window_root, text = "Reset Changes", command = reset_settings)
        restore_deault_button = Button(settings_window_root, text = "Restore Default", command = restore_default)
        show_console_button = Button(settings_window_root, text = "ShowConsole", command = show_console)
        choose_border_color = Button(settings_window_root, text = "Border/LineColor", command = change_border)
        open_image_button = Button(settings_window_root, text = "OpenImage", command = call_open_img)
        auto_copy_clip_button = Button(settings_window_root, text = f"AutoCopyClip {self.auto_copy_image}", command = call_toggle_auto_copy)
        auto_hide_clip_button = Button(settings_window_root, text = f"AutoHideClip {self.auto_hide_clip}", command = call_toggle_auto_hide)
        create_save_file_button = Button(settings_window_root, text = "Create Save", command = create_save_file)

        save_changes.grid(column = 0, row = 6)
        reset_changes.grid(column = 1, row = 6)
        restore_deault_button.grid(column = 2, row = 6)
        show_console_button.grid(column = 3, row = 6)
        choose_border_color.grid(column = 4, row = 4)
        open_image_button.grid(column = 4, row = 3)
        auto_copy_clip_button.grid(column = 2, row = 4)
        auto_hide_clip_button.grid(column = 3, row = 4)
        create_save_file_button.grid(column = 4, row = 6)

        auto_copy_clip_button_tooltip = CreateToolTip(auto_copy_clip_button, "Automatically copies the clip to your clipboard")
        auto_hide_clip_button_tooltip = CreateToolTip(auto_hide_clip_button, "Automatically hides the clip in your task bar to keep it out of the way")

        hotkey_1_label = Label(settings_window_root, text = "Clip Hotkey")
        hotkey_2_label = Label(settings_window_root, text = "Gif Hotkey")

        border_thiccness_label = Label(settings_window_root, text = "Clip Border Thickness")
        border_thiccness_label.grid(column = 0, row = 4)
        border_thiccness_label_tooltip = CreateToolTip(border_thiccness_label, "Thickness of border around clip\nIf the value is not even the border will be slightly off")

        zoom_percent_label = Label(settings_window_root, text = "Zoom Square Size")
        zoom_multiplyer_label = Label(settings_window_root, text = "Zoom Multiplyer")

        hotkey_1_label.grid(column = 0, row = 1)
        hotkey_1_label_tooltip = CreateToolTip(hotkey_1_label, "Hotkey to make a clip")

        hotkey_2_label.grid(column = 0, row = 2)
        hotkey_2_label_tooltip = CreateToolTip(hotkey_2_label, "Hotkey to make a gif")

        zoom_percent_label.grid(column = 0, row = 3)
        zoom_percent_label_tooltip = CreateToolTip(zoom_percent_label, "Size of zoom box \nLower = Smaller \nHigher = Bigger \nAbove 1.25 can be lagy")

        zoom_multiplyer_label.grid(column = 2, row = 3)
        zoom_multiplyer_label_tooltip = CreateToolTip(zoom_multiplyer_label, "How far in the zoom starts \nLower = More Zoomed \nHigher = Less Zoomed")
        #<cmd> == WindowsKey, <alt> == AltKey, <ctrl> == CtrlKey
        hotkey_1_modifyer_1 = ttk.Combobox(settings_window_root,  values = ["WindowsKey", "Alt", "Ctrl", "Shift", "None"], width=12)
        hotkey_2_modifyer_1 = ttk.Combobox(settings_window_root,  values = ["WindowsKey", "Alt", "Ctrl", "Shift", "None"], width=12)
        hotkey_1_modifyer_1.set(self.hotkey_visual_in_settings["hotkey_1_modifyer_1"])
        hotkey_2_modifyer_1.set(self.hotkey_visual_in_settings["hotkey_2_modifyer_1"])


        hotkey_1_modifyer_2 = ttk.Combobox(settings_window_root,  values = ["WindowsKey", "Alt", "Ctrl", "Shift", "None"], width=12)
        hotkey_2_modifyer_2 = ttk.Combobox(settings_window_root,  values = ["WindowsKey", "Alt", "Ctrl", "Shift", "None"], width=12)
        hotkey_1_modifyer_2.set(self.hotkey_visual_in_settings["hotkey_1_modifyer_2"])
        hotkey_2_modifyer_2.set(self.hotkey_visual_in_settings["hotkey_2_modifyer_2"])


        hotkey_1_modifyer_3 = ttk.Combobox(settings_window_root,  values = ["WindowsKey", "Alt", "Ctrl", "Shift", "None"], width=12)
        hotkey_2_modifyer_3 = ttk.Combobox(settings_window_root,  values = ["WindowsKey", "Alt", "Ctrl", "Shift", "None"], width=12)
        hotkey_1_modifyer_3.set(self.hotkey_visual_in_settings["hotkey_1_modifyer_3"])
        hotkey_2_modifyer_3.set(self.hotkey_visual_in_settings["hotkey_2_modifyer_3"])

        hotkey_1_key = ttk.Combobox(settings_window_root,  values = list(Global_hotkeys.PYNPUT_TO_VK.keys()), width=12)
        hotkey_2_key = ttk.Combobox(settings_window_root,  values = list(Global_hotkeys.PYNPUT_TO_VK.keys()), width=12)
        hotkey_1_key.set(self.hotkey_visual_in_settings["hotkey_1_key"])
        hotkey_2_key.set(self.hotkey_visual_in_settings["hotkey_2_key"])

        border_thiccness_combobox = ttk.Combobox(settings_window_root, values = [i for i in range(0, 100)], width = 4)
        border_thiccness_combobox.set(self.border_thiccness)

        zoom_percent_Combobox = ttk.Combobox(settings_window_root,  values = [round(x, 3) for x in numpy.arange(0, 2, 0.01) if x >= 0.03], width=5)
        zoom_percent_Combobox.set(self.scale_percent)

        zoom_multiplyer_Combobox = ttk.Combobox(settings_window_root,  values = [round(x, 3) for x in numpy.arange(0, 0.2, 0.01) if x >= 0.03], width=5)
        zoom_multiplyer_Combobox.set(self.multiplyer)

        snapshot_mode_button = Button(settings_window_root, text = f"SnapShotMode {self.snapshot}", command = change_snapshot)
        delay_clip_mode_button = Button(settings_window_root, text = f"DelayMode {self.delayed_clip}", command = change_delay_clip)
        multi_clip_mode_button = Button(settings_window_root, text = f"MultiMode {self.multi_clip}", command = change_multi_mode)
        cursor_guidelines_button = Button(settings_window_root, text = f"CursorLines {self.cursor_lines}", command = change_lines)
        use_win32_clipboard_copy = Button(settings_window_root, text = f"Win32clipboard {self.win32clipboard}", command = change_win32_clip)

        hotkey_1_modifyer_1.grid(column = 1, row = 1, pady = 5)
        hotkey_2_modifyer_1.grid(column = 1, row = 2, pady = 5)

        hotkey_1_modifyer_2.grid(column = 2, row = 1, pady = 5, padx = 6)
        hotkey_2_modifyer_2.grid(column = 2, row = 2, pady = 5, padx = 6)

        hotkey_1_modifyer_3.grid(column = 3, row = 1, pady = 5, padx = 6)
        hotkey_2_modifyer_3.grid(column = 3, row = 2, pady = 5, padx = 6)

        hotkey_1_key.grid(column = 4, row = 1, pady = 5)
        hotkey_2_key.grid(column = 4, row = 2, pady = 5)

        zoom_percent_Combobox.grid(column = 1, row = 3, pady = 5)
        zoom_multiplyer_Combobox.grid(column = 3, row = 3, pady = 5)
        border_thiccness_combobox.grid(column = 1, row = 4)

        snapshot_mode_button.grid(column = 0, row = 5, pady = 5)
        snapshot_mode_button_tooltip = CreateToolTip(snapshot_mode_button, "Snapshot Mode: \nFreezes your screen, allowing you to crop a current point in time")

        delay_clip_mode_button.grid(column = 1, row = 5, padx = 6, pady = 5)
        delay_clip_mode_button_tooltip = CreateToolTip(delay_clip_mode_button, "Delayed Mode: \nTakes a screenshot and holds it in memory, upon the Clip Hotkey again display the screenshot allowing you to crop it")

        multi_clip_mode_button.grid(column = 2, row = 5, padx = 6, pady = 5)
        cursor_guidlines_tooltip = CreateToolTip(multi_clip_mode_button, "Lets you clip with the same clipping window until you close it with Right Click")

        cursor_guidelines_button.grid(column = 3, row = 5, padx = 6, pady = 5)
        cursor_guidlines_tooltip = CreateToolTip(cursor_guidelines_button, "This toggles the visual pink lines when clipping")

        use_win32_clipboard_copy.grid(column = 4, row = 5, padx = 6, pady = 5)
        use_win32_clipboard_copy_tooltip = CreateToolTip(use_win32_clipboard_copy, "Copy clip using win32clipboard \nThis is more flexable and faster")

        settings_window_root.update()
        xloc = (root.winfo_screenwidth() // 2) - (settings_window_root.winfo_width() // 2)  
        yloc = (root.winfo_screenheight() // 2) - (settings_window_root.winfo_height() // 2)
        print(xloc, yloc)
        settings_window_root.geometry(f"+{xloc}+{yloc}")

        

        zoom_percent_Combobox.bind("<KeyRelease>", callbc)
        zoom_percent_Combobox.bind("<FocusOut>", check_float)

        border_thiccness_combobox.bind("<KeyRelease>", force_int)

        zoom_multiplyer_Combobox.bind("<KeyRelease>", callbc)
        zoom_multiplyer_Combobox.bind("<FocusOut>", check_float_zoom_multiplyer_Combobox)

        hotkey_1_modifyer_1.bind("<FocusOut>", check_modifyer_key)
        hotkey_2_modifyer_1.bind("<FocusOut>", check_modifyer_key)
        hotkey_1_modifyer_2.bind("<FocusOut>", check_modifyer_key)
        hotkey_2_modifyer_2.bind("<FocusOut>", check_modifyer_key)
        hotkey_1_modifyer_3.bind("<FocusOut>", check_modifyer_key)
        hotkey_2_modifyer_3.bind("<FocusOut>", check_modifyer_key)

        hotkey_1_key.bind("<KeyRelease>", prevent_multi_keys)
        hotkey_2_key.bind("<KeyRelease>", prevent_multi_keys)

        






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
        self.clip_app.call_create_clip_window()

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
        self.clip_app.toggle_snapshot_mode()
        self.update_hov_text(systray)

    #***************** Enable delay mode which saves monitor screenshots in memory to clip when called again *************. 
    def delay_mode(self, systray):
        self.clip_app.toggle_delay_mode()
        self.update_hov_text(systray)

    #***************** Enable multi mode *************. 
    def multi_mode(self, systray):
        self.clip_app.toggle_multi_mode()
        self.update_hov_text(systray)

    #***************** Kill tkinter mainloop and remove all hotkey threads *************. 
    def kill_program(self):
        try:
            Global_hotkeys.remove_hotkey(self.clip_app.hwnd, self.clip_app.clip_hotkey[3], self.clip_app.clip_hotkey[0])
            Global_hotkeys.remove_hotkey(self.clip_app.hwnd, self.clip_app.gif_hotkey[3], self.clip_app.gif_hotkey[0])
            #keyboard.GlobalHotKeys.stop(self.clip_app.clip_hotkey)
            #keyboard.GlobalHotKeys.stop(self.clip_app.gif_hotkey)
        except Exception as e:print(e)
        try: 
            for i in list(ahk_blocking_hotkeys.hotkeys.keys()).copy(): ahk_blocking_hotkeys.destroy_blocking_hotkey(i)
        except:pass
        root.destroy()
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