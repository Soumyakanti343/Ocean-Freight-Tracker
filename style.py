import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        /* Import Fonts */
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        /* Global Styling */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: linear-gradient(
                135deg,
                #f4f8fc 0%,
                #edf5fa 50%,
                #f8fbfd 100%
            );
        }

        /* Main Content */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }

        /* Main Heading */
        h1 {
            color: #12304a !important;
            font-weight: 800 !important;
            letter-spacing: -1px;
        }

        h2 {
            color: #174766 !important;
            font-weight: 700 !important;
        }

        h3 {
            color: #1d5875 !important;
            font-weight: 600 !important;
        }

        /* Paragraphs and Labels */
        p, label, .stMarkdown {
            color: #344b60;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                #102d46 0%,
                #164b68 65%,
                #17677a 100%
            );
            border-right: 1px solid #234f69;
        }

        [data-testid="stSidebar"] * {
            color: #f0f8ff !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.2);
        }

        /* Sidebar Navigation */
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            background: rgba(255, 255, 255, 0.04);
            padding: 10px 14px;
            margin: 4px 0;
            border-radius: 10px;
            transition: all 0.2s ease;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: rgba(255, 255, 255, 0.16);
            transform: translateX(3px);
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {
            background: linear-gradient(
                135deg,
                #087e9b,
                #126b91
            );
            color: white !important;
            border: none;
            border-radius: 10px;
            padding: 0.55rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(18, 107, 145, 0.15);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background: linear-gradient(
                135deg,
                #08657d,
                #104d70
            );
            transform: translateY(-2px);
            box-shadow: 0 7px 18px rgba(18, 107, 145, 0.25);
        }

        .stButton > button:active {
            transform: scale(0.98);
        }

        /* Input Fields */
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stSelectbox div[data-baseweb="select"],
        .stMultiSelect div[data-baseweb="select"] {
            border-radius: 9px !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus {
            border-color: #087e9b !important;
            box-shadow: 0 0 0 2px rgba(8, 126, 155, 0.12);
        }

        /* Form Containers */
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.85);
            padding: 22px;
            border: 1px solid #dce8f0;
            border-radius: 16px;
            box-shadow: 0 5px 18px rgba(24, 61, 87, 0.05);
        }

        /* Metric Cards */
        [data-testid="stMetric"] {
            background: linear-gradient(
                145deg,
                #ffffff,
                #f4faff
            );
            border: 1px solid #dceaf3;
            padding: 20px 18px;
            border-radius: 16px;
            box-shadow: 0 5px 16px rgba(22, 65, 91, 0.06);
            transition: all 0.2s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 9px 24px rgba(22, 65, 91, 0.12);
            border-color: #a8d5e5;
        }

        [data-testid="stMetricLabel"] {
            color: #527086 !important;
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: #123b57 !important;
            font-weight: 800;
        }

        /* DataFrames and Tables */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid #dce8f0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(22, 65, 91, 0.04);
        }

        /* File Upload */
        [data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.75);
            border: 1px dashed #9bbfd0;
            border-radius: 14px;
            padding: 12px;
            transition: border-color 0.2s ease;
        }

        [data-testid="stFileUploader"]:hover {
            border-color: #087e9b;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid #dce8f0;
            border-radius: 12px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background: #e7f0f6;
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
            transition: background 0.2s ease;
        }

        .stTabs [aria-selected="true"] {
            background: #d0eaf3 !important;
            color: #104d70 !important;
            font-weight: 700;
        }

        /* Dividers */
        hr {
            border-color: #d7e5ee;
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* Success, Error, Warning and Info Messages */
        [data-testid="stAlert"] {
            border-radius: 12px;
        }

        /* Footer Spacing */
        footer {
            visibility: hidden;
        }

        /* Responsive Layout */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem;
            }

            h1 {
                font-size: 1.8rem !important;
            }

            [data-testid="stMetric"] {
                padding: 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



    