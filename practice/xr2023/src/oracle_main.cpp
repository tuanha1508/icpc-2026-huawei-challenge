#include "xr.hpp"

#include <cstdint>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
  try {
    std::uint64_t max_nodes = 2'000'000;
    for (int index = 1; index < argc; ++index) {
      const std::string argument = argv[index];
      if (argument == "--max-nodes" && index + 1 < argc) {
        max_nodes = std::stoull(argv[++index]);
      } else {
        throw std::runtime_error("unknown or incomplete argument: " + argument);
      }
    }
    const xr2023::Instance instance = xr2023::Instance::read(std::cin);
    const xr2023::OracleResult result =
        xr2023::exact_full_resource_oracle(instance, max_nodes);
    const xr2023::Evaluation evaluation =
        xr2023::evaluate(instance, result.allocation);
    if (!evaluation.valid ||
        evaluation.successful_frames != result.successful_frames) {
      throw std::runtime_error("oracle allocation failed self-check");
    }
    std::cerr << "optimal_completions=" << result.successful_frames << '\n'
              << "explored_nodes=" << result.explored_nodes << '\n';
    xr2023::write_allocation(std::cout, instance, result.allocation);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "xr_oracle: " << error.what() << '\n';
    return 1;
  }
}
