import math
import random
import numpy as np
import pygame

SAMPLE_RATE: int = 44100


def _make_sound(samples: np.ndarray) -> pygame.mixer.Sound:
    # wandelt ein float32-array in einen pygame.sound um

    s   = np.clip(samples, -1.0, 1.0)
    s16 = (s * 32767).astype(np.int16)
    stereo = np.column_stack([s16, s16])
    return pygame.sndarray.make_sound(stereo)


def _sinus(freq: float, dauer: float, amp: float = 0.5,
           fade: bool = True) -> np.ndarray:
    # einfacher sinuston

    n = int(SAMPLE_RATE * dauer)
    t = np.linspace(0, dauer, n, endpoint=False)
    w = amp * np.sin(2 * math.pi * freq * t)
    if fade:
        w *= np.linspace(1, 0, n)
    return w


def _rauschen(dauer: float, amp: float = 0.3) -> np.ndarray:
    # weißes rauschen

    n = int(SAMPLE_RATE * dauer)
    return (np.random.uniform(-1, 1, n) * amp).astype(np.float32)


def _verzerren(wave: np.ndarray, staerke: float = 0.6) -> np.ndarray:
    # weiche clipping-verzerrung für horror-sounds

    return np.tanh(wave * (1 + staerke * 8)) / (1 + staerke * 0.5)


def _reverb(wave: np.ndarray, delay_ms: float = 60,
            abklingen: float = 0.35) -> np.ndarray:
    # einfaches echo/reverb durch verzögertes überlagern

    delay_s = int(SAMPLE_RATE * delay_ms / 1000)
    out = wave.copy()
    if delay_s < len(out):
        out[delay_s:] += wave[:-delay_s] * abklingen
    return np.clip(out, -1.0, 1.0)


def _tiefpass(wave: np.ndarray, grenz_ratio: float = 0.15) -> np.ndarray:
    # sehr einfacher tiefpassfilter (gleitender durchschnitt)

    fenster = max(2, int(1.0 / grenz_ratio))
    kernel  = np.ones(fenster) / fenster
    return np.convolve(wave, kernel, mode="same")


def make_heartbeat() -> pygame.mixer.Sound:
    # tiefer, verzerrter herzschlag für horror-atmosphäre

    sr = SAMPLE_RATE
    d1 = 0.09
    d2 = 0.07

    n1  = int(sr * d1)
    t1  = np.linspace(0, d1, n1, endpoint=False)
    w1  = 0.85 * np.sin(2 * math.pi * 52 * t1) * np.exp(-t1 * 30)
    w1 += 0.30 * np.sin(2 * math.pi * 104 * t1) * np.exp(-t1 * 40)
    w1 += _rauschen(d1, 0.08)[:n1]
    w1  = _verzerren(w1, 0.3)

    luecke = int(sr * 0.12)

    n2  = int(sr * d2)
    t2  = np.linspace(0, d2, n2, endpoint=False)
    w2  = 0.65 * np.sin(2 * math.pi * 72 * t2) * np.exp(-t2 * 38)
    w2 += 0.20 * np.sin(2 * math.pi * 144 * t2) * np.exp(-t2 * 50)
    w2  = _verzerren(w2, 0.2)

    ende  = int(sr * 0.35)
    kombi = np.concatenate([w1, np.zeros(luecke), w2, np.zeros(ende)])
    kombi = _reverb(kombi, 80, 0.25)
    return _make_sound(kombi)


def make_footstep_hard() -> pygame.mixer.Sound:
    # schwerer schritt auf parkett/fliesen

    dauer = 0.10
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    imp   = 0.55 * np.sin(2 * math.pi * 180 * t) * np.exp(-t * 70)
    imp  += 0.30 * np.sin(2 * math.pi * 340 * t) * np.exp(-t * 120)
    rau   = _rauschen(dauer, 0.2)[:n]
    raw   = _tiefpass(imp + rau, 0.4)
    return _make_sound(raw)


def make_footstep_soft() -> pygame.mixer.Sound:
    # gedämpfter schritt auf teppich

    dauer = 0.12
    n     = int(SAMPLE_RATE * dauer)
    rau   = _rauschen(dauer, 0.10)[:n]
    env   = np.exp(-np.linspace(0, 8, n))
    raw   = _tiefpass(rau * env, 0.2)
    return _make_sound(raw)


