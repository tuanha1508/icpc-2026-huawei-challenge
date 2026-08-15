#include "xr.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

namespace xr2023 {
namespace {

double full_resource_bits(const Instance& instance, int t, int user) {
  double bits = 0.0;
  for (int k = 0; k < instance.cells; ++k) {
    double log_sum = 0.0;
    for (int r = 0; r < instance.rbgs; ++r) {
      log_sum += std::log(instance.s0(t, k, r, user));
    }
    const double effective = std::exp(log_sum / instance.rbgs);
    bits += kResourceElements * instance.rbgs * std::log2(1.0 + effective);
  }
  return bits;
}

class TinyOracle {
 public:
  TinyOracle(const Instance& source, std::uint64_t node_limit)
      : instance_(source),
        max_nodes_(node_limit),
        delivered_(source.frames.size(), 0.0),
        schedule_(static_cast<std::size_t>(source.ttis), -1),
        best_schedule_(schedule_),
        capacities_(static_cast<std::size_t>(source.ttis * source.users), 0.0),
        prefix_(static_cast<std::size_t>(source.users * (source.ttis + 1)), 0.0) {
    if (max_nodes_ == 0) {
      throw std::runtime_error("oracle max_nodes must be positive");
    }
    for (int user = 0; user < instance_.users; ++user) {
      for (int t = 0; t < instance_.ttis; ++t) {
        const double capacity = full_resource_bits(instance_, t, user);
        capacities_[static_cast<std::size_t>(t * instance_.users + user)] =
            capacity;
        prefix_[prefix_index(user, t + 1)] =
            prefix_[prefix_index(user, t)] + capacity;
      }
    }
  }

  OracleResult run() {
    search(0);
    OracleResult result;
    result.successful_frames = best_successful_;
    result.explored_nodes = explored_nodes_;
    result.allocation.assign(instance_.resource_count(), 0.0);
    for (int t = 0; t < instance_.ttis; ++t) {
      const int user = best_schedule_[static_cast<std::size_t>(t)];
      if (user < 0) continue;
      for (int k = 0; k < instance_.cells; ++k) {
        for (int r = 0; r < instance_.rbgs; ++r) {
          result.allocation[instance_.power_index(t, k, r, user)] = 1.0;
        }
      }
    }
    return result;
  }

 private:
  [[nodiscard]] std::size_t prefix_index(int user, int boundary) const {
    return static_cast<std::size_t>(user * (instance_.ttis + 1) + boundary);
  }

  [[nodiscard]] double future_capacity(const Frame& frame, int t) const {
    const int first = std::max(t, frame.start);
    if (first > frame.end()) return 0.0;
    return prefix_[prefix_index(frame.user, frame.end() + 1)] -
           prefix_[prefix_index(frame.user, first)];
  }

  [[nodiscard]] int optimistic_successes(int t) const {
    int possible = 0;
    for (std::size_t index = 0; index < instance_.frames.size(); ++index) {
      const Frame& frame = instance_.frames[index];
      const double remaining = frame.size - delivered_[index];
      if (remaining <= 1e-9 || remaining <= future_capacity(frame, t) + 1e-9) {
        ++possible;
      }
    }
    return possible;
  }

  [[nodiscard]] int completed() const {
    int count = 0;
    for (std::size_t index = 0; index < instance_.frames.size(); ++index) {
      if (delivered_[index] + 1e-9 >= instance_.frames[index].size) ++count;
    }
    return count;
  }

  void search(int t) {
    if (++explored_nodes_ > max_nodes_) {
      throw std::runtime_error("tiny oracle exceeded max_nodes");
    }
    if (optimistic_successes(t) <= best_successful_) return;
    if (t == instance_.ttis) {
      const int successful = completed();
      if (successful > best_successful_) {
        best_successful_ = successful;
        best_schedule_ = schedule_;
      }
      return;
    }

    schedule_[static_cast<std::size_t>(t)] = -1;
    search(t + 1);
    for (int user = 0; user < instance_.users; ++user) {
      const int frame_index =
          instance_.frame_at[static_cast<std::size_t>(t * instance_.users + user)];
      if (frame_index < 0) continue;
      const std::size_t index = static_cast<std::size_t>(frame_index);
      if (delivered_[index] + 1e-9 >= instance_.frames[index].size) continue;
      const double capacity =
          capacities_[static_cast<std::size_t>(t * instance_.users + user)];
      schedule_[static_cast<std::size_t>(t)] = user;
      delivered_[index] += capacity;
      search(t + 1);
      delivered_[index] -= capacity;
    }
    schedule_[static_cast<std::size_t>(t)] = -1;
  }

  const Instance& instance_;
  std::uint64_t max_nodes_;
  std::vector<double> delivered_;
  std::vector<int> schedule_;
  std::vector<int> best_schedule_;
  std::vector<double> capacities_;
  std::vector<double> prefix_;
  std::uint64_t explored_nodes_ = 0;
  int best_successful_ = -1;
};

}  // namespace

OracleResult exact_full_resource_oracle(const Instance& instance,
                                        std::uint64_t max_nodes) {
  if (instance.frames.size() > 64 || instance.ttis > 20 || instance.users > 8) {
    throw std::runtime_error("tiny oracle instance exceeds safety dimensions");
  }
  return TinyOracle(instance, max_nodes).run();
}

}  // namespace xr2023
