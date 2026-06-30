'''
Position-Based Sensor Module
No camera required - uses robot/vehicle position data
'''

from robodk import robolink
import robodk as rdk

class PositionSensor:
    def __init__(self, robodk_instance=None):
        '''Initialize position sensor'''
        self.RL = robodk_instance if robodk_instance else robolink.Robolink()
        
        # Get vehicle object
        self.vehicle = self.RL.Item('Hyryder chasis_extra studs')
        if not self.vehicle.Valid():
            raise Exception("Vehicle 'Hyryder chasis_extra studs' not found")
        
        # Expected vehicle position (home position)
        self.expected_position = [-0.0, -1.386, -0.469]
        self.tolerance = 0.05  # 5cm tolerance
    
    def get_vehicle_position(self):
        '''Get current vehicle position'''
        return self.vehicle.Pose().Pos()
    
    def validate_roi(self):
        '''Check if vehicle is in correct ROI position'''
        pos = self.get_vehicle_position()
        
        # Check all axes within tolerance
        in_roi = True
        for i in range(3):
            if abs(pos[i] - self.expected_position[i]) > self.tolerance:
                in_roi = False
                break
        
        return {
            'valid': in_roi,
            'position': pos,
            'expected': self.expected_position,
            'deviation': [pos[i] - self.expected_position[i] for i in range(3)]
        }
    
    def get_shift(self):
        '''Get shift from expected position'''
        pos = self.get_vehicle_position()
        return {
            'dx': pos[0] - self.expected_position[0],
            'dy': pos[1] - self.expected_position[1],
            'dz': pos[2] - self.expected_position[2]
        }

class CollisionSensor:
    def __init__(self, robodk_instance=None):
        '''Initialize collision sensor'''
        self.RL = robodk_instance if robodk_instance else robolink.Robolink()
        
        # Get robot
        self.robot = self.RL.Item('Doosan Robotics M1013 White')
        if not self.robot.Valid():
            raise Exception("Robot not found")
        
        # Get vehicle for collision checking
        self.vehicle = self.RL.Item('Hyryder chasis_extra studs')
    
    def check_collision(self):
        '''Check if robot is in collision'''
        try:
            # Check collision with vehicle
            coll = self.robot.Collision(self.vehicle)
            return {
                'collision': bool(coll),
                'value': coll
            }
        except:
            return {
                'collision': False,
                'value': 0
            }

class SensorManager:
    def __init__(self):
        '''Initialize all sensors'''
        self.RL = robolink.Robolink()
        self.position = PositionSensor(self.RL)
        self.collision = CollisionSensor(self.RL)
    
    def get_all_sensor_data(self):
        '''Get all sensor readings'''
        roi_data = self.position.validate_roi()
        collision_data = self.collision.check_collision()
        
        return {
            'roi_validation': roi_data,
            'collision': collision_data
        }
