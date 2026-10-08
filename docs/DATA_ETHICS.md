# Historical weather data: interpretation and attribution

Weather Data Analysis uses [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api). Preserve provider attribution, API request parameters, retrieval time, coordinates, variables, units and date range with each saved dataset. Consult [Open-Meteo terms](https://open-meteo.com/en/terms) and underlying dataset attribution before publishing or using the results commercially. The manifest/source metadata is authoritative for the exact downloaded dataset.

Reanalysis combines models with observations to estimate past weather on a grid. A selected city coordinate does not identify an individual station. Grid resolution, model choice and local geography affect representativeness; interpolation and missing inputs add uncertainty. A single-city aggregate should not be described as a precise measurement for every neighborhood.

Saved historical rows are not a live feed. Forecast plots in this project evaluate a model on a historical hold-out; they are not operational forecasts. Educational heat/rainfall thresholds are not meteorological warnings, emergency advice or official disaster declarations.

Public city-level weather records do not contain individual personal information. Combining them later with addresses, mobility, health or agricultural records could create privacy risks. Collect only needed fields, retain source permissions, avoid publishing identifiable joins and separate aggregate research outputs from personal records.

Charts should show units and selected dates, reveal missing values, and distinguish totals from averages. Summing rainfall over cities yields a sum across selected city-hours, not a physical depth of rain across the whole country. Correlation is not causation. Model evaluation must include its baseline, test dates and limitations even when the model performs worse.

Source retries must not silently substitute invented weather. Preserve failed requests and incomplete coverage as visible limitations. Synthetic fixtures are acceptable for unit tests only when explicitly labeled and kept separate from the delivered dataset.
