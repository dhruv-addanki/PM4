"""Tests for the AI recognition module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from food_tracker.ai import EmbeddingModel, FoodRecognitionEngine, RecognisedFood
from food_tracker.models import FoodItem


class TestEmbeddingModel:
    """Tests for EmbeddingModel."""

    def test_encode_single_text(self):
        """Test encoding a single text."""
        model = EmbeddingModel()
        result = model.encode(["chicken breast grilled"])
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert "chicken" in result[0]
        assert "breast" in result[0]

    def test_encode_multiple_texts(self):
        """Test encoding multiple texts."""
        model = EmbeddingModel()
        texts = ["chicken breast", "greek yogurt"]
        result = model.encode(texts)
        assert len(result) == 2
        assert all(isinstance(emb, dict) for emb in result)

    def test_encode_normalizes_vectors(self):
        """Test that encoded vectors are normalized."""
        model = EmbeddingModel()
        result = model.encode(["test text"])[0]
        # Check that vector is normalized (sum of squares should be ~1.0)
        norm_squared = sum(v * v for v in result.values())
        assert abs(norm_squared - 1.0) < 0.001

    def test_encode_handles_empty_text(self):
        """Test encoding empty text."""
        model = EmbeddingModel()
        result = model.encode([""])[0]
        # Empty text should still produce a valid (normalized) vector
        assert isinstance(result, dict)

    def test_encode_case_insensitive(self):
        """Test that encoding is case insensitive."""
        model = EmbeddingModel()
        result1 = model.encode(["Chicken Breast"])[0]
        result2 = model.encode(["chicken breast"])[0]
        # Should produce same tokens
        assert set(result1.keys()) == set(result2.keys())


class TestFoodRecognitionEngine:
    """Tests for FoodRecognitionEngine."""

    def test_engine_initialization_default_path(self):
        """Test engine initialization with default path."""
        engine = FoodRecognitionEngine()
        items = engine.known_items()
        assert len(items) > 0
        assert all(isinstance(item, FoodItem) for item in items)

    def test_engine_initialization_custom_path(self, temp_foods_file):
        """Test engine initialization with custom path."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        items = engine.known_items()
        assert len(items) == 2

    def test_engine_initialization_nonexistent_file(self, tmp_path):
        """Test engine raises error for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            FoodRecognitionEngine(reference_path=nonexistent)

    def test_recognise_exact_match(self, temp_foods_file):
        """Test recognition with exact match."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("Grilled Chicken Breast", top_k=1)
        assert len(results) == 1
        assert results[0].item.name == "Grilled Chicken Breast"
        assert results[0].confidence >= 0.99  # Exact matches get high confidence

    def test_recognise_partial_match(self, temp_foods_file):
        """Test recognition with partial match."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("chicken", top_k=1)
        assert len(results) > 0
        assert results[0].confidence > 0

    def test_recognise_alias_match(self, temp_foods_file):
        """Test recognition using aliases."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("grilled chicken", top_k=1)
        assert len(results) > 0
        # Should match "Grilled Chicken Breast" via alias
        assert "chicken" in results[0].item.name.lower()

    def test_recognise_returns_top_k(self, temp_foods_file):
        """Test that recognise returns top k results."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("chicken", top_k=2)
        assert len(results) <= 2

    def test_recognise_empty_description(self, temp_foods_file):
        """Test recognition with empty description."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("")
        assert results == []
        results = engine.recognise("   ")
        assert results == []

    def test_recognise_sorted_by_confidence(self, temp_foods_file):
        """Test that results are sorted by confidence descending."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("chicken", top_k=5)
        if len(results) > 1:
            confidences = [r.confidence for r in results]
            assert confidences == sorted(confidences, reverse=True)

    def test_known_items(self, temp_foods_file):
        """Test known_items returns all loaded items."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        items = engine.known_items()
        assert len(items) == 2
        names = [item.name for item in items]
        assert "Grilled Chicken Breast" in names
        assert "Greek Yogurt" in names

    def test_add_custom_item(self, temp_foods_file):
        """Test adding a custom food item."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        initial_count = len(engine.known_items())

        custom_item = FoodItem(
            name="Custom Food",
            serving_size="1 serving",
            calories=150.0,
            macronutrients={"protein": 10.0},
        )
        engine.add_custom_item(custom_item)

        assert len(engine.known_items()) == initial_count + 1
        assert custom_item in engine.known_items()

    def test_add_custom_item_recognisable(self, temp_foods_file):
        """Test that added custom items can be recognised."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        custom_item = FoodItem(
            name="Custom Protein Bar",
            serving_size="1 bar",
            calories=200.0,
            macronutrients={"protein": 20.0},
        )
        engine.add_custom_item(custom_item)

        results = engine.recognise("Custom Protein Bar", top_k=1)
        assert len(results) > 0
        assert results[0].item.name == "Custom Protein Bar"

    def test_scan_bulk(self, temp_foods_file):
        """Test bulk scanning of multiple descriptions."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        descriptions = ["chicken", "yogurt"]
        results = engine.scan_bulk(descriptions)
        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)
        assert all(isinstance(item, RecognisedFood) for r in results for item in r)

    def test_item_representation_includes_all_info(self, temp_foods_file):
        """Test that item representation includes name, serving, aliases, and macros."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        items = engine.known_items()
        for item in items:
            representation = engine._item_representation(item)
            assert item.name in representation
            assert item.serving_size in representation
            if item.aliases:
                assert any(alias in representation for alias in item.aliases)


class TestRecognisedFood:
    """Tests for RecognisedFood dataclass."""

    def test_recognised_food_creation(self, temp_foods_file):
        """Test creating a RecognisedFood instance."""
        engine = FoodRecognitionEngine(reference_path=temp_foods_file)
        results = engine.recognise("chicken", top_k=1)
        assert len(results) > 0
        result = results[0]
        assert isinstance(result, RecognisedFood)
        assert isinstance(result.item, FoodItem)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1

