# plotter.py
import matplotlib.pyplot as plt

class RealTimePlotter:
    def __init__(self, max_points=200):
        self.max_points = max_points

        # Buffers
        self.gx, self.gy, self.gz = [], [], []
        self.ax, self.ay, self.az = [], [], []
        self.cx, self.cy, self.cz = [], [], []

        # Setup figure
        self.fig, self.axs = plt.subplots(3, 1, figsize=(8, 8))
        self.fig.suptitle("IMU Angle Monitor (Gyro / Accel / Comp)")

        titles = ["Roll", "Pitch", "Yaw"]

        # Create line objects
        self.lines = []
        colors = ["b", "r", "g"]  # gyro=blue, accel=red, comp=green

        for i in range(3):
            line_g, = self.axs[i].plot([], [], colors[0], label="Gyro")
            line_a, = self.axs[i].plot([], [], colors[1], label="Accel")
            line_c, = self.axs[i].plot([], [], colors[2], label="Comp")

            self.lines.append((line_g, line_a, line_c))

            self.axs[i].set_xlim(0, max_points)
            self.axs[i].set_ylim(-180, 180)
            self.axs[i].set_ylabel(titles[i])
            self.axs[i].legend(loc="upper right")

        plt.tight_layout()

    def update(self, ang_gyro, ang_accel, ang_comp):
        # --- Push data ---
        self.gx.append(ang_gyro.x);  self.gy.append(ang_gyro.y);  self.gz.append(ang_gyro.z)
        self.ax.append(ang_accel.x); self.ay.append(ang_accel.y); self.az.append(ang_accel.z)
        self.cx.append(ang_comp.x);  self.cy.append(ang_comp.y);  self.cz.append(ang_comp.z)

        # --- Maintain buffer size ---
        if len(self.gx) > self.max_points:
            self.gx.pop(0); self.gy.pop(0); self.gz.pop(0)
            self.ax.pop(0); self.ay.pop(0); self.az.pop(0)
            self.cx.pop(0); self.cy.pop(0); self.cz.pop(0)

        # --- Update plots ---
        for i, (g_line, a_line, c_line) in enumerate(self.lines):

            if i == 0:
                g_line.set_data(range(len(self.gx)), self.gx)
                a_line.set_data(range(len(self.ax)), self.ax)
                c_line.set_data(range(len(self.cx)), self.cx)

            elif i == 1:
                g_line.set_data(range(len(self.gy)), self.gy)
                a_line.set_data(range(len(self.ay)), self.ay)
                c_line.set_data(range(len(self.cy)), self.cy)

            else:
                g_line.set_data(range(len(self.gz)), self.gz)
                a_line.set_data(range(len(self.az)), self.az)
                c_line.set_data(range(len(self.cz)), self.cz)

        plt.pause(0.001)
