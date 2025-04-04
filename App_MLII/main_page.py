import os
import streamlit as st


def main():
    st.set_page_config(
        page_title="JobRaidy - Smart Job Application Assistant",
        page_icon="💼",
        layout="wide"
    )

    # Logo and Title section
    col_logo, col_text = st.columns([1, 3])

    with col_logo:
        logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.warning("⚠️ logo.jpg not found. Make sure it's in the App folder.")

    with col_text:
        st.markdown("<br>", unsafe_allow_html=True)

    # Welcome message
    st.markdown("""
    ### JobRaidy - Your Smart Job Application Assistant 💼✨
    Welcome to **JobRaidy**, a **Generative AI-powered platform** designed to help you find the right job and optimize your resume to stand out.
    """)

    # Updated accurate feature description
    st.write("""
    ### 🔍 What can you do with JobGenie?

    - Upload your resume and receive:
      - 📄 An **AI-generated score**
      - 🧠 Personalized **feedback**
      - 🚀 Tips to improve your answers
    - Answer AI-generated screening questions
    - See how you rank against other candidates
    - Read recent news about the company
    """)

    st.markdown("---")

if __name__ == "__main__":
    main()

