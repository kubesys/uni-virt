
1、安装fio


```bash
apt install fio

```

2、在目标目录下测试
到ceph所在目录下


```bash
cd /var/lib/libvirt/myfs

```

编写 fio 测试配置文件： 创建一个描述测试的配置文件。下面是一个简单的例子，可以进行随机读写测试：


```bash
[global]
ioengine=libaio
direct=1
size=1G
runtime=60
group_reporting

[random-read-write]
rw=randrw
bs=4k
iodepth=32

```

该配置文件包括了全局设置和一个测试作业。在全局设置中，我们指定了 IO 引擎为 libaio（异步 I/O），启用了直接 I/O（direct=1），测试文件大小为 1GB，运行时长为 60 秒，并且启用了 group_reporting。在测试作业中，我们进行了随机读写测试（rw=randrw），每次 I/O 操作的块大小为 4KB，I/O 深度为 32。

3、运行测试： 使用 fio 命令运行测试，指定你创建的配置文件。

例如，如果你将上面的配置保存为 test.fio 文件，你可以运行以下命令：


```bash
fio test.fio

```

4、HDD集群测试结果分析


```bash
random-read-write: (g=0): rw=randrw, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=libaio, iodepth=32
fio-3.28
Starting 1 process
random-read-write: Laying out IO file (1 file / 1024MiB)
Jobs: 1 (f=1): [m(1)][100.0%][r=12.2MiB/s,w=12.5MiB/s][r=3132,w=3208 IOPS][eta 00m:00s]
random-read-write: (groupid=0, jobs=1): err= 0: pid=3375864: Tue Apr 30 15:41:43 2024
  read: IOPS=2971, BW=11.6MiB/s (12.2MB/s)(512MiB/44096msec)
    slat (usec): min=21, max=636, avg=95.74, stdev=38.08
    clat (usec): min=857, max=115731, avg=3930.40, stdev=4075.72
     lat (usec): min=920, max=115810, avg=4026.37, stdev=4079.33
    clat percentiles (usec):
     |  1.00th=[ 1172],  5.00th=[ 1401], 10.00th=[ 1565], 20.00th=[ 1827],
     | 30.00th=[ 2073], 40.00th=[ 2343], 50.00th=[ 2671], 60.00th=[ 3130],
     | 70.00th=[ 3752], 80.00th=[ 4883], 90.00th=[ 7373], 95.00th=[10683],
     | 99.00th=[21365], 99.50th=[26870], 99.90th=[43779], 99.95th=[53216],
     | 99.99th=[66847]
   bw (  KiB/s): min= 6096, max=15408, per=100.00%, avg=11904.91, stdev=1707.82, samples=88
   iops        : min= 1524, max= 3852, avg=2976.23, stdev=426.95, samples=88
  write: IOPS=2973, BW=11.6MiB/s (12.2MB/s)(512MiB/44096msec); 0 zone resets
    slat (usec): min=19, max=664, avg=114.63, stdev=43.16
    clat (usec): min=1719, max=117617, avg=6619.73, stdev=5301.28
     lat (usec): min=1836, max=117720, avg=6734.60, stdev=5304.55
    clat percentiles (msec):
     |  1.00th=[    3],  5.00th=[    4], 10.00th=[    4], 20.00th=[    4],
     | 30.00th=[    5], 40.00th=[    5], 50.00th=[    5], 60.00th=[    6],
     | 70.00th=[    7], 80.00th=[    9], 90.00th=[   12], 95.00th=[   16],
     | 99.00th=[   29], 99.50th=[   35], 99.90th=[   57], 99.95th=[   66],
     | 99.99th=[  101]
   bw (  KiB/s): min= 6208, max=15968, per=100.00%, avg=11908.82, stdev=1680.39, samples=88
   iops        : min= 1552, max= 3992, avg=2977.20, stdev=420.10, samples=88
  lat (usec)   : 1000=0.04%
  lat (msec)   : 2=13.48%, 4=36.33%, 10=40.70%, 20=7.43%, 50=1.90%
  lat (msec)   : 100=0.10%, 250=0.01%
  cpu          : usr=2.03%, sys=47.39%, ctx=295344, majf=0, minf=467
  IO depths    : 1=0.1%, 2=0.1%, 4=0.1%, 8=0.1%, 16=0.1%, 32=100.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.1%, 64=0.0%, >=64=0.0%
     issued rwts: total=131040,131104,0,0 short=0,0,0,0 dropped=0,0,0,0
     latency   : target=0, window=0, percentile=100.00%, depth=32

Run status group 0 (all jobs):
   READ: bw=11.6MiB/s (12.2MB/s), 11.6MiB/s-11.6MiB/s (12.2MB/s-12.2MB/s), io=512MiB (537MB), run=44096-44096msec
  WRITE: bw=11.6MiB/s (12.2MB/s), 11.6MiB/s-11.6MiB/s (12.2MB/s-12.2MB/s), io=512MiB (537MB), run=44096-44096msec

```

结果分析如下：

- 读取操作的平均 IOPS 为 2971，带宽为 11.6MiB/s（约 12.2MB/s），读取了 512MiB 的数据，在测试期间持续了 44096 毫秒。

