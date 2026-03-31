import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # 1. Static TF
    tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '-1.5708', '0', '0', 'base_link', 'laser']
    )

    # 2. RF2O
    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rf2o_laser_odometry'), 'launch', 'rf2o_laser_odometry.launch.py')
        )
    )

    # 3. Lidar
    # Lidar goes last and is delayed to prevent RF2O from getting the transform messed up
    lidar_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('sllidar_ros2'), 'launch', 'sllidar_a1_launch.py')
        ),
        launch_arguments={'serial_port': '/dev/ttyLidar'}.items()
    )


    return LaunchDescription([
        tf_node,
        rf2o_launch,
        TimerAction(period=4.0, actions=[lidar_node])
    ])