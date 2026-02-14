import os
import sys
from unittest.mock import patch

import pytest

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, config


class TestConfig:
    """Test cases for Configuration"""

    def test_default_config_values(self):
        """Test default configuration values"""
        default_config = Config()

        # Test embedding model settings
        assert default_config.EMBEDDING_MODEL == "all-MiniLM-L6-v2"

        # Test document processing settings
        assert default_config.CHUNK_SIZE == 800
        assert default_config.CHUNK_OVERLAP == 100
        assert default_config.MAX_RESULTS == 5

        # Test database paths
        assert default_config.CHROMA_PATH == "./chroma_db"

    def test_config_with_custom_values(self):
        """Test configuration with custom values"""
        custom_config = Config(
            EMBEDDING_MODEL="custom-model",
            CHUNK_SIZE=1000,
            CHUNK_OVERLAP=150,
            MAX_RESULTS=10,
            CHROMA_PATH="./custom_db",
        )

        assert custom_config.EMBEDDING_MODEL == "custom-model"
        assert custom_config.CHUNK_SIZE == 1000
        assert custom_config.CHUNK_OVERLAP == 150
        assert custom_config.MAX_RESULTS == 10
        assert custom_config.CHROMA_PATH == "./custom_db"

    def test_config_chunk_settings_valid(self):
        """Test that chunk processing settings are valid"""
        test_config = Config()

        # Chunk size should be reasonable
        assert test_config.CHUNK_SIZE > 0
        assert test_config.CHUNK_SIZE <= 2000  # Not too large

        # Overlap should be smaller than chunk size
        assert test_config.CHUNK_OVERLAP < test_config.CHUNK_SIZE
        assert test_config.CHUNK_OVERLAP >= 0

    def test_config_path_settings(self):
        """Test database path configuration"""
        test_config = Config()

        assert isinstance(test_config.CHROMA_PATH, str)
        assert test_config.CHROMA_PATH != ""
        assert not test_config.CHROMA_PATH.startswith("/")  # Should be relative

    def test_config_model_settings(self):
        """Test embedding model configuration"""
        test_config = Config()

        # Should use sentence transformer for embeddings
        assert test_config.EMBEDDING_MODEL != ""
        assert isinstance(test_config.EMBEDDING_MODEL, str)

    def test_global_config_instance(self):
        """Test the global config instance"""
        # The global config instance should exist
        assert config is not None
        assert isinstance(config, Config)

        # Test it has the default values
        assert config.MAX_RESULTS == 5
        assert config.EMBEDDING_MODEL == "all-MiniLM-L6-v2"

    def test_config_values_are_correct_types(self):
        """Test that all config values have correct types"""
        test_config = Config()

        # String values
        assert isinstance(test_config.EMBEDDING_MODEL, str)
        assert isinstance(test_config.CHROMA_PATH, str)

        # Integer values
        assert isinstance(test_config.CHUNK_SIZE, int)
        assert isinstance(test_config.CHUNK_OVERLAP, int)
        assert isinstance(test_config.MAX_RESULTS, int)

    def test_config_validation_logic(self):
        """Test configuration validation"""
        def validate_config(cfg):
            """Example validation function"""
            errors = []

            if cfg.MAX_RESULTS <= 0:
                errors.append("MAX_RESULTS must be greater than 0")

            if cfg.CHUNK_OVERLAP >= cfg.CHUNK_SIZE:
                errors.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")

            if not cfg.EMBEDDING_MODEL:
                errors.append("EMBEDDING_MODEL is required")

            return errors

        # Test valid config
        valid_config = Config()
        errors = validate_config(valid_config)
        assert len(errors) == 0

        # Test invalid config
        invalid_config = Config()
        invalid_config.MAX_RESULTS = 0
        invalid_config.CHUNK_OVERLAP = invalid_config.CHUNK_SIZE + 100

        errors = validate_config(invalid_config)
        assert len(errors) > 0
        assert any("MAX_RESULTS must be greater than 0" in error for error in errors)
        assert any("CHUNK_OVERLAP must be less than CHUNK_SIZE" in error for error in errors)

    def test_config_edge_cases(self):
        """Test configuration edge cases"""
        test_config = Config()

        # Test very large chunk size
        test_config.CHUNK_SIZE = 10000
        assert test_config.CHUNK_SIZE == 10000

        # Test zero overlap (valid)
        test_config.CHUNK_OVERLAP = 0
        assert test_config.CHUNK_OVERLAP == 0

        # Test large max results
        test_config.MAX_RESULTS = 100
        assert test_config.MAX_RESULTS == 100

    def test_config_immutability_during_runtime(self):
        """Test that config changes affect system behavior"""
        # Create two config instances
        config1 = Config()
        config2 = Config()

        # Should be separate instances
        assert config1 is not config2

        # But have same default values
        assert config1.CHUNK_SIZE == config2.CHUNK_SIZE
        assert config1.MAX_RESULTS == config2.MAX_RESULTS

        # Changes to one shouldn't affect the other
        config1.MAX_RESULTS = 10
        assert config2.MAX_RESULTS == 5  # Still the default value

    @pytest.mark.parametrize(
        "max_results,expected_behavior",
        [
            (1, "minimal_results"),
            (5, "good_results"),
            (10, "many_results"),
            (20, "upper_bound"),
        ],
    )
    def test_max_results_impact_parametrized(self, max_results, expected_behavior):
        """Test different MAX_RESULTS values and their impact"""
        test_config = Config()
        test_config.MAX_RESULTS = max_results

        # Verify the config has the expected value
        assert test_config.MAX_RESULTS == max_results

        # Test reasonable bounds
        assert test_config.MAX_RESULTS >= 1
        assert test_config.MAX_RESULTS <= 50  # Reasonable upper bound
