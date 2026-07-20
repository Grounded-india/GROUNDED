"""Tests for the pure clustering logic (no DB)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np

from grounded.pipeline.clustering import ClusterableItem, cluster_items

BASE = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def _item(id_, vec, hours_offset=0):
    return ClusterableItem(
        id=id_,
        embedding=np.array(vec, dtype=float),
        timestamp=BASE + timedelta(hours=hours_offset),
    )


def test_empty_input_returns_empty():
    assert cluster_items([]) == []


def test_single_item_is_its_own_cluster():
    assert cluster_items([_item("a", [1, 0, 0])]) == [[0]]


def test_two_similar_items_within_window_cluster_together():
    items = [
        _item("a", [1.0, 0.0, 0.0], 0),
        _item("b", [0.99, 0.01, 0.0], 1),
    ]
    clusters = cluster_items(items, similarity_threshold=0.8, time_window_hours=48)
    assert clusters == [[0, 1]]


def test_dissimilar_items_stay_separate():
    items = [
        _item("a", [1.0, 0.0, 0.0], 0),
        _item("b", [0.0, 1.0, 0.0], 0),
    ]
    clusters = cluster_items(items, similarity_threshold=0.8, time_window_hours=48)
    assert clusters == [[0], [1]]


def test_time_window_splits_identical_content():
    # Same embedding, but published far apart -> different events.
    items = [
        _item("a", [1.0, 0.0, 0.0], 0),
        _item("b", [1.0, 0.0, 0.0], 100),
    ]
    clusters = cluster_items(items, similarity_threshold=0.8, time_window_hours=48)
    assert clusters == [[0], [1]]


def test_transitive_single_linkage_chaining():
    # a~b and b~c (both within window) but a and c are only linked through b.
    items = [
        _item("a", [1.0, 0.0, 0.0], 0),
        _item("b", [0.9, 0.44, 0.0], 1),
        _item("c", [0.7, 0.71, 0.0], 2),
    ]
    clusters = cluster_items(items, similarity_threshold=0.8, time_window_hours=48)
    assert clusters == [[0, 1, 2]]


def test_three_groups_form_three_clusters():
    items = [
        _item("a1", [1, 0, 0], 0),
        _item("a2", [0.98, 0.02, 0], 2),
        _item("b1", [0, 1, 0], 0),
        _item("b2", [0.01, 0.99, 0], 3),
        _item("c1", [0, 0, 1], 0),
    ]
    clusters = cluster_items(items, similarity_threshold=0.8, time_window_hours=48)
    assert clusters == [[0, 1], [2, 3], [4]]


def test_clusters_are_sorted_by_first_member():
    items = [
        _item("z", [0, 1, 0], 0),
        _item("y", [1, 0, 0], 0),
        _item("x", [1, 0, 0], 1),
    ]
    clusters = cluster_items(items, similarity_threshold=0.8, time_window_hours=48)
    assert clusters == [[0], [1, 2]]
