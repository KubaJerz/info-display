#!/bin/bash

pkill -f "python.*fullscreen.py"
sleep 2

cd /home/valafarlab/Desktop/InfoDisplay
python fullscreen.py &
