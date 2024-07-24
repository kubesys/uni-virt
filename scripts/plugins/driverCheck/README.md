# 服务

- 复制dist目录中二进制文件到指定目录

  ``````
  mkdir -p /usr/local/driverCheck
  cp driverCheck /usr/local/driverCheck
  ``````

- 编写服务配置文件

gpu_driver_monitor.service

``````
[Unit]
Description=Record NVIDIA GPU status
DefaultDependencies=no
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/driverCheck/driverCheck
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
``````

- 复制文件到`/etc/systemd/system/`目录

​	`	cp gpu_driver_monitor.service /etc/systemd/system/`

- 设置开机自启

`sudo systemctl enable gpu_driver_monitor.service`

- 

`sudo systemctl daemon-reload`

- 启动服务

`sudo systemctl start gpu_driver_monitor.service`


