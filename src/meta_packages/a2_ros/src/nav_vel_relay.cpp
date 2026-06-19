#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

class NavVelRelay : public rclcpp::Node {
public:
  NavVelRelay() : Node("nav_vel_relay")
  {
    pub_ = create_publisher<geometry_msgs::msg::TwistStamped>("/nav_vel", 10);
    sub_ = create_subscription<geometry_msgs::msg::TwistStamped>(
      "/path_follower_cmd", 10,
      std::bind(&NavVelRelay::cmdVelCallback, this, std::placeholders::_1));

    timer_ = create_wall_timer(std::chrono::milliseconds(1), [this]() {
      pub_->publish(cmd_vel_);
    });
  }

private:
  void cmdVelCallback(const geometry_msgs::msg::TwistStamped::SharedPtr msg)
  {
    cmd_vel_ = *msg;
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_;
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr sub_;
  rclcpp::TimerBase::SharedPtr timer_;
  geometry_msgs::msg::TwistStamped cmd_vel_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<NavVelRelay>());
  rclcpp::shutdown();
  return 0;
}
