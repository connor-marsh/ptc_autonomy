import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.actions import TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 1. Paths and Configurations
    my_pkg_dir = get_package_share_directory('ptc_autonomy')
    my_slam_params_file = os.path.join(my_pkg_dir, 'config', 'mapper_params_online_async.yaml')
    rviz_config_file = os.path.join(my_pkg_dir, 'rviz', 'slam_config.rviz')

    # 2. Declare Launch Arguments
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Whether to start RViz'
    )
    use_lidar_arg = DeclareLaunchArgument(
        'use_lidar',
        default_value='true',
        description='Whether to start the LiDAR'
    )

    lidar_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('sllidar_ros2'), 'launch', 'sllidar_a1_launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('use_lidar'))
    )

    # 3. Nodes and Includes
    tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '-1.5708', '0', '0', 'base_link', 'laser']
    )

    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rf2o_laser_odometry'), 'launch', 'rf2o_laser_odometry.launch.py')
        )
    )

    delayed_rf2o = TimerAction(
        period=2.0,
        actions=[rf2o_launch]
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')
        ),
        launch_arguments={'slam_params_file': my_slam_params_file}.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    return LaunchDescription([
        use_rviz_arg,
        use_lidar_arg,
        lidar_node,
        tf_node,
        delayed_rf2o,
        slam_launch,
        rviz_node
    ])
