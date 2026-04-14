import math
from typing import Dict, List, Tuple

import pandas as pd
import plotly.graph_objects as go
from textwrap import dedent
import streamlit as st

from PIL import Image
logo = Image.open("logo.png")
logo2 = Image.open("logo2.png")

st.set_page_config(page_title="ALIGN AI Adoption Diagnostic", page_icon="📊", layout="wide")

# -----------------------------
# App content and configuration
# -----------------------------
DIMENSIONS = {
    "Assess": [
        "We have access to reliable, well-organized data for decision-making.",
        "Our organization has the technical infrastructure to support AI tools.",
        "Employees are familiar with basic data analysis or AI concepts.",
        "We have previously experimented with AI or automation tools.",
        "Data is accessible across teams (not siloed).",
    ],
    "Link": [
        "We have clearly defined business problems that AI could help solve.",
        "AI initiatives are directly tied to measurable business outcomes.",
        "Leadership understands how AI can impact our strategy.",
        "We prioritize AI projects based on business value, not hype.",
        "There is alignment between technical teams and business stakeholders.",
    ],
    "Implement": [
        "We have the skills (internal or external) to implement AI solutions.",
        "We can move from idea to pilot to implementation efficiently.",
        "We have processes for testing and validating AI solutions.",
        "Resources (time, budget, personnel) are allocated for AI initiatives.",
        "We are comfortable integrating new tools into existing workflows.",
    ],
    "Guide": [
        "We consider ethical implications when implementing AI systems.",
        "We have guidelines or policies for AI use.",
        "We evaluate risks such as bias, privacy, and misuse.",
        "Humans remain involved in critical decision-making processes.",
        "There is accountability for AI-driven decisions.",
    ],
    "Normalize": [
        "Employees are open to using AI tools in their work.",
        "Leadership encourages experimentation with new technologies.",
        "Training or support is available for adopting AI tools.",
        "AI is seen as an opportunity rather than a threat.",
        "Successful use of AI is shared and promoted internally.",
    ],
}

LIKERT_OPTIONS = {
    1: "1 — Strongly Disagree",
    2: "2 — Disagree",
    3: "3 — Neutral / Unsure",
    4: "4 — Agree",
    5: "5 — Strongly Agree",
}

CATEGORY_DESCRIPTIONS = {
    "Assess": "Current capability: data, infrastructure, and baseline AI readiness.",
    "Link": "Business alignment: connecting AI to real organizational value.",
    "Implement": "Execution readiness: ability to move from idea to adoption.",
    "Guide": "Governance and human-centered AI: ethics, oversight, and accountability.",
    "Normalize": "Culture and adoption: trust, training, and long-term use.",
}


# -----------------------------
# Helper functions
# -----------------------------
def maturity_level(score: float):
    if score <= 2.0:
        return "Ad Hoc"
    if score <= 3.0:
        return "Emerging"
    if score <= 4.0:
        return "Operational"
    return "Strategic"

def status_flag(score: float):
    if score < 3.0:
        return "Priority Area"
    if score <= 4.0:
        return "Developing"
    return "Strength"

def category_recommendation(category: str, score: float):
    recommendations = {
        "Assess": {
            "low": "Strengthen data quality, access, and foundational AI literacy before pursuing more advanced initiatives.",
            "mid": "Build on existing capability by improving cross-team data access and expanding small-scale experimentation.",
            "high": "Leverage strong foundations to support more ambitious, strategically aligned AI initiatives.",
        },
        "Link": {
            "low": "Clarify the business problems AI should address and connect potential projects to measurable outcomes.",
            "mid": "Tighten the link between AI efforts and business goals by prioritizing initiatives with clear value.",
            "high": "Use strong strategic alignment to create a disciplined portfolio of high-impact AI opportunities.",
        },
        "Implement": {
            "low": "Focus on execution capability through pilot design, validation processes, and access to needed talent or partners.",
            "mid": "Improve the transition from idea to implementation by standardizing pilots, testing, and integration workflows.",
            "high": "Capitalize on strong execution readiness by scaling successful pilots into repeatable operational practice.",
        },
        "Guide": {
            "low": "Establish governance, accountability, and human oversight before scaling AI use cases.",
            "mid": "Formalize existing ethical practices into clearer policies, review mechanisms, and decision rights.",
            "high": "Use strong governance as a differentiator by embedding responsible AI practices into every stage of adoption.",
        },
        "Normalize": {
            "low": "Address cultural resistance with communication, training, and visible examples of responsible AI success.",
            "mid": "Increase adoption by expanding training and sharing internal wins more consistently.",
            "high": "Use cultural momentum to broaden adoption and support more advanced, organization-wide AI use.",
        },
    }

    tier = "low" if score < 3.0 else "mid" if score <= 4.0 else "high"
    return recommendations[category][tier]

