import tkinter as tk
from tkinter import ttk
import threading
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import socket


class GroundStationInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Ground Station Interface")
        self.root.geometry("1920x1080")

        # Initialize variables
        self.stIp = '127.0.0.1'
        self.stPort = 12346
        self.iotData = 36
        self.filterCommandList = '0'
        self.manuelDetachment = 0
        self.telemetry_data = []

        
        # Socket setup
        self.host = '127.0.0.1'  # IP address of the ground station
        self.port = 12346  # Port to listen on
        self.buffer_size = 1024  # Buffer size for receiving data

        # Create a socket object
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        # Start a thread to listen for telemetry data
        self.telemetry_thread = threading.Thread(target=self.listen_for_telemetry)
        self.telemetry_thread.daemon = True
        self.telemetry_thread.start()

        # Define frames for each section
        self.camera_frame = tk.Frame(root, width=640, height=480, bg='white')
        self.map_frame = tk.Frame(root, width=640, height=480, bg='white')
        self.model_frame = tk.Frame(root, width=640, height=480, bg='white')

        self.iot_frame = tk.Frame(root, width=320, height=240, bg='white')
        self.battery_frame = tk.Frame(root, width=320, height=240, bg='white')
        self.descent_frame = tk.Frame(root, width=320, height=240, bg='white')
        self.altitude_diff_frame = tk.Frame(root, width=320, height=240, bg='white')

        self.altitude_frame = tk.Frame(root, width=640, height=320, bg='white')
        self.pressure_frame = tk.Frame(root, width=640, height=320, bg='white')
        self.temperature_frame = tk.Frame(root, width=640, height=320, bg='white')

        self.roll_pitch_yaw_frame = tk.Frame(root, width=960, height=100, bg='white')
        self.filter_input_frame = tk.Frame(root, width=320, height=40, bg='white')

        self.error_code_frame = tk.Frame(root, width=500, height=40, bg='white')
        self.status_frame = tk.Frame(root, width=100, height=40, bg='white')

        self.manual_detachment_frame = tk.Frame(root, width=320, height=40, bg='white')

        # Place frames in grid
        self.camera_frame.place(x=0, y=0)
        self.map_frame.place(x=0, y=480)
        self.model_frame.place(x=640, y=480)

        self.iot_frame.place(x=640, y=0)
        self.battery_frame.place(x=960, y=0)
        self.descent_frame.place(x=640, y=240)
        self.altitude_diff_frame.place(x=960, y=240)

        self.altitude_frame.place(x=1280, y=0)
        self.pressure_frame.place(x=1280, y=320)
        self.temperature_frame.place(x=1280, y=640)

        self.roll_pitch_yaw_frame.place(x=640, y=900)  # Adjusted position
        self.filter_input_frame.place(x=0, y=900)  # Adjusted position

        self.error_code_frame.place(x=960, y=900)  # Adjusted position
        self.status_frame.place(x=1460, y=900)  # Adjusted position

        self.manual_detachment_frame.place(x=1600, y=900)  # Adjusted position

        # Add labels to frames for testing
        tk.Label(self.camera_frame, text="Camera").pack()
        tk.Label(self.map_frame, text="Map").pack()
        tk.Label(self.model_frame, text="3D Model").pack()

        tk.Label(self.iot_frame, text="IoT").pack()
        tk.Label(self.battery_frame, text="Battery Voltage (V)").pack()  # Added unit
        tk.Label(self.descent_frame, text="Descent Speed (m/s)").pack()  # Added unit
        tk.Label(self.altitude_diff_frame, text="Altitude Difference (m)").pack()  # Added unit

        tk.Label(self.altitude_frame, text="Altitude (m)").pack()  # Added unit
        tk.Label(self.pressure_frame, text="Pressure (hPa)").pack()  # Added unit
        tk.Label(self.temperature_frame, text="Temperature (C)").pack()  # Added unit

        tk.Label(self.roll_pitch_yaw_frame, text="Roll, Pitch, Yaw").pack()
        tk.Label(self.filter_input_frame, text="Filter Input").pack()

        tk.Label(self.error_code_frame, text="Error Codes").pack()
        tk.Label(self.status_frame, text="Status").pack()

        tk.Label(self.manual_detachment_frame, text="Manual Detachment").pack()

        # Add entry and button for filter command input
        self.filter_command_entry = tk.Entry(self.filter_input_frame, width=30)
        self.filter_command_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.send_button = tk.Button(self.filter_input_frame, text="Send", command=self.update_filter_command)
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Add button for manual detachment
        self.manual_detachment_button = tk.Button(self.manual_detachment_frame, text="Manual Detachment", command=self.manual_detachment)
        self.manual_detachment_button.pack(padx=5, pady=5)

        # Add matplotlib figures for graphs
        self.create_graphs()

    def listen_for_telemetry(self):
        print("Waiting for connection...")
        client_socket, addr = self.server_socket.accept()
        print(f"Connection from {addr} has been established.")

        while True:
            data = client_socket.recv(self.buffer_size)
            if data.decode('utf-8') == "SEND_DATA":
                response = [62, self.filterCommandList, self.manuelDetachment]
                client_socket.sendall(json.dumps(response).encode('utf-8'))
            else:
                try:
                    telemetry_data = json.loads(data.decode('utf-8'))
                    self.update_telemetry_data(telemetry_data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding telemetry data: {e}")

    def update_telemetry_data(self, data):
        # Update IoT data
        self.iot_data.append(data['iotData'])
        self.update_graph(self.iot_ax, self.iot_data, self.iot_canvas)

        # Update telemetry data from DataPack
        self.telemetry_data.append(data)
        if len(self.telemetry_data) > 10:
            self.telemetry_data.pop(0)

        # Update Battery Voltage data
        self.battery_data.append(data['batteryVoltage'])
        self.update_graph(self.battery_ax, self.battery_data, self.battery_canvas)

        # Update Descent Speed data
        self.descent_data.append(data['descentSpeed'])
        self.update_graph(self.descent_ax, self.descent_data, self.descent_canvas)

        # Update Altitude Difference data
        self.altitude_diff_data.append(data['altitudeDifference'])
        self.update_graph(self.altitude_diff_ax, self.altitude_diff_data, self.altitude_diff_canvas)

        # Update Altitude data
        self.satellite_altitude_data.append(data['satelliteAltitude'])
        self.shell_altitude_data.append(data['shellAltitude'])
        self.update_graph_dual(self.altitude_ax, self.satellite_altitude_data, self.shell_altitude_data, self.altitude_canvas)

        # Update Pressure data
        self.satellite_pressure_data.append(data['satellitePressure'])
        self.shell_pressure_data.append(data['shellPressure'])
        self.update_graph_dual(self.pressure_ax, self.satellite_pressure_data, self.shell_pressure_data, self.pressure_canvas)

        # Update Temperature data
        self.temperature_data.append(data['temperature'])
        self.update_graph(self.temperature_ax, self.temperature_data, self.temperature_canvas)

        # Optionally, you can also process the GPS data if needed
        gps_latitude = data['gpsLat']
        gps_longitude = data['gpsLong']
        gps_altitude = data['gpsAlt']


    def create_graphs(self):
        # IoT graph
        self.iot_fig, self.iot_ax = plt.subplots(figsize=(3, 2))
        self.iot_canvas = FigureCanvasTkAgg(self.iot_fig, master=self.iot_frame)
        self.iot_canvas.get_tk_widget().pack()
        self.iot_data = []

        # Battery Voltage graph
        self.battery_fig, self.battery_ax = plt.subplots(figsize=(3, 2))
        self.battery_canvas = FigureCanvasTkAgg(self.battery_fig, master=self.battery_frame)
        self.battery_canvas.get_tk_widget().pack()
        self.battery_data = []

        # Descent Speed graph
        self.descent_fig, self.descent_ax = plt.subplots(figsize=(3, 2))
        self.descent_canvas = FigureCanvasTkAgg(self.descent_fig, master=self.descent_frame)
        self.descent_canvas.get_tk_widget().pack()
        self.descent_data = []

        # Altitude Difference graph
        self.altitude_diff_fig, self.altitude_diff_ax = plt.subplots(figsize=(3, 2))
        self.altitude_diff_canvas = FigureCanvasTkAgg(self.altitude_diff_fig, master=self.altitude_diff_frame)
        self.altitude_diff_canvas.get_tk_widget().pack()
        self.altitude_diff_data = []

        # Altitude graph
        self.altitude_fig, self.altitude_ax = plt.subplots(figsize=(6, 3))
        self.altitude_canvas = FigureCanvasTkAgg(self.altitude_fig, master=self.altitude_frame)
        self.altitude_canvas.get_tk_widget().pack()
        self.satellite_altitude_data = []
        self.shell_altitude_data = []

        # Pressure graph
        self.pressure_fig, self.pressure_ax = plt.subplots(figsize=(6, 3))
        self.pressure_canvas = FigureCanvasTkAgg(self.pressure_fig, master=self.pressure_frame)
        self.pressure_canvas.get_tk_widget().pack()
        self.satellite_pressure_data = []
        self.shell_pressure_data = []

        # Temperature graph
        self.temperature_fig, self.temperature_ax = plt.subplots(figsize=(6, 3))
        self.temperature_canvas = FigureCanvasTkAgg(self.temperature_fig, master=self.temperature_frame)
        self.temperature_canvas.get_tk_widget().pack()
        self.temperature_data = []

    def update_graph(self, ax, data, canvas):
        ax.clear()
        ax.plot(data)
        canvas.draw()

    def update_graph_dual(self, ax, data1, data2, canvas):
        ax.clear()
        ax.plot(data1, label='Satellite')
        ax.plot(data2, label='Shell')
        ax.legend()
        canvas.draw()

    def update_filter_command(self):
        self.filterCommandList = self.filter_command_entry.get()

    def manual_detachment(self):
        self.manuelDetachment = 1

def main():
    root = tk.Tk()
    app = GroundStationInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main()