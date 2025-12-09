import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Calibration Practice", layout="centered")

st.title("☑️ Belief Calibration - Inspired by The Scout Mindset")

# st.markdown(
#     """
# This app lets you practice **probability calibration** in the sense used in Julia Galef's *The Scout Mindset*.

# 1. Answer a series of **binary** questions.
# 2. For each one, give a confidence level (55%, 65%, 75%, 85%, or 95%).
# 3. The app will show how often you're actually correct at each confidence level,
#    and compare that to perfect calibration.

# 👉 For the original question set, see Julia Galef’s calibration practice online,
# and copy the questions/answers into the data structure below.
# """
# )

# st.markdown("---")

# ------------------------------------------------------------------
# 1. DEFINE YOUR QUESTIONS HERE
# ------------------------------------------------------------------
# You can either:
#   - Edit the list below directly, OR
#   - Load from a CSV/JSON file with the same columns.
#
# Each question should have:
#   - id:        an integer (1..N)
#   - round:     a round/group label (e.g. "Animals", "History", etc.)
#   - prompt:    the question text shown to the user
#   - qtype:     "tf" (true/false), "either" (two named options)
#   - option_1:  first option text  (for tf, usually "True")
#   - option_2:  second option text (for tf, usually "False")
#   - correct:   1 if option_1 is correct, 2 if option_2 is correct
#
# Below are a few **example** questions. Replace/extend them with the
# full set you want to use.
# ------------------------------------------------------------------

EXAMPLE_QUESTIONS = [
    {
        "id": 1,
        "round": "Round 1 – Example T/F",
        "prompt": "The blue whale is the largest animal species on Earth.",
        "qtype": "tf",
        "option_1": "True",  # correct
        "option_2": "False",
        "correct": 1,
    },
    {
        "id": 2,
        "round": "Round 1 – Example T/F",
        "prompt": "Polar bears naturally live in Antarctica.",
        "qtype": "tf",
        "option_1": "True",
        "option_2": "False",  # correct
        "correct": 2,
    },
    {
        "id": 3,
        "round": "Round 2 – Example history",
        "prompt": "Who was born first?",
        "qtype": "either",
        "option_1": "Leonardo da Vinci",
        "option_2": "Albert Einstein",
        "correct": 1,  # Leonardo
    },
    {
        "id": 4,
        "round": "Round 3 – Example population",
        "prompt": "Which country had more people in 2019?",
        "qtype": "either",
        "option_1": "Brazil",
        "option_2": "Norway",
        "correct": 1,
    },
]

# If you prefer to keep questions outside the code, you can instead do something like:
# questions_df = pd.read_csv("questions.csv")
# and then convert to a list of dicts.
questions = EXAMPLE_QUESTIONS

questions = pd.read_csv("questions.csv", sep=",").to_dict("records")

# ------------------------------------------------------------------
# 2. INPUT FORM (RADIO BUTTONS, NO SKIP, NO PRESELECTION)
# ------------------------------------------------------------------

# st.header("Questions")

st.markdown(
    """
For each question:

- Choose **one answer**.
- Choose how sure you are: 55%, 65%, 75%, 85%, or 95%.

It is *not* important to be correct; the goal is to give good estimates of your confidence.

You may leave questions unanswered but more answers will yield more insights.
"""
)

CONFIDENCE_LEVELS = [55, 65, 75, 85, 95]

rounds = {}
for q in questions:
    rounds.setdefault(q["round"], []).append(q)

for round_name, qs in rounds.items():
    with st.expander(round_name, expanded=False):
        for q in qs:
            st.markdown(f"**Q{q['id']}. {q['prompt']}**")

            # -----------------------------
            # ANSWER RADIO (NO DEFAULT)
            # -----------------------------
            st.radio(
                "Your answer:",
                [q["option_1"], q["option_2"]],
                key=f"ans_{q['id']}",
                index=None,  # ✅ nothing selected initially
            )

            # -----------------------------
            # CONFIDENCE RADIO (NO DEFAULT)
            # -----------------------------
            st.radio(
                "Your confidence:",
                [f"{c}%" for c in CONFIDENCE_LEVELS],
                key=f"conf_{q['id']}",
                index=None,  # ✅ nothing selected initially
                horizontal=True,
            )

            st.markdown("---")

st.markdown("### When you’re ready, score your calibration:")
score_button = st.button("📊 Score my calibration")


# ------------------------------------------------------------------
# 3. SCORING LOGIC
# ------------------------------------------------------------------


