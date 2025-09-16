import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    robotXacroName = 'differential_drive_robot'
    namePackage = 'mobile_robot'
    localization_pkg = get_package_share_directory('rosmaster_localization')
    modelFileRelativePath = 'model/robot.xacro'
    worldFileRelativePath = 'worlds/myworld.sdf'
    rviz_cfg = os.path.join(get_package_share_directory('nav2_bringup'),
                            'rviz', 'nav2_default_view.rviz')


    # gazebo launch
    gazebo_rosPackageLaunch = PythonLaunchDescriptionSource(
        os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    )
    pathworldFile = os.path.join(get_package_share_directory(namePackage), worldFileRelativePath)

    gazeboLaunch = IncludeLaunchDescription(
        gazebo_rosPackageLaunch,
        launch_arguments={
            'gz_args': f'-r -v 4 {pathworldFile}',
            'on_exit_shutdown': 'true'
        }.items()
    )

    # xacro to urdf
    pathModelFile = os.path.join(get_package_share_directory(namePackage), modelFileRelativePath)
    robotDescription = xacro.process_file(pathModelFile).toxml()

    # spawn robot directly from string
    spawnModelNodeGazebo = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', robotXacroName, '-string', robotDescription],
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    # robot_state_publisher
    nodeRobotStatePublisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robotDescription, 'use_sim_time': True}]
    )

    # joint_state_broadcaster (عشان TF يبقى كامل)
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # ros_gz_bridge
    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p', f'config_file:=/home/ahmed/ws_mobile/src/mobile_robot/parameters/ros_gz_bridge.yaml'
        ],
        output='screen'
    )

    # ekf
    ekf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(localization_pkg, 'launch', 'ekf_gazebo.launch.py')
        )
    )

    
    open_Rviz = Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', rviz_cfg], output='screen')

    ld = LaunchDescription()
    ld.add_action(gazeboLaunch)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(nodeRobotStatePublisher)
    ld.add_action(spawnModelNodeGazebo)
    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(open_Rviz)
    ld.add_action(ekf_launch)

    return ld
