#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
window_opacity_tray.py
一个简单的 Windows 工具：把程序最小化到系统托盘，选择任意可见窗口并调节透明度（0-100%）。

依赖：PyQt5, pywin32
"""

import sys
import os
import win32gui
import win32con
from PyQt5 import QtWidgets, QtCore, QtGui


def enum_windows_callback(hwnd, windows):
"""EnumWindows 回调：收集可见且有标题的窗口"""
try:
if win32gui.IsWindowVisible(hwnd):
title = win32gui.GetWindowText(hwnd)
if title:
windows.append((hwnd, title))
except Exception:
pass


class TransparencyApp(QtWidgets.QWidget):
def __init__(self):
super().__init__()
self.setWindowTitle("窗口透明度调节器")
self.setGeometry(300, 300, 420, 160)

# 尝试加载图标（可选）
icon_path = os.path.join(os.path.dirname(__file__), "icons", "app.ico")
if os.path.exists(icon_path):
self.setWindowIcon(QtGui.QIcon(icon_path))

# 记录我们改过样式的窗口，便于恢复：hwnd -> 原始 exstyle
self.modified = {}

layout = QtWidgets.QVBoxLayout()

# 上排：窗口选择 + 刷新按钮
top_h = QtWidgets.QHBoxLayout()
self.window_combo = QtWidgets.QComboBox()
top_h.addWidget(self.window_combo)
refresh_btn = QtWidgets.QPushButton("刷新窗口列表")
refresh_btn.clicked.connect(self.refresh_window_list)
top_h.addWidget(refresh_btn)
layout.addLayout(top_h)

# 中间：滑条
self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
self.slider.setMinimum(10) # 10% 最低（避免完全不可见）
self.slider.setMaximum(100)
self.slider.setValue(100)
self.slider.setTickInterval(10)
self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
self.slider.valueChanged.connect(self.change_opacity)
layout.addWidget(self.slider)

# 下排：恢复按钮 + 恢复全部并退出
bottom_h = QtWidgets.QHBoxLayout()
restore_btn = QtWidgets.QPushButton("恢复选中窗口不透明")
restore_btn.clicked.connect(self.restore_selected)
bottom_h.addWidget(restore_btn)

restore_all_btn = QtWidgets.QPushButton("恢复全部并退出")
restore_all_btn.clicked.connect(self.restore_all_and_exit)
bottom_h.addWidget(restore_all_btn)
layout.addLayout(bottom_h)

self.setLayout(layout)

# 初次加载窗口列表
self.refresh_window_list()

def refresh_window_list(self):
"""重新枚举当前可见窗口并填充下拉框"""
self.windows = []
win32gui.EnumWindows(enum_windows_callback, self.windows)
self.window_combo.clear()
for hwnd, title in self.windows:
self.window_combo.addItem(title, hwnd)

def change_opacity(self, value):
"""当滑条变化时被调用，立即修改所选窗口透明度"""
idx = self.window_combo.currentIndex()
if idx < 0:
return
hwnd = self.window_combo.itemData(idx)
if not win32gui.IsWindow(hwnd):
QtWidgets.QMessageBox.warning(self, "错误", "选中的窗口已不存在。请刷新窗口列表。")
return
try:
ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
# 如果没有 WS_EX_LAYERED 标志，我们先记录原样式并添加它
if not (ex & win32con.WS_EX_LAYERED):
# 只记录第一次修改时的原始样式
if hwnd not in self.modified:
self.modified[hwnd] = ex
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex | win32con.WS_EX_LAYERED)
alpha = int(255 * (value / 100.0))
win32gui.SetLayeredWindowAttributes(hwnd, 0, alpha, win32con.LWA_ALPHA)
except Exception as e:
QtWidgets.QMessageBox.warning(self, "错误", f"无法修改透明度: {e}")

def restore_selected(self):
idx = self.window_combo.currentIndex()
if idx < 0:
return
hwnd = self.window_combo.itemData(idx)
self._restore_hwnd(hwnd)

def _restore_hwnd(self, hwnd):
"""将单个窗口恢复为完全不透明并还原原始 exstyle（如果记录过）"""
try:
if not win32gui.IsWindow(hwnd):
return
# 把透明度设为 255
try:
win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
except Exception:
pass
# 恢复原始 exstyle（若我们记录过）
orig = self.modified.pop(hwnd, None)
if orig is not None:
try:
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, orig)
except Exception:
pass
except Exception:
pass

def restore_all_and_exit(self):
# 尝试恢复所有被修改的窗口
for hwnd in list(self.modified.keys()):
self._restore_hwnd(hwnd)
QtWidgets.qApp.quit()


class SystemTrayApp(QtWidgets.QSystemTrayIcon):
def __init__(self, icon):
super().__init__(icon)
self.setToolTip("窗口透明度调节器")

menu = QtWidgets.QMenu()
open_action = menu.addAction("打开调节器")
open_action.triggered.connect(self.open_window)

refresh_action = menu.addAction("刷新窗口列表")
refresh_action.triggered.connect(self.refresh)

restore_action = menu.addAction("恢复全部")
restore_action.triggered.connect(self.restore_all)

menu.addSeparator()
quit_action = menu.addAction("退出")
quit_action.triggered.connect(self.quit)

self.setContextMenu(menu)

self.app_window = TransparencyApp()

# 双击图标也打开
self.activated.connect(self.on_activated)

def open_window(self):
self.app_window.show()
self.app_window.raise_()
self.app_window.activateWindow()

def refresh(self):
self.app_window.refresh_window_list()

def restore_all(self):
self.app_window.restore_all_and_exit()

def quit(self):
self.app_window.restore_all_and_exit()

def on_activated(self, reason):
if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
self.open_window()


def main():
app = QtWidgets.QApplication(sys.argv)

# 使用 icons/app.ico（若不存在则为默认）
icon_path = os.path.join(os.path.dirname(__file__), "icons", "app.ico")
icon = QtGui.QIcon(icon_path) if os.path.exists(icon_path) else app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)

tray = SystemTrayApp(icon)
tray.show()

sys.exit(app.exec_())


if __name__ == "__main__":
main()
