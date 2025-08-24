# NFC Relay Attack Demonstration

This repository demonstrates a **basic relay attack in NFC** using two ACR122U readers and a PN532 module with a Raspberry Pi acting as a pseudo Point-of-Sale (POS).

---

## 📜 Overview

The project showcases how NFC communications can be intercepted and relayed between a victim card and a pseudo-POS device to simulate real-world relay attack scenarios.  
This is purely for **educational and research purposes** in the field of cybersecurity.

---

## 🛠 Hardware & Setup

- **Two [ACR122U](https://www.acs.com.hk/en/products/3/acr122u-usb-nfc-reader/) NFC Readers**
- **PN532 NFC Module**
- **Raspberry Pi** (used for the pseudo POS)

Pseudo POS setup reference:  
- Check `CIRC.jpg` for the pseudo POS circuit diagram.

---

## ▶️ Demonstration

A working demo of the relay attack can be found here:

🔗 [Demo Video on Mega](https://mega.nz/file/2EAV0Jza#I_pvFABfu6XXkqdCK8zu5O-zgn9_tiNyZudNia8-bjI)

---

## 📂 Files in Repository

- `CIRC.jpg` → Pseudo POS circuit diagram
- `psuedopos_spi.py` - psuedo pos script
- `relay.py` - Relay script

---

## ⚠️ Disclaimer

This project is intended **strictly for academic research and educational purposes only**.  
Do not attempt to replicate this on real financial systems or without proper authorization.  
The author is **not responsible for any misuse** of this information.

---

## Recent article about  Relay attacks

These articles will help you to understand how Relay attacks are still feasible in todays modern times.
https://thehackernews.com/2025/08/new-android-malware-wave-hits-banking.html
https://www.threatfabric.com/blogs/phantomcard-new-nfc-driven-android-malware-emerging-in-brazil
https://www.webpronews.com/surge-in-android-malware-targets-banking-apps-with-nfc-fraud/
Note: more articles will be added later

## 📝 Feedback & Contact

I’d love to hear your feedback, suggestions, and reviews!  

📧 Email: [aarushitaneja777@gmail.com](mailto:aarushitaneja777@gmail.com)

---

## 📌 Future Improvements

Some possible upgrades:
- Automating relay scripts to reduce latency
- Supporting additional NFC hardware
- Extending to mobile device relay scenarios
- Improving visualization for teaching/demo purposes


