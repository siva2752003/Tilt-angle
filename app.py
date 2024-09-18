from flask import Flask, render_template, request, send_file
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib.patches as patches

app = Flask(__name__)

# Define constants
days = np.array([1, 31, 62, 92, 122, 153, 183, 213, 244, 274, 304, 335, 365])
solar_constant = 1361  # W/m^2, average solar constant

# Functions for calculations and plotting
def declination_angle(d):
    return 23.45 * np.sin(np.radians(360 * (284 + d) / 365))

def elevation_angle(phi, delta):
    return 90 - phi + delta

def Sincident(phi, delta):
    return solar_constant * np.maximum(0, np.sin(np.radians(elevation_angle(phi, delta))))

def Shoriz(Sincident, alpha):
    return Sincident * np.sin(np.radians(alpha))

def Smodule(Shorizontal, alpha, beta):
    if beta == 0:
        return Shorizontal
    return Shorizontal * np.sin(np.radians(alpha + beta)) / np.sin(np.radians(alpha))

def calculate_efficiency(rated_power_output, S_module_mean, panel_area):
    return rated_power_output / (S_module_mean * panel_area)

def calculate_power_output(efficiency, S_module_mean, panel_area):
    return efficiency * S_module_mean * panel_area

def draw_solar_panel(ax, tilt_angle):
    ax.clear()
    panel_length = 2.5
    panel_width = 0.5
    ax.plot([-2, 2], [0, 0], 'k-', lw=2)
    panel = patches.Rectangle((-panel_length/2, 0), panel_length, panel_width, angle=0, color="blue", fill=True)
    t = plt.matplotlib.transforms.Affine2D().rotate_deg_around(0, 0, -tilt_angle) + ax.transData
    panel.set_transform(t)
    ax.add_patch(panel)
    ax.set_xlim(-2, 2)
    ax.set_ylim(-1, 2)
    ax.set_aspect('equal')
    ax.set_title(f'Solar Panel Tilt: {tilt_angle}°')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot')
def plot():
    tilt_angle = float(request.args.get('tilt_angle', 30))
    latitude = float(request.args.get('latitude', 0))
    rated_power_output = float(request.args.get('rated_power_output', 2000))
    panel_area = float(request.args.get('panel_area', 2))

    delta = declination_angle(days)
    alpha = elevation_angle(latitude, delta)
    S_incident = Sincident(latitude, delta)
    S_horizontal = Shoriz(S_incident, alpha)
    S_module = Smodule(S_horizontal, alpha, tilt_angle)
    S_module_mean = S_module.mean()
    efficiency = calculate_efficiency(rated_power_output, S_module_mean, panel_area)
    actual_power_output = calculate_power_output(efficiency, S_module_mean, panel_area)

    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    ax1 = axs[0]
    ax1.plot(days, S_incident, 'r-', label='Incident (Sincident)')
    ax1.plot(days, S_horizontal, 'b-', label='Horizontal (Shoriz)')
    ax1.plot(days, S_module, 'g-', label='Module (Smodule)')
    ax1.set_xlabel('Days of the Year')
    ax1.set_ylabel('Solar Radiation (W/m²)')
    ax1.set_xticks(days)
    ax1.set_yticks(np.arange(0, 1600, 200))
    ax1.grid(True)
    ax1.legend(loc='upper right')
    ax1.set_title(f'Radiation vs Days (Tilt Angle: {tilt_angle}°, Latitude: {latitude}°)\n'
                  f'Rated Power Output: {rated_power_output} W, Efficiency: {efficiency:.2%}, '
                  f'Actual Power Output: {actual_power_output:.2f} W')

    ax2 = axs[1]
    draw_solar_panel(ax2, tilt_angle)

    plt.tight_layout()

    # Save plot to a BytesIO object and return it as a response
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
