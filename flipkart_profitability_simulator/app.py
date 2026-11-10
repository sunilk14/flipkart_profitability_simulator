"""Flipkart: The Road to Profitability -- teaching simulation."""
import pandas as pd
import streamlit as st
from simulator import BASE_COSTS, DESCRIPTIONS, DEFAULT_RULES, evaluate
from storage import backend, save_submission, load_submissions, latest_per_group

st.set_page_config(page_title="Flipkart | Road to Profitability", page_icon="📦", layout="wide")


def secrets_dict():
    try:
        return dict(st.secrets)
    except (FileNotFoundError, OSError):
        return {}


SECRETS = secrets_dict()
RULES = {**DEFAULT_RULES}
# Faculty can change these prior to class by editing these values in simulator.py.

st.title("📦 Flipkart: The Road to Profitability")
st.caption("An illustrative MBA digital-transformation simulation; not a reproduction of Flipkart's actual financial statements.")
try:
    mode = backend(SECRETS)
except Exception as exc:
    st.error(f"Storage configuration error: {exc}")
    st.stop()

student, faculty, about = st.tabs(["🎓 Student simulation", "📊 Faculty dashboard", "ℹ️ Instructions & assumptions"])

with student:
    st.markdown("### Your management mandate")
    st.info("Flipkart earns **100** revenue units but spends **135** units. You must reduce losses *without sacrificing* revenue, customer satisfaction, future scale or access to investor capital.")
    cols = st.columns(5)
    for col, (lab, val) in zip(cols, [
        ("Revenue floor (P1)", f"{RULES['min_revenue_p1']:.0f}"),
        ("Loss ceiling (P1)", f"{RULES['max_loss_p1']:.0f}"),
        ("Satisfaction floor", f"{RULES['min_satisfaction']:.0f}/100"),
        ("Revenue floor (P2)", f"{RULES['min_revenue_p2']:.0f}"),
        ("Opening cash", f"{RULES['opening_cash']:.0f}"),
    ]):
        col.metric(lab, val)
    a,b=st.columns(2)
    with a:
        section = st.selectbox("Section", ["A", "B", "Other"])
    with b:
        group_id = st.text_input("Group ID", placeholder="e.g. 03", max_chars=30)
    st.markdown("### 1. Choose cost-reduction policies")
    st.caption("Each slider is the **% reduction in spending for that cost head** (0–50%), not % of revenue. Every cut affects operational costs and some cuts reduce future demand or satisfaction. Your results are hypothetical model outputs.")
    reductions = {}
    left, right = st.columns(2)
    for ix,(head, cost) in enumerate(BASE_COSTS.items()):
        with (left if ix%2==0 else right):
            reductions[head] = st.slider(f"{head} — baseline {cost:.0f} units", 0, 50, 0, 5, key=f"cut_{ix}", help=DESCRIPTIONS[head])
    m=evaluate(reductions, RULES)
    st.markdown("### 2. Observe the consequences")
    x=st.columns(4)
    for col, (name, val, delta) in zip(x, [
        ("P1 revenue",m["revenue_p1"], m["revenue_p1"]-100),
        ("P1 operating profit",m["profit_p1"],m["profit_p1"]+35),
        ("P2 revenue",m["revenue_p2"],m["revenue_p2"]-100),
        ("P2 operating profit",m["profit_p2"],m["profit_p2"]+35),
    ]):
        col.metric(name, f"{val:.1f}", f"{delta:+.1f} vs baseline", delta_color="normal")
    x=st.columns(4)
    x[0].metric("Customer satisfaction", f"{m['satisfaction']:.1f}/100")
    x[1].metric("Retention",f"{m['retention']:.1%}")
    x[2].metric("End-of-P2 cash",f"{m['cash_end']:.1f}")
    x[3].metric("Investor milestones",f"{m['constraints_met']}/5")
    st.markdown("#### Investor assessment")
    tests_df=pd.DataFrame([{"Milestone":name,"Result":"✅ Pass" if ok else "❌ Fail"} for name,ok in m["investor_tests"].items()])
    st.dataframe(tests_df, hide_index=True, use_container_width=True)
    if m["investor_approved"]:
        st.success("Your strategy meets all five investor conditions.")
    else:
        st.warning("Your strategy does not yet satisfy all investor milestones. You may submit it for discussion, but it will not qualify as investor-approved.")
    with st.expander("Detailed P&L and illustrative valuation"):
        pd_df=pd.DataFrame({"Cost head":list(BASE_COSTS),
            "Original cost":list(BASE_COSTS.values()),
            "Period 1 cost":[m["costs_p1"][h] for h in BASE_COSTS],
            "Period 2 cost":[m["costs_p2"][h] for h in BASE_COSTS]})
        st.dataframe(pd_df.style.format({"Original cost":"{:.1f}", "Period 1 cost":"{:.1f}","Period 2 cost":"{:.1f}"}),hide_index=True,use_container_width=True)
        st.write(f"**Illustrative valuation proxy:** {m['valuation_proxy']:.1f} (Period 2 revenue × {m['valuation_multiple']:.2f}× multiple). This is not a market valuation.")
    st.markdown("### 3. Submit your team's strategy")
    st.caption("You can resubmit; the faculty dashboard uses each group's latest submission. No personal names are needed.")
    if st.button("Submit strategy", type="primary", disabled=not group_id.strip()):
        try:
            submission_id=save_submission(SECRETS, section, group_id, reductions, m)
            st.success(f"Submission recorded. Reference: {submission_id[:8]}")
        except Exception as exc:
            st.error(f"Could not save submission. Tell your instructor. Details: {exc}")

