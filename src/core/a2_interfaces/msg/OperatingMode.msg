# Source of truth: a2_sport_controller/include/mod_fsm.hpp
uint8 ESTOP = 0                # Joints disabled (most emergency)
uint8 STAND_DOWN = 1           # Stand down, joints locked
uint8 STAND_UP = 2             # Stands up, joints locked
uint8 BALANCE_STAND = 3        # Stands up, joints unlocked
uint8 VELOCITY_MOVE = 4        # Move with velocity
uint8 FREE = 5                 # Stops the robot but does not disable anything
uint8 mode
