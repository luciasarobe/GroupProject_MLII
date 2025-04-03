import streamlit as st
import os

def main():
    st.set_page_config(
        page_title="JobRaidy - Smart Job Application Assistant",
        page_icon="💼",
        layout="wide"
    )

    # Logo and Title section
    col_logo, col_text = st.columns([1, 3])

    with col_logo:
        # Robust path resolution for logo image (works both locally and in Streamlit Cloud)
        logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
        if os.path.exists(logo_path):
            st.image(logo_path, width=250)
        else:
            st.warning("⚠️ Logo image not found – make sure 'logo.jpg' is in the same folder as main_page.py")

    with col_text:
        st.markdown("<br>", unsafe_allow_html=True)

    # Welcome Message
    st.markdown("""
    ### JobGenie - Your Smart Job Application Assistant 💼✨  
    Welcome to **JobGenie**, a **Generative AI-powered platform** designed to help you find the right job and optimize your resume to stand out from the crowd.
    
    Whether you're a recent graduate, a career switcher, or a seasoned professional, **JobGenie** provides **personalized feedback** and insights powered by **Large Language Models (LLMs)** to enhance your job search experience.
    """)

    st.markdown("---")

    # Description of the system
    st.write("""
    ### 🔍 What can you do with JobGenie?

    - **Search for jobs** based on:
      - **Category**
      - **Location**
      - **Company**
    - **Upload your resume** and receive:
      - 📄 An **AI-generated score**
      - 🧠 Personalized **feedback**
      - 🚀 Suggestions to **improve your chances** in real applications

    The job listings are retrieved via a live job-posting API, and resume evaluations are powered by cutting-edge **generative AI models**.

    """)

    st.write("""
    **Group Project for Machine Learning II:**  
    Generative AI Solution for Real-World Business Challenges.

    ### Project Pages:
    - **Homepage** 🏠: Overview of the project and platform.
    - **Job Search** 🔍: Search for job openings with smart filters.
    - **Resume Feedback** 📄: Upload your CV and receive detailed feedback from an AI assistant.
    - **Team** 👥: Learn more about the team behind JobGenie.
    """)

    st.markdown("---")

    # Instructions
    st.write("""
    ### 🚀 How to use JobGenie:
    - Use the **sidebar** to navigate through the platform.
    - In the **Job Search** section, explore opportunities tailored to your preferences.
    - Upload your **PDF CV** in the **Resume Feedback** section and get instant insights powered by AI.
    - Visit the **Team** section to know more about the creators of JobGenie.
    """)

    st.markdown("---")

if __name__ == "__main__":
    main()
