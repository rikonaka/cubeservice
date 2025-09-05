from CubeRaspberryLib3 import OLED
from CubeRaspberryLib3 import Cube
from collections import deque
import time
import psutil

FAN_WORK_TEMP = 52
SLEEP_TIME = 2.0
# MAX LEN is 30
TEMP_HISTORY = deque([])
TEMP_HISTORY_MAX_LEN = 60
LAST_FAN_STATUS = 100


def oled_job(oled: OLED, temps):
    cpu_thermal = temps.get("cpu_thermal")[0]
    nvme = temps.get("nvme")[0]

    high_temp_count = 0
    for t in TEMP_HISTORY:
        if t > FAN_WORK_TEMP:
            high_temp_count += 1

    try:
        if oled.clear():
            text = "CPU TEMP: {:.2f}°C".format(cpu_thermal.current)
            oled.add_row(text=text, row=0)
            text = "NVME TEMP: {:.2f}°C".format(nvme.current)
            oled.add_row(text=text, row=1)
            h = high_temp_count / len(TEMP_HISTORY)
            text = "HIGH: {:.2f}%".format(h * 100.0)
            oled.add_row(text=text, row=2)
            oled.refresh()
        else:
            print("clear screen failed")
    except Exception as e:
        print("run error: {}".format(e))


def fan_job(cube: Cube, temps) -> bool:
    cpu_thermal = temps.get("cpu_thermal")[0]
    nvme = temps.get("nvme")[0]

    highest_temp = 0.0
    if cpu_thermal.current > highest_temp:
        highest_temp = cpu_thermal.current
    if nvme.current > highest_temp:
        highest_temp = nvme.currents

    global TEMP_HISTORY
    global LAST_FAN_STATUS

    while len(TEMP_HISTORY) > TEMP_HISTORY_MAX_LEN:
        TEMP_HISTORY.popleft()

    TEMP_HISTORY.append(highest_temp)

    high_temp_count = 0
    for t in TEMP_HISTORY:
        if t > FAN_WORK_TEMP:
            high_temp_count += 1

    h = high_temp_count / len(TEMP_HISTORY)
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


def main():
    cube = Cube()
    oled = OLED(row_height=10)
    init_status = oled.init()
    if init_status:
        try:
            while True:
                temps = psutil.sensors_temperatures()
                # print(temps)
                light_oled = fan_job(cube, temps)
                if light_oled:
                    oled_job(oled, temps)
                else:
                    oled.clear(True)

                time.sleep(SLEEP_TIME)
        except KeyboardInterrupt:
            oled.clear(True)
            print("app exit")


if __name__ == "__main__":
    main()
