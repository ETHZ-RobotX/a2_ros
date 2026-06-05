/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.

 Modified for Summer School with restricted capabilities.

 This is a ROS specific client library instead of the one from unitree_sdk2
 which uses the DDS API topics instead of directly managing a client.
***********************************************************************/
#ifndef ROS2_SPORT_CLIENT_H_
#define ROS2_SPORT_CLIENT_H_
#include <rclcpp/rclcpp.hpp>

#include "nlohmann/json.hpp"
#include "unitree_api/msg/request.hpp"
#include "unitree_api/msg/response.hpp"

const int32_t ROBOT_SPORT_API_ID_DAMP = 1001;
const int32_t ROBOT_SPORT_API_ID_BALANCESTAND = 1002;
const int32_t ROBOT_SPORT_API_ID_STOPMOVE = 1003;
const int32_t ROBOT_SPORT_API_ID_STANDUP = 1004;
const int32_t ROBOT_SPORT_API_ID_STANDDOWN = 1005;
const int32_t ROBOT_SPORT_API_ID_RECOVERYSTAND = 1006;
const int32_t ROBOT_SPORT_API_ID_MOVE = 1008;
const int32_t ROBOT_SPORT_API_ID_SPEEDLEVEL = 1015;
// const int32_t ROBOT_SPORT_API_ID_HELLO = 1016;
// const int32_t ROBOT_SPORT_API_ID_SWITCHJOYSTICK = 1027;

class SportClient {
  rclcpp::Publisher<unitree_api::msg::Request>::SharedPtr req_puber_;
  rclcpp::Subscription<unitree_api::msg::Response>::SharedPtr req_suber_;
  rclcpp::Node *node_;

 public:
  explicit SportClient(rclcpp::Node *node) : node_(node) {
    req_puber_ = node_->create_publisher<unitree_api::msg::Request>(
        "/api/sport/request", 10);
  }

  template <typename Request, typename Response>
  nlohmann::json Call(const Request &req) {
    std::promise<typename Response::SharedPtr> response_promise;
    auto response_future = response_promise.get_future();
    auto api_id = req.header.identity.api_id;
    auto req_suber_ = node_->create_subscription<Response>(
        "/api/sport/response", 1,
        [&response_promise, api_id](const typename Response::SharedPtr data) {
          if (data->header.identity.api_id == api_id) {
            response_promise.set_value(data);
          }
        });

    req_puber_->publish(req);

    auto response = *response_future.get();
    nlohmann::json js = nlohmann::json::parse(response.data.data());
    req_suber_.reset();
    return js;
  }

  /*
   * @brief Damp
   * @api: 1001
   */
  void Damp(unitree_api::msg::Request &req);

  /*
   * @brief BalanceStand
   * @api: 1002
   */
  void BalanceStand(unitree_api::msg::Request &req);

  /*
   * @brief StopMove
   * @api: 1003
   */
  void StopMove(unitree_api::msg::Request &req);

  /*
   * @brief StandUp
   * @api: 1004
   */
  void StandUp(unitree_api::msg::Request &req);

  /*
   * @brief StandDown
   * @api: 1005
   */
  void StandDown(unitree_api::msg::Request &req);

  /*
   * @brief Move
   * @api: 1008
   */
  void Move(unitree_api::msg::Request &req, float vx, float vy, float vyaw);

  /* These are commented out but may potentially be worth incorporating */

  // /*
  //  * @brief SpeedLevel
  //  * @api: 1015
  //  */
  // void SpeedLevel(unitree_api::msg::Request &req, int level);
  //
  // /*
  //  * @brief SwitchJoystick
  //  * @api: 1027
  //  */
  // void SwitchJoystick(unitree_api::msg::Request &req, bool flag);

};

#endif /* ROS2_SPORT_CLIENT_H_ */