- 写入操作的平均 IOPS 为 2973，带宽与读取操作相同，写入了相同大小的数据，持续时间也相同。

- 读取和写入操作的延迟分布在不同百分位数下，例如第 99.99 百分位数显示了读取和写入操作的最大延迟。

- 读取和写入操作的延迟分布情况，大部分操作的延迟在较低水平，但某些操作的延迟较高，特别是在百分位数较高的情况下。


5、NVMe SSD集群测试结果如下


```bash
random-read-write: (g=0): rw=randrw, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=libaio, iodepth=32
fio-3.28
Starting 1 process
random-read-write: Laying out IO file (1 file / 1024MiB)
Jobs: 1 (f=1): [m(1)][100.0%][r=19.4MiB/s,w=20.1MiB/s][r=4961,w=5142 IOPS][eta 00m:00s]
random-read-write: (groupid=0, jobs=1): err= 0: pid=1100171: Tue Apr 30 15:40:06 2024
  read: IOPS=5851, BW=22.9MiB/s (24.0MB/s)(512MiB/22395msec)
    slat (usec): min=13, max=314, avg=27.89, stdev= 9.51
    clat (usec): min=650, max=67631, avg=1996.49, stdev=1535.44
     lat (usec): min=686, max=67655, avg=2024.56, stdev=1535.47
    clat percentiles (usec):
     |  1.00th=[  988],  5.00th=[ 1139], 10.00th=[ 1237], 20.00th=[ 1352],
     | 30.00th=[ 1467], 40.00th=[ 1582], 50.00th=[ 1713], 60.00th=[ 1860],
     | 70.00th=[ 2040], 80.00th=[ 2343], 90.00th=[ 2933], 95.00th=[ 3621],
     | 99.00th=[ 5997], 99.50th=[ 7635], 99.90th=[19530], 99.95th=[32637],
     | 99.99th=[55313]
   bw (  KiB/s): min=18984, max=26032, per=100.00%, avg=23571.64, stdev=1763.91, samples=44
   iops        : min= 4746, max= 6508, avg=5892.91, stdev=440.98, samples=44
  write: IOPS=5854, BW=22.9MiB/s (24.0MB/s)(512MiB/22395msec); 0 zone resets
    slat (usec): min=13, max=442, avg=29.36, stdev=10.54
    clat (usec): min=1210, max=62083, avg=3410.21, stdev=2074.10
     lat (usec): min=1226, max=62108, avg=3439.75, stdev=2074.17
    clat percentiles (usec):
     |  1.00th=[ 2024],  5.00th=[ 2245], 10.00th=[ 2409], 20.00th=[ 2573],
     | 30.00th=[ 2737], 40.00th=[ 2868], 50.00th=[ 3032], 60.00th=[ 3228],
     | 70.00th=[ 3490], 80.00th=[ 3884], 90.00th=[ 4621], 95.00th=[ 5407],
     | 99.00th=[ 8160], 99.50th=[10028], 99.90th=[41681], 99.95th=[53740],
     | 99.99th=[57934]
   bw (  KiB/s): min=18952, max=25752, per=100.00%, avg=23573.64, stdev=1704.98, samples=44
   iops        : min= 4738, max= 6438, avg=5893.41, stdev=426.23, samples=44
  lat (usec)   : 750=0.01%, 1000=0.55%
  lat (msec)   : 2=33.74%, 4=55.09%, 10=10.22%, 20=0.24%, 50=0.09%
  lat (msec)   : 100=0.05%
  cpu          : usr=3.22%, sys=35.53%, ctx=128813, majf=0, minf=19
  IO depths    : 1=0.1%, 2=0.1%, 4=0.1%, 8=0.1%, 16=0.1%, 32=100.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.1%, 64=0.0%, >=64=0.0%
     issued rwts: total=131040,131104,0,0 short=0,0,0,0 dropped=0,0,0,0
     latency   : target=0, window=0, percentile=100.00%, depth=32

Run status group 0 (all jobs):
   READ: bw=22.9MiB/s (24.0MB/s), 22.9MiB/s-22.9MiB/s (24.0MB/s-24.0MB/s), io=512MiB (537MB), run=22395-22395msec
  WRITE: bw=22.9MiB/s (24.0MB/s), 22.9MiB/s-22.9MiB/s (24.0MB/s-24.0MB/s), io=512MiB (537MB), run=22395-22395msec

```

结果分析如下：

- 读取操作的平均 IOPS 为 5851，带宽为 22.9MiB/s（约 24.0MB/s），读取了 512MiB 的数据，在测试期间持续了 22395 毫秒。

- 写入操作的平均 IOPS 也为 5854，带宽与读取操作相同，写入了相同大小的数据，持续时间也相同。

- 读取和写入操作的延迟分布在不同百分位数下，例如第 99.99 百分位数显示了读取和写入操作的最大延迟。

- 读取和写入操作的延迟分布情况，大部分操作的延迟在较低水平，但某些操作的延迟较高，特别是在百分位数较高的情况下。
