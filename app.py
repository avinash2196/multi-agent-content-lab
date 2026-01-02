import os
import uuid

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").strip()
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "").strip()


def call_backend(query: str, session_id: str, generate_images: bool, generate_alt_text: bool, generate_blog: bool, generate_linkedin: bool, linkedin_with_images: bool):
    payload = {
        "query": query,
        "session_id": session_id,
        "context": {},
        "generate_images": generate_images,
        "generate_alt_text": generate_alt_text,
        "generate_blog": generate_blog,
        "generate_linkedin": generate_linkedin,
        "linkedin_with_images": linkedin_with_images,
    }
    headers = {"Content-Type": "application/json"}
    if BACKEND_API_KEY:
        headers["x-api-key"] = BACKEND_API_KEY

    resp = requests.post(f"{BACKEND_URL}/run", json=payload, headers=headers, timeout=180)
    resp.raise_for_status()
    return resp.json()


st.set_page_config(page_title="ContentAlchemy", layout="wide")
st.title("ContentAlchemy – Multi-Agent Content Studio")

st.caption(f"Backend: {BACKEND_URL}")

query = st.text_area(
    "Describe what you need",
    height=160,
    placeholder="E.g., Create a research-backed blog + LinkedIn post about AI in healthcare, include an image",
)

col1, col2 = st.columns(2)
with col1:
    run_button = st.button("Run workflow", key="run_btn")
with col2:
    session_id = st.text_input("Session ID", value=str(uuid.uuid4()))

st.divider()

col3, col4, col5 = st.columns(3)
with col3:
    generate_blog = st.checkbox("Generate Blog", value=True)
with col4:
    generate_linkedin = st.checkbox("Generate LinkedIn", value=True)
with col5:
    generate_images = st.checkbox("Generate Images", value=True)

generate_alt_text = st.checkbox("Alt Text for Images", value=True)

if run_button and query.strip():
    with st.spinner("Running agents via backend..."):
        try:
            # Automatically embed images in LinkedIn when both are generated
            linkedin_with_images = generate_linkedin and generate_images
            result = call_backend(
                query.strip(), 
                session_id.strip(), 
                generate_images, 
                generate_alt_text,
                generate_blog,
                generate_linkedin,
                linkedin_with_images
            )
            st.success("Completed ✓")

            # Show research results
            research = result.get("research_results") or {}
            if research:
                st.subheader("📊 Research Findings")
                summary = research.get("summary", "")
                if summary:
                    st.write(summary)
                key_points = research.get("key_points", [])
                if key_points:
                    st.write("**Key Points:**")
                    for kp in key_points[:5]:
                        st.write(f"- {kp}")
                sources = research.get("sources", [])
                if sources:
                    with st.expander(f"Sources ({len(sources)})"):
                        for src in sources[:10]:
                            st.write(f"- [{src.get('title', 'Link')}]({src.get('link', '#')})")

            # Show blog if generated
            blog = result.get("blog_content")
            if generate_blog and blog:
                st.subheader("📝 Blog Article")
                st.markdown(blog)

            # Show LinkedIn if generated
            linkedin = result.get("linkedin_content")
            if generate_linkedin and linkedin:
                st.subheader("💼 LinkedIn Post")
                st.markdown(linkedin)

            # Show images if generated
            images = result.get("image_urls", [])
            if generate_images and images:
                st.subheader("🖼️ Generated Images")
                for img_url in images:
                    st.image(img_url, width="stretch")

            # Show errors if any
            errors = result.get("errors", [])
            if errors:
                with st.expander("⚠️ Warnings/Errors"):
                    for err in errors:
                        st.warning(err)

        except requests.exceptions.ConnectionError:
            st.error(f"❌ Backend unavailable at {BACKEND_URL}")
        except Exception as e:
            st.error(f"❌ Error: {e}")
