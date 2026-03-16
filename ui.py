import os
from dotenv import load_dotenv
load_dotenv()  # ← MUST be called before os.getenv — loads .env file into environment

import tkinter as tk
import cv2
from PIL import Image, ImageTk
import threading
import queue
import numpy as np
import asyncio
from google import genai
from google.genai import types
from price_search import search_ebay_prices
from memory import save_item, get_session_report
import pyttsx3

# ── CONFIG ──────────────────────────────────────────────
# Supports both GEMINI_KEY and GEMINI_API_KEY in .env
GEMINI_KEY = os.getenv("GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("❌ GEMINI_KEY not found. Check your .env file has: GEMINI_KEY=your_key")
client = genai.Client(api_key=GEMINI_KEY)

# ── COLORS ──────────────────────────────────────────────
BG, BG2, BG3 = "#0A0A0A", "#111111", "#1A1A1A"
GOLD, GOLD2  = "#C9A84C", "#E8C97A"
WHITE        = "#F0EDE8"
GRAY, GRAY2  = "#444444", "#2A2A2A"
GREEN        = "#4CAF82"
RED          = "#C94C4C"
ORANGE       = "#C97A4C"
TEAL         = "#4CA8AF"

# ── VOICE LIVE API CONFIG ────────────────────────────────
MODEL_LIVE    = "gemini-2.5-flash-native-audio-preview-12-2025"
AUDIO_RATE    = 16000
OUT_RATE      = 24000
CHUNK         = 1024
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

# ── SHARED FRAME ────────────────────────────────────────
latest_frame = None
frame_lock   = threading.Lock()

def get_frame_bytes():
    with frame_lock:
        if latest_frame is None:
            return None
        _, buf = cv2.imencode(".jpg", latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes()

# ── SPEAK (pyttsx3 for session report) ──────────────────
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ── GEMINI ANALYSIS ─────────────────────────────────────
def analyze_frame(frame):
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    name_resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[pil_image, """Look at this item carefully.
        If ELECTRONICS: brand + model (e.g. "OnePlus 9 Pro")
        If ANTIQUE/GENERAL: 2-4 word description (e.g. "vintage pyrex bowl")
        Reply with item name ONLY. No punctuation."""]
    )
    item_name = name_resp.text.strip().lower().replace('"','').replace('.','').strip()
    print(f"🤖 [Gemini 2.5 Flash] Identified: {item_name}")
    avg_price, price_summary = search_ebay_prices(item_name)
    advice_resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[pil_image, f"""You are AuctionEye at a flea market.
    Item: {item_name}
    eBay market value: {price_summary}
    IMPORTANT RULES:
    - If item is common/disposable (pen, basic cup, plastic toy): Say PASS
    - If item is vintage/antique/branded/electronic: Say BUY if good deal, NEGOTIATE if fair
    Give advice in under 30 words. Start with BUY, NEGOTIATE, or PASS."""]
    )
    advice = advice_resp.text.strip()
    offer  = avg_price * 0.4 if avg_price else None
    print(f"📊 [SerpApi → eBay] {price_summary}")
    print(f"🧠 [Gemini Strategy] {advice[:60]}")
    return item_name, price_summary, avg_price, offer, advice

# ── MIC CALLBACK ────────────────────────────────────────
try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False
    print("⚠️  sounddevice not installed. Run: pip install sounddevice")

def mic_callback(indata, frames, time_info, status):
    pcm = (indata[:, 0] * 32767).astype(np.int16).tobytes()
    audio_queue.put(pcm)

# ── VOICE SESSION (async) ────────────────────────────────
async def voice_session(on_status):
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
            print("━" * 50)
            print("🟢 GEMINI LIVE API — Connected")
            print(f"   Model  : {MODEL_LIVE}")
            print(f"   Mode   : Bidirectional voice + vision")
            print("━" * 50)
            on_status("voice_on")

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
                                    print(f"🔊 [Gemini Live API] Audio response: {len(part.inline_data.data)} bytes")
                                    spk.write(part.inline_data.data)
                                    if not turn_saved:
                                        try:
                                            save_item(
                                                item_name="[voice] conversation",
                                                price_summary="voice agent analysis",
                                                avg_price=None,
                                                advice="Voice conversation turn"
                                            )
                                            print("☁️  [Google Cloud Firestore] Saved: voice conversation")
                                            turn_saved = True
                                        except Exception:
                                            pass
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
            on_status("voice_error")
            await asyncio.sleep(2)
            await voice_session(on_status)
    finally:
        spk.stop()
        spk.close()

