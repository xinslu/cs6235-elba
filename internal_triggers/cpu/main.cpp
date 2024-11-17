#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <cstring>

class StressTest {
private:
    std::atomic<bool> running{false};
    std::vector<std::thread> threads;

    void cpuStress() {
        std::vector<int> dummy;
        while (running) {
            for (int i = 0; i < 1000000; i++) {
                dummy.push_back(i * i);
            }
            dummy.clear();
        }
    }

public:
    void start(int thread_count) {
        running = true;
        for (int i = 0; i < thread_count; i++) {
            threads.emplace_back(&StressTest::cpuStress, this);
        }
    }

    void stop() {
        running = false;
        for (auto& thread : threads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
        threads.clear();
    }
};

int main(int argc, char* argv[]) {

    int thread_count = 4;
    int duration = 1;

    StressTest stress;
    std::cout << "Starting CPU stress test with " << thread_count << " threads for " << duration << " seconds" << std::endl;
    
    stress.start(thread_count);
    std::this_thread::sleep_for(std::chrono::seconds(duration));
    stress.stop();

    std::cout << "Stress test completed" << std::endl;
    return 0;
}
