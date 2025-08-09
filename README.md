# WindowTransparency-App
可以随意调节窗口的透明度
name: Build EXE

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install pyqt5 pyinstaller

      - name: Build EXE
        run: |
          pyinstaller --noconsole --onefile window_transparency.py

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: WindowTransparencyApp
          path: dist/window_transparency.exe
