import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from nav2_common.launch import RewrittenYaml

def generate_launch_description():
    pkg_dir = get_package_share_directory('ptc_autonomy')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # 1. Dynamically find the absolute paths on whatever machine this is running on
    bt_xml_path = os.path.join(pkg_dir, 'config', 'navigate_to_pose_w_replanning_and_recovery.xml')
    base_params_path = os.path.join(pkg_dir, 'config', 'nav2_params.yaml')

    # 2. Inject the dynamic path into the parameters
    configured_params = RewrittenYaml(
        source_file=base_params_path,
        param_rewrites={
            'default_nav_to_pose_bt_xml': bt_xml_path
        },
        convert_types=True
    )

    # 3. Pass the rewritten parameters to the standard Nav2 launch
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={'params_file': configured_params}.items()
    )

    return LaunchDescription([
        nav2_launch
    ])
