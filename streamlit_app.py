"""
GOAT Tactics: Captains of History
A turn-based tactical football game built with Streamlit.
"""
import streamlit as st
import random
import io
import wave
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="GOAT Tactics: Captains of History",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
# DARK ARCADE CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #0a0e1a 0%, #141824 100%); }
    h1, h2, h3, h4 { color: #e8eaf6 !important; }
    .stButton>button {
        background: linear-gradient(90deg, #1e3a5f, #2a5298);
        color: #fff; border: 1px solid #3d6bb3; border-radius: 8px;
        font-weight: 600; transition: all 0.15s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2a5298, #3d6bb3);
        box-shadow: 0 0 14px rgba(61,107,179,0.7);
    }
    .stButton>button:disabled { opacity: 0.35; }
    .captain-card {
        background: #1a1f2e; border: 1px solid #2d3548;
        border-radius: 14px; padding: 16px; margin: 4px 0;
    }
    .commentary-line {
        background: #111827; border-radius: 6px; padding: 6px 10px;
        margin: 3px 0; font-size: 0.9em; color: #cbd5e1;
    }
    .goal-text { color: #ffd166; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# AUDIO (sine-wave SFX via st.audio)
# ══════════════════════════════════════════════════════════════
def tone_bytes(freq=440, dur=0.15, vol=0.3, sr=22050):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    samples = (vol * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()

SFX = {
    "whistle": tone_bytes(880, 0.25),
    "kick":    tone_bytes(220, 0.08, 0.4),
    "goal":    tone_bytes(660, 0.40, 0.35),
    "ability": tone_bytes(990, 0.30),
}

def play_sfx(name):
    st.session_state.pending_sfx = name

# ══════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════
@dataclass
class Captain:
    name: str
    pos: str
    boost: str
    ability: str
    ability_desc: str
    cooldown: int = 3

@dataclass
class Icon:
    name: str
    pos: str
    stats: dict

@dataclass
class GameState:
    phase: str = "captain_select"
    captain: Optional[Captain] = None
    squad: list = field(default_factory=list)
    lineup: dict = field(default_factory=dict)
    match_round: int = 1
    player_score: int = 0
    opp_score: int = 0
    round_num: int = 0
    commentary: list = field(default_factory=list)
    stamina: int = 100
    cooldown: int = 0
    possession: int = 50
    momentum: int = 0
    shots: int = 0
    shots_on_target: int = 0
    tackles: int = 0
    saves: int = 0
    goalscorers: list = field(default_factory=list)
    tournament_points: int = 0
    matches_played: int = 0
    mvp: str = ""
    pending_sfx: Optional[str] = None

# ══════════════════════════════════════════════════════════════
# STATIC DATA
# ══════════════════════════════════════════════════════════════
CAPTAINS = {
    "Lionel Messi": Captain(
        "Lionel Messi", "RW", "Passing & Agility",
        "Ankara Messi", "Tackle immunity — guaranteed breakthrough into the box."),
    "Cristiano Ronaldo": Captain(
        "Cristiano Ronaldo", "LW", "Shooting & Headers",
        "Siu Moment", "Team overdrive — +25% shot accuracy this round."),
    "Pelé": Captain(
        "Pelé", "CAM", "Flair & Morale",
        "Joga Bonito", "Restore 40 stamina and gain +3 momentum."),
    "Diego Maradona": Captain(
        "Diego Maradona", "CAM", "Dribbling & Fouls",
        "Genius Pass", "Line-breaking through ball — 70% chance of 1v1 goal."),
    "Ronaldo Nazário": Captain(
        "Ronaldo Nazário", "ST", "Acceleration & 1v1",
        "El Fenómeno Burst", "Speed explosion — 65% chance of rounding keeper and scoring."),
}

ICONS = [
    # Goalkeepers
    Icon("Buffon", "GK", {"REF": 94, "POS": 91}),
    Icon("Yashin", "GK", {"REF": 95, "POS": 89}),
    Icon("Casillas", "GK", {"REF": 91, "POS": 90}),
    # Defenders
    Icon("Maldini", "DEF", {"DEF": 94, "PAS": 82}),
    Icon("Beckenbauer", "DEF", {"DEF": 92, "PAS": 88}),
    Icon("Baresi", "DEF", {"DEF": 95, "PAS": 80}),
    Icon("Cannavaro", "DEF", {"DEF": 93, "PAS": 76}),
    Icon("Puyol", "DEF", {"DEF": 90, "PAS": 75}),
    Icon("Roberto Carlos", "DEF", {"DEF": 86, "PAS": 84}),
    Icon("Cafu", "DEF", {"DEF": 87, "PAS": 83}),
    # Midfielders
    Icon("Zidane", "MID", {"PAS": 95, "DRI": 93}),
    Icon("Ronaldinho", "MID", {"DRI": 96, "PAS": 90}),
    Icon("Cruyff", "MID", {"DRI": 92, "PAS": 91}),
    Icon("Xavi", "MID", {"PAS": 96, "DRI": 88}),
    Icon("Iniesta", "MID", {"PAS": 93, "DRI": 94}),
    Icon("Pirlo", "MID", {"PAS": 94, "DRI": 85}),
    Icon("Gullit", "MID", {"PAS": 88, "DRI": 89}),
    # Forwards
    Icon("Henry", "FWD", {"SHO": 92, "DRI": 90}),
    Icon("Van Basten", "FWD", {"SHO": 94, "DRI": 88}),
    Icon("Puskás", "FWD", {"SHO": 95, "DRI": 86}),
]

OPPONENTS = [
    {"name": "Catalan Alchemists XI", "str": 88, "style": "Tiki-Taka"},
    {"name": "Galáctico Dynamos XI", "str": 90, "style": "Power & Pace"},
    {"name": "Santos Sambistas XI", "str": 86, "style": "Joga Bonito"},
    {"name": "Albiceleste Magicians XI", "str": 89, "style": "Flair & Fight"},
]

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def init():
    if "g" not in st.session_state:
        st.session_state.g = GameState()
    if "pending_sfx" not in st.session_state:
        st.session_state.pending_sfx = None

def roll() -> int:
    return random.randint(1, 20)

def log(g: GameState, txt: str):
    g.commentary.append(f"R{g.round_num + 1} | {txt}")

def reset_match(g: GameState):
    g.player_score = 0
    g.opp_score = 0
    g.round_num = 0
    g.stamina = 100
    g.cooldown = 0
    g.possession = 50
    g.momentum = 0
    g.shots = 0
    g.shots_on_target = 0
    g.tackles = 0
    g.saves = 0
    g.goalscorers = []
    g.commentary = []
    g.mvp = ""

def opp(g: GameState):
    return OPPONENTS[(g.match_round - 1) % 4]

# ══════════════════════════════════════════════════════════════
# BOOT
# ══════════════════════════════════════════════════════════════
init()
g: GameState = st.session_state.g

# Fire pending SFX
if st.session_state.pending_sfx:
    st.audio(SFX[st.session_state.pending_sfx], format="audio/wav", autoplay=True)
    st.session_state.pending_sfx = None

st.title("⚽ GOAT Tactics: Captains of History")
st.caption("Draft legends. Command history. Win the Eternal Trophy.")

# ══════════════════════════════════════════════════════════════
# PHASE 1 — CAPTAIN SELECT
# ══════════════════════════════════════════════════════════════
if g.phase == "captain_select":
    st.subheader("Choose Your Captain")
    cols = st.columns(5)
    for i, (name, cap) in enumerate(CAPTAINS.items()):
        with cols[i]:
            st.markdown(f"""<div class="captain-card">
                <h4>{name}</h4>
                <p><b>{cap.pos}</b> · {cap.boost}</p>
                <p style="color:#06d6a0;">✦ {cap.ability}</p>
                <p style="font-size:0.8em;color:#94a3b8;">{cap.ability_desc}</p>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Pick {name.split()[-1]}", key=f"c{i}", use_container_width=True):
                g.captain = cap
                g.phase = "draft"
                st.rerun()

# ══════════════════════════════════════════════════════════════
# PHASE 2 — SQUAD DRAFT
# ══════════════════════════════════════════════════════════════
elif g.phase == "draft":
    st.subheader(f"Draft Squad — Captain: {g.captain.name} ({g.captain.pos})")

    if not g.squad and st.button("🎲 Auto-Draft Full Squad", use_container_width=True):
        gks = random.sample([i for i in ICONS if i.pos == "GK"], 1)
        defs = random.sample([i for i in ICONS if i.pos == "DEF"], 4)
        mids = random.sample([i for i in ICONS if i.pos == "MID"], 3)
        fwds = random.sample([i for i in ICONS if i.pos == "FWD"], 2)
        g.squad = gks + defs + mids + fwds
        g.lineup = {
            "GK": gks[0],
            "DEF1": defs[0], "DEF2": defs[1], "DEF3": defs[2], "DEF4": defs[3],
            "MID1": mids[0], "MID2": mids[1], "MID3": mids[2],
            "FWD1": fwds[0], "FWD2": fwds[1],
            "CAPTAIN": Icon(g.captain.name, g.captain.pos, {"OVR": 99}),
        }
        st.rerun()

    st.markdown(f"**Squad: {len(g.squad)}/10 outfield**")
    if g.squad:
        draft_cols = st.columns(5)
        for i, ic in enumerate(g.squad):
            draft_cols[i % 5].caption(f"{ic.name} ({ic.pos})")

    st.subheader("Available Icons")
    avail = [ic for ic in ICONS if ic not in g.squad]
    pool = st.columns(5)
    for i, ic in enumerate(avail):
        with pool[i % 5]:
            if len(g.squad) < 10:
                if st.button(f"+ {ic.name}", key=f"d{i}", use_container_width=True):
                    g.squad.append(ic)
                    st.rerun()

    if len(g.squad) == 10:
        if st.button("⚔️ Assign Positions & Enter Tournament",
                     type="primary", use_container_width=True):
            gks = [i for i in g.squad if i.pos == "GK"] or [ICONS[0]]
            defs = [i for i in g.squad if i.pos == "DEF"] + [ICONS[3]]
            mids = [i for i in g.squad if i.pos == "MID"] + [ICONS[9]]
            fwds = [i for i in g.squad if i.pos == "FWD"] + [ICONS[17]]
            g.lineup = {
                "GK": gks[0],
                "DEF1": defs[0], "DEF2": defs[1], "DEF3": defs[2], "DEF4": defs[3],
                "MID1": mids[0], "MID2": mids[1], "MID3": mids[2],
                "FWD1": fwds[0], "FWD2": fwds[1],
                "CAPTAIN": Icon(g.captain.name, g.captain.pos, {"OVR": 99}),
            }
            g.phase = "match"
            g.match_round = 1
            g.tournament_points = 0
            g.matches_played = 0
            reset_match(g)
            st.rerun()

# ══════════════════════════════════════════════════════════════
# PHASE 3 — MATCH ENGINE
# ══════════════════════════════════════════════════════════════
elif g.phase == "match":
    o = opp(g)
    st.subheader(f"Match {g.match_round}/4: vs {o['name']} ({o['style']})")

    # Scoreboard
    sc = st.columns(6)
    sc[0].metric("YOU", g.player_score)
    sc[1].metric("ROUND", f"{g.round_num}/8")
    sc[2].metric("OPP", g.opp_score)
    sc[3].metric("Stamina", f"{g.stamina}%")
    sc[4].metric("Momentum", f"{g.momentum:+d}")
    sc[5].metric("Possession", f"{g.possession}%")

    st.progress(g.stamina / 100, text=f"Stamina {g.stamina}%")
    st.progress((g.momentum + 10) / 20, text=f"Momentum: {g.momentum:+d}")

    # Commentary
    with st.expander("📝 Commentary", expanded=True):
        for line in reversed(g.commentary[-8:]):
            st.markdown(f'<div class="commentary-line">{line}</div>',
                        unsafe_allow_html=True)

    st.divider()

    # Captain ability
    ab1, ab2, ab3 = st.columns([1, 1, 2])
    with ab1:
        if g.cooldown == 0:
            if st.button(f"⚡ {g.captain.ability}", type="primary",
                         use_container_width=True):
                play_sfx("ability")
                g.cooldown = g.captain.cooldown
                log(g, f"⚡ {g.captain.name} activates {g.captain.ability}!")
                cap = g.captain.name

                if "Messi" in cap:
                    g.shots += 2
                    g.shots_on_target += 2
                    g.momentum = min(10, g.momentum + 3)
                    if roll() + 10 > 12:
                        g.player_score += 1
                        g.goalscorers.append((cap, g.round_num))
                        play_sfx("goal")
                        log(g, "GOAL! Messi weaves through — tackle immunity!")
                    else:
                        log(g, "Messi's run is stopped at the last moment.")
                elif "Ronaldo" in cap:
                    g.stamina = min(100, g.stamina + 15)
                    g.momentum = min(10, g.momentum + 4)
                    log(g, "SIUUU! The team surges forward!")
                elif "Pelé" in cap:
                    g.stamina = min(100, g.stamina + 40)
                    g.momentum = min(10, g.momentum + 3)
                    log(g, "Joga Bonito! Second wind!")
                elif "Maradona" in cap:
                    if roll() + 12 > 10:
                        g.player_score += 1
                        g.goalscorers.append((cap, g.round_num))
                        play_sfx("goal")
                        log(g, "Genius Pass — GOAL!")
                    else:
                        log(g, "The pass is cut out.")
                elif "Nazário" in cap:
                    if roll() + 11 > 10:
                        g.player_score += 1
                        g.goalscorers.append((cap, g.round_num))
                        play_sfx("goal")
                        log(g, "El Fenómeno rounds the keeper — GOAL!")
                    else:
                        log(g, "The keeper stands tall.")
                st.rerun()
        else:
            st.button(f"⏳ {g.captain.ability} ({g.cooldown})",
                      disabled=True, use_container_width=True)

    with ab2:
        st.progress(
            1 - g.cooldown / g.captain.cooldown if g.captain.cooldown else 1,
            text=f"CD: {g.cooldown}/{g.captain.cooldown}")

    with ab3:
        st.info(f"**{g.captain.ability}**: {g.captain.ability_desc}")

    st.divider()

    # Tactical choice
    st.subheader("Your Play")
    choice = st.radio("", [
        "Pass to Captain", "Power Shot", "Curled Finesse",
        "Solo Dribble", "Aggressive Tackle", "Contain & Intercept",
    ], horizontal=True, label_visibility="collapsed")

    if st.button("▶️ Execute", type="primary", use_container_width=True):
        play_sfx("kick")
        g.round_num += 1
        g.cooldown = max(0, g.cooldown - 1)
        g.stamina = max(0, g.stamina - random.randint(3, 7))

        p_roll = roll() + random.randint(3, 12) + (g.momentum // 3)
        o_roll = roll() + o["str"] // 8 - (g.momentum // 3)

        opp_aggro = 0.4 if choice in ["Aggressive Tackle",
                                     "Contain & Intercept"] else 0.3

        if choice == "Pass to Captain":
            if p_roll > o_roll:
                g.shots += 1
                g.shots_on_target += 1
                g.momentum = min(10, g.momentum + 2)
                g.possession = min(70, g.possession + 3)
                log(g, f"{g.captain.name} receives and drives forward. "
                       f"(Roll {p_roll} vs {o_roll})")
            else:
                g.momentum = max(-10, g.momentum - 2)
                log(g, "Intercepted!")

        elif choice == "Power Shot":
            g.shots += 1
            if p_roll + 3 > o_roll:
                g.player_score += 1
                g.goalscorers.append(("Power Shot", g.round_num))
                play_sfx("goal")
                g.momentum = min(10, g.momentum + 4)
                log(g, f"💥 GOAL! Thunderous strike! "
                       f"(Roll {p_roll}+3 vs {o_roll})")
            else:
                g.momentum = max(-10, g.momentum - 3)
                log(g, "Over the bar!")

        elif choice == "Curled Finesse":
            g.shots += 1
            if p_roll + 2 > o_roll:
                g.player_score += 1
                g.goalscorers.append(("Finesse", g.round_num))
                play_sfx("goal")
                g.momentum = min(10, g.momentum + 3)
                log(g, "🎯 GOAL! Curled into the top corner!")
            else:
                log(g, "Saved by the keeper!")

        elif choice == "Solo Dribble":
            if p_roll + 4 > o_roll:
                g.shots += 1
                g.shots_on_target += 1
                g.momentum = min(10, g.momentum + 2)
                log(g, "Dribbles past two defenders!")
            else:
                g.momentum = max(-10, g.momentum - 2)
                log(g, "Stopped by a tackle.")

        elif choice == "Aggressive Tackle":
            if p_roll > o_roll:
                g.tackles += 1
                g.possession = min(70, g.possession + 5)
                g.momentum = min(10, g.momentum + 3)
                log(g, "🛡️ Clean tackle! Counter launched.")
            else:
                g.possession = max(30, g.possession - 5)
                g.momentum = max(-10, g.momentum - 3)
                log(g, "Mistimed — free kick to opponent.")

        elif choice == "Contain & Intercept":
            if p_roll > o_roll - 2:
                g.tackles += 1
                g.possession = min(70, g.possession + 2)
                log(g, "Positional discipline forces them back.")
            else:
                g.possession = max(30, g.possession - 3)
                log(g, "They find space in behind.")

        # Opponent attack
        if random.random() < opp_aggro:
            if roll() + o["str"] // 9 > p_roll + 4:
                g.opp_score += 1
                g.momentum = max(-10, g.momentum - 4)
                log(g, f"😤 {o['name']} scores!")
            else:
                g.saves += 1
                log(g, "Your defense holds!")

        # Halftime
        if g.round_num == 4:
            g.stamina = min(100, g.stamina + 20)
            log(g, "⏸️ HALF TIME — stamina partially restored.")

        # End of match
        if g.round_num >= 8:
            g.phase = "post"
            g.matches_played += 1

        st.rerun()

# ══════════════════════════════════════════════════════════════
# PHASE 4 — POST-MATCH
# ══════════════════════════════════════════════════════════════
elif g.phase == "post":
    o = opp(g)
    st.subheader(f"Full Time: {g.player_score} — {g.opp_score} vs {o['name']}")

    if g.player_score > g.opp_score:
        st.success("🏆 Victory! +3 points")
        g.tournament_points += 3
        g.mvp = g.captain.name
    elif g.player_score == g.opp_score:
        st.warning("🤝 Draw. +1 point")
        g.tournament_points += 1
        g.mvp = g.captain.name
    else:
        st.error("❌ Defeat.")
        g.mvp = o["name"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Shots", g.shots)
    c2.metric("On Target", g.shots_on_target)
    c3.metric("Tackles", g.tackles)
    c4.metric("Saves", g.saves)

    if g.goalscorers:
        st.subheader("Goals")
        for s, r in g.goalscorers:
            st.markdown(f"⚽ **{s}** (Round {r})")

    st.subheader("Player of the Match")
    st.info(f"⭐ {g.mvp}")

    st.subheader("Tournament")
    st.dataframe(
        [{"Team": f"{g.captain.name} XI",
          "Pts": g.tournament_points,
          "Played": g.matches_played}],
        use_container_width=True, hide_index=True)

    if g.match_round < 4:
        if st.button("➡️ Next Match", type="primary", use_container_width=True):
            g.match_round += 1
            reset_match(g)
            g.phase = "match"
            st.rerun()
    else:
        st.balloons()
        st.subheader("🏆 Campaign Complete!")
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.g = GameState()
            st.session_state.pending_sfx = None
            st.rerun()