def build_results_dataframe(scores: Dict[str, float]):
    rows = []
    for category, score in scores.items():
        rows.append(
            {
                "Category": category,
                "Score": round(score, 2),
                "Status": status_flag(score),
                "Recommendation": category_recommendation(category, score),
            }
        )
    return pd.DataFrame(rows)

def build_radar_chart(scores: Dict[str, float]):
    categories = list(scores.keys())
    values = list(scores.values())

    # Close the loop for radar chart
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                name="ALIGN Score",
            )
        ]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        height=500,
    )
    return fig


def overall_interpretation(scores: Dict[str, float]):
    insights = []

    if scores["Assess"] >= 3.5 and scores["Link"] < 3.0:
        insights.append("The organization appears to have baseline capability, but AI efforts are not yet clearly tied to business strategy.")
    if scores["Link"] >= 3.5 and scores["Implement"] < 3.0:
        insights.append("The organization may understand where AI could create value, but execution readiness is limited.")
    if scores["Guide"] < 3.0:
        insights.append("Governance and responsible AI practices are underdeveloped, which increases risk as adoption expands.")
    if scores["Normalize"] < 3.0:
        insights.append("Cultural adoption may be a barrier. Training, communication, and internal trust-building should come early.")
    if scores["Implement"] >= 4.0 and scores["Link"] >= 4.0:
        insights.append("The organization shows signs of being able to execute strategically meaningful AI initiatives.")
    if not insights:
        insights.append("The organization shows a mixed profile. The next step is to strengthen weaker dimensions while using current strengths to guide practical pilots.")

    return insights


def top_strengths_and_gaps(scores: Dict[str, float]):
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    strengths = ordered[:2]
    gaps = sorted(scores.items(), key=lambda x: x[1])[:2]
    return strengths, gaps


def make_download_dataframe(responses: Dict[str, int], category_scores: Dict[str, float], org_name: str, respondent: str):
    rows = []
    for question_key, value in responses.items():
        rows.append({"Item": question_key, "Response": value})
    for category, score in category_scores.items():
        rows.append({"Item": f"{category} Score", "Response": round(score, 2)})

    overall = sum(category_scores.values()) / len(category_scores)
    rows.append({"Item": "Overall Score", "Response": round(overall, 2)})
    rows.append({"Item": "Maturity Level", "Response": maturity_level(overall)})
    rows.append({"Item": "Organization", "Response": org_name})
    rows.append({"Item": "Respondent", "Response": respondent})
    return pd.DataFrame(rows)

# -----------------------------
# Sidebar
# -----------------------------
def build_executive_summary(org_name: str, respondent: str, category_scores: Dict[str, float]):
    overall = sum(category_scores.values()) / len(category_scores)
    level = maturity_level(overall)
    strengths, gaps = top_strengths_and_gaps(category_scores)
    insights = overall_interpretation(category_scores)

    org_label = org_name.strip() if org_name.strip() else "This organization"
    respondent_label = respondent.strip() if respondent.strip() else "Not provided"

    strengths_text = ", ".join([f"{category} ({score:.2f})" for category, score in strengths])
    gaps_text = ", ".join([f"{category} ({score:.2f})" for category, score in gaps])

    short_term = []
    mid_term = []
    long_term = []

    for category, score in sorted(category_scores.items(), key=lambda x: x[1]):
        rec = category_recommendation(category, score)
        if score < 3.0:
            short_term.append(f"{category}: {rec}")
        elif score <= 4.0:
            mid_term.append(f"{category}: {rec}")
        else:
            long_term.append(f"{category}: {rec}")

    if not short_term:
        short_term.append("No critical weaknesses were identified. Focus on maintaining current strengths while piloting strategically aligned AI initiatives.")
    if not mid_term:
        mid_term.append("Continue refining adoption practices through structured pilots, training, and cross-functional alignment.")
    if not long_term:
        long_term.append("As AI capability matures, formalize successful practices into repeatable strategy, governance, and scaling processes.")

    summary = f"""

# ALIGN Executive Summary

**Organization:** {org_label}

**Respondent:** {respondent_label}

## Overall Assessment
{org_label} received an overall ALIGN score of **{overall:.2f} / 5.00**, placing it at the **{level}** stage of AI adoption readiness.

This result suggests that the organization's current readiness for AI is best understood through five dimensions: Assess, Link, Implement, Guide, and Normalize. The strongest current dimensions are **{strengths_text}**, while the most important improvement areas are **{gaps_text}**.

## Key Interpretation
"""
    for insight in insights:
        summary += f"- {insight}"

    summary += """

## Recommended Actions

### Short-Term Priorities (0–3 months)
"""
    for item in short_term[:3]:
        summary += f"- {item}"

    summary += """

### Mid-Term Priorities (3–6 months)
"""
    for item in mid_term[:3]:
        summary += f"- {item}"

    summary += """

### Longer-Term Opportunities (6–12 months)
"""
    for item in long_term[:3]:
        summary += f"- {item}"

    summary += dedent("""

## Suggested Next Step
Use the ALIGN results to identify one or two business-relevant AI pilot opportunities that match current capability, strategic priorities, and governance readiness. This helps ensure that experimentation remains practical, responsible, and aligned with organizational goals.
""")

    return summary.strip()


