using System.Collections.Generic;
using System.Windows.Forms;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

namespace screeninfo_c
{
    public static class ScreenInfo
    {
        [ComVisible(true)]
        [DllImport("user32.dll", SetLastError = true)]
        static extern int SetProcessDpiAwarenessContext(int value);
        

        public struct Monitor
        {
            public string name;
            public Rectangle bounds;
            public Rectangle workArea;
            public int hashCode;

        }

        public static IEnumerable<Monitor> GetMonitors()
        {
            SetProcessDpiAwarenessContext(-3);
            Monitor[] monitrs = new Monitor[Screen.AllScreens.Length];

            foreach (Screen screen in Screen.AllScreens)
            {
                yield return new Monitor
                {
                    name = screen.DeviceName,
                    bounds = screen.Bounds,
                    workArea = screen.WorkingArea,
                    hashCode = screen.GetHashCode()
                };
            }

        }

        public static Monitor MonitorFromPoint(int x, int y)
        {
            Screen scr = Screen.FromPoint(new Point(x, y));
            return new Monitor
            {
                name = scr.DeviceName,
                bounds = scr.Bounds,
                workArea = scr.WorkingArea,
                hashCode = scr.GetHashCode()
            };
        }

        public static string GetRectAsImage(int x, int y, int x1, int y1, string filename)
        {
            Rectangle rect = new Rectangle(x, y, x1-x, y1-y);
            Bitmap bmp = new Bitmap(rect.Width, rect.Height, PixelFormat.Format24bppRgb);
            Graphics g = Graphics.FromImage(bmp);
            g.CopyFromScreen(rect.Left, rect.Top, 0, 0, rect.Size);
            bmp.Save(filename, ImageFormat.Png);
            bmp.Dispose();
            g.Dispose();
            
            return filename;
        }
    }
}
