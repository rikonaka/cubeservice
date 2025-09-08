from CubeRaspberryLib3 import OLED
from CubeRaspberryLib3 import Cube
from collections import deque
import time
import psutil

FAN_WORK_TEMP = 52
SLEEP_TIME = 1.0
CPU_TEMP_HISTORY = deque([])
CPU_TEMP_HISTORY_MAX_LEN = 128
SSD_TEMP_HISTORY = deque([])
SSD_TEMP_HISTORY_MAX_LEN = 128
LAST_FAN_STATUS = 100
LINE_HIGHEST_TEMP = 60
LINE_LOWEST_TEMP = 48

# CPU_USAGE_HISTORY = deque([])
# CPU_USAGE_HISTORY_MAX_LEN = 128
# LINE_HIGHEST_CPU = 100
# LINE_LOWEST_CPU = 0


def update_status():
    global CPU_TEMP_HISTORY
    global SSD_TEMP_HISTORY
    # global CPU_USAGE_HISTORY

    temps = psutil.sensors_temperatures()
    cpu_thermal = temps.get("cpu_thermal")[0]
    nvme = temps.get("nvme")[0]

    while len(CPU_TEMP_HISTORY) > CPU_TEMP_HISTORY_MAX_LEN - 1:
        CPU_TEMP_HISTORY.popleft()

    CPU_TEMP_HISTORY.append(cpu_thermal.current)

    while len(SSD_TEMP_HISTORY) > SSD_TEMP_HISTORY_MAX_LEN - 1:
        SSD_TEMP_HISTORY.popleft()

    SSD_TEMP_HISTORY.append(nvme.current)

    # cpu_percent = psutil.cpu_percent(interval=1.0)

    # while len(CPU_USAGE_HISTORY) > CPU_USAGE_HISTORY_MAX_LEN - 1:
    #     CPU_USAGE_HISTORY.popleft()

    # CPU_USAGE_HISTORY.append(cpu_percent)


def oled_text(oled: OLED):
    high_temp_count = 0
    for t in CPU_TEMP_HISTORY:
        if t > FAN_WORK_TEMP:
            high_temp_count += 1

    try:
        if oled.clear():
            h = high_temp_count / len(CPU_TEMP_HISTORY)
            text = "HIGH: {:.2f}%".format(h * 100.0)
            oled.add_row(text=text, row=0)
            text = "CPU TEMP: {:.2f}°C".format(CPU_TEMP_HISTORY[-1])
            oled.add_row(text=text, row=1)
            text = "SSD TEMP: {:.2f}°C".format(SSD_TEMP_HISTORY[-1])
            oled.add_row(text=text, row=2)
            oled.refresh()
        else:
            print("clear screen failed")
    except Exception as e:
        print("oled display text error: {}".format(e))


def fan_job(cube: Cube) -> bool:
    global LAST_FAN_STATUS

    high_temp_count = 0
    for t in CPU_TEMP_HISTORY:
        if t > FAN_WORK_TEMP:
            high_temp_count += 1

    h = high_temp_count / len(CPU_TEMP_HISTORY)
    light_oled = False
    if h > 0.3:
        if LAST_FAN_STATUS != 1:
            # open fan
            cube.set_fan(1)
            cube.set_rgb_effect(3)
            cube.set_rgb_speed(1)
            LAST_FAN_STATUS = 1
            # cube.set_single_color(0, 0, 0, 0)
        light_oled = True
    else:
        if LAST_FAN_STATUS != 0:
            # close fan
            cube.set_fan(0)
            # close the light
            cube.set_single_color(0, 0, 0, 0)
            LAST_FAN_STATUS = 0
        light_oled = False

    return light_oled


def oled_line(oled: OLED):
    new_temp = []
    for i, t in enumerate(CPU_TEMP_HISTORY):
        # 60 is highest temp
        if t > LINE_HIGHEST_TEMP:
            new_temp.append((i, 0))
        elif t < LINE_LOWEST_TEMP:
            new_temp.append((i, 32))
        else:
            nt = (
                32
                - int(
                    ((t - LINE_LOWEST_TEMP) / (LINE_HIGHEST_TEMP - LINE_LOWEST_TEMP))
                    * 32
                )
                + 0
            )
            new_temp.append((i, nt))

    # new_usage = []
    # for i, c in enumerate(CPU_USAGE_HISTORY):
    #     # 100 is highest usage
    #     if c > LINE_HIGHEST_CPU:
    #         new_usage.append((i, 16))
    #     elif c < LINE_LOWEST_CPU:
    #         new_usage.append((i, 32))
    #     else:
    #         nc = (
    #             16
    #             - int(
    #                 ((c - LINE_LOWEST_CPU) / (LINE_HIGHEST_CPU - LINE_LOWEST_CPU)) * 16
    #             )
    #             + 16
    #         )
    #         new_usage.append((i, nc))

    try:
        if oled.clear():
            oled.add_line(new_temp)
            # oled.add_line(new_usage)
            oled.refresh()
        else:
            print("clear screen failed")
    except Exception as e:
        print("oled display line error: {}".format(e))


def main():
    cube = Cube()
    oled = OLED(row_height=10)
    init_status = oled.init()
    if init_status:
        try:
            while True:
                update_status()
                # light_oled = fan_job(cube)
                # if light_oled:
                #     oled_text(oled)
                # else:
                #     # oled.clear(True)
                #     oled_line(oled)
                _ = fan_job(cube)
                oled_line(oled)

                if SLEEP_TIME > 0.0:
                    time.sleep(SLEEP_TIME)
        except KeyboardInterrupt:
            oled.clear(True)
            print("app exit")


if __name__ == "__main__":
    main()
