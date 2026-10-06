import numpy as np
import pandas as pd
import pytest
from ai_models.models.correlation import CorrelationPredictor, shrunk_correlation

from .factories import make_prices


class TestShrunkCorrelation:
    def test_is_valid_correlation_matrix(self):
        returns = np.log(make_prices()).diff().dropna()
        matrix = shrunk_correlation(returns).values
        assert np.allclose(np.diag(matrix), 1.0)
        assert np.allclose(matrix, matrix.T)
        assert np.linalg.eigvalsh(matrix).min() > 0

    def test_degenerate_input_returns_identity(self):
        frame = pd.DataFrame({"a": [0.1, 0.2], "b": [0.3, 0.1]})
        assert np.allclose(shrunk_correlation(frame).values, np.eye(2))


class TestCorrelationPredictor:
    def test_requires_two_assets(self):
        model = CorrelationPredictor(sequence_length=10, target_window=5)
        with pytest.raises(ValueError):
            model.fit(make_prices(assets=("btc",)))

    def test_predict_before_fit_fails(self):
        with pytest.raises(RuntimeError):
            CorrelationPredictor().predict(make_prices())

    def test_fit_predict_save_load(self, tmp_path):
        pytest.importorskip("tensorflow")
        prices = make_prices(160)
        model = CorrelationPredictor(
            sequence_length=15, target_window=8, lstm_units=(8, 4)
        ).fit(prices, epochs=1)
        matrix = model.predict(prices)
        assert matrix.shape == (3, 3)
        assert np.allclose(np.diag(matrix), 1.0)
        assert np.linalg.eigvalsh(matrix).min() > 0
        assert model.asset_names == ["btc", "eth", "sol"]

        model.save(tmp_path)
        restored = CorrelationPredictor.load(tmp_path)
        assert np.allclose(restored.predict(prices), matrix, atol=1e-4)

    def test_rejects_mismatched_assets(self):
        pytest.importorskip("tensorflow")
        prices = make_prices(160)
        model = CorrelationPredictor(
            sequence_length=15, target_window=8, lstm_units=(8, 4)
        ).fit(prices, epochs=1)
        with pytest.raises(ValueError):
            model.predict(prices[["asset_btc", "asset_eth"]])
