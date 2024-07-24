pyinstaller --onefile driverCheck.py
mkdir -p /usr/local/driverCheck
cp ./dist/driverCheck /usr/local/driverCheck
cp gpu_driver_monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gpu_driver_monitor.service
systemctl start gpu_driver_monitor.service