def make_footstep_hard_var2() -> pygame.mixer.Sound:
    # zweite schritt-variante für abwechslung

    dauer = 0.09
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    imp   = 0.50 * np.sin(2 * math.pi * 200 * t) * np.exp(-t * 80)
    imp  += 0.25 * np.sin(2 * math.pi * 400 * t) * np.exp(-t * 110)
    return _make_sound(imp + _rauschen(dauer, 0.18)[:n])


def make_jumpscare_scream() -> pygame.mixer.Sound:
    # erschreckender schrei mit pitch-slide

    dauer = 1.4
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)

    freq1 = 800 + 500 * np.exp(-t * 2.5)
    freq2 = freq1 * 1.52
    freq3 = freq1 * 0.49

    w1  = 0.65 * np.sin(2 * math.pi * freq1 * t)
    w2  = 0.30 * np.sin(2 * math.pi * freq2 * t)
    w3  = 0.20 * np.sin(2 * math.pi * freq3 * t)
    rau = _rauschen(dauer, 0.35)[:n]

    kombi = w1 + w2 + w3 + rau
    kombi = _verzerren(kombi, 0.5)

    ein   = np.minimum(np.ones(n), np.linspace(0, 1, n) * 30)
    aus   = np.linspace(1, 0, n) ** 0.7
    kombi *= ein * aus

    return _make_sound(_reverb(kombi, 120, 0.3))


def make_alert_sting() -> pygame.mixer.Sound:
    # kurzer warnton wenn monster spieler bemerkt

    dauer = 0.45
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    freq  = 380 + 700 * t / dauer
    w     = 0.6 * np.sin(2 * math.pi * freq * t) * np.exp(-t * 6)
    return _make_sound(_verzerren(w, 0.4))


def make_key_pickup() -> pygame.mixer.Sound:
    # heller pickup-sound beim aufsammeln eines schlüssels

    s1 = _sinus(523.25, 0.09, 0.42)
    s2 = _sinus(659.25, 0.09, 0.42)
    s3 = _sinus(783.99, 0.22, 0.48)
    return _make_sound(np.concatenate([s1, s2, s3]))


def make_task_complete() -> pygame.mixer.Sound:
    # positiver jingle bei aufgabenabschluss

    segmente = [_sinus(f, 0.07, 0.38) for f in [392, 523.25, 659.25, 783.99]]
    letzt    = _sinus(1046.5, 0.28, 0.45)
    return _make_sound(np.concatenate(segmente + [letzt]))


# KI CODE ANFANG
# Claude Opus 4.8
# Prompt: "Erstelle einen 24-sekündigen Horror-Ambient-Soundtrack-Loop mit numpy für
# pygame. Verwende mindestens 6 überlagerte Schichten: Sub-Bass-Drone (33Hz),
# dissonante Quinte (55/58Hz), Tremolo-Ton (110Hz), Sub-Rumble (22Hz), zufällige
# Thumps (Herzschlag-ähnlich) und Hintergrundrauschen. Füge einen seamless crossfade
# am Anfang und Ende ein damit der Loop nahtlos ist."
def make_bg_music() -> pygame.mixer.Sound:
    # 24-sekündiger horror-ambient-loop mit mehreren überlagerten schichten

    dauer = 24.0
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)

    lfo1 = 0.5 + 0.5 * np.sin(2 * math.pi * 0.08 * t)
    l1   = 0.22 * np.sin(2 * math.pi * 33 * t) * lfo1

    l2 = 0.12 * np.sin(2 * math.pi * 55.0 * t)
    l3 = 0.08 * np.sin(2 * math.pi * 58.7 * t)

    tremolo = 0.5 + 0.5 * np.sin(2 * math.pi * 5.3 * t)
    l4      = 0.06 * np.sin(2 * math.pi * 110 * t) * tremolo

    lfo2 = 0.7 + 0.3 * np.sin(2 * math.pi * 0.15 * t)
    l5   = 0.10 * np.sin(2 * math.pi * 22 * t) * lfo2

    thumps = np.zeros(n, dtype=np.float32)
    for thump_sek in [1.0, 4.5, 8.0, 11.5, 15.0, 18.5, 22.0]:
        ts = int(thump_sek * SAMPLE_RATE)
        tl = int(0.35 * SAMPLE_RATE)
        if ts + tl < n:
            te         = np.exp(-np.linspace(0, 10, tl))
            thump_wave = 0.18 * np.sin(
                2 * math.pi * 42 * np.linspace(0, 0.35, tl)) * te
            thumps[ts:ts + tl] += thump_wave

    rauschen = _tiefpass(_rauschen(dauer, 0.04)[:n], 0.04)

    musik = (l1 + l2 + l3 + l4 + l5 + thumps + rauschen).astype(np.float32)
    musik = np.clip(musik, -1.0, 1.0)

    xf       = int(2.0 * SAMPLE_RATE)
    fade_ein = np.linspace(0, 1, xf, dtype=np.float32)
    fade_aus = np.linspace(1, 0, xf, dtype=np.float32)
    musik[:xf]  = musik[:xf] * fade_ein  + musik[-xf:] * fade_aus
    musik[-xf:] = musik[-xf:] * fade_aus + musik[:xf]  * fade_ein

    return _make_sound(musik)
