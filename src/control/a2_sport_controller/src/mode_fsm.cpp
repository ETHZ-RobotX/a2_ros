#include "mode_fsm.hpp"
#include <algorithm>
#include <stdexcept>

static constexpr std::array<std::pair<OpMode, OpMode>, 8> kValidTransitions = {{
  // Reset Behaviors
  {OpMode::ESTOP, OpMode::STAND_DOWN},
  {OpMode::FREE, OpMode::STAND_DOWN},
  // Normal Behaviors
  {OpMode::STAND_DOWN, OpMode::STAND_UP},
  {OpMode::STAND_UP, OpMode::BALANCE_STAND},
  {OpMode::BALANCE_STAND, OpMode::VELOCITY_MOVE},
  {OpMode::VELOCITY_MOVE, OpMode::BALANCE_STAND},
  {OpMode::BALANCE_STAND, OpMode::STAND_UP},
  {OpMode::STAND_UP, OpMode::STAND_DOWN},
}};

// thread unsafe -> Caller needs to manage locks
ModeFsm::ModeFsm(const float max_vel_x, const float max_vel_y, const float max_yaw_rate) :
  mode_(OpMode::STAND_DOWN),
  mode_changed_(true), // Ensures there's an initial fire of the control
  cmd_vel_({0.0f, 0.0f, 0.0f}),
  max_vel_x_(max_vel_x),
  max_vel_y_(max_vel_y),
  max_yaw_rate_(max_yaw_rate) {
  if (max_vel_x_ < 0 || max_vel_y_ < 0 || max_yaw_rate_ < 0) {
    throw std::invalid_argument("Max velocities and yaw rate must be non-negative");
  }
}

bool ModeFsm::mode_transition(OpMode next) {
  if (mode_ == next) {
    return true;
  }
  bool allowed = (next == OpMode::ESTOP) ||
    (next == OpMode::FREE) ||
    std::find(kValidTransitions.begin(), kValidTransitions.end(), std::pair{mode_, next}) != kValidTransitions.end();
  if (!allowed) {
    return false;
  }
  mode_changed_ = true;
  mode_ = next;
  // Every mode change resets the command velocities
  reset_cmd_vel();
  return true;
}

void ModeFsm::reset_cmd_vel() {
  cmd_vel_.fill(0.0f);
}

// TODO: Do clipping here or rejections?
bool ModeFsm::set_cmd_vel(const float x, const float y, const float yaw) {
  if (mode_ == OpMode::VELOCITY_MOVE) {
    cmd_vel_[0] = std::clamp(x, -max_vel_x_, max_vel_x_);
    cmd_vel_[1] = std::clamp(y, -max_vel_y_, max_vel_y_);
    cmd_vel_[2] = std::clamp(yaw, -max_yaw_rate_, max_yaw_rate_);
    return true;
  }
  reset_cmd_vel();
  return false;
}

// Read by control loop. Once read, change is reset
std::pair<OpMode, bool> ModeFsm::get_mode() {
  auto rval = std::make_pair(mode_, mode_changed_);
  mode_changed_ = false;
  return rval;
}

std::array<float, 3> ModeFsm::get_cmd_vel() {
  return cmd_vel_;
}
