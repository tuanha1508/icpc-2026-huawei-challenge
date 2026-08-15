#pragma once

#include <chrono>
#include <cstdint>
#include <limits>
#include <random>

namespace foundation {

using Clock = std::chrono::steady_clock;

class TimeBudget {
 public:
  explicit TimeBudget(std::chrono::milliseconds limit)
      : start_(Clock::now()), deadline_(start_ + limit) {}

  [[nodiscard]] bool expired() const { return Clock::now() >= deadline_; }

  [[nodiscard]] std::int64_t elapsed_ms() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start_)
        .count();
  }

  [[nodiscard]] std::int64_t remaining_ms() const {
    const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
                               deadline_ - Clock::now())
                               .count();
    return remaining > 0 ? remaining : 0;
  }

 private:
  Clock::time_point start_;
  Clock::time_point deadline_;
};

class DeterministicRng {
 public:
  explicit DeterministicRng(std::uint64_t seed = 0x6a09e667f3bcc909ULL)
      : engine_(seed) {}

  [[nodiscard]] std::uint64_t next_u64() { return engine_(); }

  [[nodiscard]] std::int64_t uniform(std::int64_t low, std::int64_t high) {
    std::uniform_int_distribution<std::int64_t> distribution(low, high);
    return distribution(engine_);
  }

 private:
  std::mt19937_64 engine_;
};

}  // namespace foundation

