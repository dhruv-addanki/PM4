"""Tests for the tracker module."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from food_tracker.models import FoodEntry, FoodItem
from food_tracker.tracker import FoodTracker


class TestFoodTracker:
    """Tests for FoodTracker class."""

    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.recogniser is not None
        assert tracker.repository is not None
        assert tracker.entries() == []

    def test_tracker_loads_existing_entries(self, repository, sample_food_entry, recognition_engine):
        """Test that tracker loads existing entries from repository."""
        repository.save_entries([sample_food_entry])
        tracker = FoodTracker(recogniser=recognition_engine, repository=repository)
        entries = tracker.entries()
        assert len(entries) == 1
        assert entries[0].food.name == sample_food_entry.food.name

    def test_scan_description(self, tracker):
        """Test scanning a food description."""
        results = tracker.scan_description("chicken", top_k=3)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(hasattr(r, "item") and hasattr(r, "confidence") for r in results)

    def test_scan_description_empty(self, tracker):
        """Test scanning with empty description."""
        results = tracker.scan_description("", top_k=3)
        assert results == []

    def test_register_custom_food(self, tracker):
        """Test registering a custom food."""
        item = tracker.register_custom_food(
            name="Custom Food",
            serving_size="1 serving",
            calories=150.0,
            macronutrients={"protein": 10.0},
            aliases=["custom"],
        )
        assert item.name == "Custom Food"
        assert item in tracker.recogniser.known_items()

    def test_log_food(self, tracker, sample_food_item):
        """Test logging a food entry."""
        entry = tracker.log_food(sample_food_item, quantity=1.5)
        assert entry.food == sample_food_item
        assert entry.quantity == 1.5
        assert isinstance(entry.timestamp, datetime)
        assert len(tracker.entries()) == 1

    def test_log_food_custom_timestamp(self, tracker, sample_food_item):
        """Test logging a food with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 12, 30, 0)
        entry = tracker.log_food(sample_food_item, quantity=1.0, timestamp=custom_time)
        assert entry.timestamp == custom_time

    def test_log_food_persists_to_storage(self, tracker, repository, sample_food_item):
        """Test that logged food is persisted to storage."""
        entry = tracker.log_food(sample_food_item, quantity=1.0)
        # Create new tracker to verify persistence
        new_tracker = FoodTracker(recogniser=tracker.recogniser, repository=repository)
        entries = new_tracker.entries()
        assert len(entries) == 1
        assert entries[0].food.name == sample_food_item.name

    def test_manual_food_entry(self, tracker):
        """Test manual food entry creation."""
        entry = tracker.manual_food_entry(
            name="Homemade Bar",
            serving_size="1 bar",
            calories=200.0,
            quantity=1.0,
            macronutrients={"protein": 15.0, "carbs": 20.0},
        )
        assert entry.food.name == "Homemade Bar"
        assert entry.food.calories == 200.0
        assert entry.quantity == 1.0
        assert len(tracker.entries()) == 1

    def test_manual_food_entry_defaults(self, tracker):
        """Test manual food entry with default values."""
        entry = tracker.manual_food_entry(
            name="Simple Food",
            serving_size="1 serving",
            calories=100.0,
        )
        assert entry.food.macronutrients == {}
        assert entry.quantity == 1.0

    def test_entries_for_day_existing(self, tracker, sample_food_item):
        """Test getting entries for a specific day."""
        target_date = date(2024, 1, 15)
        entry = tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )
        daily_log = tracker.entries_for_day(target_date)
        assert daily_log.day == target_date
        assert len(daily_log.entries) == 1
        assert daily_log.entries[0] == entry

    def test_entries_for_day_nonexistent(self, tracker):
        """Test getting entries for a day with no entries."""
        target_date = date(2024, 1, 15)
        daily_log = tracker.entries_for_day(target_date)
        assert daily_log.day == target_date
        assert len(daily_log.entries) == 0

    def test_entries_for_day_filters_correctly(self, tracker, sample_food_item):
        """Test that entries_for_day only returns entries for that day."""
        # Log entries on different days
        tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )
        tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 16, 12, 0, 0),
        )
        daily_log = tracker.entries_for_day(date(2024, 1, 15))
        assert len(daily_log.entries) == 1

    def test_daily_summary(self, tracker, sample_food_item):
        """Test getting daily summary."""
        # Log entries on different days
        tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )
        tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 16, 12, 0, 0),
        )
        summary = tracker.daily_summary()
        assert len(summary) == 2
        assert all(isinstance(log.day, date) for log in summary)

    def test_daily_summary_sorted(self, tracker, sample_food_item):
        """Test that daily summary is sorted by date."""
        # Log entries out of order
        tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 16, 12, 0, 0),
        )
        tracker.log_food(
            sample_food_item,
            quantity=1.0,
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )
        summary = tracker.daily_summary()
        dates = [log.day for log in summary]
        assert dates == sorted(dates)

    def test_total_calories(self, tracker, sample_food_item):
        """Test total calories calculation."""
        tracker.log_food(sample_food_item, quantity=1.0)
        tracker.log_food(sample_food_item, quantity=2.0)
        # 165 * 1 + 165 * 2 = 495
        assert tracker.total_calories() == 495.0

    def test_total_calories_empty(self, tracker):
        """Test total calories with no entries."""
        assert tracker.total_calories() == 0.0

    def test_total_macros(self, tracker, sample_food_item):
        """Test total macronutrients calculation."""
        tracker.log_food(sample_food_item, quantity=1.0)
        tracker.log_food(sample_food_item, quantity=1.0)
        totals = tracker.total_macros()
        assert totals["protein"] == 62.0  # 31 * 2
        assert totals["fat"] == 7.2  # 3.6 * 2
        assert totals["carbs"] == 0.0

    def test_total_macros_empty(self, tracker):
        """Test total macros with no entries."""
        assert tracker.total_macros() == {}

    def test_entries_returns_copy(self, tracker, sample_food_item):
        """Test that entries() returns a copy, not the internal list."""
        tracker.log_food(sample_food_item, quantity=1.0)
        entries = tracker.entries()
        entries.append("should not affect internal list")
        assert len(tracker.entries()) == 1