def voice_thread_fn(on_status):
    asyncio.run(voice_session(on_status))


# ════════════════════════════════════════════════════════
class AuctionEyeApp:
    def __init__(self, root):
        self.root          = root
        self.root.title("AuctionEye")
        self.root.configure(bg=BG)
        self.root.geometry("1200x780")
        self.root.resizable(False, False)

        self.analyzing     = False
        self.session_items = []
        self.total_savings = 0.0
        self.voice_count   = 0
        self.cap           = None
        self.voice_thread  = None
        self.current_frame = None

        if HAS_SD:
            self.mic_stream = sd.InputStream(
                samplerate=AUDIO_RATE, channels=1, dtype="float32",
                blocksize=CHUNK, callback=mic_callback
            )
        else:
            self.mic_stream = None

        self._build_ui()
        self._start_camera()

        self.root.bind("<space>", lambda e: self._trigger_analyze())
        self.root.bind("<v>",     lambda e: self._toggle_voice())
        self.root.bind("<V>",     lambda e: self._toggle_voice())
        self.root.bind("<q>",     lambda e: self._quit())
        self.root.bind("<Q>",     lambda e: self._quit())

    # ────────────────────────────────────────────────────
    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG, height=64)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text="AUCTION", bg=BG, fg=GOLD,
                 font=("Georgia",22,"bold")).pack(side="left", padx=(28,0), pady=14)
        tk.Label(header, text="EYE", bg=BG, fg=WHITE,
                 font=("Georgia",22,"bold")).pack(side="left", pady=14)
        tk.Label(header, text="  ◆  AI Flea Market Agent", bg=BG, fg=GRAY,
                 font=("Georgia",11)).pack(side="left", pady=18)
        tk.Label(header, text="SPACE = Analyze    V = Voice    Q = Report & Quit",
                 bg=BG, fg=GRAY, font=("Courier",10)).pack(side="right", padx=28, pady=20)

        tk.Frame(self.root, bg=GOLD, height=1).pack(fill="x")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="LIVE FEED", bg=BG, fg=GOLD,
                 font=("Courier",9,"bold")).pack(anchor="w", pady=(0,6))
        self.cam_frame = tk.Frame(left, bg=GRAY2)
        self.cam_frame.pack()
        self.cam_label = tk.Label(self.cam_frame, bg=GRAY2)
        self.cam_label.pack()

        self.status_var = tk.StringVar(value="● READY  —  SPACE=Analyze  V=Voice  Q=Quit")
        self.status_label = tk.Label(left, textvariable=self.status_var,
                                      bg=BG, fg=GREEN, font=("Courier",10), anchor="w")
        self.status_label.pack(fill="x", pady=(8,0))

        self.voice_bar = tk.Frame(left, bg=TEAL, height=3)

        tk.Frame(body, bg=BG, width=20).pack(side="left")

        right = tk.Frame(body, bg=BG, width=420)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="LAST ITEM", bg=BG, fg=GOLD,
                 font=("Courier",9,"bold")).pack(anchor="w")
        self.card = tk.Frame(right, bg=BG3)
        self.card.pack(fill="x", pady=(6,0))
        tk.Frame(self.card, bg=GOLD, height=2).pack(fill="x")
        ci = tk.Frame(self.card, bg=BG3); ci.pack(fill="x", padx=16, pady=14)

        self.item_var = tk.StringVar(value="—")
        tk.Label(ci, textvariable=self.item_var, bg=BG3, fg=WHITE,
                 font=("Georgia",15,"bold"), wraplength=330, justify="left").pack(anchor="w")
        tk.Frame(ci, bg=GRAY2, height=1).pack(fill="x", pady=10)

        tk.Label(ci, text="eBay Range", bg=BG3, fg=GRAY, font=("Courier",8)).pack(anchor="w")
        self.price_var = tk.StringVar(value="—")
        tk.Label(ci, textvariable=self.price_var, bg=BG3, fg=GOLD2,
                 font=("Georgia",11,"bold"), wraplength=330, justify="left").pack(anchor="w")
        tk.Frame(ci, bg=BG3, height=6).pack()

        tk.Label(ci, text="Offer Price", bg=BG3, fg=GRAY, font=("Courier",8)).pack(anchor="w")
        self.offer_var = tk.StringVar(value="—")
        tk.Label(ci, textvariable=self.offer_var, bg=BG3, fg=GREEN,
                 font=("Georgia",18,"bold")).pack(anchor="w")
        tk.Frame(ci, bg=GRAY2, height=1).pack(fill="x", pady=10)

        self.verdict_var = tk.StringVar(value="WAITING")
        self.verdict_label = tk.Label(ci, textvariable=self.verdict_var,
                                       bg=GRAY2, fg=WHITE,
                                       font=("Courier",12,"bold"), padx=14, pady=6)
        self.verdict_label.pack(anchor="w")
        tk.Frame(ci, bg=BG3, height=6).pack()

        self.advice_var = tk.StringVar(value="Press SPACE to scan an item.")
        tk.Label(ci, textvariable=self.advice_var, bg=BG3, fg=GRAY,
                 font=("Georgia",10,"italic"), wraplength=330, justify="left").pack(anchor="w")

        tk.Frame(right, bg=BG, height=8).pack()
        self.voice_card = tk.Frame(right, bg=BG3)
        tk.Frame(self.voice_card, bg=TEAL, height=2).pack(fill="x")
        vc = tk.Frame(self.voice_card, bg=BG3); vc.pack(fill="x", padx=16, pady=10)
        tk.Label(vc, text="🎤  VOICE ON — speak freely",
                 bg=BG3, fg=TEAL, font=("Courier",10,"bold")).pack(anchor="w")
        tk.Label(vc, text="Agent hears you and sees camera",
                 bg=BG3, fg=GRAY, font=("Courier",8)).pack(anchor="w")
        tk.Label(vc, text="Press V again to stop",
                 bg=BG3, fg=GRAY, font=("Courier",8)).pack(anchor="w")

        tk.Frame(right, bg=BG, height=10).pack()
        tk.Label(right, text="SESSION", bg=BG, fg=GOLD,
                 font=("Courier",9,"bold")).pack(anchor="w")
        sf = tk.Frame(right, bg=BG3); sf.pack(fill="x", pady=(6,0))
        tk.Frame(sf, bg=GOLD, height=2).pack(fill="x")
        si = tk.Frame(sf, bg=BG3); si.pack(fill="x", padx=16, pady=12)

        def stat_row(parent, label, var, color):
            r = tk.Frame(parent, bg=BG3); r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=BG3, fg=GRAY, font=("Courier",8)).pack(side="left")
            tk.Label(r, textvariable=var, bg=BG3, fg=color,
                     font=("Courier",12,"bold")).pack(side="right")

        self.count_var       = tk.StringVar(value="0")
        self.voice_count_var = tk.StringVar(value="0")
        self.savings_var     = tk.StringVar(value="$0")
        stat_row(si, "Items Scanned",       self.count_var,       WHITE)
        stat_row(si, "Voice Conversations", self.voice_count_var, TEAL)
        stat_row(si, "Potential Savings",   self.savings_var,     GREEN)

        tk.Frame(right, bg=BG, height=10).pack()
        tk.Label(right, text="HISTORY", bg=BG, fg=GOLD,
                 font=("Courier",9,"bold")).pack(anchor="w")
        ho = tk.Frame(right, bg=BG3); ho.pack(fill="both", expand=True, pady=(6,0))
        tk.Frame(ho, bg=GOLD, height=2).pack(fill="x")
        self.history_frame = tk.Frame(ho, bg=BG3)
        self.history_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.history_placeholder = tk.Label(
            self.history_frame, text="No items scanned yet.",
            bg=BG3, fg=GRAY, font=("Courier",9,"italic"))
        self.history_placeholder.pack(anchor="w", pady=4)

        tk.Frame(self.root, bg=GOLD, height=1).pack(fill="x")
        bb = tk.Frame(self.root, bg=BG2, height=64)
        bb.pack(fill="x"); bb.pack_propagate(False)

        self.analyze_btn = tk.Button(
            bb, text="⬤  ANALYZE ITEM",
            bg=GOLD, fg="#000000", font=("Courier",13,"bold"),
            relief="flat", bd=0, padx=36, pady=10,
            activebackground=GOLD2, cursor="hand2",
            command=self._trigger_analyze)
        self.analyze_btn.pack(side="left", padx=20, pady=10)

        self.voice_btn = tk.Button(
            bb, text="🎤  VOICE ON",
            bg=BG3, fg=TEAL, font=("Courier",11,"bold"),
            relief="flat", bd=0, padx=20, pady=10,
            activebackground=BG2, cursor="hand2",
            command=self._toggle_voice)
        self.voice_btn.pack(side="left", padx=8, pady=10)

        tk.Button(
            bb, text="SESSION REPORT  →",
            bg=BG2, fg=GRAY, font=("Courier",11),
            relief="flat", bd=0, padx=20, pady=10,
            activebackground=BG3, cursor="hand2",
            command=self._quit).pack(side="right", padx=20, pady=10)

    # ── CAMERA ──────────────────────────────────────────
    def _start_camera(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        self._update_camera()

    def _update_camera(self):
        global latest_frame
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                with frame_lock:
                    latest_frame = frame.copy()
                rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img   = Image.fromarray(rgb).resize((700, 520))
                imgtk = ImageTk.PhotoImage(image=img)
                self.cam_label.imgtk = imgtk
                self.cam_label.configure(image=imgtk)
        self.root.after(33, self._update_camera)

    # ── ANALYZE ─────────────────────────────────────────
    def _trigger_analyze(self):
        if self.analyzing or voice_running:
            return
        self.analyzing = True
        self.analyze_btn.configure(state="disabled", bg=GRAY)
        self.status_var.set("◌ ANALYZING...  Please wait")
        self.status_label.configure(fg=GOLD)
        captured = self.current_frame.copy()
        threading.Thread(target=self._run_analysis, args=(captured,), daemon=True).start()

    def _run_analysis(self, frame):
        try:
            item_name, price_summary, avg_price, offer, advice = analyze_frame(frame)
            self.root.after(0, self._update_ui, item_name, price_summary, avg_price, offer, advice)
            save_item(item_name, price_summary, avg_price, advice)
            print(f"☁️  [Google Cloud Firestore] Saved: {item_name}")
            speak(f"{item_name}. {price_summary}. Offer ${offer:.0f}. {advice}" if offer
                  else f"{item_name}. {advice}")
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            self.analyzing = False
            self.root.after(0, self._reset_btn)

    def _update_ui(self, item_name, price_summary, avg_price, offer, advice):
        self.item_var.set(item_name.title())
        self.price_var.set(price_summary or "—")
        self.offer_var.set(f"${offer:.0f}" if offer else "—")
        self.advice_var.set(advice)

        verdict, color = "BUY", GREEN
        if "NEGOTIATE" in advice.upper(): verdict, color = "NEGOTIATE", ORANGE
        elif "PASS"    in advice.upper(): verdict, color = "PASS",      RED

        self.verdict_var.set(f"  {verdict}  ")
        self.verdict_label.configure(bg=color, fg="#000000" if verdict == "BUY" else WHITE)

        self.session_items.append(item_name)
        if offer: self.total_savings += offer
        self.count_var.set(str(len(self.session_items)))
        self.savings_var.set(f"${self.total_savings:.0f}")

        self.history_placeholder.pack_forget()
        row = tk.Frame(self.history_frame, bg=BG3); row.pack(fill="x", pady=2)
        dot = GREEN if verdict == "BUY" else (ORANGE if verdict == "NEGOTIATE" else RED)
        tk.Label(row, text="◆", bg=BG3, fg=dot,
                 font=("Courier",8)).pack(side="left", padx=(0,6))
        tk.Label(row, text=item_name.title(), bg=BG3, fg=WHITE,
                 font=("Courier",9)).pack(side="left")
        if offer:
            tk.Label(row, text=f"${offer:.0f}", bg=BG3, fg=GOLD,
                     font=("Courier",9,"bold")).pack(side="right")

        self.status_var.set(f"● DONE  —  {item_name.title()} analyzed")
        self.status_label.configure(fg=GREEN)

    def _show_error(self, msg):
        self.status_var.set(f"✕ Error: {msg[:60]}")
        self.status_label.configure(fg=RED)

    def _reset_btn(self):
        self.analyze_btn.configure(state="normal", bg=GOLD)
        self.status_var.set("● READY  —  SPACE=Analyze  V=Voice  Q=Quit")
        self.status_label.configure(fg=GREEN)

    # ── VOICE TOGGLE ────────────────────────────────────
    def _toggle_voice(self):
        global voice_running
        if not HAS_SD:
            self.status_var.set("✕ Install sounddevice: pip install sounddevice")
            self.status_label.configure(fg=RED)
            return
        if not voice_running:
            voice_running = True
            self.mic_stream.start()
            self.voice_thread = threading.Thread(
                target=voice_thread_fn,
                args=(lambda s: self.root.after(0, self._voice_cb, s),),
                daemon=True
            )
            self.voice_thread.start()
            self._set_voice_ui(True)
        else:
            voice_running = False
            try:
                self.mic_stream.stop()
            except Exception:
                pass
            self._set_voice_ui(False)


    def _voice_cb(self, status):
        if status == "voice_error":
            self.status_var.set("🔄 Voice reconnecting... check terminal for error")
            self.status_label.configure(fg=RED)

    def _set_voice_ui(self, on: bool):
        if on:
            self.voice_card.pack(fill="x")
            self.voice_bar.pack(fill="x", pady=(4, 0))
            self.voice_btn.configure(text="🔇  STOP VOICE", bg=TEAL, fg="#000000")
            self.status_var.set("🎤 VOICE ON — speak freely!  V = stop")
            self.status_label.configure(fg=TEAL)
            self.analyze_btn.configure(state="disabled", bg=GRAY)
        else:
            self.voice_card.pack_forget()
            self.voice_bar.pack_forget()
            self.voice_btn.configure(text="🎤  VOICE ON", bg=BG3, fg=TEAL)
            self.status_var.set("● READY  —  SPACE=Analyze  V=Voice  Q=Quit")
            self.status_label.configure(fg=GREEN)
            self.analyze_btn.configure(state="normal", bg=GOLD)
            self.voice_count += 1
            self.voice_count_var.set(str(self.voice_count))
            self.history_placeholder.pack_forget()
            row = tk.Frame(self.history_frame, bg=BG3)
            row.pack(fill="x", pady=2)
            tk.Label(row, text="◆", bg=BG3, fg=TEAL,
                     font=("Courier",8)).pack(side="left", padx=(0,6))
            tk.Label(row, text="[voice conversation]", bg=BG3, fg=TEAL,
                     font=("Courier",9)).pack(side="left")

    # ── QUIT ────────────────────────────────────────────
    def _quit(self):
        global voice_running
        voice_running = False
        self.status_var.set("◌ Generating session report...")
        self.status_label.configure(fg=GOLD)
        def generate():
            report = get_session_report()
            print(f"\n📊 SESSION REPORT:\n{report}\n")
            speak(report)
            self.root.after(0, self.root.destroy)
        threading.Thread(target=generate, daemon=True).start()

    def __del__(self):
        if self.cap:
            self.cap.release()

# ── RUN ─────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = AuctionEyeApp(root)
    root.mainloop()