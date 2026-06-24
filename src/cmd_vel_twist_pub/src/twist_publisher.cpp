#include <chrono>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

using namespace std::chrono_literals;

class CircleTrajectoryPublisher : public rclcpp::Node
{
public:
  CircleTrajectoryPublisher()
  : Node("circle_trajectory_publisher")
  {
    // Tunable parameters
    linear_speed_ = this->declare_parameter<double>("linear_speed", 0.2);   // m/s
    radius_       = this->declare_parameter<double>("radius", 1.0);          // m
    frame_id_     = this->declare_parameter<std::string>("frame_id", "base_link");

    // angular_velocity = v / r  (sign of r sets turn direction: + = CCW, - = CW)
    angular_velocity_ = linear_speed_ / radius_;

    publisher_ = this->create_publisher<geometry_msgs::msg::TwistStamped>("/cmd_vel", 10);

    timer_ = this->create_wall_timer(
      100ms, std::bind(&CircleTrajectoryPublisher::timer_callback, this));

    RCLCPP_INFO(this->get_logger(),
      "Circular trajectory: v=%.2f m/s, r=%.2f m, w=%.3f rad/s",
      linear_speed_, radius_, angular_velocity_);
  }

private:
  void timer_callback()
  {
    auto msg = geometry_msgs::msg::TwistStamped();

    msg.header.stamp = this->get_clock()->now();
    msg.header.frame_id = frame_id_;

    // Constant forward speed + constant yaw rate  ->  circle of radius v/w
    msg.twist.linear.x  = linear_speed_;
    msg.twist.linear.y  = 0.0;
    msg.twist.linear.z  = 0.0;
    msg.twist.angular.x = 0.0;
    msg.twist.angular.y = 0.0;
    msg.twist.angular.z = angular_velocity_;

    publisher_->publish(msg);
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;

  double linear_speed_;
  double radius_;
  double angular_velocity_;
  std::string frame_id_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CircleTrajectoryPublisher>());
  rclcpp::shutdown();
  return 0;
}