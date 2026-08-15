#include "xr.hpp"

#include <cstdint>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

int parse_int(char** argv, int& index, int argc, const std::string& option) {
  if (index + 1 >= argc) throw std::runtime_error("missing value for " + option);
  return std::stoi(argv[++index]);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    xr2023::GeneratorOptions options;
    for (int index = 1; index < argc; ++index) {
      const std::string argument = argv[index];
      if (argument == "--seed") {
        options.seed = static_cast<std::uint64_t>(
            parse_int(argv, index, argc, argument));
      } else if (argument == "--users") {
        options.users = parse_int(argv, index, argc, argument);
      } else if (argument == "--cells") {
        options.cells = parse_int(argv, index, argc, argument);
      } else if (argument == "--ttis") {
        options.ttis = parse_int(argv, index, argc, argument);
      } else if (argument == "--rbgs") {
        options.rbgs = parse_int(argv, index, argc, argument);
      } else if (argument == "--frames") {
        options.frames = parse_int(argv, index, argc, argument);
      } else if (argument == "--profile" && index + 1 < argc) {
        options.profile = argv[++index];
      } else {
        throw std::runtime_error("unknown or incomplete argument: " + argument);
      }
    }
    xr2023::generate(options).write(std::cout);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "xr_generator: " << error.what() << '\n';
    return 1;
  }
}

