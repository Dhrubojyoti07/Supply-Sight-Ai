import base64
import io
import os
import glob
import time
import streamlit as st
from PIL import Image

from image_utils import (
    load_image_from_bytes,
    resize_image,
    image_to_bytes,
    load_image_from_path,
    image_feature,
)
from gemini_service import analyze_image, generate_project_report
from prompts import build_prompt
from report_generator import generate_pdf_bytes


from auth_utils import create_user, verify_user

st.set_page_config(page_title="SupplySight AI – Visual Supply Chain Intelligence", layout="wide")

st.title("SupplySight AI – Visual Supply Chain Intelligence")

# Removed custom glassmorphism CSS to restore default Streamlit styling

# Simple auth state
if 'user' not in st.session_state:
    st.session_state['user'] = None

# Sidebar auth UI (shows above page selector)
st.sidebar.markdown('<div class="glass-card">', unsafe_allow_html=True)
if st.session_state.get('user'):
    st.sidebar.markdown(f"**Signed in as:** {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['user'] = None
        st.sidebar.success("Logged out")
else:
    auth_mode = st.sidebar.selectbox("Account", ["Login", "Sign up"])
    auth_user = st.sidebar.text_input("Username", key="auth_user")
    auth_pass = st.sidebar.text_input("Password", type="password", key="auth_pass")
    if st.sidebar.button("Submit", key="auth_submit"):
        if auth_mode == "Login":
            if verify_user(auth_user, auth_pass):
                st.session_state['user'] = auth_user
                st.sidebar.success("Signed in")
            else:
                st.sidebar.error("Invalid credentials")
        else:
            # sign up
            if not auth_user or not auth_pass:
                st.sidebar.error("Choose a username and password")
            else:
                ok = create_user(auth_user, auth_pass)
                if ok:
                    st.session_state['user'] = auth_user
                    st.sidebar.success("Account created and signed in")
                else:
                    st.sidebar.error("Username already exists")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Simple navigation: Home (gallery) and Analyze (existing flow)
page = st.sidebar.radio("Page", ["Home", "Analyze"])

GALLERY_DIR = "gallery"
os.makedirs(GALLERY_DIR, exist_ok=True)


def list_gallery_images():
    exts = ["*.jpg", "*.jpeg", "*.png"]
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(GALLERY_DIR, e)))
    files = sorted(files, key=os.path.getmtime, reverse=True)
    return files


