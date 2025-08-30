import re
import time
from collections import OrderedDict
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image

from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.qr_type import QRType
from xmrsigner.hardware.camera import Camera
from xmrsigner.models.threads import BaseThread
from xmrsigner.models.base_decoder import DecodeQRStatus

class LiveQRScanner:
    """
    Implements a live QR scanner that can handle animated QR codes (UR format) with progress tracking,
    similar to how Cake Wallet handles fast QR changes.
    """
    
    def __init__(self, wordlist_language_code: str = "english"):
        self.wordlist_language_code = wordlist_language_code
        self.decoder = DecodeQR(wordlist_language_code=wordlist_language_code)
        self.ur_parts = OrderedDict()  # Store unique UR parts by their index
        self.total_parts = None
        self.bytes_tag = None
        self.progress = 0.0
        self.is_complete = False
        self.last_scan_time = 0
        self.scan_cooldown = 0.1  # Minimum time between scans (100ms)
        self.last_ur_data = None
        
    def scan_frame(self, frame: Image) -> Tuple[bool, float, str]:
        """
        Scan a single frame for QR codes.
        
        Returns:
            Tuple[bool, float, str]: (is_complete, progress, status_message)
        """
        current_time = time.time()
        if current_time - self.last_scan_time < self.scan_cooldown:
            return self.is_complete, self.progress, "Scanning too fast"
        
        self.last_scan_time = current_time
        
        # Try to decode QR from frame
        status = self.decoder.add_image(frame)
        
        if status == DecodeQRStatus.INVALID:
            return self.is_complete, self.progress, "Invalid QR code"
            
        if status == DecodeQRStatus.FALSE:
            return self.is_complete, self.progress, "No QR code detected"
            
        # Check if we have a complete non-UR QR code
        if self.decoder.is_complete and not self.decoder.is_ur:
            self.is_complete = True
            self.progress = 1.0
            return self.is_complete, self.progress, "Complete"
            
        # Handle UR format QR codes
        if self.decoder.is_ur:
            return self._handle_ur_qr()
            
        return self.is_complete, self.progress, "Processing..."
    
    def _handle_ur_qr(self) -> Tuple[bool, float, str]:
        """
        Handle UR format QR codes with progress tracking.
        
        Returns:
            Tuple[bool, float, str]: (is_complete, progress, status_message)
        """
        # For UR formats, we need to parse the raw UR string to track progress
        # This requires accessing the underlying UR decoder in the DecodeQR object
        
        try:
            # Check if we have a UR decoder
            if hasattr(self.decoder, 'decoder') and self.decoder.decoder:
                # Try to get progress information from the UR decoder
                if hasattr(self.decoder.decoder, 'estimated_percent_complete'):
                    self.progress = self.decoder.decoder.estimated_percent_complete()
                    
                    # Try to get total parts information
                    if hasattr(self.decoder.decoder, 'expected_part_count'):
                        self.total_parts = self.decoder.decoder.expected_part_count
                    
                    # Check if complete
                    if hasattr(self.decoder.decoder, 'is_complete'):
                        self.is_complete = self.decoder.decoder.is_complete()
                        
                        if self.is_complete:
                            return self.is_complete, self.progress, f"Complete"
                        elif self.total_parts:
                            scanned = int(self.progress * self.total_parts)
                            return self.is_complete, self.progress, f"Scanning... {scanned}/{self.total_parts}"
                        else:
                            return self.is_complete, self.progress, f"Scanning... {int(self.progress * 100)}%"
                
            # Fallback: use the decoder's built-in progress method
            percent_complete = self.decoder.get_percent_complete()
            self.progress = percent_complete / 100.0
            
            if self.decoder.is_complete:
                self.is_complete = True
                return self.is_complete, self.progress, "Complete"
            else:
                return self.is_complete, self.progress, f"Scanning... {percent_complete}%"
                
        except Exception as e:
            return self.is_complete, self.progress, f"Error: {str(e)}"
    
    def reset(self):
        """Reset the scanner state."""
        self.decoder = DecodeQR(wordlist_language_code=self.wordlist_language_code)
        self.ur_parts.clear()
        self.total_parts = None
        self.bytes_tag = None
        self.progress = 0.0
        self.is_complete = False
        self.last_scan_time = 0
        self.last_ur_data = None
    
    def get_decoded_data(self):
        """
        Get the fully decoded data when scanning is complete.
        
        Returns:
            The decoded data or None if not complete
        """
        if not self.is_complete:
            return None
            
        # For UR formats, get the decoded data from the UR decoder
        if self.decoder.is_ur:
            if self.decoder.qr_type == QRType.XMR_TX_UNSIGNED_UR:
                return self.decoder.get_tx()
            elif self.decoder.qr_type == QRType.XMR_OUTPUT_UR:
                return self.decoder.get_output()
            # Add other UR types as needed
                
        # For other formats, return the direct decode result
        return self.decoder.get_qr_data()


class LiveQRScannerThread(BaseThread):
    """
    Thread for continuously scanning QR codes from camera frames.
    """
    
    def __init__(self, camera: Camera, scanner: LiveQRScanner, callback=None):
        self.camera = camera
        self.scanner = scanner
        self.callback = callback  # Callback function to report progress
        self.running = True
        super().__init__()
        
    def run(self):
        """Main scanning loop."""
        while self.running and self.keep_running:
            try:
                # Capture frame from camera
                frame = self.camera.read_video_stream(as_image=True)
                if frame is not None:
                    # Scan the frame
                    is_complete, progress, status = self.scanner.scan_frame(frame)
                    
                    # Report progress via callback if provided
                    if self.callback:
                        self.callback(is_complete, progress, status)
                        
                    # If complete, stop scanning
                    if is_complete:
                        self.running = False
                        
                # Small delay to prevent excessive CPU usage
                time.sleep(0.05)
                
            except Exception as e:
                if self.callback:
                    self.callback(False, 0.0, f"Error: {str(e)}")
                time.sleep(0.1)
                
    def stop(self):
        """Stop the scanning thread."""
        self.running = False
        super().stop()


# Example usage:
# scanner = LiveQRScanner()
# camera = Camera.get_instance()
# camera.start_video_stream_mode(resolution=(480, 480), framerate=5)
#
# def progress_callback(is_complete, progress, status):
#     print(f"Progress: {progress:.1%} - {status}")
#     if is_complete:
#         data = scanner.get_decoded_data()
#         print(f"Decoded data: {data}")
#
# scanner_thread = LiveQRScannerThread(camera, scanner, progress_callback)
# scanner_thread.start()
#
# # To stop scanning:
# # scanner_thread.stop()
# # camera.stop_video_stream_mode()