from CubeRaspberryLib3 import OLED
from CubeRaspberryLib3 import Cube
import time
import psutil

FAN_WORK_TEMP = 50
SLEEP_TIME = 2.0
# MAX LEN is 30
TEMP_HISTORY = []
TEMP_HISTORY_MAX_LEN = 30


def oled_job(oled: OLED, temps):
    cpu_thermal = temps.get("cpu_thermal")[0]
    nvme = temps.get("nvme")[0]

    try:
        if oled.clear():
            text = "CPU TEMP: {:.2f}°C".format(cpu_thermal.current)
            oled.add_row(text=text, row=1)
            text = "NVME TEMP: {:.2f}°C".format(nvme.current)
            oled.add_row(text=text, row=2)
            oled.refresh()
        else:
            print("clear screen failed")
    except Exception as e:
        print("run error: {}".format(e))


def fan_job(cube: Cube, temps):
    cpu_thermal = temps.get("cpu_thermal")[0]
    nvme = temps.get("nvme")[0]

    highest_temp = 0.0
    if cpu_thermal.current > highest_temp:
        highest_temp = cpu_thermal.current
    if nvme.current > highest_temp:
        highest_temp = nvme.currents

    while len(TEMP_HISTORY) > TEMP_HISTORY_MAX_LEN:
        TEMP_HISTORY.pop()

    TEMP_HISTORY.append(highest_temp)

    if highest_temp > FAN_WORK_TEMP:
        # open fan
        cube.set_fan(1)
        cube.set_rgb_effect(3)
        cube.set_rgb_speed(1)
        # cube.set_single_color(0, 0, 0, 0)
    else:
        # close fan
        low_temp_count = 0
        for t in TEMP_HISTORY:
            if t < FAN_WORK_TEMP:
                low_temp_count += 1

        if low_temp_count / len(TEMP_HISTORY) > 0.8:
            cube.set_fan(0)
            # close the light
            cube.set_single_color(0, 0, 0, 0)


def main():
    cube = Cube()
    oled = OLED(row_height=10)
    init_status = oled.init()
    if init_status:
        try:
            while True:
                temps = psutil.sensors_temperatures()
                # print(temps)
                fan_job(cube, temps)
                oled_job(oled, temps)
                time.sleep(SLEEP_TIME)
        except KeyboardInterrupt:
            oled.clear(True)
            del oled
            del cube
            print("app exit")


if __name__ == "__main__":
    main()
