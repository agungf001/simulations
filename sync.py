import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Wedge, Patch
from matplotlib.widgets import Slider, Button
import threading

grid_freq = 50.0
update_interval = 50  # ms

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.40, right=0.85)

circle_radius = 1.8

ax.set_xlim(-2.4, 2.4)
ax.set_ylim(-3.15, 2.4)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title("Synchroscope Simulation", fontsize=16)

circle = plt.Circle((0, 0), circle_radius, color='black', fill=False, linewidth=2)
ax.add_patch(circle)

grid_arrow = ax.arrow(0, 0, 0, circle_radius, head_width=0.09, color='blue')

# Tick marks
for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
    x_outer = circle_radius * np.cos(angle)
    y_outer = circle_radius * np.sin(angle)
    x_inner = 1.575 * np.cos(angle)
    y_inner = 1.575 * np.sin(angle)
    ax.plot([x_outer, x_inner], [y_outer, y_inner], color='black', linewidth=1)

text = plt.figtext(0.1, 0.16, '', fontsize=11, ha='left')
stopwatch_text = plt.figtext(0.1, 0.12, 'Elapsed Time: 0.00 s', fontsize=11, ha='left', color='purple')
rotation_text = plt.figtext(0.1, 0.08, 'Rotations at: ', fontsize=10, ha='left', color='green')

# Sliders
slider_ax = plt.axes([0.2, 0.40, 0.6, 0.03])
freq_slider = Slider(slider_ax, 'Gen Freq (Hz)', 49.0, 51.0, valinit=50.1, valstep=0.01)

cb_time_ax = plt.axes([0.2, 0.35, 0.6, 0.03])
cb_percent_slider = Slider(cb_time_ax, 'CB Closing Time', 0, 100, valinit=50)

# Buttons
button_width = 0.1
button_height = 0.045
button_y = 0.22
button_x_start = 0.25
button_gap = 0.02

pause_ax = plt.axes([button_x_start, button_y, button_width, button_height])
pause_button = Button(pause_ax, 'Pause')

reset_ax = plt.axes([button_x_start + (button_width + button_gap) * 1, button_y, button_width, button_height])
reset_button = Button(reset_ax, 'Reset')

clear_ax = plt.axes([button_x_start + (button_width + button_gap) * 2, button_y, button_width, button_height])
clear_button = Button(clear_ax, 'Clear Rotations')

cb_command_ax = plt.axes([button_x_start + (button_width + button_gap) * 3, button_y, button_width, button_height])
cb_command_button = Button(cb_command_ax, 'CB Close Command')

gen_arrow = None
is_paused = False
elapsed_time = 0.0
prev_phase_deg = 0.0
rotation_times = []

# Sync lights and adjusted labels
sync_lights = {
    '5': plt.Circle((-1.8, -2.1), 0.09, color='gray'),
    '10': plt.Circle((0, -2.1), 0.09, color='gray'),
    '20': plt.Circle((1.8, -2.1), 0.09, color='gray'),
}
for light in sync_lights.values():
    ax.add_patch(light)

# ✅ Label positions adjusted to avoid clashing
ax.text(-1.8, -2.45, "±5°", fontsize=10, ha='center')
ax.text(0, -2.45, "±10°", fontsize=10, ha='center')
ax.text(1.8, -2.45, "±20°", fontsize=10, ha='center')

offset = 90  # degrees

# Shaded sync zones
shaded_areas = [
    Wedge(center=(0, 0), r=circle_radius, theta1=-5 + offset, theta2=5 + offset, facecolor='green', alpha=0.25, label='±5° Window'),
    Wedge(center=(0, 0), r=circle_radius, theta1=-10 + offset, theta2=-5 + offset, facecolor='pink', alpha=0.25, label='± 5° to 10° Window'),
    Wedge(center=(0, 0), r=circle_radius, theta1=5 + offset, theta2=10 + offset, facecolor='pink', alpha=0.25),
    Wedge(center=(0, 0), r=circle_radius, theta1=-20 + offset, theta2=-10 + offset, facecolor='brown', alpha=0.25, label='±10° to 20° Window'),
    Wedge(center=(0, 0), r=circle_radius, theta1=10 + offset, theta2=20 + offset, facecolor='brown', alpha=0.25),
]
for wedge in shaded_areas:
    ax.add_patch(wedge)

