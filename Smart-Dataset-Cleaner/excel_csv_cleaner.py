import streamlit as st
import pandas as pd
import numpy as np
import io
import time
import re

st.set_page_config(page_title="Smart Dataset Cleaner", layout="wide", page_icon="🧹")

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
    }
    .stDownloadButton>button {
        background-color: #2ecc71;
    }
    .stDownloadButton>button:hover {
        background-color: #27ae60;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧹 Smart Dataset Cleaner Tool")
st.markdown("Upload any messy Excel or CSV file and clean it interactively with full control.")

# Initialize session state for dataframes
if 'raw_df' not in st.session_state:
    st.session_state.raw_df = None
if 'cleaned_df' not in st.session_state:
    st.session_state.cleaned_df = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None

# Tabs for workflow
tab1, tab2, tab3 = st.tabs(["📂 1. Upload Data", "📊 2. Data Profiling", "🛠️ 3. Data Cleaning & Review"])

# ==========================================
# TAB 1: UPLOAD DATA
# ==========================================
with tab1:
    st.header("Upload your dataset")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                # Try different encodings
                encodings = ['utf-8', 'latin1', 'windows-1252', 'iso-8859-1']
                df = None
                for enc in encodings:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=enc, low_memory=False)
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    st.error("Failed to read CSV with supported encodings.")
            else:
                df = pd.read_excel(uploaded_file)

            # Standardize missing values initially
            df.replace(["Unknown", "None", "Error", "", "NA", "N/A", "null", "NaN"], np.nan, inplace=True)
            
            st.session_state.raw_df = df
            st.session_state.cleaned_df = df.copy()
            st.session_state.file_name = uploaded_file.name
            
            st.success(f"Successfully loaded '{uploaded_file.name}' with {df.shape[0]} rows and {df.shape[1]} columns!")
            st.dataframe(df.head())
            
            # --- Initial Diagnostics ---
            st.markdown("### 🩺 Quick Dataset Diagnostics")
            with st.spinner("Analyzing dataset for potential issues..."):
                diagnostics = []
                
                # 1. Duplicates
                dup_count = df.duplicated().sum()
                if dup_count > 0:
                    diagnostics.append({"Issue": "Duplicate Rows", "Details": f"{dup_count} duplicate rows found.", "Recommendation": "Use 'Drop Duplicate Rows' in General Operations."})
                    
                # 2. Missing Values
                missing_count = df.isna().sum().sum()
                if missing_count > 0:
                    cols_with_missing = df.columns[df.isna().any()].tolist()
                    diagnostics.append({"Issue": "Missing Values", "Details": f"{missing_count} missing values across {len(cols_with_missing)} columns.", "Recommendation": "Handle missing values using Imputation or Drop Rows in 'Missing Value Handling'."})
                    
                # 3. Outliers
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                outlier_cols = []
                outlier_method_suggestions = {}
                for col in num_cols:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                    if outliers.sum() > 0:
                        outlier_cols.append(col)
                        skewness = df[col].skew()
                        if pd.isna(skewness):
                            outlier_method_suggestions[col] = "IQR"
                        elif abs(skewness) > 1:
                            outlier_method_suggestions[col] = "IQR (data is skewed)"
                        else:
                            outlier_method_suggestions[col] = "Z-Score (data is relatively symmetric)"
                            
                if outlier_cols:
                    suggestions_text = ", ".join([f"{c}: {outlier_method_suggestions[c]}" for c in outlier_cols[:2]])
                    if len(outlier_cols) > 2:
                        suggestions_text += "..."
                    diagnostics.append({"Issue": "Outliers Detected", "Details": f"Outliers found in {len(outlier_cols)} numerical columns.", "Recommendation": f"Suggested Outlier Methods: {suggestions_text}"})
                    
                # 4. Data Types (Categorical that might need encoding)
                obj_cols = df.select_dtypes(include=['object']).columns.tolist()
                if obj_cols:
                    diagnostics.append({"Issue": "Text/Categorical Data", "Details": f"{len(obj_cols)} text columns found.", "Recommendation": "Consider Label Encoding if these are categories, or Text Formatting to clean strings."})
                    
                if not diagnostics:
                    diagnostics.append({"Issue": "Perfect Dataset! 🎉", "Details": "No obvious missing values, duplicates, or outliers detected.", "Recommendation": "You can proceed directly to Data Transformation or Download."})
                    
                diag_df = pd.DataFrame(diagnostics)
                st.dataframe(diag_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading file: {e}")

# ==========================================
# TAB 2: DATA PROFILING
# ==========================================
with tab2:
    if st.session_state.raw_df is not None:
        df = st.session_state.raw_df
        st.header("Dataset Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rows", df.shape[0])
        col2.metric("Total Columns", df.shape[1])
        col3.metric("Missing Values", df.isna().sum().sum())
        col4.metric("Duplicate Rows", df.duplicated().sum())
        
        # --- Data Quality Summary ---
        st.subheader("⚠️ Data Quality Summary")
        
        # Gather issues
        missing_cols = df.columns[df.isna().any()].tolist()
        dup_count = df.duplicated().sum()
        
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        outlier_cols = []
        outlier_info = []
        for col in num_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outliers_count = outliers.sum()
            if outliers_count > 0:
                outlier_cols.append(col)
                skewness = df[col].skew()
                if pd.isna(skewness):
                    suggestion = "IQR"
                elif abs(skewness) > 1:
                    suggestion = "IQR (Data is skewed)"
                else:
                    suggestion = "Z-Score (Data is relatively symmetric)"
                outlier_info.append({"Column": col, "Outliers Count": outliers_count, "Suggested Method": suggestion})
                
        summary_data = []
        if dup_count > 0:
            summary_data.append({"Issue Type": "Duplicates", "Severity": "Medium", "Columns Affected": "Entire Rows", "Description": f"{dup_count} duplicate rows found."})
        if missing_cols:
            summary_data.append({"Issue Type": "Missing Values", "Severity": "High", "Columns Affected": ", ".join(missing_cols), "Description": f"Missing values present in {len(missing_cols)} columns."})
        if outlier_cols:
            summary_data.append({"Issue Type": "Outliers", "Severity": "Medium", "Columns Affected": ", ".join(outlier_cols), "Description": f"Outliers detected in {len(outlier_cols)} columns."})
            
        if summary_data:
            st.table(pd.DataFrame(summary_data))
        else:
            st.success("✅ No major data quality issues (missing values, duplicates, outliers) detected!")

        # --- Outlier Detection & Suggestions ---
        st.subheader("📈 Outlier Detection & Suggestions")
        if outlier_info:
            st.dataframe(pd.DataFrame(outlier_info), use_container_width=True)
        else:
            st.info("No outliers detected in numerical columns.")
        
        st.subheader("Column Information")
        col_info = pd.DataFrame({
            "Data Type": df.dtypes,
            "Missing Values": df.isna().sum(),
            "Missing %": (df.isna().sum() / len(df) * 100).round(2),
            "Unique Values": df.nunique()
        })
        st.dataframe(col_info, use_container_width=True)
        
    else:
        st.info("Please upload a dataset in Tab 1 first.")

# ==========================================
# TAB 3: DATA CLEANING & REVIEW
# ==========================================
with tab3:
    if st.session_state.raw_df is not None:
        st.header("Interactive Data Cleaning")
        st.markdown("Configure your cleaning operations below. Click **Apply Cleaning Pipeline** at the bottom to execute.")
        
        # We work on a fresh copy of raw_df every time to allow re-running the pipeline
        df_to_clean = st.session_state.raw_df.copy()
        
        # --- 1. General Operations ---
        with st.expander("🧹 General Operations", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                drop_empty_rows = st.checkbox("Drop Completely Empty Rows", value=True)
            with col2:
                drop_empty_cols = st.checkbox("Drop Completely Empty Columns", value=True)
            with col3:
                drop_duplicates = st.checkbox("Drop Duplicate Rows", value=True)
            
            st.markdown("#### Column Management")
            cols = df_to_clean.columns.tolist()
            cols_to_drop = st.multiselect("Select columns to drop entirely", cols)
            
            st.markdown("#### Rename Columns")
            rename_dict = {}
            rename_cols = st.multiselect("Select columns to rename", cols)
            if rename_cols:
                r_cols = st.columns(len(rename_cols))
                for idx, col in enumerate(rename_cols):
                    with r_cols[idx]:
                        new_name = st.text_input(f"New name for '{col}'", key=f"rename_{col}")
                        if new_name:
                            rename_dict[col] = new_name
                
        # --- 2. Data Type & Date Parsing ---
        with st.expander("📅 Data Type & Date Parsing"):
            st.markdown("Convert columns to appropriate data types or parse dates.")
            cols = df_to_clean.columns.tolist()
            
            # Select columns to cast to datetime
            datetime_cols = st.multiselect("Select columns to parse as Dates", cols)
            extract_date_features = st.checkbox("Extract Year, Month, Day features from selected date columns", value=False)
            
            # Select columns to cast to numeric
            numeric_cols = st.multiselect("Select columns to force as Numeric (invalid parsing will be set to NaN)", cols)
            
            # Select columns to cast to string
            string_cols = st.multiselect("Select columns to force as String", cols)

        # --- 3. Missing Value Handling ---
        with st.expander("🧩 Missing Value Handling"):
            st.markdown("Choose how to handle missing values for specific columns.")
            missing_cols = df_to_clean.columns[df_to_clean.isna().any()].tolist()
            
            if not missing_cols:
                st.success("No missing values detected in the raw dataset.")
            
            missing_actions = {}
            for col in missing_cols:
                col1, col2 = st.columns([1, 2])
                with col1:
                    action = st.selectbox(f"Action for '{col}'", 
                                          ["Do Nothing", "Drop Rows", "Fill with Mean", "Fill with Median", "Fill with Mode", "Forward Fill", "Backward Fill", "Linear Interpolate", "Fill with Custom Value"],
                                          key=f"na_{col}")
                with col2:
                    custom_val = None
                    if action == "Fill with Custom Value":
                        custom_val = st.text_input(f"Custom value for '{col}'", key=f"custom_{col}")
                missing_actions[col] = {"action": action, "value": custom_val}

        # --- 4. Text Formatting ---
        with st.expander("🔤 Text Formatting"):
            st.markdown("Clean up string/text columns.")
            object_cols = df_to_clean.select_dtypes(include=['object', 'string']).columns.tolist()
            
            text_actions = {}
            for col in object_cols:
                action = st.selectbox(f"Format for '{col}'", 
                                      ["Do Nothing", "Strip Whitespace", "Lowercase", "Uppercase", "Title Case", "Remove Special Characters", "Remove Numbers", "Remove Punctuation"],
                                      key=f"txt_{col}")
                text_actions[col] = action

        # --- 5. Outlier Handling ---
        with st.expander("📈 Outlier Handling (Numeric Columns)"):
            st.markdown("Detect and handle outliers using various statistical methods.")
            num_cols = df_to_clean.select_dtypes(include=[np.number]).columns.tolist()
            
            outlier_actions = {}
            for col in num_cols:
                col1, col2 = st.columns([1, 2])
                with col1:
                    method = st.selectbox(f"Method for '{col}'", 
                                          ["Do Nothing", "IQR (Interquartile Range)", "Z-Score", "Percentile (1% / 99%)"],
                                          key=f"outlier_method_{col}")
                with col2:
                    action = "Do Nothing"
                    if method != "Do Nothing":
                        if method in ["IQR (Interquartile Range)", "Z-Score"]:
                            action = st.selectbox(f"Action for '{col}' outliers", 
                                                  ["Drop Rows", "Cap at Bounds (Winsorize)", "Replace with NaN"],
                                                  key=f"outlier_action_{col}")
                        elif method == "Percentile (1% / 99%)":
                            action = st.selectbox(f"Action for '{col}' outliers", 
                                                  ["Drop Rows", "Cap at Bounds (Winsorize)"],
                                                  key=f"outlier_action_{col}")
                outlier_actions[col] = {"method": method, "action": action}

        # --- 6. Data Transformation & Encoding ---
        with st.expander("🔄 Data Transformation & Encoding"):
            st.markdown("Scale numerical data or encode categorical text data.")
            cols = df_to_clean.columns.tolist()
            num_cols = df_to_clean.select_dtypes(include=[np.number]).columns.tolist()
            object_cols = df_to_clean.select_dtypes(include=['object', 'string']).columns.tolist()
            
            # Scaling
            scaling_actions = {}
            scale_cols = st.multiselect("Select columns to Scale", num_cols)
            if scale_cols:
                s_cols = st.columns(len(scale_cols))
                for idx, col in enumerate(scale_cols):
                    with s_cols[idx]:
                        scaling_actions[col] = st.selectbox(f"Method for '{col}'", ["Min-Max Scaler (0-1)", "Standard Scaler (Z-score)"], key=f"scale_{col}")
                        
            # Encoding
            encoding_actions = {}
            encode_cols = st.multiselect("Select columns for Label Encoding", object_cols)
            for col in encode_cols:
                encoding_actions[col] = "Label Encoding"

        # --- APPLY BUTTON ---
        if st.button("🚀 Apply Cleaning Pipeline", use_container_width=True):
            with st.spinner("Applying cleaning operations..."):
                try:
                    summary_log = []
                    
                    # 1. General
                    if drop_empty_rows:
                        initial_rows = len(df_to_clean)
                        df_to_clean.dropna(how="all", inplace=True)
                        if initial_rows - len(df_to_clean) > 0:
                            summary_log.append({"Category": "General", "Operation": "Drop Empty Rows", "Details": f"Dropped {initial_rows - len(df_to_clean)} rows."})
                            
                    if drop_empty_cols:
                        initial_cols = len(df_to_clean.columns)
                        df_to_clean.dropna(axis=1, how="all", inplace=True)
                        if initial_cols - len(df_to_clean.columns) > 0:
                            summary_log.append({"Category": "General", "Operation": "Drop Empty Columns", "Details": f"Dropped {initial_cols - len(df_to_clean.columns)} columns."})
                            
                    if drop_duplicates:
                        initial_rows = len(df_to_clean)
                        df_to_clean.drop_duplicates(inplace=True)
                        if initial_rows - len(df_to_clean) > 0:
                            summary_log.append({"Category": "General", "Operation": "Drop Duplicates", "Details": f"Dropped {initial_rows - len(df_to_clean)} duplicate rows."})
                            
                    if cols_to_drop:
                        df_to_clean.drop(columns=cols_to_drop, inplace=True, errors='ignore')
                        summary_log.append({"Category": "General", "Operation": "Drop Columns", "Details": f"Dropped columns: {', '.join(cols_to_drop)}."})
                        
                    if rename_dict:
                        df_to_clean.rename(columns=rename_dict, inplace=True)
                        summary_log.append({"Category": "General", "Operation": "Rename Columns", "Details": f"Renamed {len(rename_dict)} columns."})
                        
                    # 2. Types & Dates
                    for col in datetime_cols:
                        if col in df_to_clean.columns:
                            df_to_clean[col] = pd.to_datetime(df_to_clean[col], errors="coerce")
                            summary_log.append({"Category": "Data Types", "Operation": "Parse Date", "Details": f"Parsed '{col}' as datetime."})
                            if extract_date_features:
                                df_to_clean[f"{col}_Year"] = df_to_clean[col].dt.year
                                df_to_clean[f"{col}_Month"] = df_to_clean[col].dt.month
                                df_to_clean[f"{col}_Day"] = df_to_clean[col].dt.day
                                summary_log.append({"Category": "Feature Engineering", "Operation": "Date Extraction", "Details": f"Extracted Year/Month/Day from '{col}'."})
                            
                    for col in numeric_cols:
                        if col in df_to_clean.columns:
                            df_to_clean[col] = pd.to_numeric(df_to_clean[col], errors="coerce")
                            summary_log.append({"Category": "Data Types", "Operation": "Force Numeric", "Details": f"Forced '{col}' to numeric."})
                            
                    for col in string_cols:
                        if col in df_to_clean.columns:
                            df_to_clean[col] = df_to_clean[col].astype(str)
                            summary_log.append({"Category": "Data Types", "Operation": "Force String", "Details": f"Forced '{col}' to string."})
                            
                    # 3. Missing Values
                    for col, config in missing_actions.items():
                        if col in df_to_clean.columns: # Might have been dropped
                            act = config["action"]
                            if act != "Do Nothing":
                                if act == "Drop Rows":
                                    initial_rows = len(df_to_clean)
                                    df_to_clean.dropna(subset=[col], inplace=True)
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Dropped {initial_rows - len(df_to_clean)} rows due to NaNs in '{col}'."})
                                elif act == "Fill with Mean" and pd.api.types.is_numeric_dtype(df_to_clean[col]):
                                    df_to_clean[col] = df_to_clean[col].fillna(df_to_clean[col].mean())
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Filled '{col}' with mean."})
                                elif act == "Fill with Median" and pd.api.types.is_numeric_dtype(df_to_clean[col]):
                                    df_to_clean[col] = df_to_clean[col].fillna(df_to_clean[col].median())
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Filled '{col}' with median."})
                                elif act == "Fill with Mode":
                                    if not df_to_clean[col].mode().empty:
                                        df_to_clean[col] = df_to_clean[col].fillna(df_to_clean[col].mode()[0])
                                        summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Filled '{col}' with mode."})
                                elif act == "Forward Fill":
                                    df_to_clean[col] = df_to_clean[col].ffill()
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Forward filled '{col}'."})
                                elif act == "Backward Fill":
                                    df_to_clean[col] = df_to_clean[col].bfill()
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Backward filled '{col}'."})
                                elif act == "Linear Interpolate" and pd.api.types.is_numeric_dtype(df_to_clean[col]):
                                    df_to_clean[col] = df_to_clean[col].interpolate(method='linear')
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Linearly interpolated '{col}'."})
                                elif act == "Fill with Custom Value":
                                    df_to_clean[col] = df_to_clean[col].fillna(config["value"])
                                    summary_log.append({"Category": "Missing Values", "Operation": act, "Details": f"Filled '{col}' with custom value: {config['value']}."})
                                    
                    # 4. Text Formatting
                    for col, act in text_actions.items():
                        if col in df_to_clean.columns:
                            # Apply to both pandas object/string dtypes
                            if pd.api.types.is_object_dtype(df_to_clean[col]) or pd.api.types.is_string_dtype(df_to_clean[col]):
                                if act != "Do Nothing":
                                    if act == "Strip Whitespace":
                                        df_to_clean[col] = df_to_clean[col].astype(str).str.strip()
                                    elif act == "Lowercase":
                                        df_to_clean[col] = df_to_clean[col].astype(str).str.strip().str.lower()
                                    elif act == "Uppercase":
                                        df_to_clean[col] = df_to_clean[col].astype(str).str.strip().str.upper()
                                    elif act == "Title Case":
                                        df_to_clean[col] = df_to_clean[col].astype(str).str.strip().str.title()
                                    elif act == "Remove Special Characters":
                                        df_to_clean[col] = df_to_clean[col].astype(str).apply(lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', x))
                                    elif act == "Remove Numbers":
                                        df_to_clean[col] = df_to_clean[col].astype(str).apply(lambda x: re.sub(r'\d+', '', x))
                                    elif act == "Remove Punctuation":
                                        df_to_clean[col] = df_to_clean[col].astype(str).apply(lambda x: re.sub(r'[^\w\s]', '', x))
                                    summary_log.append({"Category": "Text Formatting", "Operation": act, "Details": f"Applied '{act}' to '{col}'."})

                                    
                    # 5. Outliers
                    for col, config in outlier_actions.items():
                        if col in df_to_clean.columns and pd.api.types.is_numeric_dtype(df_to_clean[col]):
                            method = config["method"]
                            act = config["action"]
                            
                            if method != "Do Nothing" and act != "Do Nothing":
                                if method == "IQR (Interquartile Range)":
                                    Q1 = df_to_clean[col].quantile(0.25)
                                    Q3 = df_to_clean[col].quantile(0.75)
                                    IQR = Q3 - Q1
                                    lower_bound = Q1 - 1.5 * IQR
                                    upper_bound = Q3 + 1.5 * IQR
                                    
                                    is_outlier = (df_to_clean[col] < lower_bound) | (df_to_clean[col] > upper_bound)
                                    outliers_count = is_outlier.sum()
                                    
                                    if act == "Drop Rows":
                                        df_to_clean = df_to_clean[~is_outlier]
                                        summary_log.append({"Category": "Outliers", "Operation": f"Drop ({method})", "Details": f"Dropped {outliers_count} outliers in '{col}'."})
                                    elif act == "Cap at Bounds (Winsorize)":
                                        df_to_clean[col] = np.where(df_to_clean[col] < lower_bound, lower_bound, df_to_clean[col])
                                        df_to_clean[col] = np.where(df_to_clean[col] > upper_bound, upper_bound, df_to_clean[col])
                                        summary_log.append({"Category": "Outliers", "Operation": f"Cap ({method})", "Details": f"Capped {outliers_count} outliers in '{col}'."})
                                    elif act == "Replace with NaN":
                                        df_to_clean.loc[is_outlier, col] = np.nan
                                        summary_log.append({"Category": "Outliers", "Operation": f"NaN ({method})", "Details": f"Replaced {outliers_count} outliers with NaN in '{col}'."})
                                        
                                elif method == "Z-Score":
                                    mean = df_to_clean[col].mean()
                                    std = df_to_clean[col].std()
                                    z_scores = ((df_to_clean[col] - mean) / std).abs()
                                    
                                    is_outlier = z_scores > 3.0
                                    outliers_count = is_outlier.sum()
                                    
                                    if act == "Drop Rows":
                                        df_to_clean = df_to_clean[~is_outlier]
                                        summary_log.append({"Category": "Outliers", "Operation": f"Drop ({method})", "Details": f"Dropped {outliers_count} outliers in '{col}'."})
                                    elif act == "Cap at Bounds (Winsorize)":
                                        lower_bound = mean - 3 * std
                                        upper_bound = mean + 3 * std
                                        df_to_clean[col] = np.where(df_to_clean[col] < lower_bound, lower_bound, df_to_clean[col])
                                        df_to_clean[col] = np.where(df_to_clean[col] > upper_bound, upper_bound, df_to_clean[col])
                                        summary_log.append({"Category": "Outliers", "Operation": f"Cap ({method})", "Details": f"Capped {outliers_count} outliers in '{col}'."})
                                    elif act == "Replace with NaN":
                                        df_to_clean.loc[is_outlier, col] = np.nan
                                        summary_log.append({"Category": "Outliers", "Operation": f"NaN ({method})", "Details": f"Replaced {outliers_count} outliers with NaN in '{col}'."})
                                        
                                elif method == "Percentile (1% / 99%)":
                                    lower_bound = df_to_clean[col].quantile(0.01)
                                    upper_bound = df_to_clean[col].quantile(0.99)
                                    
                                    is_outlier = (df_to_clean[col] < lower_bound) | (df_to_clean[col] > upper_bound)
                                    outliers_count = is_outlier.sum()
                                    
                                    if act == "Drop Rows":
                                        df_to_clean = df_to_clean[~is_outlier]
                                        summary_log.append({"Category": "Outliers", "Operation": f"Drop ({method})", "Details": f"Dropped {outliers_count} outliers in '{col}'."})
                                    elif act == "Cap at Bounds (Winsorize)":
                                        df_to_clean[col] = np.where(df_to_clean[col] < lower_bound, lower_bound, df_to_clean[col])
                                        df_to_clean[col] = np.where(df_to_clean[col] > upper_bound, upper_bound, df_to_clean[col])
                                        summary_log.append({"Category": "Outliers", "Operation": f"Cap ({method})", "Details": f"Capped {outliers_count} outliers in '{col}'."})

                    # 6. Transformation & Encoding
                    for col, act in scaling_actions.items():
                        if col in df_to_clean.columns:
                            if act == "Min-Max Scaler (0-1)":
                                min_val = df_to_clean[col].min()
                                max_val = df_to_clean[col].max()
                                if max_val != min_val:
                                    df_to_clean[col] = (df_to_clean[col] - min_val) / (max_val - min_val)
                                summary_log.append({"Category": "Scaling", "Operation": "Min-Max", "Details": f"Scaled '{col}' to 0-1."})
                            elif act == "Standard Scaler (Z-score)":
                                mean = df_to_clean[col].mean()
                                std = df_to_clean[col].std()
                                if std != 0:
                                    df_to_clean[col] = (df_to_clean[col] - mean) / std
                                summary_log.append({"Category": "Scaling", "Operation": "Standardization", "Details": f"Standardized '{col}'."})
                                
                    for col, act in encoding_actions.items():
                        if col in df_to_clean.columns:
                            if act == "Label Encoding":
                                df_to_clean[col] = df_to_clean[col].astype('category').cat.codes
                                # Missing values become -1, set them back to NaN if they were missing
                                df_to_clean[col] = df_to_clean[col].replace(-1, np.nan)
                                summary_log.append({"Category": "Encoding", "Operation": "Label Encode", "Details": f"Label encoded '{col}'."})

                    st.session_state.cleaned_df = df_to_clean
                    st.session_state.summary_log = pd.DataFrame(summary_log) if summary_log else pd.DataFrame(columns=["Category", "Operation", "Details"])
                    st.success("✅ Cleaning pipeline applied successfully! Review your data below.")
                
                except Exception as e:
                    st.error(f"❌ Error applying pipeline: {str(e)}")

        # Quick debug: show last mean/median computed for each column if any
        if st.session_state.raw_df is not None and st.session_state.cleaned_df is not None:
            pass

                    
        # --- REVIEW & DOWNLOAD SECTION ---
        st.markdown("---")
        st.header("🔍 Review & Download")
        
        if st.session_state.cleaned_df is not None and 'summary_log' in st.session_state:
            st.subheader("Cleaning Summary")
            if not st.session_state.summary_log.empty:
                st.dataframe(st.session_state.summary_log, use_container_width=True)
            else:
                st.info("No cleaning operations were recorded.")
                
            raw_rows, raw_cols = st.session_state.raw_df.shape
            clean_rows, clean_cols = st.session_state.cleaned_df.shape
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows Removed", raw_rows - clean_rows)
            with col2:
                st.metric("Columns Removed", raw_cols - clean_cols)
                
            st.subheader("Cleaned Dataset Preview")
            st.dataframe(st.session_state.cleaned_df.head(50))
            
            # Download Buttons
            st.markdown("### 📥 Download Cleaned Data")
            col1, col2 = st.columns(2)
            
            # CSV
            csv_data = st.session_state.cleaned_df.to_csv(index=False).encode('utf-8')
            with col1:
                st.download_button(
                    label="Download as CSV",
                    data=csv_data,
                    file_name=f"cleaned_{st.session_state.file_name.split('.')[0]}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            # Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                st.session_state.cleaned_df.to_excel(writer, index=False, sheet_name='Cleaned Data')
            
            with col2:
                st.download_button(
                    label="Download as Excel",
                    data=buffer.getvalue(),
                    file_name=f"cleaned_{st.session_state.file_name.split('.')[0]}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
        else:
            st.info("Apply the cleaning pipeline to see the review and download options.")
            
    else:
        st.info("Please upload a dataset in Tab 1 first.")