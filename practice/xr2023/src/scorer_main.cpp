#include "xr.hpp"

#include <exception>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
  try {
    if (argc < 3 || argc > 4) {
      throw std::runtime_error("usage: xr_scorer INPUT OUTPUT [--details]");
    }
    const bool details = argc == 4 && std::string(argv[3]) == "--details";
    if (argc == 4 && !details) {
      throw std::runtime_error("unknown option: " + std::string(argv[3]));
    }
    std::ifstream input(argv[1]);
    std::ifstream output(argv[2]);
    if (!input) throw std::runtime_error("cannot open input file");
    if (!output) throw std::runtime_error("cannot open output file");
    const xr2023::Instance instance = xr2023::Instance::read(input);
    const xr2023::Allocation allocation = xr2023::read_allocation(output, instance);
    const xr2023::Evaluation evaluation = xr2023::evaluate(instance, allocation);
    if (!evaluation.valid) {
      std::cerr << "invalid: " << evaluation.error << '\n';
      return 2;
    }
    std::cout << std::setprecision(17) << evaluation.score << '\n';
    if (details) {
      std::cerr << "successful_frames=" << evaluation.successful_frames << '\n'
                << "total_frames=" << instance.frames.size() << '\n'
                << std::setprecision(17)
                << "total_power=" << evaluation.total_power << '\n';
    }
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "xr_scorer: " << error.what() << '\n';
    return 1;
  }
}

