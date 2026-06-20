#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

// Bidirectional Twist <-> TwistStamped bridge for /cmd_vel.
//
// The locomotion controller consumes TwistStamped on /cmd_vel (and uses the
// header stamp for its stale-command watchdog), but some tools speak plain
// Twist (e.g. nav2, teleop_twist_keyboard without stamped:=true) and some
// legacy consumers still want plain Twist. This node bridges both directions:
//
//   stamp   : twist_in_topic  (Twist)        -> stamped_topic   (TwistStamped)
//   unstamp : stamped_topic    (TwistStamped) -> twist_out_topic (Twist)
//
// Defaults are chosen so the two directions use disjoint topics and cannot form
// a feedback loop:
//   twist_in_topic  = /cmd_vel_in     (plain-Twist producers publish here)
//   stamped_topic   = /cmd_vel        (canonical TwistStamped topic)
//   twist_out_topic = /cmd_vel_twist  (mirror for plain-Twist consumers)
//   frame_id        = ""              (stamp only, no frame)
//
// A loop would arise only if twist_out_topic == twist_in_topic (unstamped output
// fed back into the stamper); that case is detected and the unstamp direction is
// disabled with an error.
class NavVelRelay : public rclcpp::Node {
public:
  NavVelRelay() : Node("nav_vel_relay")
  {
    const std::string twist_in   = declare_parameter<std::string>("twist_in_topic", "/cmd_vel_in");
    const std::string stamped    = declare_parameter<std::string>("stamped_topic", "/cmd_vel");
    const std::string twist_out  = declare_parameter<std::string>("twist_out_topic", "/cmd_vel_twist");
    frame_id_                    = declare_parameter<std::string>("frame_id", "");

    // stamp: Twist -> TwistStamped
    stamped_pub_ = create_publisher<geometry_msgs::msg::TwistStamped>(stamped, 10);
    twist_in_sub_ = create_subscription<geometry_msgs::msg::Twist>(
      twist_in, 10,
      [this](const geometry_msgs::msg::Twist::SharedPtr msg) {
        geometry_msgs::msg::TwistStamped out;
        out.header.stamp = now();
        out.header.frame_id = frame_id_;
        out.twist = *msg;
        stamped_pub_->publish(out);
      });

    // unstamp: TwistStamped -> Twist (skipped if it would feed back into the stamper)
    if (twist_out == twist_in) {
      RCLCPP_ERROR(get_logger(),
                   "twist_out_topic == twist_in_topic ('%s') would create a feedback loop; "
                   "disabling the unstamp direction.", twist_in.c_str());
    } else {
      twist_out_pub_ = create_publisher<geometry_msgs::msg::Twist>(twist_out, 10);
      stamped_sub_ = create_subscription<geometry_msgs::msg::TwistStamped>(
        stamped, 10,
        [this](const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
          twist_out_pub_->publish(msg->twist);
        });
    }

    RCLCPP_INFO(get_logger(), "stamp:   %s (Twist) -> %s (TwistStamped)",
                twist_in.c_str(), stamped.c_str());
    if (stamped_sub_)
      RCLCPP_INFO(get_logger(), "unstamp: %s (TwistStamped) -> %s (Twist)",
                  stamped.c_str(), twist_out.c_str());
  }

private:
  std::string frame_id_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr    stamped_pub_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr        twist_in_sub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr           twist_out_pub_;
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr stamped_sub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<NavVelRelay>());
  rclcpp::shutdown();
  return 0;
}