st.sidebar.image("logo.png")
st.sidebar.title("ALIGN Diagnostic")
st.sidebar.markdown(
    "This tool evaluates AI adoption readiness across five dimensions: "
    "**Assess, Link, Implement, Guide, and Normalize**."
)

with st.sidebar.expander("Scoring scale", expanded=False):
    for key, value in LIKERT_OPTIONS.items():
        st.write(value)

with st.sidebar.expander("Maturity levels", expanded=False):
    st.write("**Ad Hoc**: 1.0–2.0")
    st.write("**Emerging**: 2.1–3.0")
    st.write("**Operational**: 3.1–4.0")
    st.write("**Strategic**: 4.1–5.0")

col1, col2 = st.columns([1, 4])

with col1:
    st.image("logo2.png")

with col2:
    st.title("ALIGN AI Adoption Diagnostic")
    st.caption("A human-centered AI readiness assessment for teaching, advising, and consulting.")

# -----------------------------
# Respondent information
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    org_name = st.text_input("Organization name", placeholder="Example: Acme Manufacturing")
with col2:
    respondent = st.text_input("Respondent name or role", placeholder="Example: Director of Operations")

st.markdown("---")

"""QUESTIONNAIRE"""
responses: Dict[str, int] = {}
question_number = 1

for category, questions in DIMENSIONS.items():
    with st.expander(f"{category}", expanded=True):
        st.write(CATEGORY_DESCRIPTIONS[category])
        for q in questions:
            key = f"Q{question_number}: {q}"
            responses[key] = st.radio(
                label=f"**{question_number}.** {q}",
                options=list(LIKERT_OPTIONS.keys()),
                format_func=lambda x: LIKERT_OPTIONS[x],
                horizontal=True,
                key=f"radio_{question_number}",
            )
            question_number += 1

st.markdown("---")

# -----------------------------
# Scoring and output
# -----------------------------
if st.button("Generate Results", type="primary"):
    category_scores: Dict[str, float] = {}

    idx = 1
    for category, questions in DIMENSIONS.items():
        scores = []
        for _ in questions:
            q_key = [k for k in responses.keys() if k.startswith(f"Q{idx}:")][0]
            scores.append(responses[q_key])
            idx += 1
        category_scores[category] = sum(scores) / len(scores)

    overall_score = sum(category_scores.values()) / len(category_scores)
    overall_level = maturity_level(overall_score)
    strengths, gaps = top_strengths_and_gaps(category_scores)
    results_df = build_results_dataframe(category_scores)
    insights = overall_interpretation(category_scores)

    st.subheader("Results Overview")
    k1, k2 = st.columns(2)
    with k1:
        st.metric("Overall Score", f"{overall_score:.2f} / 5.00")
    with k2:
        st.metric("Maturity Level", overall_level)

    st.subheader("ALIGN Profile")
    c1, c2 = st.columns([1.1, 1])

    with c1:
        st.dataframe(results_df[["Category", "Score", "Status"]], use_container_width=True, hide_index=True)

    with c2:
        fig = build_radar_chart(category_scores)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Interpretation")
    for insight in insights:
        st.write(f"- {insight}")

    st.subheader("Top Strengths")
    for category, score in strengths:
        st.write(f"- **{category}** ({score:.2f}): {category_recommendation(category, score)}")

    st.subheader("Priority Areas")
    for category, score in gaps:
        st.write(f"- **{category}** ({score:.2f}): {category_recommendation(category, score)}")

    st.subheader("Recommendations by Dimension")
    for category, score in category_scores.items():
        st.markdown(f"**{category}** — {category_recommendation(category, score)}")

    st.subheader("Executive Summary")
    executive_summary = build_executive_summary(org_name, respondent, category_scores)
    st.markdown(executive_summary)

    st.subheader("Download Results")
    download_df = make_download_dataframe(responses, category_scores, org_name, respondent)
    csv_bytes = download_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV Report",
        data=csv_bytes,
        file_name="align_diagnostic_results.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download Executive Summary (.md)",
        data=executive_summary.encode("utf-8"),
        file_name="align_executive_summary.md",
        mime="text/markdown",
    )

else:
    st.info("Complete the questionnaire and select **Generate Results** to see the ALIGN readiness profile.")

st.markdown("---")
st.caption("Version 1.1 — Designed for classroom use, organizational assessment, and AI readiness conversations.")
