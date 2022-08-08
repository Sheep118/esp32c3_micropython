from machine import Pin, UART
import utime
import struct
import gy61
LED1 = Pin(12, Pin.OUT)
jy61 = gy61.JY61()
jy61.reset()
while True:
    
    angle = jy61.read_angle()
    print(jy61.angle)
#     jy61.read()
#     print(jy61.angle)
    utime.sleep_ms(10)

