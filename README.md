# StatsYuri

StatsYuri is a Streamlit-based statistical analysis platform for exploring datasets and performing common statistical analyses through a simple web interface.

The application is developed inside the `yugen-analytica/` directory of the `yugen-beyondverse` repository.

## Features

### Dataset Import
- CSV files
- Excel `.xlsx` files
- Excel `.xls` files
- Dataset preview
- Basic validation
- Missing-value detection
- Row and column summary

### Descriptive Statistics
For numerical variables, StatsYuri calculates:
- Count
- Mean
- Median
- Standard deviation
- Minimum
- First quartile (Q1)
- Third quartile (Q3)
- Maximum
- Interquartile range (IQR)

### Outlier Detection
Potential outliers are detected using the 1.5 × IQR rule.

### Data Visualization
- Histograms
- Box plots
- Numerical-column selection

### Correlation Analysis
- Pearson correlation coefficients
- Correlation matrix
- Correlation heatmap

### Hypothesis Testing

#### One-Sample t-Test
Tests whether a population mean differs from a specified hypothesized mean.

The interface provides:
- Sample mean
- Hypothesized mean
- t-statistic
- p-value
- Degrees of freedom
- Significance-level selection
- Result interpretation

#### Two-Sample t-Test
Compares the means of two independent groups using Welch's two-sample t-test.

The interface provides:
- Group selection
- Numerical-variable selection
- Group sample sizes
- Group means
- Mean difference
- t-statistic
- p-value
- Welch-Satterthwaite degrees of freedom
- Significance-level selection
- Result interpretation

## Project Structure

```text
yugen-beyondverse/
└── yugen-analytica/
    ├── app.py
    ├── requirements.txt
    └── src/
        ├── __init__.py
        ├── data_loader.py
        ├── statistics.py
        └── visualization.py
```

## Technologies

- Python
- Streamlit
- Pandas
- SciPy
- Matplotlib
- OpenPyXL
- xlrd

## Running Locally

From the `yugen-analytica` directory:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Supported Data

The application accepts:
- `.csv`
- `.xlsx`
- `.xls`

For hypothesis testing, the uploaded dataset must contain the observations required by the selected test. The two-sample t-test requires a grouping column containing at least two groups and sufficient numerical observations in both selected groups.

## Statistical Notes

The one-sample t-test is a two-sided test of a specified population mean.

The two-sample test uses Welch's method, which does not require the two groups to have equal population variances.

A p-value is interpreted relative to the selected significance level (α). A small p-value provides evidence against the corresponding null hypothesis. Failing to reject a null hypothesis does not prove that the null hypothesis is true.

## Version

StatsYuri v1.2

The current version represents the completed initial statistical-analysis scope of the project.
