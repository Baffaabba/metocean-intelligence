import os
from itertools import chain
from pathlib import Path
from typing import List, Optional

import neuralforecast as nf
import numpy as np
import pandas as pd
import pytorch_lightning as pl
from datasetsforecast.utils import download_file
from hyperopt import hp
from neuralforecast.auto import NHITS as autoNHITS
from neuralforecast.data.tsdataset import WindowsDataset
from neuralforecast.data.tsloader import TimeSeriesLoader
from neuralforecast.models.mqnhits.mqnhits import MQNHITS
from neuralforecast.models.nhits.nhits import NHITS

# GLOBAL PARAMETERS
DEFAULT_HORIZON = 30
HYPEROPT_STEPS = 10
MAX_STEPS = 1000
N_TS_VAL = 2 * 30

MODELS = {
    "Pretrained N-HiTS M4 Hourly": {
        "card": "nhitsh",
        "max_steps": 0,
        "model": "nhits_m4_hourly",
    },
    "Pretrained N-HiTS M4 Hourly (Tiny)": {
        "card": "nhitsh",
        "max_steps": 0,
        "model": "nhits_m4_hourly_tiny",
    },
    "Pretrained N-HiTS M4 Daily": {
        "card": "nhitsd",
        "max_steps": 0,
        "model": "nhits_m4_daily",
    },
    "Pretrained N-HiTS M4 Monthly": {
        "card": "nhitsm",
        "max_steps": 0,
        "model": "nhits_m4_monthly",
    },
    "Pretrained N-HiTS M4 Yearly": {
        "card": "nhitsy",
        "max_steps": 0,
        "model": "nhits_m4_yearly",
    },
    "Pretrained N-BEATS M4 Hourly": {
        "card": "nbeatsh",
        "max_steps": 0,
        "model": "nbeats_m4_hourly",
    },
    "Pretrained N-BEATS M4 Daily": {
        "card": "nbeatsd",
        "max_steps": 0,
        "model": "nbeats_m4_daily",
    },
    "Pretrained N-BEATS M4 Weekly": {
        "card": "nbeatsw",
        "max_steps": 0,
        "model": "nbeats_m4_weekly",
    },
    "Pretrained N-BEATS M4 Monthly": {
        "card": "nbeatsm",
        "max_steps": 0,
        "model": "nbeats_m4_monthly",
    },
    "Pretrained N-BEATS M4 Yearly": {
        "card": "nbeatsy",
        "max_steps": 0,
        "model": "nbeats_m4_yearly",
    },
}

MODEL_DIR = Path(os.getenv("METOCEAN_MODEL_DIR", Path(__file__).resolve().parents[1] / "models"))


def ensure_model_downloaded(model_name: str) -> Path:
    model_path = MODEL_DIR / f"{model_name}.ckpt"
    if not model_path.is_file():
        download_file(
            str(MODEL_DIR) + "/",
            f"https://nixtla-public.s3.amazonaws.com/transfer/pretrained_models/{model_name}.ckpt",
        )
    return model_path


