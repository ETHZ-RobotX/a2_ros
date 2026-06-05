#include <cstdint>
#include <utility>
#include <array>

enum class OpMode : uint8_t {
  ESTOP = 0,          // Joints disabled (most emergency)
  STAND_DOWN = 1,     // Stand down, joints locked
  STAND_UP = 2,       // Stands up, joints locked
  BALANCE_STAND = 3,  // Stands up, joints unlocked
  VELOCITY_MOVE = 4,  // Move with velocity
  FREE = 5,           // Stops the robot but does not disable anything
};

// thread unsafe -> Caller needs to manage locks
class ModeFsm {
public:
  explicit ModeFsm(const float max_vel_x, const float max_vel_y, const float max_yaw_rate);

  bool mode_transition(OpMode next);

  void reset_cmd_vel();

  // TODO: Do clipping here or rejections?
  bool set_cmd_vel(const float x, const float y, const float yaw);

  // Read by control loop. Once read, change is reset
  std::pair<OpMode, bool> get_mode();

  std::array<float, 3> get_cmd_vel();

private:
  // Modes
  OpMode mode_;
  bool mode_changed_;

  // Velocities
  std::array<float, 3> cmd_vel_;
  const float max_vel_x_;
  const float max_vel_y_;
  const float max_yaw_rate_;

};
