from glob import glob
from setuptools import setup


package_name = 'image_to_3d'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/config', glob('config/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sergei Grichine',
    maintainer_email='slg@quakemap.com',
    description=(
        'image_to_3d is a ROS 2 package for converting camera images into depth '
        'and derived 3D representations. It provides nodes for image-to-depth '
        'estimation and for converting depth images into PointCloud2 and '
        'LaserScan messages.'
    ),
    license='Apache 2.0',
    entry_points={
        'console_scripts': [
            'image_to_depth_node = image_to_3d.image_to_depth_node:main',
            'image_to_depth_yolo_node = image_to_3d.image_to_depth_yolo_node:main',
            'perception_adapter_node = image_to_3d.perception_adapter_node:main',
            'depth_to_laserscan_node = image_to_3d.depth_to_laserscan_node:main',
            'fake_camera_info_node = image_to_3d.fake_camera_info_node:main',
        ],
    },
)
