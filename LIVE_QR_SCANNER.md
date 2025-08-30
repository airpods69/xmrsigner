# Live QR Scanner Implementation

This implementation follows the Cake Wallet approach for handling animated QR codes (UR format) with progress tracking.

## Features

1. **Fast QR Scanning**: Optimized for rapid scanning of animated QR codes
2. **Progress Tracking**: Shows real-time progress as QR frames are scanned
3. **Duplicate Detection**: Prevents scanning the same QR frame multiple times
4. **UR Format Support**: Properly handles Uniform Resource encoding for Monero transactions
5. **Cake Wallet Approach**: Implements the same scanning logic used by Cake Wallet

## How It Works

The implementation follows these steps:

1. **QR Scanning Loop**:
   - Continuously captures video frames from the camera
   - Processes each frame to find QR codes using fast scanning libraries
   - Extracts raw string data when a QR code is successfully decoded

2. **UR Format Identification**:
   - Checks if decoded string starts with the prefix `ur:`
   - Identifies as part of a Uniform Resource encoding

3. **UR Part Accumulation**:
   - Maintains a collection of unique UR QR codes scanned for the current transaction
   - Checks for duplicates before adding new scanned UR strings
   - UR format: `ur:BYTES_TAG/TOTAL_COUNT-INDEX/DATA_PAYLOAD`

4. **Progress Parsing**:
   - Parses accumulated UR strings to extract:
     - BYTES_TAG (e.g., xmr-txunsigned for Monero unsigned tx)
     - TOTAL_COUNT (integer) from any part
     - INDEX (integer) and DATA_PAYLOAD from each part
     - Sorts parts based on INDEX
   - Calculates progress = number_of_parts_scanned / TOTAL_COUNT

5. **Completion Detection**:
   - Checks if progress equals 1.0 or number_of_parts_scanned equals TOTAL_COUNT
   - Signifies all required QR frames have been scanned

6. **UR Assembly & Decoding**:
   - Passes sorted UR string parts to UR decoder library
   - Combines DATA_PAYLOAD parts according to UR specification
   - Performs CBOR decoding to retrieve original binary transaction data

7. **Transaction Data Handling**:
   - Checks decoded binary data against expected BYTES_TAG
   - For unsigned transactions, parses with Monero library
   - Extracts transaction details (addresses, amounts, fee)
   - Presents details to user for confirmation

## Files

- `src/xmrsigner/helpers/cake_wallet_qr_scanner.py`: Main implementation
- `src/xmrsigner/gui/screens/scan_screens.py`: Integration with scan screens
- `test_ur_parsing.py`: Simple test for UR parsing logic

## Usage

The scanner is automatically used in the scan screens. The key improvements over the previous implementation:

1. Faster scanning with 10fps camera capture
2. Better progress reporting with detailed status messages
3. Duplicate frame detection to avoid re-scanning
4. Cake Wallet-style UR parsing and handling

## UR Format Examples

```
ur:xmr-txunsigned/5-1/data
ur:xmr-txunsigned/5-2/data
ur:xmr-txunsigned/5-3/data
ur:xmr-txunsigned/5-4/data
ur:xmr-txunsigned/5-5/data
```

This represents a transaction split across 5 QR codes, with the scanner showing "Scanning... 3/5" when 3 parts have been captured.