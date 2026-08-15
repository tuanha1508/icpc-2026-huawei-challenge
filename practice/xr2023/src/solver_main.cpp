#include "xr.hpp"

#include <exception>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
  try {
    xr2023::Policy policy = xr2023::Policy::kAdmissionShortestRemaining;
    bool trim_power = true;
    for (int index = 1; index < argc; ++index) {
      const std::string argument = argv[index];
      if (argument == "--policy" && index + 1 < argc) {
        policy = xr2023::parse_policy(argv[++index]);
      } else if (argument == "--no-trim") {
        trim_power = false;
      } else {
        throw std::runtime_error("unknown or incomplete argument: " + argument);
      }
    }
    const xr2023::Instance instance = xr2023::Instance::read(std::cin);
    const xr2023::Allocation allocation =
        xr2023::solve(instance, policy, trim_power);
    xr2023::write_allocation(std::cout, instance, allocation);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "xr_solver: " << error.what() << '\n';
    return 1;
  }
}
