
## Running HTTP Depth Server 

Install *Python virtual environment*:

```
sudo apt install python3.14-venv

cd ~/robot_ws/src/image_to_3d/depth_anything
python3 -m venv venv
source venv/bin/activate
```

With the virtual environment activated install *PyTorch*:

```
python -m pip install --upgrade pip
pip install torch torchvision
```

Check *PyTorch* installation:
```
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"
   PyTorch: 2.14.0+cu130
   CUDA: True
   GPU: NVIDIA GeForce RTX 3060 Ti
```

More installs:
```
pip install "transformers>=4.45" pillow opencv-python
pip install fastapi uvicorn

```

Run the server:
```
./depth_server.py

```

It should be ready to take HTTP/POST images and will return depth maps/images in PNG uint_16 format, ready for ROS2 processing.

> Check out `~/robot_ws/src/image_to_3d/tests` directory

The following tests interact with the server in a client role:

- tests/test_depth_server.py
- tests/test_depth_server_gui.py
- tests/test_depth_webcam.py

A stand-alone `tests/test_depth.py` can directly call Depth Anything V2 model (while running under a virtual environment).

-------------------------

Back to [Package README](https://github.com/slgrobotics/image_to_3d/blob/main/README.md)

Back to [Main Project Home](https://github.com/slgrobotics/articubot_one/wiki)
