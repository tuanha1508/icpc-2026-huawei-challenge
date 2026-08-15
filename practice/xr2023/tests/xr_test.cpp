#include "xr.hpp"

#include <cmath>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

int fail_if(bool condition, int code) { return condition ? code : 0; }

constexpr xr2023::Policy kPolicies[] = {
    xr2023::Policy::kIdle,
    xr2023::Policy::kFifo,
    xr2023::Policy::kEdf,
    xr2023::Policy::kShortestRemaining,
    xr2023::Policy::kLeastSlack,
    xr2023::Policy::kAdmissionShortestRemaining,
    xr2023::Policy::kAdmissionSlack,
    xr2023::Policy::kCompletion,
};

xr2023::Evaluation evaluate_policy(const std::string& path, xr2023::Policy policy,
                                   bool trim_power = true) {
  std::ifstream input(path);
  const xr2023::Instance instance = xr2023::Instance::read(input);
  return xr2023::evaluate(instance, xr2023::solve(instance, policy, trim_power));
}

}  // namespace

int main() {
  const std::string data_directory = XR2023_DATA_DIR;
  std::ifstream sample_input(data_directory + "/sample.in");
  std::ifstream sample_output(data_directory + "/sample.out");
  if (!sample_input || !sample_output) return 1;
  const xr2023::Instance sample = xr2023::Instance::read(sample_input);
  const xr2023::Allocation official = xr2023::read_allocation(sample_output, sample);
  const xr2023::Evaluation official_evaluation = xr2023::evaluate(sample, official);
  if (fail_if(!official_evaluation.valid, 2)) return 2;
  if (fail_if(official_evaluation.successful_frames != 2, 3)) return 3;
  if (fail_if(std::abs(official_evaluation.total_power - 0.499978) > 1e-9, 4)) {
    return 4;
  }

  for (const xr2023::Policy policy : kPolicies) {
    const xr2023::Allocation solution = xr2023::solve(sample, policy, true);
    const xr2023::Evaluation evaluation = xr2023::evaluate(sample, solution);
    if (!evaluation.valid) return 10 + static_cast<int>(policy);
  }

  xr2023::GeneratorOptions options;
  options.seed = 42;
  options.users = 4;
  options.cells = 2;
  options.ttis = 12;
  options.rbgs = 2;
  options.frames = 8;
  const xr2023::Instance generated = xr2023::generate(options);
  std::ostringstream serialized;
  generated.write(serialized);
  std::ostringstream regenerated_serialized;
  xr2023::generate(options).write(regenerated_serialized);
  if (serialized.str() != regenerated_serialized.str()) return 34;
  std::istringstream reparsed_input(serialized.str());
  const xr2023::Instance reparsed = xr2023::Instance::read(reparsed_input);
  if (reparsed.users != generated.users || reparsed.cells != generated.cells ||
      reparsed.ttis != generated.ttis || reparsed.rbgs != generated.rbgs ||
      reparsed.frames.size() != generated.frames.size()) {
    return 20;
  }

  xr2023::Allocation invalid(reparsed.resource_count(), 0.0);
  invalid[reparsed.power_index(0, 0, 0, 0)] = 4.1;
  if (xr2023::evaluate(reparsed, invalid).valid) return 21;

  invalid.assign(reparsed.resource_count(), 0.0);
  invalid[reparsed.power_index(0, 0, 0, 0)] =
      std::numeric_limits<double>::quiet_NaN();
  const xr2023::Evaluation nonfinite = xr2023::evaluate(reparsed, invalid);
  if (nonfinite.valid || nonfinite.error.find("t=0 k=0 r=0 n=0") ==
                             std::string::npos) {
    return 28;
  }

  std::ostringstream sample_allocation_text;
  xr2023::write_allocation(sample_allocation_text, sample, official);
  std::istringstream allocation_with_extra(sample_allocation_text.str() + "1\n");
  try {
    static_cast<void>(xr2023::read_allocation(allocation_with_extra, sample));
    return 29;
  } catch (const std::runtime_error&) {
  }

  for (const xr2023::Policy policy : kPolicies) {
    const xr2023::Evaluation trimmed =
        xr2023::evaluate(generated, xr2023::solve(generated, policy, true));
    const xr2023::Evaluation fixed =
        xr2023::evaluate(generated, xr2023::solve(generated, policy, false));
    if (!trimmed.valid || !fixed.valid) return 22;
    if (trimmed.successful_frames != fixed.successful_frames) return 23;
    if (trimmed.total_power > fixed.total_power + 1e-7) return 24;
  }

  const std::string adversarial = data_directory + "/adversarial/";
  const xr2023::Evaluation deadline_fifo = evaluate_policy(
      adversarial + "deadline.in", xr2023::Policy::kFifo);
  const xr2023::Evaluation deadline_edf =
      evaluate_policy(adversarial + "deadline.in", xr2023::Policy::kEdf);
  if (deadline_fifo.successful_frames != 1 ||
      deadline_edf.successful_frames != 2) {
    return 25;
  }

  const xr2023::Evaluation hopeless_slack = evaluate_policy(
      adversarial + "hopeless-trap.in", xr2023::Policy::kLeastSlack);
  const xr2023::Evaluation hopeless_admission = evaluate_policy(
      adversarial + "hopeless-trap.in",
      xr2023::Policy::kAdmissionShortestRemaining);
  if (hopeless_slack.successful_frames != 0 ||
      hopeless_admission.successful_frames != 1) {
    return 26;
  }

  const xr2023::Evaluation untrimmed = evaluate_policy(
      adversarial + "power-trim.in", xr2023::Policy::kFifo, false);
  const xr2023::Evaluation power_trimmed = evaluate_policy(
      adversarial + "power-trim.in", xr2023::Policy::kFifo, true);
  if (untrimmed.successful_frames != 1 ||
      power_trimmed.successful_frames != 1 ||
      !(power_trimmed.total_power < untrimmed.total_power)) {
    return 27;
  }

  for (std::uint64_t seed = 1; seed <= 16; ++seed) {
    xr2023::GeneratorOptions tiny_options;
    tiny_options.seed = seed;
    tiny_options.users = 3;
    tiny_options.cells = 1;
    tiny_options.ttis = 7;
    tiny_options.rbgs = 1;
    tiny_options.frames = 5;
    const char* profiles[] = {"mixed", "burst", "tight", "interference"};
    tiny_options.profile = profiles[seed % 4];
    const xr2023::Instance tiny = xr2023::generate(tiny_options);
    const xr2023::OracleResult oracle =
        xr2023::exact_full_resource_oracle(tiny, 2'000'000);
    const xr2023::Evaluation oracle_evaluation =
        xr2023::evaluate(tiny, oracle.allocation);
    if (!oracle_evaluation.valid ||
        oracle_evaluation.successful_frames != oracle.successful_frames) {
      return 30;
    }
    for (const xr2023::Policy policy : kPolicies) {
      const xr2023::Allocation first = xr2023::solve(tiny, policy, true);
      const xr2023::Allocation second = xr2023::solve(tiny, policy, true);
      if (first != second) return 31;
      const xr2023::Evaluation candidate = xr2023::evaluate(tiny, first);
      if (!candidate.valid ||
          candidate.successful_frames > oracle.successful_frames) {
        return 32;
      }
    }
  }

  xr2023::Instance interference_case;
  interference_case.users = 2;
  interference_case.cells = 2;
  interference_case.ttis = 1;
  interference_case.rbgs = 1;
  interference_case.initial_sinr = {4.0, 3.0, 2.0, 9.0};
  interference_case.interference = {0.0, -1.0, -1.0, 0.0,
                                    0.0, -0.5, -0.5, 0.0};
  interference_case.frames = {{0, 1.0, 0, 0, 1}, {1, 1.0, 1, 0, 1}};
  interference_case.frame_at = {0, 1};
  xr2023::Allocation interference_allocation(
      interference_case.resource_count(), 0.0);
  interference_allocation[interference_case.power_index(0, 0, 0, 0)] = 0.5;
  interference_allocation[interference_case.power_index(0, 1, 0, 1)] = 0.5;
  const xr2023::Evaluation interference =
      xr2023::evaluate(interference_case, interference_allocation);
  const double expected_user_0 =
      xr2023::kResourceElements *
      std::log2(1.0 + 2.0 / (1.0 + std::exp(0.5)));
  const double expected_user_1 =
      xr2023::kResourceElements *
      std::log2(1.0 + 4.5 / (1.0 + 1.5 * std::exp(1.0)));
  if (!interference.valid ||
      std::abs(interference.delivered_bits[0] - expected_user_0) > 1e-9 ||
      std::abs(interference.delivered_bits[1] - expected_user_1) > 1e-9) {
    return 33;
  }
  return 0;
}
