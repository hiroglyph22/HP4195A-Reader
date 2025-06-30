import pyvisa

# --- Configuration ---
# Explicitly point to the NI-VISA library on macOS.
# This is often represented by '@ni' for the NI backend.
visa_backend = '@ni'

# The standard GPIB address string.
# We will force the NI backend to interpret this.
gpib_address = 'GPIB0::11::INSTR'

# --- End of Configuration ---

print("Starting VISA connection test with explicit NI backend...")
print("-" * 60)

try:
    # Initialize the resource manager, forcing it to use the NI backend
    rm = pyvisa.ResourceManager(visa_backend)
    print(f"Successfully initialized NI-VISA backend.")
    print(f"Attempting to connect to: {gpib_address}")

    # Try to open the instrument
    instrument = rm.open_resource(gpib_address)
    instrument.timeout = 5000  # 5-second timeout

    # Ask for its identity
    identity = instrument.query('*IDN?')

    print("\n" + "="*20)
    print("  SUCCESS! Connection established.")
    print(f"  Instrument ID: {identity.strip()}")
    print("  The NI backend method worked!")
    print("="*20 + "\n")

    instrument.close()

except pyvisa.errors.VisaIOError as e:
    print(f"\n  FAILED: A VISA I/O Error occurred.")
    print(f"  Error Code: {e.error_code}")
    print(f"  Description: {e.description}")

except Exception as e:
    print(f"\nCRITICAL ERROR: An unexpected error occurred: {e}")
    print("This could be due to a problem with the NI-VISA installation itself.")

print("-" * 60)
print("Test complete.")