class StandardScaler:
    """This class helps to standardize a dataframe with multiple time series."""

    def __init__(self):
        self.norm: pd.DataFrame

    def fit(self, X: pd.DataFrame) -> "StandardScaler":
        self.norm = X.groupby("unique_id").agg({"y": [np.mean, np.std]})
        self.norm = self.norm.droplevel(0, 1).reset_index()

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        transformed = X.merge(self.norm, how="left", on=["unique_id"])
        transformed["y"] = (transformed["y"] - transformed["mean"]) / transformed["std"]
        return transformed[["unique_id", "ds", "y"]]

    def inverse_transform(self, X: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        transformed = X.merge(self.norm, how="left", on=["unique_id"])
        for col in cols:
            transformed[col] = (
                transformed[col] * transformed["std"] + transformed["mean"]
            )
        return transformed[["unique_id", "ds"] + cols]


def compute_ds_future(Y_df, fh):
    if Y_df["unique_id"].nunique() == 1:
        ds_ = pd.to_datetime(Y_df["ds"].values)
        try:
            freq = pd.infer_freq(ds_)
        except:
            freq = None
        if freq is not None:
            ds_future = pd.date_range(ds_[-1], periods=fh + 1, freq=freq)[1:]
        else:
            freq = ds_[-1] - ds_[-2]
            ds_future = [ds_[-1] + (i + 1) * freq for i in range(fh)]
        ds_future = list(map(str, ds_future))
        return ds_future
    else:
        ds_future = chain(
            *[compute_ds_future(df, fh) for _, df in Y_df.groupby("unique_id")]
        )
        return list(ds_future)


def forecast_pretrained_model(
    Y_df: pd.DataFrame, model: str, fh: int, max_steps: int = 0
):
    if "unique_id" not in Y_df:
        Y_df.insert(0, "unique_id", "ts_1")

    scaler = StandardScaler()
    scaler.fit(Y_df)
    Y_df = scaler.transform(Y_df)

    # Model
    file_ = str(ensure_model_downloaded(model))
    mqnhits = MQNHITS.load_from_checkpoint(file_)

    # FIX: PyTorch Lightning 1.6.5 LR Scheduler Incompatibility
    # The model's configure_optimizers() returns an incompatible StepLR scheduler
    # Workaround: Override the method to return only the optimizer without scheduler
    if max_steps > 0:
        original_configure = mqnhits.configure_optimizers
        
        def configure_optimizers_no_scheduler(self=None):
            """Return optimizer only, skip incompatible scheduler."""
            result = original_configure()
            if isinstance(result, dict) and 'optimizer' in result:
                # Return only optimizer, drop scheduler
                return {'optimizer': result['optimizer']}
            elif isinstance(result, (list, tuple)):
                # Return only optimizer from tuple/list
                return result[0]
            return result
        
        mqnhits.configure_optimizers = configure_optimizers_no_scheduler

    # Fit
    if max_steps > 0:
        train_dataset = WindowsDataset(
            Y_df=Y_df,
            X_df=None,
            S_df=None,
            mask_df=None,
            f_cols=[],
            input_size=mqnhits.n_time_in,
            output_size=mqnhits.n_time_out,
            sample_freq=1,
            complete_windows=True,
            verbose=False,
        )

        train_loader = TimeSeriesLoader(
            dataset=train_dataset, batch_size=1, n_windows=32, shuffle=True
        )

        trainer = pl.Trainer(
            max_epochs=None,
            checkpoint_callback=False,
            logger=False,
            max_steps=max_steps,
            gradient_clip_val=1.0,
            progress_bar_refresh_rate=1,
            log_every_n_steps=1,
        )

        trainer.fit(mqnhits, train_loader)

    # Forecast
    forecast_df = mqnhits.forecast(Y_df=Y_df)
    forecast_df = scaler.inverse_transform(forecast_df, cols=["y_5", "y_50", "y_95"])

    # Foreoast
    n_ts = forecast_df["unique_id"].nunique()
    if fh * n_ts > len(forecast_df):
        forecast_df = (
            forecast_df.groupby("unique_id")
            .apply(lambda df: pd.concat([df] * fh).head(fh))
            .reset_index(drop=True)
        )
    else:
        forecast_df = forecast_df.groupby("unique_id").head(fh)
    forecast_df["ds"] = compute_ds_future(Y_df, fh)

    return forecast_df


if __name__ == "__main__":
    df = pd.read_csv(
        "https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series/main/datasets/ercot_COAST.csv"
    )
    df.columns = ["ds", "y"]
    multi_df = pd.concat([df.assign(unique_id=f"ts{i}") for i in range(2)])
    assert len(compute_ds_future(multi_df, 80)) == 2 * 80
    for _, meta in MODELS.items():
        # test just a time series (without unique_id)
        forecast = forecast_pretrained_model(df, model=meta["model"], fh=80)
        assert forecast.shape == (80, 5)
        # test multiple time series
        multi_forecast = forecast_pretrained_model(multi_df, model=meta["model"], fh=80)
        assert multi_forecast.shape == (80 * 2, 5)
