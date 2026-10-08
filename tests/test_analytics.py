"""Explicit tiny fixtures verify formulas; none are application fallback data."""
import math
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.analytics import clean_data, filter_weather, summarize, daily_extremes, monthly_trends
from backend.forecast import make_features, chronological_split
from backend.mapreduce import map_reduce
from backend.streaming import reservoir_sample
from backend import main


def sample():
    return pd.DataFrame({"city": ["Hyderabad"] * 4, "time": pd.to_datetime(["2021-01-01 00:00", "2021-01-01 01:00", "2021-01-02 00:00", "2021-01-02 01:00"]), "temperature": [10.,20.,40.,42.], "humidity": [40.,50.,60.,70.], "precipitation": [1.,2.,30.,25.], "wind_speed": [2.,4.,6.,8.], "latitude": [17.385]*4, "longitude": [78.487]*4})


def test_clean_rejects_bad_values_and_deduplicates():
    raw = pd.concat([sample(), sample().iloc[[0]], sample().iloc[[1]].assign(humidity=101), sample().iloc[[1]].assign(time="bad"), sample().iloc[[2]].assign(temperature=float("nan"))], ignore_index=True)
    clean, quality = clean_data(raw)
    assert len(clean) == 4
    assert quality["input_rows"] == 8
    assert quality["duplicates_removed"] == 1
    assert quality["invalid_rows"] == 3
    assert quality["missing_values"] == 1


def test_summary_uses_sample_variance_and_city_hour_rain_total():
    result = summarize(sample())
    assert result["avg_temperature"] == 28
    assert result["total_precipitation"] == 58
    assert result["temperature_variance"] == pytest.approx(sample().temperature.var(ddof=1))
    assert summarize(sample().iloc[:1])["temperature_std"] is None


def test_daily_extremes_count_events_not_hours():
    events = daily_extremes(sample())
    assert len(events) == 2
    assert {x["type"] for x in events} == {"Heat", "Heavy rain"}
    assert {x["value"] for x in events} == {42, 55}


def test_inclusive_date_end_and_invalid_ranges():
    assert len(filter_weather(sample(), "Hyderabad", "2021-01-01", "2021-01-01")) == 2
    for city,start,end in [("Unknown","2021-01-01","2021-01-02"),("all","2021-02-01","2021-01-01"),("all","2021-02-30","2021-03-01")]:
        with pytest.raises(ValueError):
            filter_weather(sample(),city,start,end)


def test_monthly_mean_and_total():
    trend = monthly_trends(sample())[0]
    assert trend["date"] == "2021-01"
    assert trend["temperature"] == 28
    assert trend["precipitation"] == 58


def test_chronological_features_do_not_use_target_day():
    daily = pd.DataFrame({"date": pd.date_range("2021-01-01", periods=50), "temperature": range(50)})
    features = make_features(daily)
    assert (features.lag_1 + 1 == features.temperature).all()
    train, test = chronological_split(features)
    assert train.date.max() < test.date.min()
    assert train.temperature.max() < test.temperature.min()


def test_map_reduce_matches_direct_totals():
    result = map_reduce(sample(), partitions=3)
    assert result["rows"] == 4
    assert result["cities"][0]["temperature"] == 28
    assert result["cities"][0]["precipitation"] == 58


def test_reservoir_is_bounded_deterministic_and_counts_all():
    a = reservoir_sample(iter(range(100)), size=7, seed=19)
    assert a == reservoir_sample(iter(range(100)), size=7, seed=19)
    assert a["seen"] == 100 and len(a["sample"]) == 7
    assert len(set(a["sample"])) == 7


def test_api_validation_empty_and_csv(monkeypatch):
    monkeypatch.setattr(main, "load_weather", sample)
    client = TestClient(main.app)
    assert client.get("/api/dashboard?city=Unknown").status_code == 422
    assert client.get("/api/dashboard?start=2022-01-01&end=2021-01-01").status_code == 422
    assert client.get("/api/dashboard?start=2021-02-30").status_code == 422
    assert client.get("/api/dashboard?start=2022-01-01&end=2022-01-02").status_code == 404
    response = client.get("/api/export?city=Hyderabad&start=2021-01-01&end=2021-01-01")
    assert response.status_code == 200
    assert len(pd.read_csv(__import__('io').StringIO(response.text))) == 2
    response = client.get("/api/dashboard?start=2021-01-01&end=2021-01-02")
    assert response.status_code == 200
    result = response.json()
    assert result["summary"]["extreme_count"] == 2
    assert result["meta"]["filtered_records"] == 4
    assert result["correlation"]["matrix"][0][0] == pytest.approx(1)
    assert "city-hours" in " ".join(result["insights"])