# KI CODE ENDE


def make_ambient_horror() -> pygame.mixer.Sound:
    # kurzer horror-ambiente-loop (4 sekunden)

    dauer = 4.0
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)

    drone1 = 0.06 * np.sin(2 * math.pi * 38 * t)
    drone2 = 0.04 * np.sin(2 * math.pi * 55 * t)
    drone3 = 0.03 * np.sin(2 * math.pi * 82 * t)
    wind   = _rauschen(dauer, 0.025)[:n]
    mod    = 0.02 * np.sin(2 * math.pi * 0.3 * t)
    summen = 0.035 * np.sin(2 * math.pi * (110 + mod * 5) * t)

    kombi = drone1 + drone2 + drone3 + wind + summen
    fade  = int(SAMPLE_RATE * 0.25)
    kombi[:fade]  *= np.linspace(0, 1, fade)
    kombi[-fade:] *= np.linspace(1, 0, fade)
    return _make_sound(kombi)


def make_wall_creak() -> pygame.mixer.Sound:
    # gruseliges wandknarren für wandgesichter-jumpscares

    dauer = 0.8
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    freq  = 140 + 80 * np.sin(math.pi * t / dauer * 2.5)
    w     = 0.4 * np.sin(2 * math.pi * freq * t)
    w    += _rauschen(dauer, 0.12)[:n]
    w    *= np.exp(-t * 2.5)
    return _make_sound(_verzerren(w, 0.3))


def make_hanging_drop() -> pygame.mixer.Sound:
    # schweres aufschlagen für hängende figur

    dauer = 0.6
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    auf   = 0.8 * np.sin(2 * math.pi * 60 * t) * np.exp(-t * 15)
    auf  += 0.4 * np.sin(2 * math.pi * 120 * t) * np.exp(-t * 25)
    raw   = _verzerren(auf + _rauschen(dauer, 0.3)[:n], 0.5)
    return _make_sound(_reverb(raw, 150, 0.4))


def make_shadow_rush() -> pygame.mixer.Sound:
    # whoosh-sound für schatten-jumpscare

    dauer = 0.5
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    freq  = 1200 * np.exp(-t * 5)
    w     = 0.5 * np.sin(2 * math.pi * freq * t)
    raw   = _tiefpass((w + _rauschen(dauer, 0.25)[:n]) * np.sin(math.pi * t / dauer), 0.5)
    return _make_sound(raw)


def make_blackout_sound() -> pygame.mixer.Sound:
    # tiefes grollen + hoher pfiff für blackout-jumpscare

    dauer = 2.5
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    grollen  = _verzerren(_tiefpass(
        0.35 * np.sin(2 * math.pi * 30 * t) + _rauschen(dauer, 0.2)[:n], 0.08), 0.6)
    pfiff_n  = int(SAMPLE_RATE * 0.15)
    pfiff_t  = np.linspace(0, 0.15, pfiff_n, endpoint=False)
    pfiff    = 0.5 * np.sin(2 * math.pi * 2200 * pfiff_t) * np.exp(-pfiff_t * 25)
    start    = int(SAMPLE_RATE * 0.05)
    if start + pfiff_n < n:
        grollen[start:start + pfiff_n] += pfiff
    env = np.ones(n)
    env[:int(SAMPLE_RATE * 0.1)]  *= np.linspace(0, 1, int(SAMPLE_RATE * 0.1))
    env[-int(SAMPLE_RATE * 0.3):] *= np.linspace(1, 0, int(SAMPLE_RATE * 0.3))
    return _make_sound(grollen * env)


