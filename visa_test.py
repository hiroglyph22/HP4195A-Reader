import pyvisa
import sys

# --- Configuration ---
# The USB RAW address for your NI GPIB-USB-HS controller
# This is identified by its Vendor ID (0x3923) and Product ID (0x709B)
usb_raw_address = 'USB0::0x3923::0x709B::018340E2::RAW'

# --- End of Configuration ---

def test_py_backend_connection():
    """Attempts to connect using the pyvisa-py backend."""
    print("-" * 60)
    print("Attempting connection using the native @py backend...")
    print(f"Controller Address: {usb_raw_address}")
    print("-" * 60)
    
    controller = None
    try:
        # Explicitly specify the @py backend
        # This tells pyvisa to use the pure python implementation
        rm = pyvisa.ResourceManager('@py')
        
        # Open the USB RAW resource
        controller = rm.open_resource(usb_raw_address)
        controller.timeout = 20000  # Increased timeout to 20 seconds for first contact
        
        print("Successfully opened a handle to the USB controller with @py backend.")
        
        # --- Directly query the instrument ---
        # The pyvisa-py backend for USB RAW is simple.
        # It sends the command directly down the USB pipe. The NI controller
        # is designed to interpret text commands and route them to the GPIB bus.
        
        print("Sending command to instrument: *IDN?")
        # The query method writes the command and then reads the response.
        identity = controller.query('*IDN?')
        
        print("\n" + "="*20)
        print("  SUCCESS! Communication established.")
        print(f"  Instrument Response: {identity.strip()}")
        print("  The @py backend is working correctly!")
        print("="*20 + "\n")
        
    except pyvisa.errors.VisaIOError as e:
        print(f"\n  FAILED: A VISA I/O Error occurred.")
        print(f"  Error Code: {e.error_code}")
        print(f"  Description: {e.description}")
        print("\n  Troubleshooting steps:")
        print("  1. Make sure you have run 'pip install pyvisa-py pyusb'.")
        print("  2. Check that the HP4195A is on and the GPIB address is 11.")
        print("  3. On some macOS versions, you may need to grant your Terminal app")
        print("     full disk access or input monitoring permissions in System Settings.")

    except Exception as e:
        print(f"\nCRITICAL ERROR: An unexpected error occurred: {e}")
        
    finally:
        if controller:
            controller.close()
            print("Controller connection closed.")

# --- Run the test ---
if __name__ == "__main__":
    test_py_backend_connection()