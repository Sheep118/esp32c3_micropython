from machine import UART
import utime
import struct
YAWCMD = [0XFF, 0XAA, 0X52]  # z轴复位
ACCCMD = [0XFF, 0XAA, 0X67]  # 加速度计校准
SLEEPCMD = [0XFF, 0XAA, 0X60]  # 休眠模式
UARTMODECMD = [0XFF, 0XAA, 0X61]  # 串口地址设置
IICMODECMD = [0XFF, 0XAA, 0X62]  # IIC地址设置

#注意读取速率为10ms间隔合适

class JY61(object):
    def __init__(self, uart_=1, baudrate_=115200, tx_=0, rx_=1):
        if uart_ == 0 and tx_ == 21 and rx_ == 20:
            self.uart = UART(uart_, baudrate_, tx=tx_, rx=rx_)
#             print("jy61_init_uart0")
        elif uart_ == 1 and tx_ == 0 and rx_ == 1:
            self.uart = UART(uart_, baudrate_, tx=tx_, rx=rx_)
#             print("jy61_init_uart1")
        else:
            pass
#             print("jy61_init_uart_error")
        self.buffer = bytearray(11)
        self.time = list()
        self.angle = [0,0,0,0]
        self.acc = [0,0,0]
        self.gyro = [0,0,0]
        self.q = [0,0,0,0]
    def reset(self):
        self.uart.write(bytearray(YAWCMD))
        utime.sleep_ms(100)
        self.uart.write(bytearray(ACCCMD))
        utime.sleep_ms(1000)
#         print("confirm_success")
        
    def read_angle(self):
        if self.uart.any():
            self.uart.readinto(self.buffer)
            if self.buffer[0:2]== b'\x55\x53':
                self.angle = list(struct.unpack('<hhhh', self.buffer[2:10]))
                for i in range(3):
                    self.angle[i] = self.angle[i]/32768*180
                self.angle[3] = self.angle[3]/100
#             print("recv angle")
        return self.angle
    def read(self):
        if self.uart.any():
            self.uart.readinto(self.buffer)
            if self.buffer[0].to_bytes(1,'big') == b'\x55':  #帧头
                if self.buffer[1].to_bytes(1,'big') == b'\x50':   #时间
                    self.time = (list(struct.unpack('<BBBBBBh', self.buffer[2:10])))
                elif self.buffer[1].to_bytes(1,'big') == b'\x51':  #加速度
                    self.acc = list(struct.unpack('<hhh', self.buffer[2:8]))
                    for i in range(3):
                        self.acc[i] = self.acc[i]/32768*16
                elif self.buffer[1].to_bytes(1,'big') == b'\x52':    #角速度
                    self.gyro = list(struct.unpack('<hhh', self.buffer[2:8]))
                    for i in range(3):
                        self.gyro[i] = self.gyro[i]/32768*2000
                elif self.buffer[1].to_bytes(1,'big') == b'\x53':  #角度 ,直接使用int型比较也可以
                    self.angle = list(struct.unpack('<hhh', self.buffer[2:8]))
                    for i in range(3):
                        self.angle[i] = self.angle[i]/32768*180
                elif self.buffer[1].to_bytes(1,'big') == b'\x59':  #四元数
                    self.q = list(struct.unpack('<hhhh', self.buffer[2:10]))
        return 0
