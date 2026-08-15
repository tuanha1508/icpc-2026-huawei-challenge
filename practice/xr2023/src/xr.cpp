#include "xr.hpp"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <iomanip>
#include <istream>
#include <iterator>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <tuple>

namespace xr2023 {
namespace {

class FastScanner {
 public:
  explicit FastScanner(std::istream& input)
      : data_(std::istreambuf_iterator<char>(input),
              std::istreambuf_iterator<char>()),
        cursor_(data_.data()),
        end_(data_.data() + data_.size()) {}

  template <typename Number>
  bool read(Number& value) {
    skip_whitespace();
    if (cursor_ == end_) return false;
    const auto conversion = std::from_chars(cursor_, end_, value);
    if (conversion.ec != std::errc() || conversion.ptr == cursor_) return false;
    cursor_ = conversion.ptr;
    return true;
  }

  bool at_end() {
    skip_whitespace();
    return cursor_ == end_;
  }

 private:
  void skip_whitespace() {
    while (cursor_ != end_ &&
           (*cursor_ == ' ' || *cursor_ == '\n' || *cursor_ == '\r' ||
            *cursor_ == '\t' || *cursor_ == '\f' || *cursor_ == '\v')) {
      ++cursor_;
    }
  }

  std::string data_;
  const char* cursor_;
  const char* end_;
};

void require(bool condition, const std::string& message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

std::vector<int> build_frame_at(const Instance& instance) {
  std::vector<int> result(
      static_cast<std::size_t>(instance.ttis * instance.users), -1);
  for (std::size_t index = 0; index < instance.frames.size(); ++index) {
    const Frame& frame = instance.frames[index];
    for (int t = frame.start; t <= frame.end(); ++t) {
      const std::size_t slot =
          static_cast<std::size_t>(t * instance.users + frame.user);
      require(result[slot] == -1, "multiple frames for one user at one TTI");
      result[slot] = static_cast<int>(index);
    }
  }
  return result;
}

double single_user_bits(const Instance& instance, int t, int user, double power) {
  if (power <= 0.0) {
    return 0.0;
  }
  double bits = 0.0;
  for (int k = 0; k < instance.cells; ++k) {
    double log_sum = 0.0;
    for (int r = 0; r < instance.rbgs; ++r) {
      log_sum += std::log(instance.s0(t, k, r, user) * power);
    }
    const double effective = std::exp(log_sum / instance.rbgs);
    bits += kResourceElements * instance.rbgs * std::log2(1.0 + effective);
  }
  return bits;
}

struct CapacityTable {
  const Instance& instance;
  std::vector<double> per_tti;
  std::vector<double> prefix;

  explicit CapacityTable(const Instance& source)
      : instance(source),
        per_tti(static_cast<std::size_t>(source.ttis * source.users), 0.0),
        prefix(static_cast<std::size_t>(source.users * (source.ttis + 1)), 0.0) {
    for (int n = 0; n < source.users; ++n) {
      for (int t = 0; t < source.ttis; ++t) {
        const double value = single_user_bits(source, t, n, 1.0);
        per_tti[static_cast<std::size_t>(t * source.users + n)] = value;
        prefix[static_cast<std::size_t>(n * (source.ttis + 1) + t + 1)] =
            prefix[static_cast<std::size_t>(n * (source.ttis + 1) + t)] + value;
      }
    }
  }

  [[nodiscard]] double at(int t, int user) const {
    return per_tti[static_cast<std::size_t>(t * instance.users + user)];
  }

  [[nodiscard]] double range(int user, int first, int last_inclusive) const {
    const int width = instance.ttis + 1;
    return prefix[static_cast<std::size_t>(user * width + last_inclusive + 1)] -
           prefix[static_cast<std::size_t>(user * width + first)];
  }
};

void add_tti_bits(const Instance& instance, const Allocation& allocation, int t,
                  std::vector<double>& delivered) {
  for (int k = 0; k < instance.cells; ++k) {
    for (int n = 0; n < instance.users; ++n) {
      int allocated_rbgs = 0;
      double log_sinr_sum = 0.0;
      for (int r = 0; r < instance.rbgs; ++r) {
        const double own_power =
            allocation[instance.power_index(t, k, r, n)];
        if (!(own_power > 0.0)) {
          continue;
        }
        ++allocated_rbgs;
        double intra_log = 0.0;
        for (int m = 0; m < instance.users; ++m) {
          if (m != n && allocation[instance.power_index(t, k, r, m)] > 0.0) {
            intra_log += instance.d(k, r, m, n);
          }
        }

        double denominator = 1.0;
        for (int other_cell = 0; other_cell < instance.cells; ++other_cell) {
          if (other_cell == k) {
            continue;
          }
          for (int other_user = 0; other_user < instance.users; ++other_user) {
            if (other_user == n) {
              continue;
            }
            const double other_power = allocation[instance.power_index(
                t, other_cell, r, other_user)];
            if (other_power > 0.0) {
              denominator +=
                  instance.s0(t, other_cell, r, n) * other_power *
                  std::exp(-instance.d(other_cell, r, other_user, n));
            }
          }
        }
        const double rbg_sinr = instance.s0(t, k, r, n) * own_power *
                                std::exp(intra_log) / denominator;
        log_sinr_sum += std::log(rbg_sinr);
      }
      if (allocated_rbgs == 0) {
        continue;
      }
      const double effective_sinr =
          std::exp(log_sinr_sum / static_cast<double>(allocated_rbgs));
      const double bits = kResourceElements * allocated_rbgs *
                          std::log2(1.0 + effective_sinr);
      const int frame_index =
          instance.frame_at[static_cast<std::size_t>(t * instance.users + n)];
      if (frame_index >= 0) {
        delivered[static_cast<std::size_t>(frame_index)] += bits;
      }
    }
  }
}

double estimated_slack(const CapacityTable& capacities, const Frame& frame, int t,
                       double remaining) {
  const double capacity =
      std::max(capacities.at(t, frame.user),
               std::numeric_limits<double>::min());
  const double service_slots = remaining / capacity;
  return static_cast<double>(frame.end() - t + 1) - service_slots;
}

double estimated_future_capacity(const CapacityTable& capacities,
                                 const Frame& frame, int t) {
  return capacities.range(frame.user, t, frame.end());
}

double estimated_capacity_slack(const CapacityTable& capacities, const Frame& frame,
                                int t, double remaining) {
  const double future_capacity = estimated_future_capacity(capacities, frame, t);
  const int slots = frame.end() - t + 1;
  const double average_capacity =
      future_capacity / static_cast<double>(std::max(1, slots));
  return (future_capacity - remaining) /
         std::max(average_capacity, std::numeric_limits<double>::min());
}

int select_frame(const Instance& instance, const CapacityTable& capacities,
                 Policy policy, int t,
                 const std::vector<double>& delivered) {
  int best = -1;
  std::tuple<int, double, double, int> best_key;
  for (int user = 0; user < instance.users; ++user) {
    const int frame_index =
        instance.frame_at[static_cast<std::size_t>(t * instance.users + user)];
    if (frame_index < 0) {
      continue;
    }
    const std::size_t index = static_cast<std::size_t>(frame_index);
    const Frame& frame = instance.frames[index];
    const double remaining = frame.size - delivered[index];
    if (remaining <= 1e-9) {
      continue;
    }
    const double capacity = capacities.at(t, frame.user);
    const double slack = estimated_slack(capacities, frame, t, remaining);
    const double future_capacity =
        estimated_future_capacity(capacities, frame, t);
    const bool estimated_feasible = remaining <= future_capacity + 1e-9;
    const double capacity_slack =
        estimated_capacity_slack(capacities, frame, t, remaining);
    if (!estimated_feasible &&
        (policy == Policy::kAdmissionShortestRemaining ||
         policy == Policy::kAdmissionSlack || policy == Policy::kCompletion)) {
      continue;
    }
    std::tuple<int, double, double, int> key;
    switch (policy) {
      case Policy::kIdle:
        throw std::runtime_error("idle policy must not select a frame");
      case Policy::kFifo:
        key = {0, static_cast<double>(frame.id), 0.0, frame.id};
        break;
      case Policy::kEdf:
        key = {0, static_cast<double>(frame.end()), remaining, frame.id};
        break;
      case Policy::kShortestRemaining:
        key = {0, remaining, static_cast<double>(frame.end()), frame.id};
        break;
      case Policy::kLeastSlack:
        key = {0, slack, static_cast<double>(frame.end()), frame.id};
        break;
      case Policy::kAdmissionShortestRemaining:
        key = {0, remaining, static_cast<double>(frame.end()), frame.id};
        break;
      case Policy::kAdmissionSlack:
        key = {0, capacity_slack,
               static_cast<double>(frame.end()), frame.id};
        break;
      case Policy::kCompletion:
        key = {0, remaining <= capacity ? 0.0 : 1.0, capacity_slack, frame.id};
        break;
    }
    if (best < 0 || key < best_key) {
      best = static_cast<int>(index);
      best_key = key;
    }
  }
  return best;
}

double trimmed_power(const Instance& instance, int t, const Frame& frame,
                     double remaining) {
  if (single_user_bits(instance, t, frame.user, 1.0) + 1e-9 < remaining) {
    return 1.0;
  }
  double low = 0.0;
  double high = 1.0;
  for (int iteration = 0; iteration < 70; ++iteration) {
    const double middle = (low + high) * 0.5;
    if (single_user_bits(instance, t, frame.user, middle) >= remaining) {
      high = middle;
    } else {
      low = middle;
    }
  }
  return std::min(1.0, high * (1.0 + 1e-9) + 1e-12);
}

}  // namespace

std::size_t Instance::resource_count() const {
  return static_cast<std::size_t>(ttis) * static_cast<std::size_t>(cells) *
         static_cast<std::size_t>(rbgs) * static_cast<std::size_t>(users);
}

std::size_t Instance::power_index(int t, int k, int r, int n) const {
  return static_cast<std::size_t>(((t * cells + k) * rbgs + r) * users + n);
}

std::size_t Instance::sinr_index(int t, int k, int r, int n) const {
  return power_index(t, k, r, n);
}

std::size_t Instance::interference_index(int k, int r, int m, int n) const {
  return static_cast<std::size_t>(((k * rbgs + r) * users + m) * users + n);
}

double Instance::s0(int t, int k, int r, int n) const {
  return initial_sinr[sinr_index(t, k, r, n)];
}

double Instance::d(int k, int r, int m, int n) const {
  return interference[interference_index(k, r, m, n)];
}

Instance Instance::read(std::istream& input) {
  Instance result;
  FastScanner scanner(input);
  require(scanner.read(result.users) && scanner.read(result.cells) &&
              scanner.read(result.ttis) && scanner.read(result.rbgs),
          "failed to read dimensions");
  require(result.users >= 1 && result.users <= 100, "N out of range");
  require(result.cells >= 1 && result.cells <= 10, "K out of range");
  require(result.ttis >= 1 && result.ttis <= 1000, "T out of range");
  require(result.rbgs >= 1 && result.rbgs <= 10, "R out of range");

  result.initial_sinr.resize(result.resource_count());
  for (double& value : result.initial_sinr) {
    require(scanner.read(value), "failed to read initial SINR");
    require(std::isfinite(value) && value > 0.0 && value < 10000.0,
            "initial SINR out of range");
  }

  const std::size_t interference_count =
      static_cast<std::size_t>(result.cells) *
      static_cast<std::size_t>(result.rbgs) *
      static_cast<std::size_t>(result.users) *
      static_cast<std::size_t>(result.users);
  result.interference.resize(interference_count);
  for (double& value : result.interference) {
    require(scanner.read(value), "failed to read interference");
    require(std::isfinite(value) && value >= -2.0 && value <= 0.0,
            "interference out of range");
  }

  int frame_count = 0;
  require(scanner.read(frame_count), "failed to read frame count");
  require(frame_count >= 1 && frame_count <= 5000, "J out of range");
  result.frames.resize(static_cast<std::size_t>(frame_count));
  for (int index = 0; index < frame_count; ++index) {
    Frame& frame = result.frames[static_cast<std::size_t>(index)];
    require(scanner.read(frame.id) && scanner.read(frame.size) &&
                scanner.read(frame.user) && scanner.read(frame.start) &&
                scanner.read(frame.duration),
            "failed to read frame");
    require(frame.id == index, "frame IDs must be consecutive");
    require(frame.size > 0.0 && frame.size <= 100000.0,
            "frame size out of range");
    require(frame.user >= 0 && frame.user < result.users,
            "frame user out of range");
    require(frame.start >= 0 && frame.start < result.ttis,
            "frame start out of range");
    require(frame.duration >= 1 && frame.duration <= 100,
            "frame duration out of range");
    require(frame.end() < result.ttis, "frame deadline out of range");
  }
  require(scanner.at_end(), "extra token after input instance");
  result.frame_at = build_frame_at(result);
  return result;
}

void Instance::write(std::ostream& output) const {
  output << users << '\n' << cells << '\n' << ttis << '\n' << rbgs << '\n';
  output << std::setprecision(12);
  for (int t = 0; t < ttis; ++t) {
    for (int k = 0; k < cells; ++k) {
      for (int r = 0; r < rbgs; ++r) {
        for (int n = 0; n < users; ++n) {
          output << s0(t, k, r, n) << (n + 1 == users ? '\n' : ' ');
        }
      }
    }
  }
  for (int k = 0; k < cells; ++k) {
    for (int r = 0; r < rbgs; ++r) {
      for (int m = 0; m < users; ++m) {
        for (int n = 0; n < users; ++n) {
          output << d(k, r, m, n) << (n + 1 == users ? '\n' : ' ');
        }
      }
    }
  }
  output << frames.size() << '\n';
  for (const Frame& frame : frames) {
    output << frame.id << ' ' << frame.size << ' ' << frame.user << ' '
           << frame.start << ' ' << frame.duration << '\n';
  }
}

Allocation read_allocation(std::istream& input, const Instance& instance) {
  FastScanner scanner(input);
  Allocation result(instance.resource_count());
  for (double& value : result) {
    require(scanner.read(value), "not enough output power values");
  }
  require(scanner.at_end(), "extra token after output allocation");
  return result;
}

void write_allocation(std::ostream& output, const Instance& instance,
                      const Allocation& allocation) {
  require(allocation.size() == instance.resource_count(),
          "allocation has incorrect size");
  std::string buffer;
  buffer.reserve(1U << 20U);
  const auto flush = [&]() {
    output.write(buffer.data(), static_cast<std::streamsize>(buffer.size()));
    buffer.clear();
  };
  for (int t = 0; t < instance.ttis; ++t) {
    for (int k = 0; k < instance.cells; ++k) {
      for (int r = 0; r < instance.rbgs; ++r) {
        for (int n = 0; n < instance.users; ++n) {
          const double value = allocation[instance.power_index(t, k, r, n)];
          if (value == 0.0) {
            buffer.push_back('0');
          } else {
            char text[64];
            const auto conversion = std::to_chars(
                text, text + sizeof(text), value, std::chars_format::fixed, 12);
            require(conversion.ec == std::errc(), "failed to format output power");
            buffer.append(text, conversion.ptr);
          }
          buffer.push_back(n + 1 == instance.users ? '\n' : ' ');
          if (buffer.size() >= (1U << 20U)) {
            flush();
          }
        }
      }
    }
  }
  flush();
}

Evaluation evaluate(const Instance& instance, const Allocation& allocation) {
  Evaluation result;
  result.delivered_bits.assign(instance.frames.size(), 0.0);
  if (allocation.size() != instance.resource_count()) {
    result.error = "allocation has incorrect size: expected " +
                   std::to_string(instance.resource_count()) + ", got " +
                   std::to_string(allocation.size());
    return result;
  }
  for (int t = 0; t < instance.ttis; ++t) {
    for (int k = 0; k < instance.cells; ++k) {
      double cell_power = 0.0;
      for (int r = 0; r < instance.rbgs; ++r) {
        double rbg_power = 0.0;
        for (int n = 0; n < instance.users; ++n) {
          const double power = allocation[instance.power_index(t, k, r, n)];
          if (!std::isfinite(power) || power < 0.0) {
            result.error = "power must be finite and nonnegative at t=" +
                           std::to_string(t) + " k=" + std::to_string(k) +
                           " r=" + std::to_string(r) +
                           " n=" + std::to_string(n);
            return result;
          }
          rbg_power += power;
          cell_power += power;
          result.total_power += power;
        }
        if (rbg_power > 4.0 + kPowerTolerance) {
          result.error = "RBG power exceeds 4 at t=" + std::to_string(t) +
                         " k=" + std::to_string(k) +
                         " r=" + std::to_string(r) +
                         ": " + std::to_string(rbg_power);
          return result;
        }
      }
      if (cell_power > static_cast<double>(instance.rbgs) + kPowerTolerance) {
        result.error = "cell power exceeds R at t=" + std::to_string(t) +
                       " k=" + std::to_string(k) +
                       ": " + std::to_string(cell_power);
        return result;
      }
    }
    add_tti_bits(instance, allocation, t, result.delivered_bits);
  }

  for (std::size_t index = 0; index < instance.frames.size(); ++index) {
    if (result.delivered_bits[index] + 1e-9 >= instance.frames[index].size) {
      ++result.successful_frames;
    }
  }
  result.score = static_cast<double>(result.successful_frames) -
                 1e-6 * result.total_power;
  result.valid = true;
  return result;
}

Policy parse_policy(const std::string& name) {
  if (name == "idle") return Policy::kIdle;
  if (name == "fifo") return Policy::kFifo;
  if (name == "edf") return Policy::kEdf;
  if (name == "srf") return Policy::kShortestRemaining;
  if (name == "slack") return Policy::kLeastSlack;
  if (name == "admission-srf") return Policy::kAdmissionShortestRemaining;
  if (name == "admission-slack") return Policy::kAdmissionSlack;
  if (name == "completion") return Policy::kCompletion;
  throw std::runtime_error("unknown policy: " + name);
}

std::string policy_name(Policy policy) {
  switch (policy) {
    case Policy::kIdle: return "idle";
    case Policy::kFifo: return "fifo";
    case Policy::kEdf: return "edf";
    case Policy::kShortestRemaining: return "srf";
    case Policy::kLeastSlack: return "slack";
    case Policy::kAdmissionShortestRemaining: return "admission-srf";
    case Policy::kAdmissionSlack: return "admission-slack";
    case Policy::kCompletion: return "completion";
  }
  throw std::runtime_error("unreachable policy");
}

Allocation solve(const Instance& instance, Policy policy, bool trim_power) {
  Allocation allocation(instance.resource_count(), 0.0);
  if (policy == Policy::kIdle) {
    return allocation;
  }
  std::vector<double> delivered(instance.frames.size(), 0.0);
  const CapacityTable capacities(instance);
  for (int t = 0; t < instance.ttis; ++t) {
    const int selected = select_frame(instance, capacities, policy, t, delivered);
    if (selected < 0) {
      continue;
    }
    const Frame& frame = instance.frames[static_cast<std::size_t>(selected)];
    const double remaining =
        std::max(0.0, frame.size - delivered[static_cast<std::size_t>(selected)]);
    const double power = trim_power ? trimmed_power(instance, t, frame, remaining)
                                    : 1.0;
    for (int k = 0; k < instance.cells; ++k) {
      for (int r = 0; r < instance.rbgs; ++r) {
        allocation[instance.power_index(t, k, r, frame.user)] = power;
      }
    }
    delivered[static_cast<std::size_t>(selected)] +=
        single_user_bits(instance, t, frame.user, power);
  }
  return allocation;
}

Instance generate(const GeneratorOptions& options) {
  require(options.users >= 1 && options.users <= 100, "generator users out of range");
  require(options.cells >= 1 && options.cells <= 10, "generator cells out of range");
  require(options.ttis >= 1 && options.ttis <= 1000, "generator TTIs out of range");
  require(options.rbgs >= 1 && options.rbgs <= 10, "generator RBGs out of range");
  require(options.frames >= 1 && options.frames <= 5000,
          "generator frames out of range");
  require(options.profile == "mixed" || options.profile == "burst" ||
              options.profile == "tight" || options.profile == "interference",
          "unknown generator profile");

  Instance result;
  result.users = options.users;
  result.cells = options.cells;
  result.ttis = options.ttis;
  result.rbgs = options.rbgs;
  std::mt19937_64 random(options.seed);
  std::uniform_real_distribution<double> unit(0.0, 1.0);

  result.initial_sinr.resize(result.resource_count());
  for (double& value : result.initial_sinr) {
    const double exponent = -1.0 + 3.5 * unit(random);
    value = std::pow(10.0, exponent);
  }

  result.interference.assign(
      static_cast<std::size_t>(result.cells) *
          static_cast<std::size_t>(result.rbgs) *
          static_cast<std::size_t>(result.users) *
          static_cast<std::size_t>(result.users),
      0.0);
  const double severity = options.profile == "interference" ? 1.8 : 0.8;
  for (int k = 0; k < result.cells; ++k) {
    for (int r = 0; r < result.rbgs; ++r) {
      for (int m = 0; m < result.users; ++m) {
        for (int n = m + 1; n < result.users; ++n) {
          const double value = -severity * (0.2 + 0.8 * unit(random));
          result.interference[result.interference_index(k, r, m, n)] = value;
          result.interference[result.interference_index(k, r, n, m)] = value;
        }
      }
    }
  }

  std::vector<unsigned char> occupied(
      static_cast<std::size_t>(result.users * result.ttis), 0);
  const int max_duration = std::min(100, std::max(1, result.ttis / 3));
  int attempts = 0;
  while (static_cast<int>(result.frames.size()) < options.frames && attempts < 200000) {
    ++attempts;
    const int user = static_cast<int>(random() % static_cast<std::uint64_t>(result.users));
    int duration = 1 + static_cast<int>(random() % static_cast<std::uint64_t>(max_duration));
    if (options.profile == "tight") duration = std::min(duration, 3);
    int start_limit = result.ttis - duration;
    int start = static_cast<int>(random() % static_cast<std::uint64_t>(start_limit + 1));
    if (options.profile == "burst") {
      start = static_cast<int>(random() % static_cast<std::uint64_t>(
                  std::max(1, std::min(start_limit + 1, result.ttis / 5 + 1))));
    }
    bool free = true;
    for (int t = start; t < start + duration; ++t) {
      if (occupied[static_cast<std::size_t>(user * result.ttis + t)] != 0) {
        free = false;
        break;
      }
    }
    if (!free) continue;
    for (int t = start; t < start + duration; ++t) {
      occupied[static_cast<std::size_t>(user * result.ttis + t)] = 1;
    }
    double average_capacity = 0.0;
    for (int t = start; t < start + duration; ++t) {
      average_capacity += single_user_bits(result, t, user, 1.0);
    }
    const double load = options.profile == "tight" ? 0.8 + 0.8 * unit(random)
                                                    : 0.2 + 1.2 * unit(random);
    Frame frame;
    frame.id = static_cast<int>(result.frames.size());
    frame.size = std::clamp(average_capacity * load, 1.0, 100000.0);
    frame.user = user;
    frame.start = start;
    frame.duration = duration;
    result.frames.push_back(frame);
  }
  require(!result.frames.empty(), "generator could not place any frames");
  result.frame_at = build_frame_at(result);
  return result;
}

}  // namespace xr2023
