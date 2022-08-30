#调包
import ubluetooth
import binascii
from micropython import const
# 全局变量和常量
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_NOTIFY = const(18)
    
class SoftSpp(object):
    MASTER = const(0)
    SLAVE = const(1)
    def __init__(self, mode , log_en = True):
        self.mode = mode
        self.log = log_en
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        #共用的标志位
        self.con_flag = False
        self.recv_flag = False
        self.buff = bytes(20)
        #主机的标志位
        self.conn_hand = 1
        #从机的标志位
        self.master_addr = bytes(20)
        self.master_addr_type = 1
        self.slave_tx_conn = 1
        self.slave_tx_valu = 0
        self.slave_tx_pre_flag = False
        if self.log:
            for i in self.ble.config('mac'):
                print(binascii.hexlify(str(i)))
            
        
        def ble_master_cb(event, data):
            if event ==_IRQ_CENTRAL_CONNECT:
                self.con_flag =True
                if self.log:
                    print("已有蓝牙连接成功！")            
            elif event == _IRQ_CENTRAL_DISCONNECT:
                self.con_flag =False
                self.ble.gap_advertise(100,b'\x06\x09'+"Sheep".encode("utf-8"))
                if self.log:
                    print("蓝牙连接已断开！")
            elif event == _IRQ_GATTS_WRITE:
                self.recv_flag = True
                conn_handle, char_handle = data
                self.conn_hand = conn_handle
                if char_handle == self.char_rx:
                    self.buff = self.ble.gatts_read(char_handle)
                    if self.log:
                        print(f'rece_data = {self.buff}')
        
        
        def ble_slave_cb(event, data):
            master_name = 'Sheep'
            if event == _IRQ_SCAN_RESULT :  #单次扫描成功
                addr_type, addr, adv_type, rssi, adv_data = data
                if self.log:
                    print(f'扫描到蓝牙地址为%s' % binascii.hexlify(bytes(addr)))
                try :
                    addr_str = bytes(adv_data[bytes(adv_data).find(b'\x09')+1:]).decode('utf-8')
                    #print(f'addr_str = {addr_str},type = {type(addr_str)},judge = {addr_str == master_name}')
                    if addr_str == master_name:
                        if self.log:
                            print(f'连接的主机地址为%s' % binascii.hexlify(bytes(addr)))
                            print('连接的主机名称为%s' % addr_str)
                        self.master_addr = addr
                        self.master_addr_type = addr_type
                        self.ble.gap_scan(None)
                except Exception as e:
                    print(e)
                    
            elif event == _IRQ_SCAN_DONE:   #扫描停止时
                if self.log:
                    print("已经停止扫描")
                    print(f'正在连接%s' % binascii.hexlify(bytes(self.master_addr)))
                self.ble.gap_connect(self.master_addr_type,bytes(self.master_addr))

            elif event == _IRQ_PERIPHERAL_CONNECT:  #外设连接成功时，注意此时连接成功转到协议层。
                # A successful gap_connect().
                conn_handle, addr_type, addr = data
                self.con_flag = True
                if self.log:
                    print(f'已成功连接%s' % binascii.hexlify(bytes(addr)))
                self.ble.gattc_discover_services(conn_handle,ubluetooth.UUID(0x9011))
                
            elif event == _IRQ_GATTC_SERVICE_RESULT:
                # Called for each service found by gattc_discover_services().
                conn_handle, start_handle, end_handle, uuid = data
                if self.log:
                    print(f'主机拥有的服务有{data}')
                self.ble.gattc_discover_characteristics(conn_handle,start_handle,end_handle)
                
            elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
                # Called for each characteristic found by gattc_discover_services().
                conn_handle, def_handle, value_handle, properties, uuid = data
                if self.log:
                    print(f'主机提供的特征值有={data}')
                if uuid == ubluetooth.UUID(0x9013):
                    self.slave_tx_pre_flag = True 
                    self.slave_tx_conn = conn_handle
                    self.slave_tx_valu = value_handle
                    
            elif event == _IRQ_GATTC_NOTIFY:
                # A server has sent a notify request.
                conn_handle, value_handle, notify_data = data
                self.recv_flag = True
                self.buff = bytes(notify_data)
                if self.log:
                    print(f'18-data == {bytes(notify_data)}')

        
        if self.mode == 0:  #Master
            SERVER_SPP_UUID = ubluetooth.UUID(0x9011)  #交换数据服务
            CHAR_TX_UUID = ubluetooth.UUID(0x9012)
            CHAR_RX_UUID = ubluetooth.UUID(0x9013)    
            CHAR_TX = (CHAR_TX_UUID,ubluetooth.FLAG_READ|ubluetooth.FLAG_NOTIFY)
            CHAR_RX = (CHAR_RX_UUID,ubluetooth.FLAG_WRITE)
            SERVER_SPP = (SERVER_SPP_UUID,(CHAR_TX,CHAR_RX))
            SERVICES = (SERVER_SPP,)
            ((self.char_tx,self.char_rx),)= self.ble.gatts_register_services(SERVICES)
            if self.log:
                print(f'char_tx = {self.char_tx}')
                print(f'char_rx = {self.char_rx}')
            self.ble.irq(ble_master_cb)
            self.ble.gap_advertise(100,b'\x06\x09'+'Sheep'.encode('utf-8'))
        elif self.mode == self.SLAVE:
            self.ble.irq(ble_slave_cb)
            self.ble.gap_scan(0)
           
    def active(self):
        return self.con_flag
    def read(self):
        self.recv_flag = False
        return self.buff
    def available(self):
        return self.recv_flag
    def write(self,data):
        if self.mode == self.MASTER:
            self.ble.gatts_notify(self.conn_hand,self.char_tx,data)
        elif self.mode == self.SLAVE and self.slave_tx_pre_flag:
            self.ble.gattc_write(self.slave_tx_conn,self.slave_tx_valu,data)
        
'''主机的测试程序
if __name__ == '__main__':
    import utime
    from machine import Pin
    spp = SoftSpp(SoftSpp.MASTER,False)
    led0 = Pin(12,Pin.OUT,value=0)
    led1 = Pin(13,Pin.OUT,value=0)
    tx_data = 0
    while True:
        tx_data+=3
        if spp.active():
            spp.write(str(tx_data))
            led0.on()
            if spp.available():
                rec_data = spp.read()
                if rec_data == b'A':
                    led1.on()
                if rec_data == b'B':
                    led1.off()
        else:
            led0.off()
            
        utime.sleep_ms(500)
'''
'''从机的测试代码
if __name__ == '__main__':
    import utime
    from machine import Pin
    spp = SoftSpp(SoftSpp.SLAVE,False)
    led0 = Pin(12,Pin.OUT,value=0)
    led1 = Pin(13,Pin.OUT,value=0)
    while True:
        if spp.active():
            if spp.available():
                print(f'recv_data = {spp.read()}')
            led0.on()
            spp.write(b'A')
            utime.sleep_ms(500)
            spp.write(b'B')
            utime.sleep_ms(500)
            spp.write(b'Sheep_hello_world12345')
            utime.sleep_ms(500)
        else :
            led0.off()
'''