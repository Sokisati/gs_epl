import tkinter as tk
from tkinter import ttk
import threading
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import socket
import numpy as np
import cv2
from PIL import Image, ImageTk
import os
from datetime import datetime
import pandas as pd
import ctypes
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from tkinter import Canvas
import ctypes
from PIL import Image

class OpenGLThread(threading.Thread):
    def __init__(self, canvas, width, height):
        threading.Thread.__init__(self)
        self.canvas = canvas
        self.width = width
        self.height = height
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.y_offset = -1  
        self.running = True

    def run(self):
        pygame.init()
        display = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | pygame.NOFRAME)
        hwnd = pygame.display.get_wm_info()['window']  
        ctypes.windll.user32.ShowWindow(hwnd, 0)  

        glViewport(0, 0, self.width, self.height)
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        
        glTranslatef(0, self.y_offset, -5)  
        glRotatef(-90, 1, 0, 0) 
        glClearColor(1.0, 1.0, 1.0, 0)
        
        while self.running:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glPushMatrix()
            R = self.rotate_matrix(self.roll, self.pitch ,self.yaw)
            glMultMatrixf(R.T.flatten())  
            self.draw_cylinder(0.5, 2, 36, 18)  
            glPopMatrix()
            pygame.display.flip()
            pygame.time.wait(50) 
            self.update_canvas()

    def stop(self):
        self.running = False
        pygame.quit()

    def update_orientation(self, roll, pitch, yaw):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

    def set_y_offset(self, offset):
        self.y_offset = offset

    def update_canvas(self):
        buffer = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
        image = np.frombuffer(buffer, dtype=np.uint8).reshape((self.height, self.width, 3))
        image = np.flipud(image)  
        image = Image.fromarray(image)
        photo = ImageTk.PhotoImage(image=image)
        
        
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo  

    def draw_cylinder(self, radius, height, slices, stacks):
       
        glBegin(GL_QUADS)
        for i in range(slices):
            theta1 = i * 2 * np.pi / slices
            theta2 = (i + 1) * 2 * np.pi / slices
            x1 = radius * np.cos(theta1)
            y1 = radius * np.sin(theta1)
            x2 = radius * np.cos(theta2)
            y2 = radius * np.sin(theta2)
            
            for j in range(stacks):
                z1 = j * height / stacks
                z2 = (j + 1) * height / stacks
                
                if (i + j) % 2 == 0:
                    glColor3f(1.0, 0.0, 0.0)  
                else:
                    glColor3f(0.0, 0.0, 0.0)  
                
                glVertex3f(x1, y1, z1)
                glVertex3f(x2, y2, z1)
                glVertex3f(x2, y2, z2)
                glVertex3f(x1, y1, z2)
        glEnd()
        
        if self.pitch>=0:
            glBegin(GL_TRIANGLE_FAN)
            glColor3f(0.0, 1.0, 0.0)  
            glVertex3f(0, 0, 0)  
            for i in range(slices + 1):
                theta = i * 2 * np.pi / slices
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                glVertex3f(x, y, 0)
            glEnd()
        
            glBegin(GL_TRIANGLE_FAN)
            glColor3f(0.0, 0.0, 1.0)  
            glVertex3f(0, 0, height)  
            for i in range(slices + 1):
                theta = i * 2 * np.pi / slices
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                glVertex3f(x, y, height)
            glEnd()
        else:
        
            glBegin(GL_TRIANGLE_FAN)
            glColor3f(0.0, 0.0, 1.0)  
            glVertex3f(0, 0, height)  
            for i in range(slices + 1):
                theta = i * 2 * np.pi / slices
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                glVertex3f(x, y, height)
            glEnd()
            
            glBegin(GL_TRIANGLE_FAN)
            glColor3f(0.0, 1.0, 0.0)  
            glVertex3f(0, 0, 0)  
            for i in range(slices + 1):
                theta = i * 2 * np.pi / slices
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                glVertex3f(x, y, 0)
            glEnd()
        
       

    def rotate_matrix(self, roll, pitch, yaw):
        
        roll, pitch, yaw = np.radians(pitch), np.radians(roll), np.radians(yaw)
        
        R_x = np.array([
            [1, 0, 0, 0],
            [0, np.cos(roll), -np.sin(roll), 0],
            [0, np.sin(roll), np.cos(roll), 0],
            [0, 0, 0, 1]
        ])
        
        R_y = np.array([
            [np.cos(pitch), 0, np.sin(pitch), 0],
            [0, 1, 0, 0],
            [-np.sin(pitch), 0, np.cos(pitch), 0],
            [0, 0, 0, 1]
        ])
        
        R_z = np.array([
            [np.cos(yaw), -np.sin(yaw), 0, 0],
            [np.sin(yaw), np.cos(yaw), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        R = R_z @ R_y @ R_x
        return R


class GroundStationInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Ground Station Interface")
        self.root.geometry("1920x1080")

        self.stIp = '127.0.0.1'
        self.stPort = 12346
        self.iotData = 36
        self.filterCommandList = '0'
        self.manuelDetachment = 0
        self.telemetry_data = []
        self.errorCodeList = [0, 0, 0, 0, 0]
        self.status = 0

        self.buffer_size = 1024

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.stIp, self.stPort))
        self.server_socket.listen(5)

        self.telemetry_thread = threading.Thread(target=self.listen_for_telemetry)
        self.telemetry_thread.daemon = True
        self.telemetry_thread.start()

        self.camera_thread = threading.Thread(target=self.listen_for_camera_footage)
        self.camera_thread.daemon = True
        self.camera_thread.start()
        
        self.model_frame = tk.Frame(self.root, width=450, height=400, bg='white')
        self.model_frame.place(x=640, y=480)

        self.model_canvas = tk.Canvas(self.model_frame, width=450, height=400, bg='white')
        self.model_canvas.pack(fill=tk.BOTH, expand=True)
           
        self.opengl_thread = OpenGLThread(self.model_canvas, 460, 400)
        self.opengl_thread.start()

        self.setup_frames()
        self.setup_labels()
        self.create_graphs()

        self.camera_window = None

        self.error_code_boxes = []
        for i in range(5):
            box = tk.Label(self.error_code_frame, width=4, height=2, bg='green')
            box.pack(side=tk.LEFT, padx=2, pady=2)
            self.error_code_boxes.append(box)

        self.status_label = tk.Label(self.status_frame, text="Status: Waiting for data", bg='white')
        self.status_label.pack()

        self.video_filename = self.get_video_filename()
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(self.video_filename, self.fourcc, 20.0, (640, 480))


        self.roll_pitch_yaw_canvas = tk.Canvas(self.root, width=180, height=400, bg='white')
        self.roll_pitch_yaw_canvas.place(x=1080, y=480)  
        self.update_roll_pitch_yaw(0,0,0);

    def update_roll_pitch_yaw(self, roll, pitch, yaw):
        self.roll_pitch_yaw_canvas.delete("all")  
        
        font = ('Helvetica', 18, 'bold')
        
        self.roll_pitch_yaw_canvas.create_text(92, 120, text=f"Roll = {roll:.2f}", font=font, fill='black')
        self.roll_pitch_yaw_canvas.create_text(95, 190, text=f"Pitch = {pitch:.2f}", font=font, fill='black')
        self.roll_pitch_yaw_canvas.create_text(92, 260, text=f"Yaw = {yaw:.2f}", font=font, fill='black')

    def setup_frames(self):
        self.camera_frame = tk.Frame(self.root, width=640, height=480, bg='white')
        self.map_frame = tk.Frame(self.root, width=640, height=480, bg='white')
        #self.model_frame = tk.Frame(self.root, width=640, height=480, bg='white')

        self.iot_frame = tk.Frame(self.root, width=320, height=240, bg='white')
        self.battery_frame = tk.Frame(self.root, width=320, height=240, bg='white')
        self.descent_frame = tk.Frame(self.root, width=320, height=240, bg='white')
        self.altitude_diff_frame = tk.Frame(self.root, width=320, height=240, bg='white')

        self.altitude_frame = tk.Frame(self.root, width=640, height=320, bg='white')
        self.pressure_frame = tk.Frame(self.root, width=640, height=320, bg='white')
        self.temperature_frame = tk.Frame(self.root, width=640, height=320, bg='white')

        self.filter_input_frame = tk.Frame(self.root, width=320, height=40, bg='white')

        self.error_code_frame = tk.Frame(self.root, width=500, height=40, bg='white')
        self.status_frame = tk.Frame(self.root, width=100, height=40, bg='white')

        self.manual_detachment_frame = tk.Frame(self.root, width=320, height=40, bg='white')

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

        
        self.filter_input_frame.place(x=0, y=900)

        self.error_code_frame.place(x=840, y=900)
        self.status_frame.place(x=1040, y=900)

        self.manual_detachment_frame.place(x=350, y=900)

    def setup_labels(self):
        tk.Label(self.camera_frame, text="").pack()
        tk.Label(self.map_frame, text="Map").pack()

        tk.Label(self.iot_frame, text="IoT").pack()
        tk.Label(self.battery_frame, text="Battery Voltage (V)").pack()
        tk.Label(self.descent_frame, text="Descent Speed (m/s)").pack()
        tk.Label(self.altitude_diff_frame, text="Altitude Difference (m)").pack()

        tk.Label(self.altitude_frame, text="Altitude (m)").pack()
        tk.Label(self.pressure_frame, text="Pressure (hPa)").pack()
        tk.Label(self.temperature_frame, text="Temperature (C)").pack()

        #tk.Label(self.roll_pitch_yaw_frame, text="Roll, Pitch, Yaw").pack()
        tk.Label(self.filter_input_frame, text="Filter Input").pack()

        tk.Label(self.error_code_frame, text="Error Codes").pack()
        tk.Label(self.status_frame, text="Status").pack()

        tk.Label(self.manual_detachment_frame, text="Manual Detachment").pack()

        # Add four character boxes
        self.filter_command_entries = []
        for _ in range(4):
            entry = tk.Entry(self.filter_input_frame, width=2, font=('Helvetica', 18))
            entry.pack(side=tk.LEFT, padx=5, pady=5)
            self.filter_command_entries.append(entry)
            
        self.send_button = tk.Button(self.filter_input_frame, text="Send", command=self.update_filter_command)
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.manual_detachment_button = tk.Button(self.manual_detachment_frame, text="Manual Detachment", command=self.manual_detachment)
        self.manual_detachment_button.pack(padx=5, pady=5)
        
    def validate_filter_input(self):
        valid_chars = {'R', 'G', 'B'}
        entries = [entry.get() for entry in self.filter_command_entries]

        if any(entry == '' for entry in entries):
            return False

        try:
            num1, char2, num3, char4 = int(entries[0]), entries[1], int(entries[2]), entries[3]
        except ValueError:
            return False
        if not (1 <= num1 <= 9) or not (1 <= num3 <= 9) or num1 + num3 != 10:
            return False
   
        if char2 not in valid_chars or char4 not in valid_chars or char2 == char4:
            return False

        return True

                    
    def get_video_filename(self):
        currentDateTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        save_directory = "camera_footage"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        return os.path.join(save_directory, f"{currentDateTime}_footage.mp4")

    def save_frame(self, frame):
        if self.out is not None:
            self.out.write(frame)

    def listen_for_telemetry(self):
        while True:  
            try:
                print("Waiting for connection...")
                client_socket, addr = self.server_socket.accept()
                print(f"Connection from {addr} has been established.")

                while True:
                    data = client_socket.recv(self.buffer_size)
                    if not data:
                        print("Connection closed by the client.")
                        break
                    if data.decode('utf-8') == "SEND_DATA" or data.decode('utf-8') == "SEND_DATA\n":
                        response = [62, self.filterCommandList, self.manuelDetachment]
                        client_socket.sendall(json.dumps(response).encode('utf-8'))
                    else:
                        try:
                            telemetry_data = json.loads(data.decode('utf-8'))
                            self.update_telemetry_data(telemetry_data)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding telemetry data: {e}")
            except socket.error as e:
                if e.errno == 10054: 
                    print("Error in telemetry listener: Connection was forcibly closed by the remote host.")
                else:
                    print(f"Socket error in telemetry listener: {e}")
            except Exception as e:
                print(f"Error in telemetry listener: {e}")

    def on_closing(self):
        try:
            if self.out is not None:
                self.out.release()
            self.opengl_thread.stop() 
            self.server_socket.close()
            self.root.destroy()
        except Exception as e:
            print(f"Error closing application: {e}")

    def listen_for_camera_footage(self):
        udp_ip = "0.0.0.0"
        udp_port = 5005
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((udp_ip, udp_port))

        print("Listening for incoming camera footage...")

        while True:
            try:
                data, _ = sock.recvfrom(65536)
                np_data = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
                if frame is not None:
                    self.display_camera_frame(frame)
                    self.save_frame(frame)
            except Exception as e:
                print(f"Error receiving camera footage: {e}")

    def display_camera_frame(self, frame):
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            img = img.resize((576, 432), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image=img)

            if not hasattr(self, 'camera_label'):
                self.camera_label = tk.Label(self.camera_frame, image=photo)
                self.camera_label.image = photo
                self.camera_label.pack()
            else:
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
        except Exception as e:
            print(f"Error displaying camera frame: {e}")

    def update_telemetry_data(self, data):
        try:
            
            self.iot_data.append(data['iotData'])
            self.update_graph(self.iot_ax, self.iot_data, self.iot_canvas)

            self.status = data['stStatus']

            self.telemetry_data.append(data)
            if len(self.telemetry_data) > 10:
                self.telemetry_data.pop(0)

            self.battery_data.append(data['batteryVoltage'])
            self.update_graph(self.battery_ax, self.battery_data, self.battery_canvas)

            self.descent_data.append(data['descentSpeed'])
            self.update_graph(self.descent_ax, self.descent_data, self.descent_canvas)

            self.altitude_diff_data.append(data['altitudeDifference'])
            self.update_graph(self.altitude_diff_ax, self.altitude_diff_data, self.altitude_diff_canvas)

            self.satellite_altitude_data.append(data['satelliteAltitude'])
            self.shell_altitude_data.append(data['shellAltitude'])
            self.update_graph_dual(self.altitude_ax, self.satellite_altitude_data, self.shell_altitude_data, self.altitude_canvas)

            self.satellite_pressure_data.append(data['satellitePressure'])
            self.shell_pressure_data.append(data['shellPressure'])
            self.update_graph_dual(self.pressure_ax, self.satellite_pressure_data, self.shell_pressure_data, self.pressure_canvas)

            self.temperature_data.append(data['temperature'])
            self.update_graph(self.temperature_ax, self.temperature_data, self.temperature_canvas)

            self.errorCodeList = data.get('errorCodeList', self.errorCodeList)
            self.update_error_code_boxes()

            self.status_label.config(text=f"Status: {data.get('status', self.status)}")

            gps_latitude = data['gpsLat']
            gps_longitude = data['gpsLong']
            gps_altitude = data['gpsAlt']

            if 'roll' in data and 'pitch' in data and 'yaw' in data:
                self.opengl_thread.update_orientation(data['roll'], data['pitch'], data['yaw'])


            if 'roll' in data and 'pitch' in data and 'yaw' in data:
                self.update_roll_pitch_yaw(data['roll'], data['pitch'], data['yaw'])

            
            self.save_telemetry_data(data)

        except Exception as e:
            print(f"Error updating telemetry data: {e}")

    def save_telemetry_data(self, data):
        telemetry_row = {
            "Paket Numarasi": data['packetNumber'],
            "Uydu Statusu": data['stStatus'],
            "Hata Kodu": ''.join(map(str, data['errorCodeList'])),  
            "Gonderme Saati": data['transmissionTime'],  
            "Basinc1": data['satellitePressure'],
            "Basinc2": data['shellPressure'],
            "Yukseklik1": data['satelliteAltitude'],
            "Yukseklik2": data['shellAltitude'],
            "Irtifa Farki": data['altitudeDifference'],
            "Inis Hizi": data['descentSpeed'],
            "Sicaklik": data['temperature'],
            "Pil Gerilimi": data['batteryVoltage'],
            "GPS1 Latitude": data['gpsLat'],
            "GPS1 Longitude": data['gpsLong'],
            "GPS1 Altitude": data['gpsAlt'],
            "Pitch": data['pitch'],
            "Roll": data['roll'],
            "Yaw": data['yaw'],
            "RHRH": data.get('filterCommandList', ''),  
            "IoT Data": data.get('iotData', ''),
            "Takim No": data['teamNumber'],
        }

        # Save telemetry data to text file
        with open('telemetry_data.txt', 'a', encoding='utf-8') as txt_file:
            txt_file.write(json.dumps(telemetry_row, ensure_ascii=False) + '\n')

        # Create or append to the Excel file
        if os.path.exists('telemetry_data.xlsx'):
            existing_df = pd.read_excel('telemetry_data.xlsx')
            df = pd.DataFrame([telemetry_row])
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = pd.DataFrame([telemetry_row])

        # Write to Excel with a new ExcelWriter context
        with pd.ExcelWriter('telemetry_data.xlsx', mode='w', engine='xlsxwriter') as writer:
            combined_df.to_excel(writer, index=False, sheet_name='Sheet1')
            worksheet = writer.sheets['Sheet1']
            for idx, col in enumerate(combined_df.columns):
                max_len = max(combined_df[col].astype(str).map(len).max(), len(col)) + 2  
                worksheet.set_column(idx, idx, max_len)

    def update_error_code_boxes(self):
        for i, code in enumerate(self.errorCodeList):
            if code == 0:
                self.error_code_boxes[i].config(bg='green')
            else:
                self.error_code_boxes[i].config(bg='red')

    def create_graphs(self):
        try:
            self.iot_fig, self.iot_ax = plt.subplots(figsize=(3, 2))
            self.iot_canvas = FigureCanvasTkAgg(self.iot_fig, master=self.iot_frame)
            self.iot_canvas.get_tk_widget().pack()
            self.iot_data = []

            self.battery_fig, self.battery_ax = plt.subplots(figsize=(3, 2))
            self.battery_canvas = FigureCanvasTkAgg(self.battery_fig, master=self.battery_frame)
            self.battery_canvas.get_tk_widget().pack()
            self.battery_data = []

            self.descent_fig, self.descent_ax = plt.subplots(figsize=(3, 2))
            self.descent_canvas = FigureCanvasTkAgg(self.descent_fig, master=self.descent_frame)
            self.descent_canvas.get_tk_widget().pack()
            self.descent_data = []

            self.altitude_diff_fig, self.altitude_diff_ax = plt.subplots(figsize=(3, 2))
            self.altitude_diff_canvas = FigureCanvasTkAgg(self.altitude_diff_fig, master=self.altitude_diff_frame)
            self.altitude_diff_canvas.get_tk_widget().pack()
            self.altitude_diff_data = []

            self.altitude_fig, self.altitude_ax = plt.subplots(figsize=(6, 3))
            self.altitude_canvas = FigureCanvasTkAgg(self.altitude_fig, master=self.altitude_frame)
            self.altitude_canvas.get_tk_widget().pack()
            self.satellite_altitude_data = []
            self.shell_altitude_data = []

            self.pressure_fig, self.pressure_ax = plt.subplots(figsize=(6, 3))
            self.pressure_canvas = FigureCanvasTkAgg(self.pressure_fig, master=self.pressure_frame)
            self.pressure_canvas.get_tk_widget().pack()
            self.satellite_pressure_data = []
            self.shell_pressure_data = []

            self.temperature_fig, self.temperature_ax = plt.subplots(figsize=(6, 3))
            self.temperature_canvas = FigureCanvasTkAgg(self.temperature_fig, master=self.temperature_frame)
            self.temperature_canvas.get_tk_widget().pack()
            self.temperature_data = []
        except Exception as e:
            print(f"Error creating graphs: {e}")

    def update_filter_command(self):
        if self.validate_filter_input():
            self.filterCommandList = ''.join(entry.get() for entry in self.filter_command_entries)
            print(f"Filter command updated: {self.filterCommandList}")
        else:
            print("Invalid input in filter command boxes.")


    def update_graph(self, ax, data, canvas):
        try:
            ax.clear()
            ax.plot(data)
            canvas.draw()
        except Exception as e:
            print(f"Error updating graph: {e}")

    def update_graph_dual(self, ax, data1, data2, canvas):
        try:
            ax.clear()
            ax.plot(data1, label='Satellite')
            ax.plot(data2, label='Shell')
            ax.legend()
            canvas.draw()
        except Exception as e:
            print(f"Error updating dual graph: {e}")

    def manual_detachment(self):
        self.manuelDetachment = 1


def main():
    root = tk.Tk()
    app = GroundStationInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()