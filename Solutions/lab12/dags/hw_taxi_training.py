import pandas as pd
import pendulum
from airflow.sdk import dag, task


@task.virtualenv(
    requirements=["polars", "s3fs", "lazy_object_proxy"],
    serializer="cloudpickle",
)
def download_summary_data(storage_options: dict) -> dict[str, pd.DataFrame]:
    import polars as pl

    taxi_summary_path = f"s3://nyc-taxi/processed/taxi_data_summary_*-*.parquet"

    df = pl.read_parquet(taxi_summary_path, storage_options=storage_options)

    return {
        "train": df.filter(pl.col("date") < pl.date(2024, 12, 1)).to_pandas(),
        "test": df.filter(pl.col("date") >= pl.date(2024, 12, 1)).to_pandas(),
    }


@task.virtualenv(
    requirements=["scikit-learn", "pandas", "optuna", "lazy_object_proxy", "s3fs", "apache-airflow-task-sdk"],
    serializer="cloudpickle",
)
def train_ridge_regression_model(data: dict[str, pd.DataFrame]) -> dict:
    import optuna
    import cloudpickle
    from sklearn.linear_model import Ridge
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from sklearn.metrics import mean_squared_error
    from sklearn.preprocessing import StandardScaler
    from airflow.sdk import ObjectStoragePath

    model_path = ObjectStoragePath("s3://nyc-taxi/models/", conn_id='aws_default')
    model_path.mkdir(parents=True, exist_ok=True)

    train_df = data["train"]
    test_df = data["test"]

    feature_cols = ["month", "day_of_month", "quarter", "day_of_week", "is_weekend"]
    target_col = "total_trips"

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("Number of training samples: ", len(X_train), " Number of testing samples: ", len(X_test))
    print("Number of labels in training set: ", len(y_train), " Number of labels in testing set: ", len(y_test))

    def objective(trial):
        alpha = trial.suggest_loguniform("alpha", 1e-3, 1e3)

        model = Ridge(alpha=alpha)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        return mse

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50)

    best_params = study.best_params
    print(f"Best hyperparameters: {best_params}")

    model = Ridge(**best_params)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print(f"Mean Squared Error on test set: {mse}")

    model_file_path = model_path / "ridge_regression_model.pkl"
    with model_file_path.open("wb") as file:
        file.write(
            cloudpickle.dumps({"model": model, "scaler": scaler})
        )

    print(f"Model saved to {model_file_path}")

    hook = PostgresHook(postgres_conn_id="postgres_storage")
    hook.insert_rows(
        table="models",
        rows=[('ridge_regression', mse, len(X_train))],
        target_fields=["name", "test_performance", "training_size"]
    )

    return {"model": "ridge_regression", "mse": mse}


