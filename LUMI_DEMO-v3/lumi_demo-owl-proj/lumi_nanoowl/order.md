
启动容器 ：
./docker-compose-linux-aarch64 up --no-recreate -d

报错解决：FileExistsError: [Errno 17] File exists: '/root/.cache/clip'

   rm /root/.cache/clip
   mkdir -p /root/.cache/clip

安装
pip install aiohttp -i https://pypi.tuna.tsinghua.edu.cn/simple

关于X11： 
宿主机上

安装x11：
 apt update && apt install -y x11-apps
然后xclock  如果宿主机弹出时钟窗口，X11 配置就正常了。
注意配置
echo $DISPLAY
export DISPLAY=:1



jaka sdk：
echo 'export LD_LIBRARY_PATH=$(pwd)/JAKA_SDK_ARM:$LD_LIBRARY_PATH' >> ~/.bashrc
或者
echo 'export LD_LIBRARY_PATH=/opt/nanoowl/JAKA_SDK_ARM:$LD_LIBRARY_PATH' >> ~/.bashrc

cd examples/tree_demo
python3 tree_demo.py --camera 4 --resolution 640x400 \
    ../../data/owl_image_encoder_patch32.engine

cd examples/lumi_demo
python3 lumi_demo_owl.py --camera 4 --resolution 1280x800 \
    ../../data/owl_image_encoder_patch32.engine

注意相机的使用  其中哦：
cd pyorbbecsdk
export PYTHONPATH=$PYTHONPATH:$(pwd)/install/lib/
sudo bash ./scripts/install_udev_rules.sh  # 没有正确执行  如果后续有问题 从这里排查
sudo udevadm control --reload-rules && sudo udevadm trigger  # # 没有正确执行  如果后续有问题 从这里排查
python3 examples/depth_viewer.py
python3 examples/net_device.py # Requires ffmpeg installation for network devices


echo 'export PYTHONPATH=$PYTHONPATH:$(pwd)/pyorbbecsdk/install/lib/' >> ~/.bashrc



cd examples
python3 owl_predict.py 


python3 infer_owl.py --image './assets/owl_glove_small.jpg' --tags 'glove, owl' 


警告的提示来设置 
root@ubuntu:/opt/nanoowl# echo $TRANSFORMERS_CACHE
/data/models/huggingface
“你当前的 Transformers 库（HuggingFace Transformers）检测到你设置了环境变量 TRANSFORMERS_CACHE。
这个环境变量用于指定模型和数据的缓存目录。
但是，从 Transformers v5 版本开始，TRANSFORMERS_CACHE 将被废弃（不再支持）。
官方建议改用 HF_HOME 环境变量来指定 HuggingFace 相关的缓存和数据目录。”
export HF_HOME=/data/models/huggingface

echo 'export PYTHONPATH=$PYTHONPATH:$(pwd)/pyorbbecsdk/install/lib/' >> ~/.bashrc


端口1： python3 lumi_demo_owl.py /opt/nanoowl/data/owl_image_encoder_patch32.engine --camera-sn AY8V74300Y8 AY8V74300NK  AY8V74300NK
AY8V74300F4

# 检测人和瓶子
curl -X POST http://localhost:7860/detect \
  -H "Content-Type: application/json" \
  -d '{"tags": ["bottle", "doll"], "conf": 0.5, "iou": 0.8}'

# 检测医疗用品
curl -X POST http://localhost:7860/detect \
  -H "Content-Type: application/json" \
  -d '{"tags": ["medicine", "bottle"], "conf": 0.4, "iou": 0.8}'

# 检测办公用品
curl -X POST http://localhost:7860/detect \
  -H "Content-Type: application/json" \
  -d '{"tags": ["book", "laptop", "cell phone"], "conf": 0.6, "iou": 0.8}'



python3 lumi_demo_ali.py --camera-sn AY8V74300NK

AY8V74300Y8
模拟消息发送
# 检测人和瓶子
curl -X POST http://localhost:7861/detect \
  -H "Content-Type: application/json" \
  -d '{"tags": ["person", "bottle"], "conf": 0.5, "iou": 0.8}'
# 检测医疗用品
curl -X POST http://localhost:7861/detect \
  -H "Content-Type: application/json" \
  -d '{"tags": ["medicine", "bottle"], "conf": 0.4, "iou": 0.8}'



