"""
MetOcean Intelligence Platform — FastAPI Backend v2.1.0
Transfer Learning Time Series Forecasting with LLM Integration
"""

import logging
import os
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from time import time
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth import create_access_token, create_user, authenticate_user, get_current_user
from src.db import init_db, get_db
from src.models import AuthMessage, LoginRequest, SignupRequest, TokenResponse, User
from sqlalchemy.orm import Session

# ── Logging Setup ──────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent
LOG_DIR = Path(os.getenv("METOCEAN_LOG_DIR", APP_DIR))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / os.getenv("METOCEAN_LOG_FILE", "app.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("metocean.api")

# ── Deferred heavy import (prevents crash if torch not installed yet) ─────────
try:
    from datasetsforecast.losses import mae, mape, rmse, smape
    from src.nf import MODELS, forecast_pretrained_model
    ML_AVAILABLE = True
    logger.info("ML dependencies loaded successfully.")
except Exception as exc:  # pragma: no cover
    ML_AVAILABLE = False
    logger.warning("ML dependencies unavailable: %s — running in stub mode.", exc)
    MODELS = {}

# ── Constants ──────────────────────────────────────────────────────────────────
DATASETS: Dict[str, str] = {
    "Electricity (Ercot COAST)": (
        "https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series"
        "/main/datasets/ercot_COAST.csv"
    ),
    "Web Traffic (Peyton Manning)": (
        "https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series"
        "/main/datasets/peyton_manning.csv"
    ),
    "Demand (AirPassengers)": (
        "https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series"
        "/main/datasets/air_passengers.csv"
    ),
    "Finance (Exchange USD-EUR)": (
        "https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series"
        "/main/datasets/usdeur.csv"
    ),
    "Oil & Gas (MetOcean Demo)": "timeseries_oil_and_Gas.csv",
}

# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MetOcean Intelligence Platform starting up…")
    init_db()
    logger.info("Database initialised.")
    logger.info("ML available: %s | Models loaded: %d", ML_AVAILABLE, len(MODELS))
    yield
    logger.info("Platform shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MetOcean Intelligence Platform",
    description=(
        "Integration of MetOcean Data for Intelligent Operations and Automation "
        "Using Large Language Models (LLMs) — Time Series Forecasting API"
    ),
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Logging Middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time()
    logger.info("→ %s %s  client=%s", request.method, request.url.path, request.client.host)
    response = await call_next(request)
    duration = time() - start
    logger.info(
        "← %s %s  status=%d  %.3fs",
        request.method, request.url.path, response.status_code, duration
    )
    return response


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method, request.url.path, exc, traceback.format_exc()
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs for details."},
    )


# ── Auth Endpoints ─────────────────────────────────────────────────────────────
@app.post("/auth/signup", response_model=AuthMessage, summary="Register a new account")
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        user = create_user(db, str(payload.email), payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return AuthMessage(message="Account created successfully.", email=user.email)


@app.post("/auth/login", response_model=TokenResponse, summary="Sign in and get JWT")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token(user.email)
    return TokenResponse(access_token=token, email=user.email)


@app.get("/auth/verify", response_model=AuthMessage, summary="Verify a JWT bearer token")
async def verify(current_user: User = Depends(get_current_user)):
    return AuthMessage(message="Token is valid.", email=current_user.email)

# ── Core Plot Helper ──────────────────────────────────────────────────────────
def plot(df, uid, df_forecast, model):
    """Creates a Plotly figure for the forecast."""
    logger.info(f"[PLOT DEBUG] uid={uid}, df shape={df.shape}, df_forecast shape={df_forecast.shape if df_forecast is not None else 'None'}")
    logger.info(f"[PLOT DEBUG] df_forecast columns: {df_forecast.columns.tolist() if df_forecast is not None else 'N/A'}")
    
    # Ensure datetime columns are properly formatted
    ds_hist = df["ds"].dt.strftime('%Y-%m-%d %H:%M:%S').to_list() if pd.api.types.is_datetime64_any_dtype(df["ds"]) else df["ds"].astype(str).to_list()
    y_hist = df["y"].to_list()
    
    figs = [
        go.Scatter(
            x=ds_hist,
            y=y_hist,
            mode="lines",
            marker=dict(color="#236796"),
            name=uid,
            showlegend=True,
        )
    ]
    if df_forecast is not None and not df_forecast.empty:
        # Format dates consistently
        ds_f = df_forecast["ds"].dt.strftime('%Y-%m-%d %H:%M:%S').to_list() if pd.api.types.is_datetime64_any_dtype(df_forecast["ds"]) else df_forecast["ds"].astype(str).to_list()
        lo = df_forecast["forecast_lo_90"].to_list()
        hi = df_forecast["forecast_hi_90"].to_list()
        
        # DEBUG: Check all columns for forecast-like data
        logger.info(f"[PLOT DEBUG] df_forecast.head():\n{df_forecast.head()}")
        logger.info(f"[PLOT DEBUG] df_forecast dtypes: {df_forecast.dtypes}")
        
        forecast_vals = df_forecast["forecast"].to_list()
        
        logger.info(f"[PLOT DEBUG] hi sample: {hi[:3]}, lo sample: {lo[:3]}")
        logger.info(f"[PLOT DEBUG] forecast_vals sample: {forecast_vals[:3]}")
        logger.info(f"[PLOT DEBUG] forecast min={min(forecast_vals) if forecast_vals else 'EMPTY'}, max={max(forecast_vals) if forecast_vals else 'EMPTY'}")
        logger.info(f"[PLOT DEBUG] forecast_vals count: {len(forecast_vals)}, actual type: {type(forecast_vals[0]) if forecast_vals else 'N/A'}")
        
        # Check if 'y' column exists and its values
        if 'y' in df_forecast.columns:
            y_vals = df_forecast["y"].to_list()
            logger.info(f"[PLOT DEBUG] EXTRA 'y' column found! y sample: {y_vals[:3]}, y min/max: {min(y_vals)}/{max(y_vals)}")
        
        figs.extend([
            go.Scatter(
                x=ds_f + ds_f[::-1],
                y=hi + lo[::-1],
                fill="toself",
                fillcolor="#E7C4C0",
                mode="lines",
                line=dict(color="#E7C4C0"),
                name="Prediction Intervals (90%)",
                opacity=0.5,
                hoverinfo="skip",
                showlegend=True,
            ),
            go.Scatter(
                x=ds_f,
                y=forecast_vals,  # Use the converted list, not the column directly
                mode="lines",
                marker=dict(color="#E7C4C0"),
                name=f"Forecast {uid}",
                showlegend=True,
            ),
        ])
    fig = go.Figure(figs)
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        title=f"Forecasts for {uid} using Transfer Learning (from {model})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, b=20),
        xaxis=dict(rangeslider=dict(visible=True)),
    )
    if not df.empty and df_forecast is not None and not df_forecast.empty:
        # Set initial x-axis range using formatted strings
        ds_start = df.tail(200)["ds"].iloc[0]
        ds_end = df_forecast["ds"].max()
        
        if pd.api.types.is_datetime64_any_dtype(ds_start):
            ds_start_str = pd.Timestamp(ds_start).strftime('%Y-%m-%d %H:%M:%S')
            ds_end_str = pd.Timestamp(ds_end).strftime('%Y-%m-%d %H:%M:%S')
        else:
            ds_start_str = str(ds_start)
            ds_end_str = str(ds_end)
        
        fig["layout"]["xaxis"].update(range=[ds_start_str, ds_end_str])
    
    # LOG FINAL FIGURE STRUCTURE
    fig_dict = fig.to_dict()
    logger.info(f"[FIGURE CREATION] Total traces in figure: {len(fig_dict.get('data', []))}")
    for i, trace in enumerate(fig_dict.get('data', [])):
        logger.info(f"[FIGURE CREATION] Trace {i}: name='{trace.get('name')}', mode='{trace.get('mode')}', "
                   f"x_len={len(trace.get('x', []))}, y_len={len(trace.get('y', []))}, "
                   f"visible={trace.get('visible')}, showlegend={trace.get('showlegend')}, "
                   f"fill={trace.get('fill')}")
        if trace.get('y'):
            y_sample = trace.get('y')[:3]
            logger.info(f"[FIGURE CREATION] Trace {i} y_sample: {y_sample}")
    
    return fig

# ── Core Processing ──────────────────────────────────────────────────────────
def process_forecast(
    df: pd.DataFrame,
    model_name: str,
    fh: int,
    max_steps: int,
    cv_windows: int,
):
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML dependencies not installed. Run: uv pip install -r requirements.txt",
        )

    if model_name not in MODELS:
        available = list(MODELS.keys())
        raise HTTPException(
            status_code=422,
            detail=f"Unknown model '{model_name}'. Available: {available}",
        )

    model_file = MODELS[model_name]["model"]
    
    # RUN FORECAST FIRST with clean, unmodified data
    init = time()
    try:
        df_forecast = forecast_pretrained_model(df.copy(), model_file, fh, max_steps)
    except Exception as exc:
        if max_steps > 0:
            raise HTTPException(status_code=422, detail=(
                "Fine-tuning failed — the installed PyTorch Lightning version is "
                "incompatible with the model's LR scheduler. "
                "Set fine-tuning steps to 0 to use the pretrained model directly."
            ))
        raise HTTPException(status_code=500, detail=f"Forecast inference failed: {exc}")
    end = time()
    
    # NOW prepare the original df for plotting and CV (after forecast is done and df hasn't been mutated)
    if "unique_id" not in df.columns:
        df.insert(0, "unique_id", "ts_0")
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
    df = df.dropna(subset=["ds"])
    df = df.sort_values(["unique_id", "ds"])
    uid = df["unique_id"].unique()[0]
    
    # CRITICAL FIX: Ensure df_forecast uses the same unique_id as df (not "ts_1" from nf.py)
    if "unique_id" in df_forecast.columns:
        df_forecast["unique_id"] = uid

    df_forecast = df_forecast.rename(columns={
        "y_5": "forecast_lo_90",
        "y_50": "forecast",
        "y_95": "forecast_hi_90",
    })
    
    logger.info(f"[FORECAST DATA] Before plot - df_forecast columns: {df_forecast.columns.tolist()}")
    logger.info(f"[FORECAST DATA] Forecast column stats: min={df_forecast['forecast'].min():.2f}, max={df_forecast['forecast'].max():.2f}, mean={df_forecast['forecast'].mean():.2f}")
    logger.info(f"[FORECAST DATA] First 5 forecast values: {df_forecast['forecast'].head(5).tolist()}")
    logger.info(f"[FORECAST DATA] ds column sample: {df_forecast['ds'].head(3).tolist()}")
    logger.info(f"[FORECAST DATA] Calling plot with df_forecast_for_plot shape: {df_forecast.query('unique_id == @uid').copy().shape}")
    
    forecast_plot = plot(df.query("unique_id == @uid").copy(), uid, df_forecast.query("unique_id == @uid").copy(), model_name)
    inference_time_message = f'Approximate inference time CPU: {0.7*(end - init):.2f} seconds.'

    df_cv_forecast_list = []
    if cv_windows > 0:
        for i_window in range(cv_windows, 0, -1):
            test = df.groupby("unique_id").tail(i_window * fh)
            train = df.drop(test.index)
            if not train.empty:
                df_fcst = forecast_pretrained_model(train.copy(), model_file, fh, max_steps)
                # CRITICAL FIX: Ensure unique_id matches (nf.py defaults to "ts_1")
                if "unique_id" in df_fcst.columns:
                    df_fcst["unique_id"] = uid
                df_fcst = df_fcst.rename(columns={
                    "y_5": "forecast_lo_90",
                    "y_50": "forecast",
                    "y_95": "forecast_hi_90",
                })
                df_fcst.insert(2, "window", i_window)
                df_cv_forecast_list.append(df_fcst)

    if df_cv_forecast_list:
        df_cv_forecast = pd.concat(df_cv_forecast_list)
        df_cv_forecast["ds"] = pd.to_datetime(df_cv_forecast["ds"])
        df_cv_forecast = df_cv_forecast.merge(df, how="left", on=["unique_id", "ds"])
        # Reset index to ensure forecast column values are preserved (fixes 0-17 index issue)
        df_cv_forecast = df_cv_forecast.reset_index(drop=True)
        # Ensure ds remains datetime after merge for proper serialization
        df_cv_forecast["ds"] = pd.to_datetime(df_cv_forecast["ds"])
        evaluation = df_cv_forecast.groupby(["unique_id", "window"]).apply(lambda x: pd.Series([round(mae(x['y'].values, x['forecast'].values), 2), round(mape(x['y'].values, x['forecast'].values), 2), round(rmse(x['y'].values, x['forecast'].values), 2), round(smape(x['y'].values, x['forecast'].values), 2)], index=["MAE", "MAPE", "RMSE", "sMAPE"])).reset_index()
        cv_plot = plot(df.query("unique_id == @uid"), uid, df_cv_forecast.query("unique_id == @uid"), model_name)
        cv_metrics_df = evaluation.query("unique_id == @uid").set_index("window")
    else:
        cv_plot = go.Figure()
        cv_metrics_df = pd.DataFrame()

    return forecast_plot, df_forecast, inference_time_message, cv_plot, cv_metrics_df


