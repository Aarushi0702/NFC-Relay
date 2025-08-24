import board
import busio
import time
import random
import datetime
import RPi.GPIO as GPIO
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

# === SPI Setup ===
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pin = DigitalInOut(board.D8)  # Chip Select pin (modify as per your wiring)
pn532 = PN532_SPI(spi, cs_pin, debug=False)
pn532.SAM_configuration()

# === GPIO Setup (Optional LED for response indication) ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)  # LED on GPIO 18

print("\n=== PN532 EMV Dummy Transaction Simulator ===")
print("[*] Waiting for NFC target (emulated card)...")

uid = None
while uid is None:
    uid = pn532.read_passive_target(timeout=0.5)

print(f"[+] Target Detected! UID: {uid.hex().upper()}")

# === Generate dynamic CDOL1 dummy input for GENERATE AC ===
amount = "000000010000"              # 9F02: 1.00 in BCD (6 bytes)
other_amount = "000000000000"       # 9F03: Cashback amount (zero)
country_code = "0356"               # 9F1A: Country code for India
tvr = "0000000000"                  # 95: Terminal Verification Results
currency_code = "0356"              # 5F2A: Transaction currency code
txn_date = datetime.datetime.now().strftime('%y%m%d')  # 9A: Transaction date YYMMDD
txn_type = "00"                     # 9C: Purchase
unpredictable_number = random.getrandbits(32).to_bytes(4, 'big').hex().upper()  # 9F37

# Construct CDOL1 sequence (simplified dummy structure)
cdol1_data = (
    amount +
    other_amount +
    country_code +
    tvr +
    currency_code +
    txn_date +
    txn_type +
    unpredictable_number
)
cdol1_length = f"{int(len(cdol1_data) // 2):02X}"
ac_apdu = "80AE8000" + cdol1_length + cdol1_data + "00"  # Le = 00

# === APDU Command Sequence ===
apdu_sequence = [
    ("SELECT PPSE", "00A404000E325041592E5359532E4444463031"),
    ("SELECT AID (Visa)", "00A4040007A0000000031010"),
    ("GET PROCESSING OPTIONS", "80A8000002830000"),
    ("READ RECORD 1", "00B2010C00"),
    ("READ RECORD 2", "00B2020C00"),
    ("GET ATC", "80CA9F3600"),
    ("GET PIN TRY COUNTER", "80CA9F1700"),
    ("GENERATE AC (ARQC)", ac_apdu)
]

# === Main Loop: Send APDUs ===
for step_name, apdu_str in apdu_sequence:
    apdu = bytes.fromhex(apdu_str)
    print(f"\n[*] Step: {step_name}")
    print(f"[*] Sending APDU: {apdu.hex().upper()}")

    response = None
    while response is None:
        try:
            response = pn532.call_function(
                0x40,  # InDataExchange
                params=[0x01] + list(apdu),  # Target 1 (card)
                response_length=255,
                timeout=2
            )

            if response:
                response_hex = bytes(response).hex().upper()
                print(f"[<] Response: {response_hex}")
                if response_hex.endswith("9000"):
                    print("[✓] Step Successful")
                else:
                    print("[!] Step returned unusual status")
                GPIO.output(18, GPIO.HIGH)
                time.sleep(0.3)
                GPIO.output(18, GPIO.LOW)
            else:
                print("[!] No response. Retrying...")
                time.sleep(1)

        except Exception as e:
            print(f"[!] Exception during APDU transmit: {e}")
            time.sleep(1)

print("\n=== Dummy EMV Transaction Complete ===")
