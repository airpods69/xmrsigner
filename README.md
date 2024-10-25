# 🔒 XmrSigner: Build Your Own Air-Gapped Monero Hardware Wallet

[![Status: Beta](https://img.shields.io/badge/Status-Beta-yellow.svg)](#%EF%B8%8F-current-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![Monero: Compatible](https://img.shields.io/badge/Monero-Compatible-orange.svg)](https://getmonero.org)

> Build your own secure, air-gapped Monero hardware wallet for less than a cup of coffee per day. Perfect for privacy-conscious individuals who want complete control over their digital assets.

## 🚀 Why XmrSigner?

XmrSigner empowers you to create a truly air-gapped Monero signing device using affordable, off-the-shelf hardware. Born from the battle-tested SeedSigner Bitcoin project, XmrSigner brings the same level of security and sovereignty to the Monero ecosystem.

### 🛡️ Key Security Features
- **Truly Air-Gapped**: No WiFi, no Bluetooth, no backdoors
- **Stateless Design**: No persistent storage of sensitive data
- **Open Source**: Every component is verifiable and transparent
- **DIY Approach**: You build it, you trust it

## ✨ Flagship Features

- 🎲 Create secure seeds using dice rolls or camera entropy
- 📷 Live preview for QR scanning and seed generation
- 🔐 Support for both 25-word Monero seeds and 16-word Polyseed phrases
- 🌐 Compatible with Mainnet, Stagenet & Testnet
- 🤝 Integration with Feather Wallet and official Monero GUI
- 💻 Companion desktop application for seamless transaction handling

## 🛠️ Hardware Shopping List

| Component | Specifications | Why This Matters |
|-----------|----------------|------------------|
| Raspberry Pi Zero | v1.3 (no WiFi/BT) | Maximum air-gap security |
| Waveshare LCD | 1.3" 240x240px | Perfect size-to-usability ratio |
| Camera Module | OV5647 Sensor | Reliable QR code scanning |

**Estimated Total Cost**: $40-50 USD

## 🏗️ Current Status

XmrSigner is currently in active development, with a strong focus on security and usability. Some exciting developments on the horizon:

- ✅ Core signing functionality
- ✅ QR code transaction parsing
- 🚧 Comprehensive documentation
- 🚧 Multisig support (planned)
- 🚧 Native C++ reimplementation

## 📸 The Device

![XmrSigner Enclosure](enclosures/XmrSigner_enclosure/XmrSigner_Thumb.jpeg)

*Community-designed enclosure by [@Go Brrr](https://github.com/gobrrrme) ([website](https://gobrrr.me) [X](https://twitter.com/Printer_Gobrrr))*

[The files to print the enclosure](enclosures/XmrSigner_enclosure)

## 🤝 Community & Support

- [Join the Discussion](https://github.com/XmrSigner/xmrsigner/discussions)
- [Report Issues](https://github.com/XmrSigner/xmrsigner/issues)
- [Contribute](CONTRIBUTING.md)

## ⚠️ Important Notes

- Device takes ~60 seconds to boot (patience is a virtue!)
- Always test with testnet before handling real funds
- This is beta software - use at your own risk

## 📚 Related Projects

- [XmrSigner OS](https://github.com/DiosDelRayo/monerosigner-os) - Custom operating system
- [XmrSigner Emulator](https://github.com/DiosDelRayo/monerosigner-emulator) - Development testing environment
- [XmrSigner Companion](https://github.com/DiosDelRayo/XmrSignerCompanion) - Desktop integration app

## 🙏 Acknowledgments

This project stands on the shoulders of giants:
- [SeedSigner](https://github.com/SeedSigner/seedsigner) - The original inspiration
- [Monero Project](https://github.com/monero-project/monero) - The privacy foundation
- Community contributors who make this project possible

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

---

Built with [![XMR](docs/img/xmr.png)] and ❤️ by the Monero community, for the Monero community
