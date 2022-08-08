这是一个esp32c3使用micropython读取JY61的文件夹，提供可以直接使用的JY61类和库函数。

简介如下：

>JY61.reset() 用于重启矫正,轴清零
>
>JY61.read_angle()用于读取角度，返回值为roll,pitch，yaw组成的列表
>
>JY61.read() 用于读取时间*time*，角度 *angle*，角速度 *gyro*，加速度 *acc*，四元数 *q* 的数据，根据访问JY61的属性即可访问