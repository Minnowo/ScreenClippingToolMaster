import ctypes
import ctypes.wintypes
import win32con
from tkinter import messagebox
 
class GlobalHotKeys(object):
    """
    Register a key using the register() method, or using the @register decorator
    Use listen() to start the message pump
 
    Example:
 
    from globalhotkeys import GlobalHotKeys
 
    @GlobalHotKeys.register(GlobalHotKeys.VK_F1)
    def hello_world():
        print 'Hello World'
 
    GlobalHotKeys.listen()
    """
 
    key_mapping = []
    stop = False
    
    user32 = ctypes.windll.user32
 
    MOD_ALT = win32con.MOD_ALT
    MOD_CTRL = win32con.MOD_CONTROL
    MOD_CONTROL = win32con.MOD_CONTROL
    MOD_SHIFT = win32con.MOD_SHIFT
    MOD_WIN = win32con.MOD_WIN

    PUNCTUATION_CHARACTERS = {"BACKSPACE" : 8, "TAB" : 9, "ENTER" : 13, "SHIFT" : 16, "CONTROL" : 17, "ALT" : 18, "CAPSLOCK" : 20, "ESCAPE" : 27, "SPACE" : 32
                              , "PAGEUP" : 33, "PAGEDOWN" : 34, "END" : 35, "HOME" : 36, "LEFT" : 37, "UP" : 38, "RIGHT" : 39, "DOWN" : 40, "DELETE" : 46
                              , ";" : 186, ":" : 186, "+" : 187, "=" : 187, "," : 188, "<" : 188, "-" : 189, "_" : 189, "." : 190, ">" : 190, "?" : 191
                              , "/" : 191, "`" : 192, "~" : 192, "[" : 219, "{" : 219, "\\" : 220, "|" : 220, "]" : 221, "}" : 221, "'" : 222, "\"" : 222}
 
    @classmethod
    def register(cls, vk, modifier=0, func=None):
        """
        vk is a windows virtual key code
         - can use ord('X') for A-Z, and 0-1 (note uppercase letter only)
         - or win32con.VK_* constants
         - for full list of VKs see: http://msdn.microsoft.com/en-us/library/dd375731.aspx
 
        modifier is a win32con.MOD_* constant
 
        func is the function to run.  If False then break out of the message loop
        """
 
        # Called as a decorator?
        if func is None:
            def register_decorator(f):
                cls.register(vk, modifier, f)
                return f
            return register_decorator
        else:
            cls.key_mapping.append((vk, modifier, func))
 
 
    @classmethod
    def listen(cls):
        """
        Start the message pump
        """
 
        for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
            if not cls.user32.RegisterHotKey(None, index, modifiers, vk):
                messagebox.showerror(title = "", message ='Unable to register hot key: ' + str(vk) + ' error code is: ' + str(ctypes.windll.kernel32.GetLastError()))
                #cls.register_hotkey_error += '\nUnable to register hot key: ' + chr(vk) + ' error code is: ' + str(ctypes.windll.kernel32.GetLastError())
                #raise Exception('Unable to register hot key: ' + str(vk) + ' error code is: ' + str(ctypes.windll.kernel32.GetLastError()))
 
        try:
            msg = ctypes.wintypes.MSG()
            while cls.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0 and cls.stop == False:
                print(cls.stop)
                if cls.stop:break
                if msg.message == win32con.WM_HOTKEY:
                    (vk, modifiers, func) = cls.key_mapping[msg.wParam]
                    if not func:
                        break
                    func()
 
                cls.user32.TranslateMessage(ctypes.byref(msg))
                cls.user32.DispatchMessageA(ctypes.byref(msg))
 
        finally:
            for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
                cls.user32.UnregisterHotKey(None, index)
            cls.stop = False
            cls.key_mapping.clear()
            print("Hotkey loop has stopped")
 
    @classmethod
    def unregisterHotkKey(cls):
        cls.stop = True


    @classmethod
    def _include_defined_vks(cls):
        for item in win32con.__dict__:
            item = str(item)
            if item[:3] == 'VK_':
                setattr(cls, item, win32con.__dict__[item])
 
 
    @classmethod
    def _include_alpha_numeric_vks(cls):
        for key_code in (list (range(ord('A'), ord('Z') + 1)) + list(range(ord('0'), ord('9') + 1)) ):
            setattr(cls, 'VK_' + chr(key_code), key_code)
 
GlobalHotKeys._include_defined_vks()
GlobalHotKeys._include_alpha_numeric_vks()



#@GlobalHotKeys.register(GlobalHotKeys.PUNCTUATION_CHARACTERS["enter"], GlobalHotKeys.MOD_CTRL + GlobalHotKeys.MOD_ALT)
#def hello_world():
#    print("gggg")
    
    #GlobalHotKeys.unregisterHotkKey()

#GlobalHotKeys.listen()