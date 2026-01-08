#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <unitree/robot/g1/audio/g1_audio_client.hpp>
#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/common/time/time_tool.hpp>

// Compile instructions:
// cd led_control
// mkdir build && cd build
// cmake ..
// make

int main(int argc, char const *argv[]) {
    // Check arguments
    if (argc < 5) {
        std::cout << "Usage: " << argv[0] << " <networkInterface> <R> <G> <B>" << std::endl;
        return -1;
    }

    std::string networkInterface = argv[1];
    int r_in = std::stoi(argv[2]);
    int g_in = std::stoi(argv[3]);
    int b_in = std::stoi(argv[4]);

    // Safety clamp (0-255)
    uint8_t r = (uint8_t)(r_in > 255 ? 255 : (r_in < 0 ? 0 : r_in));
    uint8_t g = (uint8_t)(g_in > 255 ? 255 : (g_in < 0 ? 0 : g_in));
    uint8_t b = (uint8_t)(b_in > 255 ? 255 : (b_in < 0 ? 0 : b_in));

    // Initialize SDK
    unitree::robot::ChannelFactory::Instance()->Init(0, networkInterface);

    // Initialize AudioClient (controls LEDs)
    unitree::robot::g1::AudioClient audio_client;
    audio_client.Init();
    audio_client.SetTimeout(1.0f);

    // Send Command
    int32_t ret = audio_client.LedControl(r, g, b);

    if (ret == 0) {
        return 0; // Success
    } else {
        std::cerr << "LED Error: " << ret << std::endl;
        return 1; // Failure
    }
}