def make_monster_breathing() -> pygame.mixer.Sound:
    # tiefer, verzerrter atemgeräusch-loop für das monster

    dauer    = 2.8
    n        = int(SAMPLE_RATE * dauer)
    t        = np.linspace(0, dauer, n, endpoint=False)
    atem_env = 0.5 + 0.5 * np.sin(2 * math.pi * 0.35 * t)
    ton      = 0.3 * np.sin(2 * math.pi * 65 * t)
    ton     += 0.15 * np.sin(2 * math.pi * 130 * t)
    raw = _tiefpass(_verzerren((ton + _rauschen(dauer, 0.2)[:n]) * atem_env, 0.45), 0.2)
    fade = int(SAMPLE_RATE * 0.3)
    raw[:fade]  *= np.linspace(0, 1, fade)
    raw[-fade:] *= np.linspace(1, 0, fade)
    return _make_sound(raw)


def make_door_creak() -> pygame.mixer.Sound:
    # türknarren

    dauer = 0.7
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    freq  = 160 + 100 * np.sin(math.pi * t / dauer)
    w     = 0.3 * np.sin(2 * math.pi * freq * t)
    w    += _rauschen(dauer, 0.1)[:n]
    w    *= np.exp(-t * 1.5)
    return _make_sound(w)


def make_torch_click() -> pygame.mixer.Sound:
    # klick-sound beim umschalten der taschenlampe

    dauer = 0.05
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    w     = 0.4 * np.sin(2 * math.pi * 1200 * t) * np.exp(-t * 80)
    return _make_sound(w)


def make_whisper() -> pygame.mixer.Sound:
    # kaum hörbares flüstern für atmosphäre

    dauer = 1.8
    n     = int(SAMPLE_RATE * dauer)
    rau   = _tiefpass(_rauschen(dauer, 0.12)[:n], 0.3)
    env   = np.sin(math.pi * np.linspace(0, 1, n)) ** 2
    return _make_sound(rau * env)


def make_dash() -> pygame.mixer.Sound:
    # kurzer whoosh für den dash

    dauer = 0.18
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    freq  = 600 + 800 * (1 - t / dauer)
    w     = 0.55 * np.sin(2 * math.pi * freq * t)
    env   = np.sin(math.pi * t / dauer) ** 0.5
    return _make_sound((w + _rauschen(dauer, 0.15)[:n]) * env)


def make_drip() -> pygame.mixer.Sound:
    # wassertropfen für den keller (r5)

    dauer = 0.25
    n     = int(SAMPLE_RATE * dauer)
    t     = np.linspace(0, dauer, n, endpoint=False)
    w     = 0.5 * np.sin(2 * math.pi * 900 * t) * np.exp(-t * 20)
    w    += 0.2 * np.sin(2 * math.pi * 1400 * t) * np.exp(-t * 30)
    return _make_sound(_reverb(w, 40, 0.4))


