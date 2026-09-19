from setuptools import setup


package_name = 'image_to_3d'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/image_to_3d.launch.py']),
        ('share/' + package_name + '/config', ['config/image_to_3d.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sergei',
    maintainer_email='sergei@example.com',
    description='image_to_3d is a ROS 2 package for converting camera images into depth and derived 3D representations. It provides nodes for image-to-depth estimation and for converting depth images into PointCloud2 and LaserScan messages.',
    license='TODO',
    entry_points={
        'console_scripts': [
            'image_to_depth_node = image_to_3d.image_to_depth_node:main',
            'depth_to_laserscan_node = image_to_3d.depth_to_laserscan_node:main',
            'fake_camera_info_node = image_to_3d.fake_camera_info_node:main',
        ],
    },
)