with faculty:
    st.markdown("### Faculty dashboard")
    password=SECRETS.get("faculty_password", "")
    if not password:
        st.error("Configure faculty_password in Streamlit Secrets before using this dashboard. See README.md.")
    else:
        if not st.session_state.get("faculty_authenticated", False):
            with st.form("faculty_auth"):
                provided=st.text_input("Faculty password", type="password")
                login=st.form_submit_button("Unlock dashboard")
            if login:
                import hmac
                if hmac.compare_digest(provided, str(password)):
                    st.session_state["faculty_authenticated"]=True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            colA,colB=st.columns([1,1])
            colA.caption(f"Storage: {mode}")
            if colB.button("Log out"):
                st.session_state["faculty_authenticated"]=False
                st.rerun()
            if st.button("🔄 Refresh submissions"):
                st.rerun()
            try:
                raw=load_submissions(SECRETS)
                latest=latest_per_group(raw)
            except Exception as exc:
                st.error(f"Unable to read submissions: {exc}")
                latest=[];raw=[]
            if not latest:
                st.info("No submissions found yet.")
            else:
                st.metric("Unique groups",len(latest))
                st.caption(f"{len(raw)} total submission(s); latest per group shown below.")
                options=["All"]+sorted({str(r["section"]) for r in latest})
                chosen=st.selectbox("Filter section",options)
                filtered=[r for r in latest if chosen=="All" or r["section"]==chosen]
                data=[]
                for row in filtered:
                    m0=row["metrics"]
                    data.append({"Section":row["section"],"Group":str(row["group_id"]),
                        "Submitted UTC":row["timestamp_utc"],"P1 revenue":m0["revenue_p1"],
                        "P1 profit":m0["profit_p1"],"P2 revenue":m0["revenue_p2"],
                        "P2 profit":m0["profit_p2"],"Satisfaction":m0["satisfaction"],
                        "Retention":m0["retention"],"End cash":m0["cash_end"],
                        "Investor approved":m0["investor_approved"],
                        "Milestones met":m0["constraints_met"],
                        **{f"Cut: {k}":v for k,v in row["cuts"].items()}})
                df=pd.DataFrame(data)
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.download_button("⬇️ Download current table (CSV)",data=df.to_csv(index=False).encode("utf-8"),file_name="flipkart_group_results.csv",mime="text/csv")
                if not df.empty:
                    st.markdown("#### Revenue and profitability trade-off")
                    import altair as alt
                    chart=alt.Chart(df).mark_circle(size=130).encode(
                        x=alt.X("P1 revenue:Q",title="Period 1 revenue"),
                        y=alt.Y("P1 profit:Q",title="Period 1 operating profit"),
                        color=alt.Color("Investor approved:N"),
                        tooltip=["Section","Group","P1 revenue","P1 profit","P2 revenue","End cash"])
                    st.altair_chart(chart.interactive(),use_container_width=True)
                    st.markdown("#### Average cost reductions by head")
                    avg=pd.DataFrame([{"Cost head":key,"Average reduction (%)":sum(float(r["cuts"][key]) for r in filtered)/len(filtered)} for key in BASE_COSTS])
                    st.bar_chart(avg.set_index("Cost head"))
                st.caption("For a discussion of the revenue–profit Pareto frontier, compare non-dominated groups manually. The app does not treat a higher profit alone as a win.")

with about:
    st.markdown("""### Learning objectives
1. Costs and demand are interdependent.
2. Reducing a loss is not enough if revenue, customers, or cash viability collapse.
3. Investors can tolerate losses conditionally, when growth and value creation remain credible.
4. Retention and customer experience affect the second period.

### Accounting and modelling notes
- The exhibit is represented exactly as **revenue 100, costs 135**, including **discounts 30** as an explicit simulated cost. This is *not* a verified statutory accounting treatment.
- All elasticities, satisfaction penalties, cash, valuation multiples and funding thresholds are *illustrative teaching assumptions*, not calibrated estimates of Flipkart.
- Costs have variable and committed shares. Revenue per order is fixed at 1 in this first version; the model changes order volume rather than realised selling price. This is a deliberately simplified retailer-like model, not a true marketplace GMV/take-rate model.
- The second period is a single forward scenario, not a forecast. Negative end cash triggers a failed survival milestone.
- Investors are assessed on **five thresholds**; meeting all is a classroom success condition, not a guarantee of actual financing.
- Students may resubmit. Only their last submission per section+group is shown in the faculty dashboard.

### Suggested classroom flow
**8 min:** choose cuts → **5 min:** review investor tests → **7 min:** adjust strategy and submit → **10 min:** faculty comparative debrief.

**Discussion:** Why might a company with smaller losses have a weaker strategic position than a company with larger revenue and a credible path to improved margins?
""")
    if mode.startswith("Local"):
        st.warning("Local CSV is for testing only. Use Google Sheets for a shared cloud class; local storage on Streamlit Community Cloud may be lost on restart.")
