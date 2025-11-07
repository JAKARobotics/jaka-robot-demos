  <!-- 第1步（Linux必须）：配置系统权限 设置摄像头权限 -->
  cd pyorbbecsdk/scripts
  sudo chmod +x ./install_udev_rules.sh
  sudo ./install_udev_rules.sh
  sudo udevadm control --reload && sudo udevadm trigger

  第2步（二选一）：
你的需求	推荐做法
只想跑Demo	pip install + 单独下载samples文件夹
要修改SDK源码	克隆仓库 + 手动编译安装（文档没详细讲）