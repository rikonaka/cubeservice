from CubeRaspberryLib3 import OLED
from CubeRaspberryLib3 import Cube
from collections import deque
import time
import psutil

FAN_WORK_TEMP = 55
SLEEP_TIME = 1.0
CPU_TEMP_HISTORY = deque([])
CPU_TEMP_HISTORY_MAX_LEN = 256
SSD_TEMP_HISTORY = deque([])
SSD_TEMP_HISTORY_MAX_LEN = 256
LAST_FAN_STATUS = False
LINE_HIGHEST_TEMP = 60
LINE_LOWEST_TEMP = 45


def check_status(cube: Cube, oled: OLED):
    fan_state = cube.get_fan()
    display_mode = oled.get_display_mode()

    if display_mode == "line":
        if fan_state == 1:
            # line mode but fan on and light on, need to turn off light
            # cube.set_rgb(0)
            cube.set_fan(0)
            cube.set_single_color(0, 0, 0, 0)


def update_status():
    global CPU_TEMP_HISTORY
    global SSD_TEMP_HISTORY

    temps = psutil.sensors_temperatures()
    cpu_thermal = temps.get("cpu_thermal")[0]
    nvme = temps.get("nvme")[0]

    while len(CPU_TEMP_HISTORY) >= CPU_TEMP_HISTORY_MAX_LEN:
        CPU_TEMP_HISTORY.popleft()

    CPU_TEMP_HISTORY.append(cpu_thermal.current)

    while len(SSD_TEMP_HISTORY) >= SSD_TEMP_HISTORY_MAX_LEN:
        SSD_TEMP_HISTORY.popleft()

    SSD_TEMP_HISTORY.append(nvme.current)


def light_job(cube: Cube, on: bool):
    if on:
        # set breathing light
        print("light on")
        # cube.set_rgb(1)
        cube.set_rgb_effect(3)
        cube.set_rgb_speed(1)
    else:
        # turn off the light
        print("light off")
        cube.set_single_color(0, 0, 0, 0)
        # cube.set_rgb(0)


def fan_job(cube: Cube) -> bool:
    global LAST_FAN_STATUS

    high_temp_count = 0
    for t in CPU_TEMP_HISTORY:
        if t > FAN_WORK_TEMP:
            high_temp_count += 1

    h = high_temp_count / len(CPU_TEMP_HISTORY)

    # if more than 30% of history temps are higher than FAN_WORK_TEMP, turn on the fan
    if h > 0.3:
        # if fan already on, do nothing
        if LAST_FAN_STATUS:
            pass
        else:
            # open fan
            print("fan on")
            cube.set_fan(1)
            light_job(cube, True)
            LAST_FAN_STATUS = True
    else:
        # if fan already on, close it
        if LAST_FAN_STATUS:
            # close fan
            print("fan off")
            cube.set_fan(0)
            light_job(cube, False)
            LAST_FAN_STATUS = False
        else:
            # fan already off, do nothing
            pass

    return LAST_FAN_STATUS


def oled_text(oled: OLED):
    high_temp_count = 0
    for t in CPU_TEMP_HISTORY:
        if t > FAN_WORK_TEMP:
            high_temp_count += 1

    try:
        oled.clear()
        h = high_temp_count / len(CPU_TEMP_HISTORY)
        text = "HIGH: {:.2f}%".format(h * 100.0)
        oled.add_row(text=text, row=0)
        text = "CPU TEMP: {:.2f}°C".format(CPU_TEMP_HISTORY[-1])
        oled.add_row(text=text, row=1)
        text = "SSD TEMP: {:.2f}°C".format(SSD_TEMP_HISTORY[-1])
        oled.add_row(text=text, row=2)
        oled.refresh()
    except Exception as e:
        print("oled display text error: {}".format(e))


def oled_line(oled: OLED):
    temp_line = []
    for i, t in enumerate(list(CPU_TEMP_HISTORY)[-128:]):
        # 60 is highest temp
        if t > LINE_HIGHEST_TEMP:
            temp_line.append((i, 0))
        elif t < LINE_LOWEST_TEMP:
            # the height of screen is 32 pixels
            temp_line.append((i, 31))
        else:
            nt = 31 - int(
                ((t - LINE_LOWEST_TEMP) / (LINE_HIGHEST_TEMP - LINE_LOWEST_TEMP)) * 31
            )
            temp_line.append((i, nt))

    try:
        oled.clear()
        oled.add_line(temp_line)
        oled.refresh()
    except Exception as e:
        print("oled display line error: {}".format(e))


def fan_init(cube: Cube):
    global LAST_FAN_STATUS
    # close fan
    cube.set_fan(0)
    # close the light
    cube.set_single_color(0, 0, 0, 0)
    # cube.set_rgb(0)
    LAST_FAN_STATUS = False


def main():
    cube = Cube()
    oled = OLED()
    fan_init(cube)

    oled.init()
    try:
        while True:
            update_status()

            big_fan_on = fan_job(cube)
            if big_fan_on:
                # show text when fan is working
                oled_text(oled)
            else:
                # show line graph when fan is not working
                oled_line(oled)

            if SLEEP_TIME > 0.0:
                time.sleep(SLEEP_TIME)
    except KeyboardInterrupt:
        oled.clear(True)
        print("app exit")


if __name__ == "__main__":
    main()