def test_rejects_non_iso_date_formats():
    for value in ["20210101", "2021-W01-1", "2021-1-01", "2021-01-01T00:00:00"]:
        with pytest.raises(ValueError):
            filter_weather(sample(), "all", value, "2021-01-02")


def test_api_missing_data_returns_useful_503(monkeypatch):
    def absent():
        raise FileNotFoundError("Run ingestion and pipeline")
    monkeypatch.setattr(main, "load_weather", absent)
    response = TestClient(main.app).get("/api/dashboard")
    assert response.status_code == 503
    assert "ingestion" in response.json()["detail"]


def test_constant_correlation_serializes_null(monkeypatch):
    monkeypatch.setattr(main, "load_weather", lambda: sample().assign(humidity=50))
    response=TestClient(main.app).get("/api/dashboard")
    assert response.status_code==200
    matrix=response.json()["correlation"]["matrix"]
    assert all(value is None for value in matrix[1])


def test_forecast_persistence_uses_exact_previous_observed_day():
    from backend.forecast import evaluate_city
    times=pd.date_range("2021-01-01", periods=24*60, freq="h")
    frame=pd.DataFrame({"city":"Hyderabad","time":times,"temperature":[10 + (x//24)%7 for x in range(len(times))]})
    result=evaluate_city(frame,"Hyderabad")
    assert result["available"]
    assert result["train_end"] < result["test_start"]
    for point in result["points"]:
        day=(pd.Timestamp(point["date"])-pd.Timestamp("2021-01-01")).days
        assert point["actual"] == 10+day%7
        assert point["baseline"] == 10+(day-1)%7
    expected=sum(abs(p["actual"]-p["baseline"]) for p in result["points"])/result["test_samples"]
    assert result["baseline_mae"]==pytest.approx(expected,abs=1e-6)


def test_stale_spark_evidence_cannot_mark_refreshed_dataset_verified(tmp_path, monkeypatch):
    import hashlib, json
    monkeypatch.setattr(main,"PROCESSED",tmp_path)
    data=tmp_path/"weather.parquet"; data.write_bytes(b"version 1")
    evidence={"status":"verified","parity_passed":True,"dataset_sha256":hashlib.sha256(data.read_bytes()).hexdigest(),"engine":"Apache Spark local"}
    (tmp_path/"spark_evidence.json").write_text(json.dumps(evidence))
    assert main.pipeline_status()["spark_verified"] is True
    data.write_bytes(b"version 2")
    assert main.pipeline_status()["spark_verified"] is False


def test_health_rejects_corrupt_or_incoherent_dataset(tmp_path, monkeypatch):
    import json
    import backend.analytics as analytics
    monkeypatch.setattr(analytics,"PROCESSED",tmp_path)
    monkeypatch.setattr(main,"PROCESSED",tmp_path)
    path=tmp_path/"weather.parquet"
    path.write_bytes(b"not parquet")
    (tmp_path/"manifest.json").write_text(json.dumps({"total_records":4,"city_count":1,"quality":{"clean_rows":4}}))
    assert TestClient(main.app).get("/api/health").json()["data_ready"] is False
    sample().to_parquet(path,index=False)
    assert TestClient(main.app).get("/api/health").json()["data_ready"] is False  # missing content hash


def test_loaded_weather_refreshes_when_file_changes(tmp_path, monkeypatch):
    import backend.analytics as analytics
    monkeypatch.setattr(analytics,"PROCESSED",tmp_path)
    path=tmp_path/"weather.parquet"
    sample().to_parquet(path,index=False)
    assert len(analytics.load_weather())==4
    sample().iloc[:2].to_parquet(path,index=False)
    assert len(analytics.load_weather())==2
