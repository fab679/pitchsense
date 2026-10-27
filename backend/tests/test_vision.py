import pytest
from backend.vision.renderer import FrameRenderer
from backend.vision.scout import VideoScoutAgent

class MockGateway:
    def complete_chat(self, role, messages, fallback_template_fn=None, response_format=None):
        if fallback_template_fn:
            text = fallback_template_fn()
        else:
            text = '{"detected_action": "pass", "confidence": 0.88}'
        return text, {"provider": "mock", "latency_ms": 1.0, "validated": True}

def test_frame_renderer_svg():
    renderer = FrameRenderer()
    ball_pos = {"x": 52.5, "y": 34.0}
    home = [{"x": 30.0, "y": 20.0, "number": 8}]
    away = [{"x": 60.0, "y": 40.0, "number": 10}]
    
    svg = renderer.render_frame_svg(ball_pos, home, away)
    assert "<svg" in svg
    assert "#0F766E" in svg  # Teal kit color
    assert "#E11D48" in svg  # Vermilion kit color
    assert "#FACC15" in svg  # Ball color

def test_trajectory_scout_reconciliation():
    scout = VideoScoutAgent(gateway=MockGateway(), tolerance_m=2.0)
    
    start = {"x": 50.0, "y": 30.0}
    end = {"x": 65.0, "y": 35.0}  # dist = sqrt(15^2 + 5^2) = 15.81 m
    dt = 1.2
    
    truth = {
        "event_seq": 101,
        "true_dist": 15.5
    }
    
    detected = scout.derive_event_from_trajectory(
        start_pos=start,
        end_pos=end,
        dt_sec=dt,
        actor_code="sal_08",
        recipient_code="sal_10",
        ground_truth=truth
    )
    
    assert detected["type"] == "trajectory_estimate"
    assert detected["derived"]["pass_distance_m"] == 15.8
    assert detected["reconciliation"]["agreement"] is True
    assert scout.get_agreement_percentage() == 100.0

def test_trajectory_scout_reports_no_agreement_before_measurements():
    scout = VideoScoutAgent(gateway=MockGateway(), tolerance_m=2.0)

    summary = scout.get_reconciliation_summary()

    assert summary["total_detections"] == 0
    assert summary["agreed_detections"] == 0
    assert summary["agreement_percentage"] == 0.0


def test_trajectory_scout_tolerance_boundary():
    scout = VideoScoutAgent(gateway=MockGateway(), tolerance_m=2.0)
    
    start = {"x": 10.0, "y": 10.0}
    end = {"x": 30.0, "y": 10.0}  # dist = 20.0 m
    
    # 1. Matching within tolerance (diff = 1.0 <= 2.0)
    scout.derive_event_from_trajectory(start, end, 1.0, "sal_01", "sal_04", {"true_dist": 21.0})
    # 2. Outside tolerance (diff = 4.0 > 2.0)
    scout.derive_event_from_trajectory(start, end, 1.0, "sal_01", "sal_04", {"true_dist": 24.0})
    
    summary = scout.get_reconciliation_summary()
    assert summary["total_detections"] == 2
    assert summary["agreed_detections"] == 1
    assert summary["agreement_percentage"] == 50.0