if page == "Home":
    st.header("New & Related Pictures")
    st.write("Browse recently added pictures and find related images useful for business ideation.")

    # Upload to gallery
    uploaded = st.file_uploader("Add images to gallery", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            data = f.read()
            fname = f"{int(time.time())}_{f.name}"
            path = os.path.join(GALLERY_DIR, fname)
            with open(path, "wb") as out:
                out.write(data)
        st.success("Saved to gallery. Refresh to see images.")

    gallery_files = list_gallery_images()
    if not gallery_files:
        st.info("No gallery images yet. Upload images to populate the gallery.")
    else:
        cols = st.columns(3)
        for i, fp in enumerate(gallery_files):
            col = cols[i % 3]
            try:
                img = load_image_from_path(fp)
                disp = resize_image(img, max_size=(400, 300))
                col.image(disp, caption=os.path.basename(fp))
            except Exception:
                col.write(os.path.basename(fp))

            mtime = os.path.getmtime(fp)
            if time.time() - mtime < 7 * 24 * 3600:
                col.markdown("**New**")

            # Analyze single gallery image on demand
            if col.button("Analyze for Opportunity", key=f"analyze_{i}"):
                if not st.session_state.get('user'):
                    st.warning("Please sign in to analyze images.")
                else:
                    with st.spinner("Analyzing image for business opportunities..."):
                        try:
                            img_bytes = open(fp, "rb").read()
                            res = analyze_image(img_bytes, build_prompt())
                            st.subheader("Opportunity Detection")
                            st.markdown(res.get("opportunity_detection", ""))
                            st.subheader("Startup Idea (short)")
                            st.markdown(res.get("startup_idea_markdown", ""))
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")

        # Related-image finder
        st.markdown("---")
        st.subheader("Find Related Pictures")
        sel = st.selectbox("Select image to find related pictures", options=gallery_files, format_func=lambda x: os.path.basename(x))
        if sel:
            try:
                src = load_image_from_path(sel)
                src_feat = image_feature(src)
                candidates = []
                for fp in gallery_files:
                    if fp == sel:
                        continue
                    other = load_image_from_path(fp)
                    f = image_feature(other)
                    # Euclidean distance on avg color + normalized size diff
                    dc = sum((a - b) ** 2 for a, b in zip(src_feat["avg"], f["avg"])) ** 0.5
                    ds = abs((src_feat["size"][0] * src_feat["size"][1]) - (f["size"][0] * f["size"][1]))
                    # normalize ds by dividing by a large factor
                    score = dc + (ds / 10000.0)
                    candidates.append((score, fp))

                candidates = sorted(candidates, key=lambda x: x[0])[:6]
                if candidates:
                    rcols = st.columns(len(candidates))
                    for col, (_, fp) in zip(rcols, candidates):
                        img = load_image_from_path(fp)
                        col.image(resize_image(img, max_size=(250, 200)), caption=os.path.basename(fp))
                else:
                    st.info("No related images found.")
            except Exception as e:
                st.error(f"Failed to compute related images: {e}")

elif page == "Analyze":
    st.sidebar.markdown("### Upload one or more images (JPG/PNG)")
    uploaded_files = st.sidebar.file_uploader("Choose image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if not uploaded_files:
        st.info("Upload one or more images using the sidebar to get started.")
        st.stop()

    images = [load_image_from_bytes(f.read()) for f in uploaded_files]
    display_images = [resize_image(img, max_size=(800, 600)) for img in images]

    st.subheader("Image Preview")
    cols = st.columns(len(display_images))
    for c, img in zip(cols, display_images):
        c.image(img, use_column_width=True)

    prompt_text = build_prompt()

    if st.button("Analyze Supply Chain"):
        if not st.session_state.get('user'):
            st.warning("Please sign in to run analysis.")
        else:
            results = []
            with st.spinner("Analyzing image(s) with AI model..."):
                for img in images:
                    img_bytes = image_to_bytes(img)
                    try:
                        res = analyze_image(img_bytes, prompt_text)
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
                        res = {"observation": "(error)", "insights": "", "recommendations": "", "opportunity_detection": "", "startup_idea_markdown": "", "market_score": "", "investor_pitch": ""}
                    results.append(res)

        # If multiple images, show per-image results and a comparison
        for i, res in enumerate(results):
            st.markdown(f"**Image {i+1} Analysis**")
            st.subheader("Supply Chain Observation")
            st.markdown(res.get("observation", "No observation returned."))
            st.subheader("Inventory / Logistics Insights")
            st.markdown(res.get("insights", "No insights returned."))
            st.subheader("Operational Recommendations")
            st.markdown(res.get("recommendations", "No recommendations returned."))
            st.subheader("Startup Opportunity Detection")
            st.markdown(res.get("opportunity_detection", "No opportunity detected."))
            st.subheader("Startup Idea Generator")
            st.markdown(res.get("startup_idea_markdown", "No startup idea returned."))
            st.subheader("Market Opportunity Score")
            st.markdown(res.get("market_score", "N/A"))
            st.subheader("Investor Pitch Summary")
            st.markdown(res.get("investor_pitch", "N/A"))

        # Comparison summary when more than one image
        if len(results) > 1:
            st.subheader("Multi-image Comparison Summary")
            cmp_parts = []
            for idx, r in enumerate(results):
                cmp_parts.append(f"Image {idx+1}: {r.get('opportunity_detection','').strip()} ")
            st.markdown("\n\n".join(cmp_parts))

        # Prepare combined report
        report_sections = []
        for idx, res in enumerate(results):
            report_sections.append(f"Image {idx+1} - Observation:\n{res.get('observation','')}\n")
            report_sections.append(f"Insights:\n{res.get('insights','')}\n")
            report_sections.append(f"Recommendations:\n{res.get('recommendations','')}\n")
            report_sections.append(f"Opportunity:\n{res.get('opportunity_detection','')}\n")
            report_sections.append(f"Startup Idea:\n{res.get('startup_idea_markdown','')}\n")
            report_sections.append(f"Market Score: {res.get('market_score','')}\n")
            report_sections.append(f"Investor Pitch:\n{res.get('investor_pitch','')}\n")

        report_text = "\n\n".join(report_sections)

        # Plain text download
        b64 = base64.b64encode(report_text.encode()).decode()
        href = f"data:text/plain;base64,{b64}"
        st.markdown(f"[Download analysis report (TXT)]({href})")

        # Markdown download
        md_b64 = base64.b64encode(report_text.encode()).decode()
        md_href = f"data:text/markdown;base64,{md_b64}"
        st.markdown(f"[Download analysis report (MD)]({md_href})")

        # PDF generation
        try:
            pdf_bytes = generate_pdf_bytes(report_text)
            st.download_button("Download analysis report (PDF)", data=pdf_bytes, file_name="supplysight_report.pdf", mime="application/pdf")
        except Exception as e:
            st.warning(f"PDF generation not available: {e}")

        # Investor-ready project report generation
        st.markdown("---")
        st.subheader("Investor-ready Project Report")
        st.write("Generate a polished, investor-ready project report based on the AI analysis above.")
        if st.button("Generate Investor Report"):
            if not st.session_state.get('user'):
                st.warning("Please sign in to generate project reports.")
            else:
                with st.spinner("Generating investor-ready project report..."):
                    combined = {
                        "observation": "\n\n".join([r.get("observation", "") for r in results]),
                        "insights": "\n\n".join([r.get("insights", "") for r in results]),
                        "recommendations": "\n\n".join([r.get("recommendations", "") for r in results]),
                        "opportunity_detection": "\n\n".join([r.get("opportunity_detection", "") for r in results]),
                        "startup_idea_markdown": "\n\n".join([r.get("startup_idea_markdown", "") for r in results]),
                        "market_score": ", ".join([r.get("market_score", "") for r in results if r.get("market_score", "")]),
                        "investor_pitch": "\n\n".join([r.get("investor_pitch", "") for r in results]),
                    }

                    try:
                        project_report_md = generate_project_report(combined)
                    except Exception as e:
                        st.error(f"Failed to generate project report: {e}")
                        project_report_md = ""

            if project_report_md:
                st.markdown("**Investor-ready Project Report (Markdown Preview)**")
                st.markdown(project_report_md)

                # Offer downloads
                pr_b = project_report_md.encode()
                pr_b64 = base64.b64encode(pr_b).decode()
                st.markdown(f"[Download project report (MD)](data:text/markdown;base64,{pr_b64})")
                try:
                    pr_pdf = generate_pdf_bytes(project_report_md)
                    st.download_button("Download project report (PDF)", data=pr_pdf, file_name="supplysight_investor_report.pdf", mime="application/pdf")
                except Exception as e:
                    st.warning(f"PDF generation not available for project report: {e}")
            else:
                st.info("No project report generated.")

    
