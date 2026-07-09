# 🧹 Smart Dataset Cleaner

A powerful and interactive **Streamlit-based Data Cleaning Tool** that helps users clean messy CSV and Excel datasets without writing code. The application provides automated dataset diagnostics, data profiling, missing value handling, outlier treatment, data transformation, encoding, and downloadable cleaned datasets.

---

## 🚀 Features

### 📂 Dataset Upload
- Upload CSV and Excel (.xlsx) files
- Supports multiple CSV encodings
- Automatically standardizes common missing values
- # Test

![Home](./screenshots/home.png)

### 🩺 Automatic Dataset Diagnostics
- Detects duplicate rows
- Detects missing values
- Identifies outliers
- Suggests suitable outlier detection methods
- Identifies categorical/text columns

### 📊 Data Profiling
- Dataset overview
- Number of rows and columns
- Missing value statistics
- Duplicate row count
- Column information
- Data quality summary
- Outlier report

### 🧹 Data Cleaning Operations

#### General Cleaning
- Remove empty rows
- Remove empty columns
- Remove duplicate rows
- Drop unwanted columns
- Rename columns

#### Data Type Conversion
- Convert columns to numeric
- Convert columns to string
- Parse date columns
- Extract Year, Month, and Day features

#### Missing Value Handling
Choose different methods for each column:
- Drop rows
- Fill with Mean
- Fill with Median
- Fill with Mode
- Forward Fill
- Backward Fill
- Linear Interpolation
- Fill with Custom Value

#### Text Cleaning
- Strip whitespace
- Convert to lowercase
- Convert to uppercase
- Title case conversion
- Remove special characters
- Remove numbers
- Remove punctuation

#### Outlier Handling
Supports multiple techniques:
- IQR Method
- Z-Score Method
- Percentile Method

Available actions:
- Drop outliers
- Winsorize (Cap at Bounds)
- Replace with NaN

#### Data Transformation
- Min-Max Scaling
- Standard Scaling (Z-score)

#### Encoding
- Label Encoding for categorical columns

---

## 📥 Output

After cleaning, users can:

- Preview cleaned dataset
- View complete cleaning summary
- Compare rows and columns removed
- Download cleaned dataset as:
  - CSV
  - Excel (.xlsx)

---

## 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- XlsxWriter
- Regular Expressions (re)

---

## 📦 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/smart-dataset-cleaner.git
```

Move into the project directory

```bash
cd smart-dataset-cleaner
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
Smart-Dataset-Cleaner/
│
├── excel_csv_cleaner.py
├── requirements.txt
├── README.md
└── screenshots/
│     ├── home.png
│     ├── upload.png
│     ├── profiling.png
│     ├── cleaning.png
│     └── result.png 
```

---

## 🎯 Use Cases

- Data preprocessing
- Machine Learning projects
- Exploratory Data Analysis (EDA)
- Academic assignments
- Business analytics
- Data science workflows
- Internship projects

---

## ⭐ Key Highlights

- Interactive no-code interface
- Smart dataset diagnostics
- Automatic data quality reporting
- Flexible cleaning pipeline
- Multiple missing value handling methods
- Multiple outlier detection techniques
- Feature engineering support
- Data scaling and encoding
- Download cleaned datasets instantly

---

## 🔮 Future Improvements

- One-Hot Encoding
- PCA for dimensionality reduction
- Data visualization dashboard
- Automatic report generation
- Machine Learning preprocessing pipeline
- Database connectivity
- Cloud deployment

---

## 👩‍💻 Author

**Tapaswini Shaw**

B.Tech Computer Science Engineering (AIML)

Passionate about Data Science, Artificial Intelligence, Machine Learning, and Python Development.

---
