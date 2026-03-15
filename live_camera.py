from google import genai
from google.genai import types
from PIL import Image
import cv2
import threading
import queue
import numpy as np
import sounddevice as sd
from price_search import search_ebay_prices
from memory import save_item, get_session_report
import os
from dotenv import load_dotenv

GEMINI_KEY = os.getenv("GEMINI_KEY")
client = genai.Client(api_key=GEMINI_KEY)

# ── VOICE CONFIG ─────────────────────────────────────────
AUDIO_RATE    = 16000
OUT_RATE      = 24000
CHUNK         = 1024
MODEL_LIVE    = "gemini-2.5-flash-native-audio-preview-12-2025"
audio_queue   = queue.Queue()
voice_running = False

VOICE_PROMPT = """You are AuctionEye — flea market AI assistant.
You see the camera AND hear the user.
RULES:
- Only respond when the user speaks
- Keep replies under 20 words
- Give BUY / NEGOTIATE / PASS when asked about an item
- Mention price range if relevant
- Sound like a friend whispering, not a robot"""

# ── SPEAK (pyttsx3 for session report) ──────────────────
def speak(text):
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ── SPACE KEY FLOW (original — unchanged) ───────────────
def analyze_and_speak(frame):
    print("\n🔍 Analyzing item...")

    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    name_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[pil_image, """Look at this item carefully.
        If ELECTRONICS: brand + model (e.g. "OnePlus 9 Pro")
        If ANTIQUE/GENERAL: 2-4 word description (e.g. "vintage pyrex bowl")
        Reply with item name ONLY. No punctuation."""]
    )
    item_name = name_response.text.strip().lower().replace('"','').replace('.','').strip()
    print(f"📦 Identified: {item_name}")

    print("💲 Searching eBay...")
    avg_price, price_summary = search_ebay_prices(item_name)
    print(f"📊 {price_summary}")

    advice_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[pil_image, f"""You are AuctionEye at a flea market.
        Item: {item_name}
        eBay market value: {price_summary}
        Give buying advice in under 30 words.
        Say BUY, NEGOTIATE, or PASS. Be direct."""]
    )
    advice = advice_response.text.strip()

    if avg_price:
        offer = avg_price * 0.4
        final_message = f"{item_name}. {price_summary}. Offer ${offer:.0f}. {advice}"
    else:
        final_message = f"{item_name}. {advice}"

    print(f"\n💰 AuctionEye: {final_message}\n")
    print("-" * 40)
    speak(final_message)
    save_item(item_name, price_summary, avg_price, advice)
    print("✅ Ready — Press SPACE for next item")

# ── SHARED FRAME FOR VOICE MODE ──────────────────────────
latest_frame = None
frame_lock   = threading.Lock()

def get_frame_bytes():
    with frame_lock:
        if latest_frame is None:
            return None
        _, buf = cv2.imencode(".jpg", latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes()

# ── MIC CALLBACK ────────────────────────────────────────
def mic_callback(indata, frames, time_info, status):
    pcm = (indata[:, 0] * 32767).astype(np.int16).tobytes()
    audio_queue.put(pcm)

# ── VOICE SESSION ────────────────────────────────────────
import asyncio

async def voice_session():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=VOICE_PROMPT,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
            )
        ),
    )

    spk = sd.RawOutputStream(samplerate=OUT_RATE, channels=1,
                              dtype="int16", blocksize=CHUNK)
    spk.start()

    try:
        async with client.aio.live.connect(model=MODEL_LIVE, config=config) as session:
            print("🎤 Voice mode ON — speak freely!\n")

            async def receive_and_play():
                turn_saved = False
                async for response in session.receive():
                    if not voice_running:
                        return
                    sc = getattr(response, "server_content", None)
                    if sc and getattr(sc, "model_turn", None):
                        for part in sc.model_turn.parts:
                            if getattr(part, "inline_data", None):
                                if isinstance(part.inline_data.data, bytes):
                                    spk.write(part.inline_data.data)
                                    # Save once per turn when real audio arrives
                                    if not turn_saved:
                                        try:
                                            save_item(
                                                item_name="[voice] conversation",
                                                price_summary="voice agent analysis",
                                                avg_price=None,
                                                advice="Voice conversation turn"
                                            )
                                            turn_saved = True
                                        except Exception:
                                            pass
                    # Reset flag after each complete turn
                    if getattr(getattr(response, "server_content", None), "turn_complete", False):
                        turn_saved = False

            async def send_audio_and_camera():
                fc = 0
                while voice_running:
                    try:
                        while True:
                            pcm = audio_queue.get_nowait()
                            await session.send_realtime_input(
                                audio=types.Blob(mime_type="audio/pcm;rate=16000", data=pcm)
                            )
                    except queue.Empty:
                        pass
                    fc += 1
                    if fc % 60 == 0:
                        fb = get_frame_bytes()
                        if fb:
                            await session.send_realtime_input(
                                video=types.Blob(mime_type="image/jpeg", data=fb)
                            )
                    await asyncio.sleep(0.03)

            await asyncio.gather(send_audio_and_camera(), receive_and_play())

    except Exception as e:
        if voice_running:
            print(f"🔄 Voice reconnecting... ({e})")
            await asyncio.sleep(2)
            await voice_session()
    finally:
        spk.stop()
        spk.close()

def voice_thread_fn():
    asyncio.run(voice_session())

# ── MAIN CAMERA LOOP ─────────────────────────────────────
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

mic_stream = sd.InputStream(samplerate=AUDIO_RATE, channels=1,
                             dtype="float32", blocksize=CHUNK,
                             callback=mic_callback)

print("🎯 AuctionEye Ready!")
print("   SPACE = Analyze item (eBay prices + advice)")
print("   V     = Toggle voice chat ON/OFF")
print("   Q     = Quit + session report\n")

analyzing    = False
voice_thread = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    with frame_lock:
        latest_frame = frame.copy()

    if analyzing:
        status, color = "ANALYZING...", (0, 0, 255)
    elif voice_running:
        status, color = "VOICE ON — speak freely!  V=stop", (0, 200, 100)
    else:
        status, color = "SPACE=Analyze  V=Voice  Q=Quit", (0, 255, 0)

    cv2.putText(frame, status, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.imshow("AuctionEye", frame)

    key = cv2.waitKey(100) & 0xFF

    # SPACE → analyze (only when not in voice mode)
    if key == 32 and not analyzing and not voice_running:
        analyzing = True
        captured  = frame.copy()
        def run():
            global analyzing
            analyze_and_speak(captured)
            analyzing = False
        threading.Thread(target=run, daemon=True).start()

    # V → toggle voice mode
    elif key == ord('v') or key == ord('V'):
        if not voice_running:
            voice_running = True
            mic_stream.start()
            voice_thread = threading.Thread(target=voice_thread_fn, daemon=True)
            voice_thread.start()
        else:
            voice_running = False
            try:
                mic_stream.stop()
            except Exception:
                pass
            print("🔇 Voice OFF — back to SPACE key mode")

    # Q → quit + report
    elif key == ord('q') or key == ord('Q'):
        voice_running = False
        print("\n📊 Generating session report...")
        report = get_session_report()
        print(f"\n{report}\n")
        speak(report)
        break

cap.release()
cv2.destroyAllWindows()
try:
    mic_stream.close()
except Exception:
    pass