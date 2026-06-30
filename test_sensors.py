import sys
sys.path.insert(0, 'src')

from sensors import PositionSensor, CollisionSensor, SensorManager

print('='*60)
print('POSITION SENSOR TEST')
print('='*60)

# Test Position Sensor
pos_sensor = PositionSensor()
pos = pos_sensor.get_vehicle_position()
print('Vehicle position:', pos)

roi = pos_sensor.validate_roi()
print('ROI Validation:', roi['valid'])
print('Deviation:', roi['deviation'])

shift = pos_sensor.get_shift()
print('Shift from expected:', shift)

print('')
print('='*60)
print('COLLISION SENSOR TEST')
print('='*60)

# Test Collision Sensor
coll_sensor = CollisionSensor()
coll = coll_sensor.check_collision()
print('Collision detected:', coll['collision'])

print('')
print('='*60)
print('SENSOR MANAGER TEST')
print('='*60)

# Test Sensor Manager
manager = SensorManager()
all_data = manager.get_all_sensor_data()
print('All sensor data:')
print('  ROI valid:', all_data['roi_validation']['valid'])
print('  Collision:', all_data['collision']['collision'])
print('  Position:', all_data['roi_validation']['position'])