@task.virtualenv(
    requirements=["scikit-learn", "pandas", "optuna", "lazy_object_proxy", "s3fs", "apache-airflow-task-sdk"],
    serializer="cloudpickle",
)
def train_random_forest_model(data: dict[str, pd.DataFrame]) -> dict:
    import optuna
    import cloudpickle
    from airflow.sdk import ObjectStoragePath
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error
    from sklearn.preprocessing import StandardScaler

    model_path = ObjectStoragePath("s3://nyc-taxi/models/", conn_id='aws_default')
    model_path.mkdir(parents=True, exist_ok=True)

    train_df = data["train"]
    test_df = data["test"]

    feature_cols = ["month", "day_of_month", "quarter", "day_of_week", "is_weekend"]
    target_col = "total_trips"

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    print("Number of training samples: ", len(X_train), " Number of testing samples: ", len(X_test))
    print("Number of labels in training set: ", len(y_train), " Number of labels in testing set: ", len(y_test))

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    def objective(trial):
        n_estimators = trial.suggest_int("n_estimators", 20, 200)
        max_depth = trial.suggest_int("max_depth", 2, 30)

        model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        return mse

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50)

    best_params = study.best_params
    print(f"Best hyperparameters: {best_params}")

    model = RandomForestRegressor(**best_params, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print(f"Mean Squared Error on test set: {mse}")

    model_file_path = model_path / "random_forest_model.pkl"
    with model_file_path.open("wb") as file:
        file.write(
            cloudpickle.dumps({"model": model, "scaler": scaler})
        )

    print(f"Model saved to {model_file_path}")

    hook = PostgresHook(postgres_conn_id="postgres_storage")
    hook.insert_rows(
        table="models",
        rows=[('random_forest', mse, len(X_train))],
        target_fields=["name", "test_performance", "training_size"]
    )

    return {"model": "random_forest", "mse": mse}


@task.virtualenv(
    requirements=["scikit-learn", "pandas", "optuna", "lazy_object_proxy", "s3fs", "apache-airflow-task-sdk"],
    serializer="cloudpickle",
)
def train_svm(data: dict[str, pd.DataFrame]) -> dict:
    import optuna
    import cloudpickle
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from airflow.sdk import ObjectStoragePath
    from sklearn.svm import SVR
    from sklearn.metrics import mean_squared_error
    from sklearn.preprocessing import StandardScaler

    model_path = ObjectStoragePath("s3://nyc-taxi/models/", conn_id='aws_default')
    model_path.mkdir(parents=True, exist_ok=True)

    train_df = data["train"]
    test_df = data["test"]

    feature_cols = ["month", "day_of_month", "quarter", "day_of_week", "is_weekend"]
    target_col = "total_trips"

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("Number of training samples: ", len(X_train), " Number of testing samples: ", len(X_test))
    print("Number of labels in training set: ", len(y_train), " Number of labels in testing set: ", len(y_test))

    def objective(trial):
        C = trial.suggest_loguniform("C", 1e-3, 1e3)
        gamma = trial.suggest_loguniform("gamma", 1e-4, 1e1)
        kernel = trial.suggest_categorical("kernel", ["rbf", "poly", "sigmoid"])

        model = SVR(C=C, gamma=gamma, kernel=kernel)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        return mse

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50)

    best_params = study.best_params
    print(f"Best hyperparameters: {best_params}")

    model = SVR(**best_params)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print(f"Mean Squared Error on test set: {mse}")

    model_file_path = model_path / "svm_model.pkl"
    with model_file_path.open("wb") as file:
        file.write(
            cloudpickle.dumps({"model": model, "scaler": scaler})
        )

    print(f"Model saved to {model_file_path}")

    hook = PostgresHook(postgres_conn_id="postgres_storage")
    hook.insert_rows(
        table="models",
        rows=[('svm', mse, len(X_train))],
        target_fields=["name", "test_performance", "training_size"]
    )

    return {"model": "svm", "mse": mse}


@task
def select_best(results: list[dict]) -> None:
    from airflow.sdk import ObjectStoragePath

    best_model = min(results, key=lambda x: x["mse"])
    print(f"Best model: {best_model['model']} with MSE: {best_model['mse']}")

    models_dir = ObjectStoragePath("s3://nyc-taxi/models/", conn_id='aws_default')
    best_model_path = models_dir / f"{best_model['model'].lower()}_model.pkl"
    best_model_final_path = models_dir / "best_model.pkl"

    best_model_final_path.write_bytes(best_model_path.read_bytes())

    for result in results:
        model_path = models_dir / f"{result['model'].lower()}_model.pkl"
        model_path.unlink()

    print(f"Best model saved to {best_model_final_path}, other models removed.")


@dag(
    dag_id="nyc_taxi_training",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2024, 12, 31, tz="UTC"),
    schedule="@yearly",
    catchup=True
)
def nyc_taxi_training_dag():
    data = download_summary_data(
        storage_options={
            "aws_access_key_id": "{{ conn.aws_default.login }}",
            "aws_secret_access_key": "{{ conn.aws_default.password }}",
            "endpoint_url": "{{ conn.aws_default.extra_dejson.endpoint_url }}",
            "region_name": "{{ conn.aws_default.extra_dejson.region_name }}",
        }
    )

    results_ridge = train_ridge_regression_model(data)
    results_rf = train_random_forest_model(data)
    results_svm = train_svm(data)

    select_best([results_ridge, results_rf, results_svm])


nyc_taxi_training_dag()
