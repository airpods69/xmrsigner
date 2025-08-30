from time import sleep

from dataclasses import dataclass
from typing import Tuple
from PIL import Image, ImageDraw

from xmrsigner.gui import renderer
from xmrsigner.hardware.buttons import HardwareButtonsConstants
from xmrsigner.hardware.camera import Camera
from xmrsigner.models.decode_qr import DecodeQR, DecodeQRStatus
from xmrsigner.models.threads import BaseThread
from xmrsigner.helpers.cake_wallet_qr_scanner import LiveQRScanner

from xmrsigner.gui.screens.screen import BaseScreen, ButtonListScreen
from xmrsigner.gui.components import GUIConstants, Fonts, TextArea


@dataclass
class ScanScreen(BaseScreen):
    """
    Live preview has to balance three competing threads:
    * Camera capturing frames and making them available to read.
    * Decoder analyzing frames for QR codes.
    * Live preview display writing frames to the screen.

    All of this would ideally be rewritten as in C/C++/Rust with python bindings for
    vastly improved performance.

    Until then, we have to balance the resources the Pi Zero has to work with. Thus, we
    set a modest fps target for the camera: 5fps. At this pace, the decoder and the live
    display can more or less keep up with the flow of frames without much wasted effort
    in any of the threads.

    Note: performance tuning was targeted for the Pi Zero.

    The resolution (480x480) has not been tweaked in order to guarantee that our
    decoding abilities remain as-is. It's possible that more optimizations could be made
    here (e.g. higher res w/no performance impact? Lower res w/same decoding but faster
    performance? etc).

    Note: This is quite a lot of important tasks for a Screen to be managing; much of
    this should probably be refactored into the Controller.
    """
    decoder: DecodeQR = None
    instructions_text: str = None
    resolution: Tuple[int,int] = (480, 480)
    framerate: int = 10  # Increased framerate for better QR scanning experience
    render_rect: Tuple[int,int,int,int] = None

    def __post_init__(self):
        from xmrsigner.hardware.camera import Camera
        # Initialize the base class
        super().__post_init__()
        self.instructions_text = "< back  |  " + self.instructions_text
        self.camera = Camera.get_instance()
        self.camera.start_video_stream_mode(resolution=self.resolution, framerate=self.framerate, format="rgb")
        
        # Initialize the live QR scanner following Cake Wallet approach
        self.live_qr_scanner = LiveQRScanner()
        
        self.threads.append(ScanScreen.LivePreviewThread(
            camera=self.camera,
            decoder=self.decoder,
            live_qr_scanner=self.live_qr_scanner,
            renderer=self.renderer,
            instructions_text=self.instructions_text,
            render_rect=self.render_rect,
        ))


    class LivePreviewThread(BaseThread):

        def __init__(self, camera: Camera, decoder: DecodeQR, live_qr_scanner: LiveQRScanner, 
                     renderer: renderer.Renderer, instructions_text: str, render_rect: Tuple[int,int,int,int]):
            self.camera = camera
            self.decoder = decoder
            self.live_qr_scanner = live_qr_scanner
            self.renderer = renderer
            self.instructions_text = instructions_text
            if render_rect:
                self.render_rect = render_rect            
            else:
                self.render_rect = (0, 0, self.renderer.canvas_width, self.renderer.canvas_height)
            self.render_width = self.render_rect[2] - self.render_rect[0]
            self.render_height = self.render_rect[3] - self.render_rect[1]
            super().__init__()

        def run(self):
            from timeit import default_timer as timer
            instructions_font = Fonts.get_font(GUIConstants.BODY_FONT_NAME, GUIConstants.BUTTON_FONT_SIZE)
            print("DEBUG: LivePreviewThread started")
            frame_count = 0
            while self.keep_running:
                start = timer()
                frame = self.camera.read_video_stream(as_image=True)
                if frame is not None:
                    frame_count += 1
                    print(f"DEBUG: Frame {frame_count} captured - size: {frame.size}, mode: {frame.mode}")
                    
                    # Scan the frame with our Cake Wallet-style live QR scanner for progress tracking
                    is_complete, progress, status = self.live_qr_scanner.scan_frame(frame)
                    
                    # Occasionally save a frame for debugging
                    if frame_count % 30 == 0:  # Save every 30th frame
                        try:
                            frame.save(f"/tmp/debug_frame_{frame_count}.png")
                            print(f"DEBUG: Saved debug frame {frame_count} to /tmp/debug_frame_{frame_count}.png")
                        except Exception as e:
                            print(f"DEBUG: Failed to save debug frame: {e}")
                    
                    # Determine what text to display based on scanning progress
                    scan_text = self.instructions_text
                    if progress > 0 and progress < 1.0:
                        scan_text = status  # Use the detailed status message from our scanner
                        print(f"DEBUG: Scan progress: {scan_text}")
                    elif is_complete:
                        scan_text = "Complete!"
                    elif status and status != "Processing...":
                        scan_text = status
                    
                    with self.renderer.lock:
                        if frame.width > self.render_width or frame.height > self.render_height:
                            frame = frame.resize(
                                (self.render_width, self.render_height),
                                resample=Image.NEAREST  # Use nearest neighbor for max speed
                            )
                        draw = ImageDraw.Draw(frame)
                        if scan_text:
                            # Note: shadowed text (adding a 'stroke' outline) can
                            # significantly slow down the rendering.
                            # Temp solution: render a slight 1px shadow behind the text
                            draw.text(xy=(
                                        int(self.renderer.canvas_width / 2 + 2),
                                        self.renderer.canvas_height - GUIConstants.EDGE_PADDING + 2
                                     ),
                                     text=scan_text,
                                     fill=GUIConstants.BRIGHTNESS_TEXT_COLOR,
                                     font=instructions_font,
                                     anchor="ms")
                            # Render the onscreen instructions
                            draw.text(xy=(
                                        int(self.renderer.canvas_width/2),
                                        self.renderer.canvas_height - GUIConstants.EDGE_PADDING
                                     ),
                                     text=scan_text,
                                     fill=GUIConstants.BODY_FONT_COLOR,
                                     font=instructions_font,
                                     anchor="ms")
                        self.renderer.show_image(frame, show_direct=True)
                sleep(0.01) # Reduced sleep for faster QR scanning
                if self.camera._video_stream is None:
                    break


    def _run(self):
        """
        _render() is mostly meant to be a one-time initial drawing call to set up the
        Screen. Once interaction starts, the display updates have to be managed in
        _run(). The live preview is an extra-complex case.
        """
        print("DEBUG: Starting scan screen loop")
        while True:
            frame = self.camera.read_video_stream()
            if frame is not None:
                print("DEBUG: Frame captured, processing...")
                status = self.decoder.add_image(frame)
                print(f"DEBUG: Decoder status: {status}")
                if status in (DecodeQRStatus.COMPLETE, DecodeQRStatus.INVALID):
                    print(f"DEBUG: Scan completed with status: {status}")
                    self.camera.stop_video_stream_mode()
                    break
                if self.hw_inputs.check_for_low(HardwareButtonsConstants.KEY_RIGHT) or self.hw_inputs.check_for_low(HardwareButtonsConstants.KEY_LEFT):
                    print("DEBUG: User cancelled scan")
                    self.camera.stop_video_stream_mode()
                    break
