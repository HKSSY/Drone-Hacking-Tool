<p align="center"><img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_img/drone_main_icon.png">

# Drone-Hacking-Tool

Drone Hacking Tool is a GUI tool that works with a USB Wifi adapter and HackRF One for hacking drones.

![License](https://img.shields.io/github/license/HKSSY/Drone-Hacking-Tool)

## Before to start

### Install ROS

Before you start using this tool, you must install Robot Operating System (ROS) Kinetic on your Ubuntu. For more information, please [click here](https://wiki.ros.org/kinetic). Due to this release primarily targeting Ubuntu 16.04, so we advise using Ubuntu 16.04 for running this tool.

### Install ROS driver
  
After that, please install the driver for ROS to communicate with the drone. The driver called [tello_driver](https://github.com/appie-17/tello_driver) and [bebop_autonomy](https://github.com/AutonomyLab/bebop_autonomy). In this tool, we tested DJI Tello and Parrot Bebop 2 works with this tool, users can use this tool for takeoff, landing and viewing the live camera content. You may also install another ROS driver for hacking other drones, but you need to edit the source code and we cannot promise it can work with this tool.

### Ready hardware
