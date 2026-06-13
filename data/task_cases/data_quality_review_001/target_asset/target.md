dataset_contract.yaml: required_fields=[user_id,event_date,country_code,label]; allowed_labels=[basic,premium,enterprise]; validation_cutoff=2025-04-30.

train.csv sample:
- row 1042: user_id=991, event_date=2025-04-11, country_code=, label=basic
- row 9811: user_id=112, event_date=2025-05-04, country_code=US, label=gold_plus

validation.csv sample:
- row 120: user_id=556, event_date=2025-05-05, country_code=CN, label=premium
