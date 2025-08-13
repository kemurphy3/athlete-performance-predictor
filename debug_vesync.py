import os
import asyncio
from dotenv import load_dotenv

async def test_vesync_deep_debug():
    print('=== DEEP VESYNC DEBUG ===')
    
    try:
        from pyvesync import VeSync
        
        username = os.getenv('VESYNC_USERNAME')
        password = os.getenv('VESYNC_PASSWORD')
        timezone = 'America/Denver'
        
        print(f'Username: {username}')
        print(f'Timezone: {timezone}')
        
        # Create VeSync instance
        vesync = VeSync(username, password, timezone)
        print('✅ VeSync instance created')
        
        # Login
        login_result = vesync.login()
        print(f'Login result: {login_result}')
        
        # Check account details
        print('\n--- Account Details ---')
        print(f'Account ID: {vesync.account_id}')
        print(f'Country Code: {vesync.country_code}')
        print(f'Time Zone: {vesync.time_zone}')
        print(f'Token: {vesync.token[:20] if vesync.token else "None"}...')
        
        # Check if there are any devices in the account
        print('\n--- Device Discovery Debug ---')
        
        # Try to access the raw API response
        if hasattr(vesync, '_devices'):
            print(f'_devices attribute: {vesync._devices}')
        
        # Check if there's a device list attribute
        if hasattr(vesync, 'device_list'):
            print(f'device_list attribute: {vesync.device_list}')
        
        # Try to check the API response directly
        if hasattr(vesync, 'api'):
            print(f'API object: {vesync.api}')
            if hasattr(vesync.api, 'devices'):
                print(f'API devices: {vesync.api.devices}')
        
        # Check if there's a method to get device count
        if hasattr(vesync, 'device_count'):
            print(f'device_count: {vesync.device_count}')
        
        # Try to check if devices are being loaded but empty
        print('\n--- Checking Device Loading Process ---')
        
        # Check if there's a _load_devices method
        if hasattr(vesync, '_load_devices'):
            print('Found _load_devices method')
            try:
                load_result = vesync._load_devices()
                print(f'_load_devices result: {load_result}')
            except Exception as e:
                print(f'_load_devices error: {e}')
        
        # Check if there's a refresh_devices method
        if hasattr(vesync, 'refresh_devices'):
            print('Found refresh_devices method')
            try:
                refresh_result = vesync.refresh_devices()
                print(f'refresh_devices result: {refresh_result}')
            except Exception as e:
                print(f'refresh_devices error: {e}')
        
        # Check the devices again after trying to load
        print(f'\nDevices after loading attempts: {vesync.devices}')
        
        # Check specific device types again
        print('\n--- Device Types After Loading ---')
        device_types = ['scales', 'fans', 'bulbs', 'outlets', 'switches', 'kitchen']
        for device_type in device_types:
            if hasattr(vesync, device_type):
                devices = getattr(vesync, device_type)
                print(f'{device_type}: {len(devices) if devices else 0} devices')
        
    except Exception as e:
        print(f'❌ Main error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_vesync_deep_debug())