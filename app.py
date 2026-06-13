"""
Saffin OS - Desktop UI (Streamlit)

A simple graphical interface for the Saffin OS automation tools:
- Dashboard / status
- Log a daily session
- Idea vault (add ideas, score eligible ideas)
- Weekly review generator
- Streaks & heatmap
- Decision framework calculator

Run with:  streamlit run app.py
"""

import os
import sys
import csv
import re
from datetime import datetime, date, timedelta

import streamlit as st

# ---------------------------------------------------------------------------
# Paths / imports from the existing scripts package
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from decision_score import decision_score, compute, interpret  # noqa: E402
import streaks as streaks_mod  # noqa: E402

JOURNAL_CSV = os.path.join(ROOT, "journal", "journal.csv")
IDEA_VAULT = os.path.join(ROOT, "idea_vault.md")
WEEKLY_DIR = os.path.join(ROOT, "weekly_reviews")
WEEKLY_TEMPLATE = os.path.join(WEEKLY_DIR, "TEMPLATE.md")

IDEA_BLOCK_RE = re.compile(
    r"### (.+?)\n"
    r"- Date added: (.+?)\n"
    r"- Description: (.*?)\n"
    r"- Impact \(1-5\): (.*?)\n"
    r"- Alignment \(1-5\): (.*?)\n"
    r"- Effort \(1-5\): (.*?)\n"
    r"- Risk \(1-5\): (.*?)\n"
    r"- Opportunity Cost \(1-5\): (.*?)\n"
    r"- Score: (.*?)\n"
    r"- Action: (.*?)(?:\n|$)"
)

st.set_page_config(page_title="Saffin OS", page_icon="🧭", layout="centered")

# Initialize session state for tab navigation
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "dashboard"

