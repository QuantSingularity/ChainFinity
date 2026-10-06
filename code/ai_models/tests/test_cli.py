import json

import pytest
from ai_models.cli import main

from .factories import make_ohlcv, make_wallet_df


def test_train_smart_money_and_inspect(tmp_path, capsys):
    csv = tmp_path / "wallets.csv"
    wallets = make_wallet_df(40)
    wallets.index.name = "address"
    wallets.to_csv(csv)
    out = tmp_path / "artifacts"

    assert (
        main(
            [
                "train",
                "smart_money",
                "--data",
                str(csv),
                "--artifacts-dir",
                str(out),
                "--clusters",
                "3",
            ]
        )
        == 0
    )
    trained = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert trained["model"] == "smart_money"

    assert main(["inspect", "--artifacts-dir", str(out)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["smart_money"]["model_type"] == "smart_money_tracker"
    assert report["volatility"] is None


def test_missing_input_file_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        main(["train", "volatility", "--data", str(tmp_path / "nope.csv")])


def test_unknown_model_rejected(tmp_path):
    with pytest.raises(SystemExit):
        main(["train", "bogus", "--data", str(tmp_path / "x.csv")])


def test_volatility_rows_are_read(tmp_path):
    csv = tmp_path / "prices.csv"
    frame = make_ohlcv(10)
    frame.index.name = "timestamp"
    frame.to_csv(csv)
    from ai_models.cli import read_table

    loaded = read_table(csv, "timestamp")
    assert len(loaded) == 10
    assert loaded.index.is_monotonic_increasing
