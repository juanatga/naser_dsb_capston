# Western Balkan Route: Migration Trends and Forecasting

DSB Capstone Project — with a focus on Montenegro

This project looks at recorded migration arrivals along the Western Balkan Route (WBR) and explores how historical monthly data can be used to forecast arrivals in Montenegro. It combines exploratory analysis with a comparison of three regression models and a seasonal baseline.

The main question is straightforward: **how well can past arrival patterns help estimate the next 3, 6 and 12 months?** The analysis covers both the regional WBR series and Montenegro separately, so the local results can be considered alongside the wider route.

## Data

The notebooks use the International Organization for Migration (IOM) Displacement Tracking Matrix (DTM) workbook, `DTM Europe_Q1_2026_Dataset.xlsx`.

Five sheets are explored:

| Sheet | Use in the project |
| --- | --- |
| `First_Arrival_Countries_Monthly` | Overview of monthly arrivals across first-arrival routes |
| `Other_Countries_Areas_Monthly` | Main source for WBR and Montenegro forecasting |
| `First_Arrival_Countries_CoO` | Inspection of country-of-origin data |
| `Others_Countries_CoO` | Country-of-origin breakdown for Montenegro |
| `All_Migrant_Presence` | Separate overview of reported migrant presence |

The saved outputs show 123 monthly observations from **January 2016 to March 2026** for both forecasting series, with no missing months. Montenegro's filtered series contains 40,897 recorded arrivals over that period.

Here, “arrivals” means recorded arrival events, not necessarily unique people. Regional totals add records across the countries represented in the source and may count the same person more than once. Migrant presence is a different measure and is kept separate.

## Project files

| Notebook | Contents |
| --- | --- |
| `01_EDA_Final.ipynb` | Data loading, quality checks, route trends, Montenegro analysis and CSV exports |
| `02_Modeling (1).ipynb` | Model comparison and recursive forecasting for the overall WBR series; includes an interactive map |
| `02_1_Modeling_Montenegro_Only (1).ipynb` | Dedicated model comparison and forecasts for Montenegro |

Each modeling notebook loads the Excel workbook directly. It does not depend on the CSV exports from the EDA notebook.

## Approach

The EDA checks missing values, duplicate rows, date coverage and route labels before building monthly series. Montenegro is selected using both `Route == 'WBR'` and `ISO3 - Country of arrival == 'MNE'`.

The models use a time index, seasonal month features, arrival lags of 1, 3, 6 and 12 months, and rolling averages over the previous 3 and 6 months. Rolling averages are shifted to exclude the month being predicted.

Three models are compared: Linear Regression, Ridge Regression and Random Forest. A seasonal-naive baseline predicts the value recorded in the same month a year earlier.

After creating features, 111 observations remain. The first 99 are used for training, and the last 12 — April 2025 to March 2026 — for testing. Three expanding-window cross-validation splits provide an additional check on performance across earlier periods.

## Results

These figures come from the saved notebook outputs. MAE and RMSE are measured in recorded arrivals; lower values indicate smaller errors.

| Series | Model | MAE | RMSE | R² |
| --- | --- | ---: | ---: | ---: |
| WBR | Random Forest | 578.75 | 740.38 | 0.12 |
| WBR | Seasonal Naive | 1,154.25 | 1,261.21 | -1.56 |
| WBR | Linear Regression | 1,210.77 | 1,499.68 | -2.62 |
| WBR | Ridge Regression | 1,405.93 | 1,756.58 | -3.96 |
| Montenegro | Linear Regression | 61.50 | 84.89 | 0.24 |
| Montenegro | Random Forest | 63.00 | 95.85 | 0.03 |
| Montenegro | Ridge Regression | 71.46 | 88.97 | 0.16 |
| Montenegro | Seasonal Naive | 146.92 | 176.97 | -2.31 |

Random Forest has the lowest test MAE for the regional series, while Linear Regression performs best for Montenegro. The Montenegro model's MAE corresponds to an average absolute error of about 62 recorded arrivals per test month.

The ranking changes in cross-validation: Ridge performs best for WBR and Random Forest for Montenegro. Errors are also higher in those earlier periods, so the final test results should not be taken as evidence of consistently strong performance. The code selects the final models by test MAE; cross-validation results are reported separately.

## Forecasts

The selected models are refitted on all available observations and used recursively: each monthly prediction becomes part of the history used to predict the next month. Negative forecasts are clipped to zero.

The current forecast covers **April 2026 to March 2027**, with shorter 3- and 6-month views of the same period. It does not cover the whole of calendar year 2027.

For Montenegro, the saved forecast rises from approximately 478 arrivals in April 2026 to 642 in August, before declining to 315 by March 2027. These are model estimates, not confirmed future arrivals.

## Running the notebooks

Use Google Colab or a local Jupyter environment. The required packages are:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn openpyxl folium
```

1. Obtain `DTM Europe_Q1_2026_Dataset.xlsx` from IOM DTM. The workbook is required separately.
2. Upload it to Colab, or update `file_path` in each notebook to its local location. The current path is `/content/DTM Europe_Q1_2026_Dataset.xlsx`.
3. Start with the EDA notebook, then run the regional and Montenegro modeling notebooks from top to bottom.
4. For local runs, also update the map output paths, which currently point to `/content/`.

The EDA export cell writes five prepared sheet CSVs and two monthly-series CSVs to `data/processed/`. The regional notebook saves `wbr_full_route_map.html`.

**Known issue:** the final map cell in the Montenegro notebook references `folium`, `AntPath`, `locations`, `corridors` and `country_totals` without defining them in that notebook. Skip that cell to run the forecasting analysis independently, or add the map setup from the regional notebook. The map corridors are illustrative paths defined in code, not tracked individual journeys.

## Limitations and next steps

The test predictions use observed historical lags within the test period. They therefore assess one-month-ahead predictions with updated observations, rather than a full 12-month recursive forecast made at one starting date. A useful next step is to backtest the actual 3-, 6- and 12-month forecasting procedure and select models through validation before a separate final test.

The models use historical arrivals and calendar patterns only. Policy changes, border restrictions, conflicts and other external factors are not included. Forecasts have no prediction intervals, and uncertainty can grow as predictions are fed into later months. Q1 2026 is also a partial year and should not be compared directly with complete annual totals.

This is an exploratory forecasting project. It offers a starting point for understanding recorded migration patterns and testing forecasting methods, rather than a ready-to-use operational planning system.
