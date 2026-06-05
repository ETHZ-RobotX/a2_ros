/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/
#include "ros2_sport_client.hpp"

void SportClient::Damp(unitree_api::msg::Request &req) {
  req.header.identity.api_id = ROBOT_SPORT_API_ID_DAMP;
  req_puber_->publish(req);
}

void SportClient::BalanceStand(unitree_api::msg::Request &req) {
  req.header.identity.api_id = ROBOT_SPORT_API_ID_BALANCESTAND;
  req_puber_->publish(req);
}

void SportClient::StopMove(unitree_api::msg::Request &req) {
  req.header.identity.api_id = ROBOT_SPORT_API_ID_STOPMOVE;
  req_puber_->publish(req);
}

void SportClient::StandUp(unitree_api::msg::Request &req) {
  req.header.identity.api_id = ROBOT_SPORT_API_ID_STANDUP;
  req_puber_->publish(req);
}

void SportClient::StandDown(unitree_api::msg::Request &req) {
  req.header.identity.api_id = ROBOT_SPORT_API_ID_STANDDOWN;
  req_puber_->publish(req);
}

void SportClient::Move(unitree_api::msg::Request &req, float vx, float vy,
                       float vyaw) {
  nlohmann::json js;
  js["x"] = vx;
  js["y"] = vy;
  js["z"] = vyaw;
  req.parameter = js.dump();
  req.header.identity.api_id = ROBOT_SPORT_API_ID_MOVE;
  req_puber_->publish(req);
}
