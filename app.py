import streamlit as st
import pickle
import re
import requests

# Load model
model = pickle.load(open('model.pkl', 'rb'))
tfidf = pickle.load(open('tfidf.pkl', 'rb'))

st.set_page_config(page_title="Sentiment Dashboard", page_icon="📊", layout="centered")

# -------- CSS --------
st.markdown("""
<style>
.title {text-align:center; font-size:40px; font-weight:bold;}
.result-box {padding:20px; border-radius:10px; text-align:center; font-size:22px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">📊 Text Sentiment Analysis </p>', unsafe_allow_html=True)

# -------- CLEAN FUNCTION --------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    return text


import requests

def get_reddit_posts(topic, limit=20):
    url = f"https://www.reddit.com/search.json?q={topic}&limit={limit}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return []

        data = response.json()

        posts = []
        for item in data.get("data", {}).get("children", []):
            posts.append(item["data"]["title"])

        return posts

    except Exception as e:
        return []

def analyze_posts(posts):
    results = {"Positive": 0, "Negative": 0}
    
    for post in posts:
        pred, _, _ = predict(post)   # reuse your predict() function
        
        if pred == 1:
            results["Positive"] += 1
        else:
            results["Negative"] += 1
    
    return results

# -------- PREDICT FUNCTION --------
def predict(text):
    cleaned = clean_text(text)
    vector = tfidf.transform([cleaned])
    
    pred = model.predict(vector)[0]
    prob = model.predict_proba(vector)[0]
    
    confidence = max(prob) * 100
    return pred, confidence, prob

# -------- UI INPUT --------
user_input = st.text_area("💬 Enter your text here:", height=150)

if st.button("Analyze Sentiment"):
    if user_input:

        pred, confidence, prob = predict(user_input)

        # -------- RESULT BOX --------
        if pred == 1:
            st.markdown(
                f'<div class="result-box" style="background:#d4edda; color:#155724;">😊 Positive ({confidence:.2f}%)</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="result-box" style="background:#f8d7da; color:#721c24;">😠 Negative ({confidence:.2f}%)</div>',
                unsafe_allow_html=True
            )

        # -------- EMOJI METER --------

        st.subheader("🎯 Sentiment Strength")
        st.progress(int(confidence))
        st.write(f"Confidence Level: {confidence:.2f}%")

        # -------- STATS BOX --------

        st.subheader("📌 Summary")
        st.write(f"""
        - **Predicted Sentiment:** {'Positive' if pred == 1 else 'Negative'}
        - **Confidence:** {confidence:.2f}%
        - **Model Used:** Logistic Regression + TF-IDF
       """)

        # -------- PROBABILITY CHART --------
        import plotly.graph_objects as go

        st.subheader("📊 Prediction Confidence")

        labels = ['Negative', 'Positive']
        values = prob

        fig = go.Figure(data=[
           go.Bar(x=labels, y=values)
    ])

        fig.update_layout(
           title="Confidence Distribution",
           xaxis_title="Sentiment",
           yaxis_title="Probability",
    )

        st.plotly_chart(fig)

    else:
        st.warning("⚠️ Please enter some text!")

st.markdown("---")
st.header("🌐 Live Reddit Sentiment Analysis ")

topic = st.text_input("Enter topic to analyze:")

if st.button("Analyze Reddit Sentiment"):
    if topic:
        with st.spinner("Fetching Reddit posts..."):
            posts = get_reddit_posts(topic)

        st.markdown("---")
        st.subheader("📝 Sample Reddit Posts with Sentiment")
        for post in posts[:5]:   # show top 5 posts
           pred, conf, _ = predict(post)
           if pred == 1:
             st.success(f"😊 {post} ({conf:.1f}%)")
           else:
             st.error(f"😠 {post} ({conf:.1f}%)")
        

        results = analyze_posts(posts)

        st.write("### Results:")
        total = results["Positive"] + results["Negative"]

        if total==0:
            st.error("No data available for this topic. Try another keyword.")
        else:
           pos_percent = (results["Positive"] / total) * 100
           neg_percent = (results["Negative"] / total) * 100

        st.subheader("📊 Sentiment Summary")
        col1, col2 = st.columns(2)

        with col1:
           st.metric("😊 Positive", f"{results['Positive']} ({pos_percent:.1f}%)")
        with col2:
             st.metric("😠 Negative", f"{results['Negative']} ({neg_percent:.1f}%)")
           

        # Chart
        import plotly.graph_objects as go

        labels = list(results.keys())
        values = list(results.values())

        fig = go.Figure(data=[go.Bar(x=labels, y=values)])
        st.plotly_chart(fig)

    else:
        st.warning("Enter a topic")