# Quickstart

## Install

```powershell
python -m pip install -e .[dev]
```

## Run The Demo UI

```powershell
python -m streamlit run demo\streamlit_app.py --server.port 8502
```

Open:

```text
http://127.0.0.1:8502/
```

## Run Core Validation

```powershell
python -m pytest -q
python scripts\validate_task_cases.py
python scripts\run_generalization_suite.py --scenarios upload,auth,config,api_review --backend offline_deterministic
python scripts\run_ablation_suite.py
python scripts\run_system_acceptance.py
```

## Export Review Package

```powershell
python scripts\export_review_package.py
python scripts\validate_review_package.py
```

Open:

```text
review_package/index.html
```

## Optional WSL2 / Harbor Check

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_wsl2_spark_backend.ps1
```
