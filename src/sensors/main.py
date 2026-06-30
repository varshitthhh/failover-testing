'''
Sensor Module - Standalone Test & Demo
Run: python -m sensors.main
Purpose: Test sensor integration without running full inspection
'''

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robodk.robolink import Robolink
from sensors import SensorManager, PositionSensor, CollisionSensor


class SensorDemo:
    def __init__(self):
        print('='*60)
        print('  SENSOR MODULE - Standalone Demo')
        print('='*60)
        
        # Connect to RoboDK
        self.RDK = Robolink()
        if not self.RDK.Connect():
            print('[ERROR] Cannot connect to RoboDK')
            sys.exit(1)
        
        print('[OK] Connected to RoboDK')
        print('  Version:', self.RDK.Version())
        
        # Initialize sensor manager
        self.sensor_mgr = SensorManager()
        print('[OK] Sensor Manager initialized')
    
    def test_position_sensor(self):
        print('\n' + '-'*60)
        print('  POSITION SENSOR TEST')
        print('-'*60)
        
        pos_sensor = self.sensor_mgr.position
        
        # Get current position
        pos = pos_sensor.get_vehicle_position()
        print(f'Vehicle position:')
        print(f'  X: {pos[0]:.4f} mm')
        print(f'  Y: {pos[1]:.4f} mm')
        print(f'  Z: {pos[2]:.4f} mm')
        
        # Validate ROI
        roi = pos_sensor.validate_roi()
        print(f'\nROI Validation: {roi["valid"]}')
        if roi["valid"]:
            print('  [OK] Vehicle is in correct position')
        else:
            print('  [WARN] Vehicle is outside ROI!')
            print(f'  Deviation: X={roi["deviation"][0]:.4f}, Y={roi["deviation"][1]:.4f}, Z={roi["deviation"][2]:.4f}')
        
        # Get shift
        shift = pos_sensor.get_shift()
        print(f'\nShift from expected:')
        print(f'  dx: {shift["dx"]:.4f} mm')
        print(f'  dy: {shift["dy"]:.4f} mm')
        print(f'  dz: {shift["dz"]:.4f} mm')
        
        return roi["valid"]
    
    def test_collision_sensor(self):
        print('\n' + '-'*60)
        print('  COLLISION SENSOR TEST')
        print('-'*60)
        
        coll_sensor = self.sensor_mgr.collision
        
        # Check collision
        coll = coll_sensor.check_collision()
        print(f'Collision detected: {coll["collision"]}')
        if coll["collision"]:
            print('  [WARN] Collision detected!')
            print(f'  Value: {coll["value"]}')
        else:
            print('  [OK] No collision')
        
        return coll["collision"]
    
    def test_sensor_manager(self):
        print('\n' + '-'*60)
        print('  SENSOR MANAGER - All Data')
        print('-'*60)
        
        # Get all sensor data
        data = self.sensor_mgr.get_all_sensor_data()
        
        # ROI data
        roi = data['roi_validation']
        print(f'ROI Valid: {roi["valid"]}')
        print(f'Position: X={roi["position"][0]:.4f}, Y={roi["position"][1]:.4f}, Z={roi["position"][2]:.4f}')
        print(f'Deviation: X={roi["deviation"][0]:.4f}, Y={roi["deviation"][1]:.4f}, Z={roi["deviation"][2]:.4f}')
        
        # Collision data
        coll = data['collision']
        print(f'Collision: {coll["collision"]}')
        
        return data
    
    def monitor_continuous(self, duration=10):
        print('\n' + '-'*60)
        print(f'  CONTINUOUS MONITORING ({duration}s)')
        print('-'*60)
        print('  Press Ctrl+C to stop early')
        
        start_time = time.time()
        count = 0
        
        try:
            while time.time() - start_time < duration:
                count += 1
                roi = self.sensor_mgr.position.validate_roi()
                coll = self.sensor_mgr.collision.check_collision()
                
                status = '[OK]' if roi['valid'] else '[WARN]'
                print(f'  [{count:3d}] ROI: {status}  Collision: {coll["collision"]}  Pos: ({roi["position"][0]:.2f}, {roi["position"][1]:.2f}, {roi["position"][2]:.2f})')
                
                time.sleep(1.0)
        except KeyboardInterrupt:
            print('\n  [STOP] Monitoring stopped by user')
        
        print(f'  Total samples: {count}')
    
    def run_all_tests(self):
        print('\n' + '='*60)
        print('  RUNNING ALL TESTS')
        print('='*60)
        
        results = {}
        
        # Test 1: Position
        results['position'] = self.test_position_sensor()
        
        # Test 2: Collision
        results['collision'] = self.test_collision_sensor()
        
        # Test 3: All data
        self.test_sensor_manager()
        
        # Summary
        print('\n' + '='*60)
        print('  TEST SUMMARY')
        print('='*60)
        print(f'Position Sensor: {"[OK]" if results["position"] else "[FAIL]"}')
        print(f'Collision Sensor: {"[OK]" if not results["collision"] else "[WARN]"}')
        
        if results['position'] and not results['collision']:
            print('\n[RESULT] All sensors operational - System ready')
        else:
            print('\n[RESULT] Some sensors need attention')
        
        return results
    
    def run_interactive(self):
        print('\n' + '='*60)
        print('  INTERACTIVE MODE')
        print('='*60)
        
        while True:
            print('\nOptions:')
            print('  1. Test Position Sensor')
            print('  2. Test Collision Sensor')
            print('  3. Test All Sensors')
            print('  4. Monitor (10s)')
            print('  5. Exit')
            
            choice = input('\nEnter choice (1-5): ').strip()
            
            if choice == '1':
                self.test_position_sensor()
            elif choice == '2':
                self.test_collision_sensor()
            elif choice == '3':
                self.test_sensor_manager()
            elif choice == '4':
                self.monitor_continuous(10)
            elif choice == '5':
                print('Exiting...')
                break
            else:
                print('Invalid choice')


def main():
    demo = SensorDemo()
    
    # Check if running with argument
    if len(sys.argv) > 1:
        if sys.argv[1] == '--monitor':
            demo.monitor_continuous(30)
        elif sys.argv[1] == '--interactive':
            demo.run_interactive()
        elif sys.argv[1] == '--quick':
            demo.run_all_tests()
        else:
            print('Usage: python -m sensors.main [--quick | --monitor | --interactive]')
    else:
        # Default: run all tests
        demo.run_all_tests()


if __name__ == '__main__':
    main()
