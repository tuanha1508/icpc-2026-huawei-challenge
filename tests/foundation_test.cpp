#include <chrono>
#include <cstdint>

#include "foundation.hpp"

int main() {
  foundation::DeterministicRng first(123456789ULL);
  foundation::DeterministicRng second(123456789ULL);
  for (int index = 0; index < 100; ++index) {
    if (first.next_u64() != second.next_u64()) {
      return 1;
    }
  }

  for (int index = 0; index < 100; ++index) {
    const std::int64_t value = first.uniform(-7, 11);
    if (value < -7 || value > 11) {
      return 2;
    }
  }

  foundation::TimeBudget budget(std::chrono::milliseconds(1000));
  if (budget.expired()) {
    return 3;
  }
  if (budget.elapsed_ms() < 0) {
    return 4;
  }
  if (budget.remaining_ms() < 0 || budget.remaining_ms() > 1000) {
    return 5;
  }
  return 0;
}
