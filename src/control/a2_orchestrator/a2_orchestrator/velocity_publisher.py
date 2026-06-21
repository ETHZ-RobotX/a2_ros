#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped

class VelocityPublisher(Node):
    def __init__(self):
        super().__init__('velocity_publisher')
        
        # Topic is /cmd_vel (expected by SafeVelocityRosInterface)
        self.publisher_ = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        
        # Safety FSM expects a control period of ~20ms (50Hz)
        self.timer_period = 0.02  # seconds (50 Hz)
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        
        self.counter = 0
        self.get_logger().info(
            "Velocity Publisher started.\n"
            "Publishing forward velocity of 0.1 m/s to /cmd_vel at 50Hz.\n"
        )

    def timer_callback(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        
        msg.twist.linear.x = 0.1
        msg.twist.linear.y = 0.0
        msg.twist.angular.z = 0.0
        
        self.publisher_.publish(msg)
        
        self.counter += 1
        if self.counter >= 100:
            self.get_logger().info("Published 100 messages (2 seconds elapsed). Stopping node.")
            raise SystemExit

def main(args=None):
    rclpy.init(args=args)
    node = VelocityPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