# ── Metadata Endpoints ────────────────────────────────────────────────────────
@app.get("/models", summary="List available forecasting models")
async def list_models(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        from src.model_descriptions import model_cards as _cards
    except Exception:
        _cards = {}
    cards_out: Dict[str, Any] = {}
    for name, meta in MODELS.items():
        card_key = meta.get("card", "")
        card = _cards.get(card_key, {})
        cards_out[name] = {
            "Abstract": card.get("Abstract", ""),
            "Intended use": card.get("Intended use", ""),
            "Limitations": card.get("Limitations", ""),
            "Training data": card.get("Training data", ""),
            "Citation Info": card.get("Citation Info", ""),
        }
    return {
        "models": list(MODELS.keys()),
        "count": len(MODELS),
        "ml_available": ML_AVAILABLE,
        "model_cards": cards_out,
    }


@app.get("/datasets", summary="List available built-in datasets")
async def list_datasets(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "datasets": list(DATASETS.keys()),
        "count": len(DATASETS),
    }


@app.get("/health", summary="Health check")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "ml_available": ML_AVAILABLE,
        "models_loaded": len(MODELS),
    }


# ── Forecast Endpoint ─────────────────────────────────────────────────────────
@app.post("/forecast/", summary="Run a time series forecast")
async def create_forecast(
    file: Optional[UploadFile] = File(None),
    url_input: Optional[str] = Form(None),
    data_selection: Optional[str] = Form("Electricity (Ercot COAST)"),
    model_name: str = Form("Pretrained N-HiTS M4 Hourly"),
    fh: int = Form(18),
    max_steps: int = Form(0),
    cv_windows: int = Form(1),
    timestamp_col: Optional[str] = Form(None),
    value_col: Optional[str] = Form(None),
    unique_id_col: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Unified forecast endpoint.
    Data priority: uploaded file > url_input > data_selection (built-in dataset).
    All parameters sent as multipart/form-data.
    """
    # ── Validate parameters ───────────────────────────────────────────────────
    if fh < 1 or fh > 500:
        raise HTTPException(status_code=422, detail="fh must be between 1 and 500.")
    if max_steps < 0 or max_steps > 5000:
        raise HTTPException(status_code=422, detail="max_steps must be between 0 and 5000.")
    if cv_windows < 0 or cv_windows > 20:
        raise HTTPException(status_code=422, detail="cv_windows must be between 0 and 20.")

    # ── Load data ─────────────────────────────────────────────────────────────
    try:
        if file and file.filename:
            if not file.filename.endswith(".csv"):
                raise HTTPException(status_code=422, detail="Only CSV files are supported.")
            logger.info("Loading uploaded file: %s  size=%s", file.filename, file.size)
            df = pd.read_csv(file.file)
        elif url_input:
            logger.info("Loading CSV from URL: %s", url_input)
            df = pd.read_csv(url_input)
        else:
            if data_selection not in DATASETS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unknown dataset '{data_selection}'. Available: {list(DATASETS.keys())}",
                )
            path_or_url = DATASETS[data_selection]
            logger.info("Loading built-in dataset: %s", data_selection)
            df = pd.read_csv(path_or_url)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to load data: %s", exc)
        raise HTTPException(status_code=422, detail=f"Failed to load data: {exc}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Loaded dataset is empty.")

    # ── Standardize column names ──────────────────────────────────────────────
    if "ds" not in df.columns or "y" not in df.columns:
        if timestamp_col and value_col:
            if timestamp_col not in df.columns or value_col not in df.columns:
                raise HTTPException(
                    status_code=422,
                    detail=f"Columns '{timestamp_col}' or '{value_col}' not found in uploaded file.",
                )
            df = df.rename(columns={timestamp_col: "ds", value_col: "y"})
        elif "timestamp" in df.columns and "value" in df.columns:
            df = df.rename(columns={"timestamp": "ds", "value": "y"})
        else:
            logger.warning(
                "No ds/y columns found. Using first two columns: %s, %s",
                df.columns[0], df.columns[1],
            )
            df = df.rename(columns={df.columns[0]: "ds", df.columns[1]: "y"})

    # ── Resolve unique_id column ──────────────────────────────────────────────
    if "unique_id" not in df.columns:
        # Only rename if the user explicitly selected an ID column.
        # Otherwise let process_forecast insert "ts_0" for the whole dataset,
        # which matches main.py behaviour (treats all rows as one series).
        if unique_id_col and unique_id_col != "" and unique_id_col in df.columns:
            logger.info("Using column '%s' as unique_id", unique_id_col)
            df = df.rename(columns={unique_id_col: "unique_id"})

    # ── Strip to essential columns only ───────────────────────────────────────
    keep = [c for c in ("unique_id", "ds", "y") if c in df.columns]
    df = df[keep]

    # ── Run forecast ──────────────────────────────────────────────────────────
    forecast_plot, df_forecast, inference_time, cv_plot, eval_df = process_forecast(
        df, model_name, fh, max_steps, cv_windows
    )

    return {
        "inference_time": inference_time,
        "forecast_data": df_forecast.to_dict(orient="records"),
        "evaluation_metrics": eval_df.reset_index().to_dict(orient="records"),
        "forecast_plot_json": forecast_plot.to_json(),
        "cv_plot_json": cv_plot.to_json(),
    }
