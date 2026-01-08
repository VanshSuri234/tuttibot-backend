cmake_minimum_required(VERSION 3.10)
project(g1_led_controller)

set(CMAKE_CXX_STANDARD 14)

# Find Unitree SDK (Ensure Unitree SDK is installed on your system)
find_package(unitree_sdk2 REQUIRED)

add_executable(g1_led_controller led_controller.cpp)
target_link_libraries(g1_led_controller unitree_sdk2)