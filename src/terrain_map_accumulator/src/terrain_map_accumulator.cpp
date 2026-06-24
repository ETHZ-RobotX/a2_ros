#include <memory>
#include <mutex>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>

#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl_conversions/pcl_conversions.h>

class TerrainMapAccumulator : public rclcpp::Node
{
public:
  TerrainMapAccumulator() : Node("terrain_map_accumulator")
  {
    // Parameters
    voxel_leaf_size_ = this->declare_parameter<double>("voxel_leaf_size", 0.2);
    publish_rate_hz_ = this->declare_parameter<double>("publish_rate_hz", 2.0);
    world_frame_id_  = this->declare_parameter<std::string>("world_frame_id", "map");

    global_cloud_ = std::make_shared<pcl::PointCloud<pcl::PointXYZI>>();

    sub_terrain_cloud_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        "/terrain_map", 2,
        std::bind(&TerrainMapAccumulator::terrainCloudHandler, this,
                  std::placeholders::_1));

    pub_global_map_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(
        "/terrain_map_global", 2);

    auto period =
        std::chrono::duration<double>(1.0 / std::max(publish_rate_hz_, 0.1));
    publish_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::nanoseconds>(period),
        std::bind(&TerrainMapAccumulator::publishGlobalMap, this));

    RCLCPP_INFO(this->get_logger(),
                "Terrain map accumulator started (leaf=%.2f m, rate=%.1f Hz)",
                voxel_leaf_size_, publish_rate_hz_);
  }

private:
  void terrainCloudHandler(
      const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg)
  {
    pcl::PointCloud<pcl::PointXYZI>::Ptr incoming(
        new pcl::PointCloud<pcl::PointXYZI>());
    pcl::fromROSMsg(*msg, *incoming);

    if (incoming->empty()) {
      return;
    }

    std::lock_guard<std::mutex> lock(cloud_mutex_);

    // Accumulate
    *global_cloud_ += *incoming;

    // Downsample the accumulated cloud to keep it bounded
    pcl::VoxelGrid<pcl::PointXYZI> voxel;
    voxel.setInputCloud(global_cloud_);
    voxel.setLeafSize(voxel_leaf_size_, voxel_leaf_size_, voxel_leaf_size_);

    pcl::PointCloud<pcl::PointXYZI>::Ptr filtered(
        new pcl::PointCloud<pcl::PointXYZI>());
    voxel.filter(*filtered);
    global_cloud_ = filtered;
  }

  void publishGlobalMap()
  {
    pcl::PointCloud<pcl::PointXYZI>::Ptr snapshot;
    {
      std::lock_guard<std::mutex> lock(cloud_mutex_);
      if (global_cloud_->empty()) {
        return;
      }
      snapshot = std::make_shared<pcl::PointCloud<pcl::PointXYZI>>(*global_cloud_);
    }

    sensor_msgs::msg::PointCloud2 out_msg;
    pcl::toROSMsg(*snapshot, out_msg);
    out_msg.header.stamp = this->now();
    out_msg.header.frame_id = world_frame_id_;
    pub_global_map_->publish(out_msg);
  }

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_terrain_cloud_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_global_map_;
  rclcpp::TimerBase::SharedPtr publish_timer_;

  pcl::PointCloud<pcl::PointXYZI>::Ptr global_cloud_;
  std::mutex cloud_mutex_;

  double voxel_leaf_size_;
  double publish_rate_hz_;
  std::string world_frame_id_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TerrainMapAccumulator>());
  rclcpp::shutdown();
  return 0;
}