class SoundManager:
    # verwaltet alle generierten sounds und ihre lautstärken

    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16,
                              channels=2, buffer=512)
        pygame.mixer.set_num_channels(16)

        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._schritt_var: int = 0
        self._kanal_ambient: pygame.mixer.Channel | None = None
        self._kanal_atem:    pygame.mixer.Channel | None = None
        self._kanal_tropf:   pygame.mixer.Channel | None = None
        self._kanal_musik:   pygame.mixer.Channel | None = None

        self._alle_generieren()

    def _alle_generieren(self) -> None:
        # generiert alle sounds und setzt basislautstärken

        generator_map = {
            "heartbeat":      make_heartbeat,
            "step_hard":      make_footstep_hard,
            "step_hard2":     make_footstep_hard_var2,
            "step_soft":      make_footstep_soft,
            "jumpscare":      make_jumpscare_scream,
            "alert":          make_alert_sting,
            "key_pickup":     make_key_pickup,
            "task_done":      make_task_complete,
            "ambient":        make_ambient_horror,
            "wall_creak":     make_wall_creak,
            "hanging_drop":   make_hanging_drop,
            "shadow_rush":    make_shadow_rush,
            "blackout_sound": make_blackout_sound,
            "monster_breath": make_monster_breathing,
            "door_creak":     make_door_creak,
            "torch_click":    make_torch_click,
            "whisper":        make_whisper,
            "drip":           make_drip,
            "dash":           make_dash,
            "bg_music":       make_bg_music,
        }
        for name, fn in generator_map.items():
            try:
                self._sounds[name] = fn()
            except Exception as e:
                print(f"[SoundManager] Konnte '{name}' nicht erstellen: {e}")

        self._sfx_basis: dict[str, float] = {
            "ambient":        0.40,
            "heartbeat":      0.00,
            "jumpscare":      0.95,
            "alert":          0.80,
            "monster_breath": 0.00,
            "drip":           0.25,
            "whisper":        0.20,
            "blackout_sound": 0.85,
            "shadow_rush":    0.65,
            "hanging_drop":   0.80,
            "wall_creak":     0.70,
            "torch_click":    0.55,
            "dash":           0.70,
            "step_hard":      0.55,
            "step_hard2":     0.55,
            "step_soft":      0.45,
            "key_pickup":     0.80,
            "task_done":      0.75,
        }
        self._musik_basis: float = 0.35
        for name, vol in self._sfx_basis.items():
            if name in self._sounds:
                self._sounds[name].set_volume(vol)
        if "bg_music" in self._sounds:
            self._sounds["bg_music"].set_volume(0.0)

    def play(self, name: str, loops: int = 0) -> pygame.mixer.Channel | None:
        snd = self._sounds.get(name)
        return snd.play(loops=loops) if snd else None

    def play_step(self, weich: bool) -> None:
        if weich:
            self.play("step_soft")
        else:
            self._schritt_var = 1 - self._schritt_var
            self.play("step_hard" if self._schritt_var == 0 else "step_hard2")

    def start_ambient(self) -> None:
        snd = self._sounds.get("ambient")
        if snd and self._kanal_ambient is None:
            self._kanal_ambient = snd.play(loops=-1)

    def stop_ambient(self) -> None:
        if self._kanal_ambient:
            self._kanal_ambient.stop()
            self._kanal_ambient = None

    def start_monster_breathing(self) -> None:
        snd = self._sounds.get("monster_breath")
        if snd and self._kanal_atem is None:
            self._kanal_atem = snd.play(loops=-1)
            snd.set_volume(0.0)

    def stop_monster_breathing(self) -> None:
        if self._kanal_atem:
            self._kanal_atem.stop()
            self._kanal_atem = None

    def start_dripping(self) -> None:
        snd = self._sounds.get("drip")
        if snd and self._kanal_tropf is None:
            self._kanal_tropf = snd.play(loops=-1)

    def stop_dripping(self) -> None:
        if self._kanal_tropf:
            self._kanal_tropf.stop()
            self._kanal_tropf = None

    def set_heartbeat_volume(self, volume: float) -> None:
        snd = self._sounds.get("heartbeat")
        if snd:
            snd.set_volume(max(0.0, min(1.0, volume)))

    def set_breath_volume(self, volume: float) -> None:
        snd = self._sounds.get("monster_breath")
        if snd:
            snd.set_volume(max(0.0, min(1.0, volume)))

    def start_bg_music(self, master_vol: int = 80, music_vol: int = 55) -> None:
        snd = self._sounds.get("bg_music")
        if not snd:
            return
        vol = self._musik_basis * (master_vol / 100.0) * (music_vol / 100.0)
        snd.set_volume(max(0.0, min(1.0, vol)))
        if self._kanal_musik is None:
            self._kanal_musik = snd.play(loops=-1)

    def stop_bg_music(self) -> None:
        if self._kanal_musik:
            self._kanal_musik.stop()
            self._kanal_musik = None

    def set_music_volume(self, master_vol: int, music_vol: int) -> None:
        snd = self._sounds.get("bg_music")
        if snd:
            vol = self._musik_basis * (master_vol / 100.0) * (music_vol / 100.0)
            snd.set_volume(max(0.0, min(1.0, vol)))

    def apply_volume_settings(self, master_vol: int,
                               music_vol: int, sfx_vol: int) -> None:
        # wendet alle lautstärkeeinstellungen in einem schritt an

        m  = master_vol / 100.0
        mu = music_vol  / 100.0
        sf = sfx_vol    / 100.0

        dynamisch = {"heartbeat", "monster_breath"}
        for name, basis in self._sfx_basis.items():
            if name in dynamisch:
                continue
            snd = self._sounds.get(name)
            if snd:
                snd.set_volume(max(0.0, min(1.0, basis * m * sf)))

        snd = self._sounds.get("bg_music")
        if snd:
            snd.set_volume(max(0.0, min(1.0, self._musik_basis * m * mu)))

    def stop_all(self) -> None:
        # stoppt sämtliche sounds

        pygame.mixer.stop()
        self._kanal_ambient = None
        self._kanal_atem    = None
        self._kanal_tropf   = None
        self._kanal_musik   = None
