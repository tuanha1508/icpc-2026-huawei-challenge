#pragma once

#include <cstdint>
#include <iosfwd>
#include <random>
#include <string>
#include <vector>

namespace xr2023 {

constexpr double kResourceElements = 192.0;
constexpr double kPowerTolerance = 1e-7;

struct Frame {
  int id = 0;
  double size = 0.0;
  int user = 0;
  int start = 0;
  int duration = 0;

  [[nodiscard]] int end() const { return start + duration - 1; }
};

struct Instance {
  int users = 0;
  int cells = 0;
  int ttis = 0;
  int rbgs = 0;
  std::vector<double> initial_sinr;
  std::vector<double> interference;
  std::vector<Frame> frames;
  std::vector<int> frame_at;

  [[nodiscard]] std::size_t resource_count() const;
  [[nodiscard]] std::size_t power_index(int t, int k, int r, int n) const;
  [[nodiscard]] std::size_t sinr_index(int t, int k, int r, int n) const;
  [[nodiscard]] std::size_t interference_index(int k, int r, int m, int n) const;
  [[nodiscard]] double s0(int t, int k, int r, int n) const;
  [[nodiscard]] double d(int k, int r, int m, int n) const;

  static Instance read(std::istream& input);
  void write(std::ostream& output) const;
};

using Allocation = std::vector<double>;

struct Evaluation {
  bool valid = false;
  std::string error;
  int successful_frames = 0;
  double total_power = 0.0;
  double score = 0.0;
  std::vector<double> delivered_bits;
};

Allocation read_allocation(std::istream& input, const Instance& instance);
void write_allocation(std::ostream& output, const Instance& instance,
                      const Allocation& allocation);
Evaluation evaluate(const Instance& instance, const Allocation& allocation);

enum class Policy {
  kIdle,
  kFifo,
  kEdf,
  kShortestRemaining,
  kLeastSlack,
  kAdmissionShortestRemaining,
  kAdmissionSlack,
  kCompletion
};

Policy parse_policy(const std::string& name);
std::string policy_name(Policy policy);
Allocation solve(const Instance& instance, Policy policy, bool trim_power = true);

struct OracleResult {
  int successful_frames = 0;
  std::uint64_t explored_nodes = 0;
  Allocation allocation;
};

// Exact for the solver family that assigns every cell/RBG in a TTI to at most
// one user at unit power. Intended only for tiny correctness instances.
OracleResult exact_full_resource_oracle(const Instance& instance,
                                        std::uint64_t max_nodes = 2'000'000);

struct GeneratorOptions {
  std::uint64_t seed = 1;
  int users = 8;
  int cells = 2;
  int ttis = 30;
  int rbgs = 3;
  int frames = 30;
  std::string profile = "mixed";
};

Instance generate(const GeneratorOptions& options);

}  // namespace xr2023