# Legend at right
legend_patches = [
    Patch(color='green', alpha=0.25, label='±5° Window'),
    Patch(color='pink', alpha=0.25, label='±5° to 10° Window'),
    Patch(color='brown', alpha=0.25, label='±10° to 20° Window'),
]
ax.legend(
    handles=legend_patches,
    loc='center left',
    bbox_to_anchor=(1.05, 0.5),
    fontsize=9,
    borderaxespad=0.5,
    title="Sync Windows"
)

def angular_diff(a1, a2):
    diff = abs(a1 - a2) % 360
    return diff if diff <= 180 else 360 - diff

def update(frame):
    global gen_arrow, is_paused, elapsed_time, prev_phase_deg, rotation_times

    if is_paused:
        return

    gen_freq = freq_slider.val
    freq_diff = gen_freq - grid_freq
    elapsed_time = frame * update_interval / 1000.0

    phase_rad = 2 * np.pi * freq_diff * elapsed_time
    phase_deg = np.degrees(phase_rad) % 360

    if prev_phase_deg > 300 and phase_deg < 60:
        rotation_times.append(round(elapsed_time, 2))
    prev_phase_deg = phase_deg

    x = circle_radius * np.sin(phase_rad)
    y = circle_radius * np.cos(phase_rad)

    if gen_arrow:
        gen_arrow.remove()
    gen_arrow = ax.arrow(0, 0, x, y, head_width=0.09, color='red')

    phase_error = angular_diff(phase_deg, 0)

    sync_lights['5'].set_color('green' if phase_error <= 5 else 'gray')
    sync_lights['10'].set_color('blue' if phase_error <= 10 else 'gray')
    sync_lights['20'].set_color('orange' if phase_error <= 20 else 'gray')

    direction = ("Fast (Clockwise)" if freq_diff > 0 else "Slow (Counter-Clockwise)" if freq_diff < 0 else "In Sync")

    text.set_text(
        f"Grid: {grid_freq:.2f} Hz | Gen: {gen_freq:.2f} Hz | Δf = {freq_diff:.2f} Hz | "
        f"Phase: {phase_deg:.1f}° | {direction}"
    )
    stopwatch_text.set_text(f'Elapsed Time: {elapsed_time:.2f} s | CB Closing Time: {cb_closing_time_ms:.1f} ms')

    if rotation_times:
        times_str = ', '.join(f"{t:.2f}" for t in rotation_times[-5:])
        rotation_text.set_text(f'Full Rotation Occurs at t(s): {times_str}')
    else:
        rotation_text.set_text("Full Rotation Occurs at t(s) : ")

def pause(event):
    global is_paused
    is_paused = not is_paused
    pause_button.label.set_text("Resume" if is_paused else "Pause")

def reset(event):
    global elapsed_time, rotation_times, prev_phase_deg, is_paused
    freq_slider.reset()
    cb_percent_slider.reset()
    elapsed_time = 0.0
    rotation_times.clear()
    prev_phase_deg = 0.0
    ani.frame_seq = ani.new_frame_seq()
    if is_paused:
        pause(None)

def clear_rotations(event):
    global rotation_times
    rotation_times.clear()
    rotation_text.set_text("Rotations at: ")

cb_closing_time_ms = 100

def cb_percent_slider_update(val):
    percent = val
    if percent <= 50:
        step_percent = 50 / 10
        snapped_step = round(percent / step_percent)
        snapped_percent = snapped_step * step_percent
        cb_time_ms = snapped_step * 10
    else:
        step_percent = 50 / 9
        snapped_step = round((percent - 50) / step_percent)
        snapped_percent = 50 + snapped_step * step_percent
        cb_time_ms = 100 + snapped_step * 100

    cb_percent_slider.eventson = False
    cb_percent_slider.set_val(snapped_percent)
    cb_percent_slider.eventson = True

    cb_percent_slider.valtext.set_text(f"{cb_time_ms:.0f} ms")

    global cb_closing_time_ms
    cb_closing_time_ms = cb_time_ms

cb_percent_slider.on_changed(cb_percent_slider_update)
cb_percent_slider_update(50)

def cb_close_command(event):
    global is_paused
    delay_s = cb_closing_time_ms / 1000.0
    def stop_after_delay():
        threading.Event().wait(delay_s)
        global is_paused
        is_paused = True
        pause_button.label.set_text("Resume")
    threading.Thread(target=stop_after_delay).start()

pause_button.on_clicked(pause)
reset_button.on_clicked(reset)
clear_button.on_clicked(clear_rotations)
cb_command_button.on_clicked(cb_close_command)

ani = animation.FuncAnimation(fig, update, interval=update_interval)

plt.show()