def collect_responses():
    """Collect user responses from session_state into a DataFrame."""
    rows = []
    for q in questions:
        ans = st.session_state.get(f"ans_{q['id']}")
        conf_str = st.session_state.get(f"conf_{q['id']}")

        if not ans or ans == "?" or not conf_str or conf_str == "?":
            continue  # skip unanswered

        # Parse confidence: "75%" -> 75
        conf_percent = int(conf_str.rstrip("%"))

        # Map correct option to the actual option text
        correct_option_text = q["option_1"] if q["correct"] == 1 else q["option_2"]
        is_correct = ans == correct_option_text

        rows.append(
            {
                "id": q["id"],
                "round": q["round"],
                "prompt": q["prompt"],
                "selected_answer": ans,
                "correct_answer": correct_option_text,
                "is_correct": is_correct,
                "confidence_percent": conf_percent,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "id",
                "round",
                "prompt",
                "selected_answer",
                "correct_answer",
                "is_correct",
                "confidence_percent",
            ]
        )

    return pd.DataFrame(rows)


def compute_calibration(df: pd.DataFrame) -> pd.DataFrame:
    """Compute calibration stats per confidence level."""
    if df.empty:
        return df

    grouped = (
        df.groupby("confidence_percent")["is_correct"]
        .agg(["size", "sum"])
        .rename(columns={"size": "n_questions", "sum": "n_correct"})
        .reset_index()
    )

    grouped["percent_correct"] = grouped["n_correct"] / grouped["n_questions"] * 100
    grouped["stated_confidence"] = grouped["confidence_percent"]

    # Brier score-like summary and overall accuracy
    df = df.copy()
    df["conf_prob"] = df["confidence_percent"] / 100.0
    df["outcome"] = df["is_correct"].astype(int)
    brier = float(((df["conf_prob"] - df["outcome"]) ** 2).mean())
    accuracy = float(df["is_correct"].mean()) if len(df) > 0 else np.nan

    return grouped, brier, accuracy, len(df)


if score_button:
    responses_df = collect_responses()

    if len(responses_df) < 1:
        st.warning("You need to answer at least one questions.")
    else:
        calib_df, brier_score, accuracy, n_used = compute_calibration(responses_df)

        st.subheader("Summary")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions scored", n_used)
        with col2:
            st.metric("Overall accuracy", f"{accuracy * 100:.1f}%")
        with col3:
            st.metric("Brier score (lower is better)", f"{brier_score:.3f}")

        st.markdown("#### Calibration by confidence level")

        # Nice, readable table
        display_df = calib_df.copy()
        display_df["stated_confidence"] = display_df["stated_confidence"].astype(str) + "%"
        display_df["percent_correct"] = display_df["percent_correct"].map(lambda x: f"{x:.1f}%")

        st.dataframe(
            display_df[
                [
                    "stated_confidence",
                    "n_questions",
                    "n_correct",
                    "percent_correct",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )

        # ------------------------------------------------------------------
        # 4. CALIBRATION CHART
        # ------------------------------------------------------------------

        st.markdown("#### Calibration chart")

        chart_df = calib_df.copy()
        chart_df["actual_percent_correct"] = chart_df["percent_correct"]

        perfect_df = pd.DataFrame(
            {
                "stated_confidence": CONFIDENCE_LEVELS,
                "perfect_line": CONFIDENCE_LEVELS,
            }
        )

        user_line = (
            alt.Chart(chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "stated_confidence:Q",
                    title="Stated confidence (%)",
                    scale=alt.Scale(domain=[50, 100]),
                ),
                y=alt.Y(
                    "actual_percent_correct:Q",
                    title="Actual % correct at this confidence",
                    scale=alt.Scale(domain=[50, 100]),
                ),
                tooltip=[
                    alt.Tooltip("stated_confidence:Q", title="Stated confidence"),
                    alt.Tooltip("actual_percent_correct:Q", title="Actual % correct", format=".1f"),
                    alt.Tooltip("n_questions:Q", title="# of questions"),
                ],
            )
        )

        perfect_line = (
            alt.Chart(perfect_df)
            .mark_line(strokeDash=[4, 4])
            .encode(
                x="stated_confidence:Q",
                y=alt.Y("perfect_line:Q").scale(
                    domain=[min(min(CONFIDENCE_LEVELS), min(chart_df.percent_correct)), 100]
                ),
            )
        )

        st.altair_chart(user_line + perfect_line, use_container_width=True)

        st.markdown(
            """
- The **dashed line** shows *perfect calibration*: if you say “75% sure”,
  you’re right 75% of the time.
- The **solid line** shows your actual performance at each confidence level.

If your points are consistently **above** the dashed line, you’re *underconfident*.
If they’re consistently **below**, you’re *overconfident*.
"""
        )

# ------------------------------------------------------------------
# 5. OPTIONAL: SHOW RAW RESPONSES (DEBUG / LEARNING)
# ------------------------------------------------------------------

with st.expander("Show raw responses (optional)"):
    resp_debug = collect_responses()
    if resp_debug.empty:
        st.write("No responses yet.")
    else:
        st.dataframe(resp_debug, use_container_width=True)