# Injected UI styles and small component helpers
def render_css():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Sora:wght@600;700&display=swap');
    html, body, .stApp {
        background: #0D1117 !important;
        color: #E6EDF3 !important;
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }
    .saffin-header {
        font-family: 'Sora', 'Inter', monospace;
        font-weight: 700;
        font-size: 28px;
        letter-spacing: 1px;
        color: #E6EDF3;
        margin-bottom: 2px;
        animation: slideInDown 0.4s ease-out;
    }
    .saffin-sub { color: #9AA6B2; margin-top:0; margin-bottom:12px; }

    @keyframes slideInDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideInLeft { from { opacity: 0; transform: translateX(-16px); } to { opacity: 1; transform: translateX(0); } }

    .card {
        background: #1C2128;
        border-radius: 16px;
        padding: 16px;
        border: 1px solid rgba(255,255,255,0.04);
        transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
        animation: slideInLeft 0.3s ease-out;
    }
    .card:hover { 
        box-shadow: 0 12px 36px rgba(139,92,246,0.08); 
        transform: translateY(-3px); 
        border-color: rgba(139,92,246,0.16); 
    }
    .card:active { transform: translateY(-1px); }

    .glass {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 14px;
        animation: fadeIn 0.3s ease-out;
    }

    .metric-card { display:flex; flex-direction:column; gap:8px; padding: 12px !important; }
    .metric-label { color: #9AA6B2; font-size:12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size:24px; font-weight:700; color: #E6EDF3; }
    .accent-violet { color: #8B5CF6; }
    .accent-sky { color: #38BDF8; }

    /* Left dock (pill sidebar) */
    .saffin-dock {
        position: fixed; left: 18px; top: 86px; width: 72px; display:flex; flex-direction:column; gap:14px; z-index:9999;
    }
    .saffin-dock .pill { 
        width:56px; height:56px; border-radius:14px; display:flex; align-items:center; justify-content:center; 
        background: rgba(255,255,255,0.02); color:#E6EDF3; font-size:20px; 
        cursor: pointer; transition: all 0.2s ease;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .saffin-dock .pill:hover { 
        background: rgba(255,255,255,0.04); 
        box-shadow: 0 6px 18px rgba(139,92,246,0.04); 
        transform: scale(1.05);
    }
    .saffin-dock .pill:active { transform: scale(0.98); }
    .saffin-dock .pill.active { 
        box-shadow: 0 10px 28px rgba(139,92,246,0.12); 
        border-left:4px solid #8B5CF6;
        background: rgba(139,92,246,0.06);
    }

    .saffin-focus {
        position: fixed; left: 18px; bottom: 18px; width: 220px; z-index:9999;
        animation: slideInLeft 0.4s ease-out 0.1s both;
    }

    /* nudge main app content to avoid overlap */
    .stApp {
        padding-left: 108px !important;
    }

    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def metric_card(label, value, accent="violet"):
    cls = "accent-violet" if accent == "violet" else "accent-sky"
    html = f"""
    <div class="card metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value {cls}">{value}</div>
    </div>
    """
    return html


def section_header(title, subtitle=None):
    sub_html = f"<div class='saffin-sub'>{subtitle}</div>" if subtitle else ""
    html = f"<div class='saffin-header'>{title}</div>{sub_html}"
    st.markdown(html, unsafe_allow_html=True)


render_css()


def glass_card(title=None, body_html=None, small=False):
    small_cls = "" if not small else "style='padding:8px;border-radius:10px;font-size:13px'"
    title_html = f"<div style='font-weight:700;margin-bottom:6px'>{title}</div>" if title else ""
    body = body_html or ""
    return f"<div class='card glass' {small_cls}>{title_html}{body}</div>"


def get_current_focus():
    rows = load_journal_rows()
    if not rows:
        return None
    # prefer today's last entry, else most recent with notes
    for row in reversed(rows[-10:]):
        notes = (row.get("notes") or "").strip()
        if notes:
            return notes
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_journal_rows():
    rows = []
    if os.path.isfile(JOURNAL_CSV):
        with open(JOURNAL_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return rows


def week_bounds(today=None):
    today = today or date.today()
    days_since_sunday = (today.weekday() + 1) % 7  # Sunday = 0
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_status():
    today = date.today()
    week_start, week_end = week_bounds(today)

    primary_sessions = 0
    secondary_sessions = 0
    for row in load_journal_rows():
        try:
            d = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if week_start <= d <= today:
            pm = int(row.get("primary_minutes", 0) or 0)
            sm = int(row.get("secondary_minutes", 0) or 0)
            if pm > 0:
                primary_sessions += 1
            if sm > 0:
                secondary_sessions += 1

    pending = 0
    ready = 0
    if os.path.isfile(IDEA_VAULT):
        with open(IDEA_VAULT, "r", encoding="utf-8") as f:
            content = f.read()
        now = datetime.now()
        for m in IDEA_BLOCK_RE.finditer(content):
            (title, date_added_str, desc, impact, align, effort, risk, opp,
             score, action) = m.groups()
            score = score.strip()
            action = action.strip()
            if score and action in ("Act", "Vault", "Drop"):
                continue
            pending += 1
            date_added = parse_idea_date(date_added_str)
            if date_added and now - date_added >= timedelta(hours=48):
                ready += 1

    return {
        "today": today,
        "week_start": week_start,
        "primary_sessions": primary_sessions,
        "secondary_sessions": secondary_sessions,
        "pending_ideas": pending,
        "ready_ideas": ready,
    }


def parse_idea_date(date_added_str):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_added_str.strip(), fmt)
        except ValueError:
            continue
    return None


def get_ideas():
    """Return list of dicts describing each idea block found in idea_vault.md."""
    ideas = []
    if not os.path.isfile(IDEA_VAULT):
        return ideas
    with open(IDEA_VAULT, "r", encoding="utf-8") as f:
        content = f.read()
    now = datetime.now()
    for m in IDEA_BLOCK_RE.finditer(content):
        (title, date_added_str, desc, impact, align, effort, risk, opp,
         score, action) = m.groups()
        score = score.strip()
        action = action.strip()
        date_added = parse_idea_date(date_added_str)
        scored = bool(score) and action in ("Act", "Vault", "Drop")
        eligible = (
            not scored and date_added is not None
            and now - date_added >= timedelta(hours=48)
        )
        ideas.append({
            "match": m,
            "title": title.strip(),
            "date_added": date_added_str.strip(),
            "description": desc.strip(),
            "scored": scored,
            "eligible": eligible,
            "score": score,
            "action": action,
        })
    return ideas


def save_idea_score(content, m, impact, alignment, effort, risk, opp_cost):
    score, interpretation = decision_score(impact, alignment, effort, risk, opp_cost)
    action_word = {
        "Act now": "Act",
        "Vault (revisit next quarter)": "Vault",
        "Drop": "Drop",
    }.get(interpretation, "Vault")

    old_block = m.group(0)
    new_block = old_block
    new_block = re.sub(r"- Impact \(1-5\): .*", f"- Impact (1-5): {impact}", new_block)
    new_block = re.sub(r"- Alignment \(1-5\): .*", f"- Alignment (1-5): {alignment}", new_block)
    new_block = re.sub(r"- Effort \(1-5\): .*", f"- Effort (1-5): {effort}", new_block)
    new_block = re.sub(r"- Risk \(1-5\): .*", f"- Risk (1-5): {risk}", new_block)
    new_block = re.sub(r"- Opportunity Cost \(1-5\): .*", f"- Opportunity Cost (1-5): {opp_cost}", new_block)
    new_block = re.sub(r"- Score: .*", f"- Score: {score}", new_block)
    new_block = re.sub(r"- Action: .*", f"- Action: {action_word}", new_block)

    new_content = content.replace(old_block, new_block)
    with open(IDEA_VAULT, "w", encoding="utf-8") as f:
        f.write(new_content)

    return score, interpretation


def generate_review(force=False):
    today = datetime.now()
    week_start, week_end = week_bounds(today.date())
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.min.time())

    primary_sessions = 0
    secondary_sessions = 0
    primary_minutes_total = 0
    secondary_minutes_total = 0

    for row in load_journal_rows():
        try:
            d = datetime.strptime(row["date"].strip(), "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        if week_start_dt.date() <= d.date() <= week_end_dt.date():
            pm = int(row.get("primary_minutes", 0) or 0)
            sm = int(row.get("secondary_minutes", 0) or 0)
            if pm > 0:
                primary_sessions += 1
                primary_minutes_total += pm
            if sm > 0:
                secondary_sessions += 1
                secondary_minutes_total += sm

    exec_score_primary = round((primary_sessions / 5) * 100) if primary_sessions else 0
    exec_score_secondary = round((secondary_sessions / 3) * 100) if secondary_sessions else 0

    filename = os.path.join(WEEKLY_DIR, f"{week_end.strftime('%Y-%m-%d')}.md")

    if os.path.isfile(filename) and not force:
        return None, filename, "exists"

    content = f"""# Weekly Review

- **Date:** {week_end.strftime('%Y-%m-%d')} (week of {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})
- **Primary sessions:** {primary_sessions} / 5  ({primary_minutes_total} min total)
- **Secondary sessions:** {secondary_sessions} / 3  ({secondary_minutes_total} min total)
- **Protein days:** __ / 7
- **Execution Score (Primary):** {exec_score_primary}%
- **Execution Score (Secondary):** {exec_score_secondary}%

## Reflection
- **One thing finished:**
- **One thing avoided:**
- **Smallest next action for Primary:**

## Idea Vault Check
Run the "Idea Vault" tab to process any items 48h+ old.
"""

    os.makedirs(WEEKLY_DIR, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return content, filename, "created"


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
section_header("SAFFIN.EXE — Personal OS", "Your productivity & self-development assistant")

# render the left dock and current focus widget (visual only - navigation via buttons below)
focus_text = get_current_focus() or "No current focus"
dock_html = '''
<div class="saffin-dock">
  <div class="pill" title="Dashboard" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">📊</div>
  <div class="pill" title="Log">📝</div>
  <div class="pill" title="Ideas">💡</div>
  <div class="pill" title="Review">📅</div>
  <div class="pill" title="Streaks">🔥</div>
  <div class="pill" title="Calc">🧮</div>
</div>
<div class="saffin-focus">'''+ glass_card("Current Focus", f"<div style='color:#9AA6B2;font-size:13px'>{focus_text}</div>") + '''</div>
'''
st.markdown(dock_html, unsafe_allow_html=True)

# Tab navigation buttons (hidden but functional)
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6 = st.columns(6)
with col_nav1:
    if st.button("📊", key="nav_dash", use_container_width=True):
        st.session_state.current_tab = "dashboard"
with col_nav2:
    if st.button("📝", key="nav_log", use_container_width=True):
        st.session_state.current_tab = "log"
with col_nav3:
    if st.button("💡", key="nav_ideas", use_container_width=True):
        st.session_state.current_tab = "ideas"
with col_nav4:
    if st.button("📅", key="nav_review", use_container_width=True):
        st.session_state.current_tab = "review"
with col_nav5:
    if st.button("🔥", key="nav_streaks", use_container_width=True):
        st.session_state.current_tab = "streaks"
with col_nav6:
    if st.button("🧮", key="nav_calc", use_container_width=True):
        st.session_state.current_tab = "calc"

st.markdown("<style>.stButton > button { opacity: 0; width: 0; height: 0; padding: 0; margin: 0; position: absolute; } </style>", unsafe_allow_html=True)

# Render content based on current tab
if st.session_state.current_tab == "dashboard":
    status = get_status()
    col1, col2 = st.columns(2)
    col1.markdown(metric_card("Primary sessions this week", f"{status['primary_sessions']} / 5", accent="violet"), unsafe_allow_html=True)
    col2.markdown(metric_card("Secondary sessions this week", f"{status['secondary_sessions']} / 3", accent="sky"), unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    col3.markdown(metric_card("Unscored ideas", status["pending_ideas"], accent="violet"), unsafe_allow_html=True)
    col4.markdown(metric_card("Ready to score (48h+)", status["ready_ideas"], accent="sky"), unsafe_allow_html=True)

    if status["today"].weekday() == 6:
        st.info("🔔 It's Sunday — time for your weekly review! See the 'Weekly Review' tab.")

    st.divider()
    st.subheader("🔥 Streak summary")
    st.markdown(streaks_mod.streaks_summary())

elif st.session_state.current_tab == "log":
    st.markdown(glass_card("Log Session", "<div class='saffin-sub'>Record your daily work and track progress.</div>"), unsafe_allow_html=True)
    with st.form("log_form", clear_on_submit=True):
        log_date = st.date_input("Date", value=date.today())
        col1, col2 = st.columns(2)
        with col1:
            primary = st.number_input("Primary minutes", min_value=0, step=5, value=0)
        with col2:
            secondary = st.number_input("Secondary minutes", min_value=0, step=5, value=0)
        notes = st.text_area("Notes", placeholder="What did you work on?")
        
        col_mood, col_energy = st.columns(2)
        with col_mood:
            mood = st.slider("Mood (1=poor, 5=great)", 1, 5, 3)
        with col_energy:
            energy = st.slider("Energy (1=exhausted, 5=peak)", 1, 5, 3)
        
        submitted = st.form_submit_button("Save entry")

        if submitted:
            file_exists = os.path.isfile(JOURNAL_CSV)
            os.makedirs(os.path.dirname(JOURNAL_CSV), exist_ok=True)
            with open(JOURNAL_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["date", "primary_minutes", "secondary_minutes", "mood", "energy", "notes"])
                writer.writerow([log_date.isoformat(), int(primary), int(secondary), mood, energy, notes])
            st.success(
                f"Logged {log_date.isoformat()} — Primary: {int(primary)}m, Secondary: {int(secondary)}m | Mood: {mood}/5, Energy: {energy}/5"
            )

    st.divider()
    st.markdown(glass_card("Recent Entries", ""), unsafe_allow_html=True)
    rows = load_journal_rows()
    if rows:
        st.dataframe(rows[-10:][::-1], use_container_width=True, hide_index=True)
    else:
        st.caption("No journal entries yet.")

elif st.session_state.current_tab == "ideas":
    st.markdown(glass_card("Idea Vault — Add a new idea", "<div class='saffin-sub'>Capture, cool-off, and score ideas with the Decision Framework.</div>"), unsafe_allow_html=True)
    with st.form("idea_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_area("Description")
        idea_submitted = st.form_submit_button("Add idea")

        if idea_submitted:
            if not title.strip():
                st.error("Please enter a title.")
            else:
                date_added = datetime.now().strftime("%Y-%m-%d %H:%M")
                entry = f"""
### {title}
- Date added: {date_added}
- Description: {description or ""}
- Impact (1-5): 
- Alignment (1-5): 
- Effort (1-5): 
- Risk (1-5): 
- Opportunity Cost (1-5): 
- Score: 
- Action: [Vault / Act / Drop]
"""
                with open(IDEA_VAULT, "a", encoding="utf-8") as f:
                    f.write(entry)
                st.success(f"Idea '{title}' added (eligible for scoring after 48 hours).")

    st.divider()
    st.markdown(glass_card("Score Eligible Ideas", "<div class='saffin-sub'>Review and rate ideas that have cooled off for 48+ hours.</div>"), unsafe_allow_html=True)
    ideas = get_ideas()
    eligible_ideas = [i for i in ideas if i["eligible"]]

    if not eligible_ideas:
        st.caption("No ideas are ready for scoring right now.")
    else:
        with open(IDEA_VAULT, "r", encoding="utf-8") as f:
            current_content = f.read()

        for idx, idea in enumerate(eligible_ideas):
            with st.expander(f"💡 {idea['title']} (added {idea['date_added']})"):
                st.write(idea["description"])
                impact = st.slider("Impact", 1, 5, 3, key=f"impact_{idx}")
                alignment = st.slider("Alignment", 1, 5, 3, key=f"alignment_{idx}")
                effort = st.slider("Effort", 1, 5, 3, key=f"effort_{idx}")
                risk = st.slider("Risk", 1, 5, 3, key=f"risk_{idx}")
                opp_cost = st.slider("Opportunity Cost", 1, 5, 3, key=f"opp_{idx}")

                if st.button("Save score", key=f"save_{idx}"):
                    score, interpretation = save_idea_score(
                        current_content, idea["match"], impact, alignment, effort, risk, opp_cost
                    )
                    st.success(f"Score: {score} → {interpretation}")
                    st.rerun()

    st.divider()
    st.markdown(glass_card("All Ideas in Vault", ""), unsafe_allow_html=True)
    if ideas:
        for idea in ideas:
            status_label = "✅ Scored" if idea["scored"] else ("⏳ Pending (eligible)" if idea["eligible"] else "🕒 Pending (cooling off)")
            st.markdown(f"**{idea['title']}** — {status_label}")
            if idea["scored"]:
                st.caption(f"Score: {idea['score']} | Action: {idea['action']}")
    else:
        st.caption("No ideas in the vault yet.")

elif st.session_state.current_tab == "review":
    st.markdown(glass_card("Generate Weekly Review", "<div class='saffin-sub'>Create a structured review of this week's progress.</div>"), unsafe_allow_html=True)
    force = st.checkbox("Overwrite if this week's review already exists")
    if st.button("Generate review"):
        content, filename, result = generate_review(force=force)
        if result == "exists":
            st.warning(f"{os.path.basename(filename)} already exists. Check the box above to overwrite.")
        else:
            st.success(f"Created {os.path.basename(filename)}")
            st.markdown(content)

    st.divider()
    st.markdown(glass_card("Past Reviews", ""), unsafe_allow_html=True)
    if os.path.isdir(WEEKLY_DIR):
        files = sorted(
            f for f in os.listdir(WEEKLY_DIR)
            if f.endswith(".md") and f != "TEMPLATE.md"
        )
        if files:
            selected = st.selectbox("View a past review", files[::-1])
            if selected:
                with open(os.path.join(WEEKLY_DIR, selected), "r", encoding="utf-8") as f:
                    st.markdown(f.read())
        else:
            st.caption("No weekly reviews generated yet.")

elif st.session_state.current_tab == "streaks":
    st.markdown(glass_card("Streaks — Progress & Goals", "<div class='saffin-sub'>Track your streaks, set goals, and view your heatmap.</div>"), unsafe_allow_html=True)
    stats = streaks_mod.calculate_streaks()
    col1, col2, col3 = st.columns(3)
    col1.markdown(metric_card("Current streak", f"{stats['current_streak']} day(s)", accent="violet"), unsafe_allow_html=True)
    col2.markdown(metric_card("Longest streak", f"{stats['longest_streak']} day(s)", accent="sky"), unsafe_allow_html=True)
    col3.markdown(metric_card("Total days logged", stats["total_days"], accent="violet"), unsafe_allow_html=True)
    st.markdown(f"<div class='card' style='padding:8px;text-align:center;color:#9AA6B2;font-size:13px'>Last logged: {stats['last_logged'] or 'never'}</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown(glass_card("Set a Streak Goal", ""), unsafe_allow_html=True)
    current_goal = streaks_mod.get_streak_goal()
    new_goal = st.number_input(
        "Days", min_value=1, value=current_goal or 7, step=1
    )
    if st.button("Save goal"):
        msg = streaks_mod.set_streak_goal(int(new_goal))
        st.success(msg)
        st.rerun()

    if current_goal:
        st.markdown(streaks_mod.progress_toward_goal())

    st.divider()
    st.markdown(glass_card("Heatmap (last 12 weeks)", ""), unsafe_allow_html=True)
    st.code(streaks_mod.generate_heatmap(weeks=12), language=None)

elif st.session_state.current_tab == "calc":
    st.markdown(glass_card("Decision Framework", "<div class='saffin-sub'>Score = Impact + Alignment + Opportunity Cost − Effort − Risk</div>"), unsafe_allow_html=True)

    st.markdown(glass_card("Score the Decision", ""), unsafe_allow_html=True)
    impact = st.slider("Impact", 1, 5, 3, key="calc_impact")
    alignment = st.slider("Alignment", 1, 5, 3, key="calc_alignment")
    effort = st.slider("Effort", 1, 5, 3, key="calc_effort")
    risk = st.slider("Risk", 1, 5, 3, key="calc_risk")
    opp_cost = st.slider("Opportunity Cost", 1, 5, 3, key="calc_opp")

    score = compute(impact, alignment, effort, risk, opp_cost)
    decision = interpret(score)

    st.divider()
    st.markdown(glass_card("Result", ""), unsafe_allow_html=True)
    col_score, col_decision = st.columns(2)
    col_score.markdown(metric_card("Score", score, accent="violet"), unsafe_allow_html=True)
    col_decision.markdown(metric_card("Decision", decision, accent="sky"), unsafe_allow_html=True)
    if decision == "Act":
        st.success("✓ ≥ 15 → Act now")
    elif decision == "Vault":
        st.info("◆ 5–14 → Vault (revisit next quarter)")
    else:
        st.warning("✕ < 5 → Drop")
