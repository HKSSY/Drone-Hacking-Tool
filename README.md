<p align="center"><img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_img/drone_main_icon.png">

# Drone-Hacking-Tool

Drone Hacking Tool is a GUI tool that works with a USB Wifi adapter and HackRF One for hacking drones.

[![License](https://img.shields.io/github/license/HKSSY/Drone-Hacking-Tool)](https://github.com/HKSSY/Drone-Hacking-Tool/blob/main/LICENSE)

## Overview
  
Drones, as a high mobility item that can be carried around easily and launched, are becoming cheaper and more popular among the public, they can be seen almost anywhere nowadays.
 
However, the drone built-in flying cameras could use for illegal usage like candid photos on private property. This shows drones clearly present risks to public safety and personal privacy.

Therefore, we are working on using wireless connection methods (Wi-Fi, GPS) to hack it and take over. In this project, our goal is to capture drones to stop users with malicious intent for proof of concept and a sense of accomplishment.
  
## Before to start

### Software

#### Operating System selection

Due to Robot Operating System (ROS) Kinetic primarily targeting Ubuntu 16.04, so we advise using Ubuntu 16.04 for running this tool.
  
#### Install ROS

Before you start using this tool, you must install Robot Operating System (ROS) Kinetic on your Ubuntu. For more information, please [click here](https://wiki.ros.org/kinetic).

#### Install ROS driver
  
Please install the driver for ROS to communicate with the drone. The driver called [tello_driver](https://github.com/appie-17/tello_driver) and [bebop_autonomy](https://github.com/AutonomyLab/bebop_autonomy). In this tool, we tested DJI Tello and Parrot Bebop 2 works with this tool, users can use this tool for takeoff, landing and viewing the live camera content.
  
You may also install another ROS driver for hacking other drones, but you need to edit the source code and we cannot promise it can work with this tool.

#### Install Aircrack–ng suite
  
[Aircrack-ng](https://github.com/aircrack-ng/aircrack-ng) is a security software related to 802.11 standard wireless network analysis. Our tool relies on the Aircrack-ng suite for wireless network detection, capturing four-way handshake packets, and implementing a Wi-Fi deauthentication attack.
  
#### Install hackrf utility 

This utility is used to communicate with your HackRF One.

#### Python version and installed modules

This tool is built on Python 3.8 and works with the following modules:

* [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI interface
* [pandas](https://github.com/pandas-dev/pandas) - analysis CVS data
* [paramiko](https://github.com/paramiko/paramiko) - SSH connection
* [ipaddress](https://docs.python.org/3/library/ipaddress.html) - checking whether or not a string represents a valid IP address

### Hardware

#### HackRF One

HackRF One from Great Scott Gadgets is a Software Defined Radio peripheral capable of transmission or reception of radio signals from 1 MHz to 6 GHz. For more information, please visit the [official website](https://greatscottgadgets.com/hackrf/one/).

In this tool, we are using HackRF One to perform a fake GPS attack to force the drone to land or fly away from the fake GPS signal covered area.

#### USB Wifi adapter

NOT all Wi-Fi adapter is compatible with the Aircrack-ng suite. Please [read](https://www.aircrack-ng.org/doku.php?id=compatible_cards) this tutorial to help you select a compatible Wi-Fi adapter.

#### The Remote server (optional)
  
You may be using a laptop or virtual machine to run this tool, but the performance of most of the laptops is not enough for cracking WiFi passwords. So, this tool can use an SSH connection to the remote server with the powerful GPU performance and use hashcat to reduce the time for cracking passwords.

## Launch the tool

For launching the tool, please type in the following command on the terminal:
```
python3 drone_hacking_tool.py
```

## User interface

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/homepage.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/select_wifi_adapter_page.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/select_target_page.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/attack_target_page.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/control_target_page.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/remote_server_login_page.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/connect_to_hackrf_one_page.png" width="40%"></img>

<img src="https://raw.githubusercontent.com/HKSSY/Drone-Hacking-Tool/main/data/gui_demo/fake_gps_attack_page.png" width="40%"></img>

## Development team

* [HKSSY](https://github.com/HKSSY)
* Sam KAN
* Michael Yuen

## Special thanks with

* [BBQHK](https://github.com/BBQHK)
* [ScodeC-kk](https://github.com/ScodeC-kk)
