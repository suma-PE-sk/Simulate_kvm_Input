import pyautogui
import pynput
from pynput.keyboard import Key, Listener
import tkinter as tk
import pyperclip
import sys
import os


def resource_path(relative_path):
    """ 获取资源的绝对路径(兼容打包后的exe)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class ClipboardMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("按F11模拟输入")
        self.scroll_position = 0.0
        self.input_interval = 0.0
        self.last_clipboard_content = ""  # 新增:用于记录上次剪贴板内容

        # 图标设置
        try:
            icon_path = resource_path('icon.ico')
            self.root.iconbitmap(icon_path)
        except tk.TclError as e:
            print(f"图标加载失败: {str(e)}")

        # 窗口尺寸和位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = screen_width // 5
        window_height = screen_height // 4
        x = (screen_width - window_width) // 3
        y = (screen_height - window_height) // 3
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 窗口属性
        self.root.resizable(True, True)
        self.root.attributes('-alpha', 0.9)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#f0f0f0')
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 文本区域和滚动条
        self.text_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.text_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.clipboard_text = tk.Text(
            self.text_frame,
            width=50,
            height=10,
            bg='white',
            fg='black',
            wrap=tk.WORD
        )
        self.clipboard_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(
            self.text_frame,
            command=self.clipboard_text.yview,
            bg='#d9d9d9'
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clipboard_text.config(yscrollcommand=self.scrollbar.set)

        # 初始化内容
        initial_text = pyperclip.paste()
        self.clipboard_text.insert(tk.END, initial_text)
        self.last_clipboard_content = initial_text  # 初始化记录

        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(pady=10, fill=tk.X)

        # 置顶按钮
        self.toggle_button = tk.Button(
            control_frame,
            text="取消置顶",
            command=self.toggle_topmost,
            bg='#808080',
            fg='white'
        )
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        # 输入速度调节滑块
        self.speed_scale = tk.Scale(
            control_frame,
            from_=0,
            to=0.5,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            label="输入速度 (秒/字符)",
            bg='#f0f0f0',
            length=150,
            command=self.update_speed
        )
        self.speed_scale.set(0)
        self.speed_scale.pack(side=tk.RIGHT, padx=10)

        # 底部信息栏
        bottom_frame = tk.Frame(self.root, bg='#f0f0f0')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            bottom_frame,
            text="By: 日拱一卒",
            anchor='w',
            bg='#f0f0f0',
            fg='black'
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # 修改键盘监听器初始化
        self.keyboard_controller = pynput.keyboard.Controller()
        self.keyboard_listener = Listener(on_press=self.on_press, suppress=False)
        self.keyboard_listener.start()
        self.is_typing = False  # 添加一个标志来控制输入状态

        # 启动功能
        self.root.after(100, self.monitor_clipboard)

    def update_speed(self, value):
        self.input_interval = float(value)

    def monitor_clipboard(self):
        new_text = pyperclip.paste()
        # 获取文本框内容(排除自动添加的换行符)
        current_text = self.clipboard_text.get("1.0", "end-1c")

        if new_text != current_text:
            # 记录滚动位置和选择范围
            self.scroll_position = self.clipboard_text.yview()
            selection_start, selection_end = self.get_selection_indices()

            # 更新内容
            self.clipboard_text.config(state=tk.NORMAL)
            self.clipboard_text.delete("1.0", tk.END)
            self.clipboard_text.insert(tk.END, new_text)
            self.clipboard_text.config(state=tk.DISABLED)

            # 恢复滚动位置和选择范围
            self.clipboard_text.yview_moveto(self.scroll_position[0])
            self.restore_selection(selection_start, selection_end)

            # 强制刷新界面
            self.clipboard_text.update_idletasks()

        self.root.after(100, self.monitor_clipboard)

    def get_selection_indices(self):
        """ 获取当前选择范围的起始和结束索引 """
        try:
            start = self.clipboard_text.index(tk.SEL_FIRST)
            end = self.clipboard_text.index(tk.SEL_LAST)
            return (start, end)
        except tk.TclError:
            return (None, None)

    def restore_selection(self, start, end):
        """ 恢复选择范围 """
        if start and end:
            self.clipboard_text.tag_add(tk.SEL, start, end)
            self.clipboard_text.mark_set(tk.INSERT, end)

    def on_press(self, key):
        if key == Key.f11 and not self.is_typing:
            self.is_typing = True
            self.paste_clipboard()
            self.is_typing = False

    def paste_clipboard(self):
        text = self.clipboard_text.get("1.0", "end-1c")
        # 在开始输入前释放所有按键
        for key in [Key.f11]:
            self.keyboard_controller.release(key)
        pyautogui.sleep(0.1)  # 短暂延迟确保按键完全释放

        # 在模拟输入前，按下退格键清除可能的多余字符
        pyautogui.press('backspace')
        pyautogui.sleep(0.1)  # 等待退格键生效

        self._simulate_typing(text)

    def _simulate_typing(self, text):
        pyautogui.typewrite(text, interval=self.input_interval)

    def toggle_topmost(self):
        is_topmost = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not is_topmost)
        self.toggle_button.config(text="置顶" if is_topmost else "取消置顶")

    def on_close(self):
        self.keyboard_listener.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ClipboardMonitor()
    app.run()
