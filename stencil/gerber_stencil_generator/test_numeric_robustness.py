from stencil_core import StencilError, _circle_quad_segs


def test_circle_segmentation_does_not_divide_by_zero() -> None:
    assert _circle_quad_segs(1.0, 0.01) >= 2
    assert _circle_quad_segs(1e20, 0.01) >= 2
    assert _circle_quad_segs(0.0, 0.01) == 0


def test_zero_tolerance_is_rejected_cleanly() -> None:
    try:
        _circle_quad_segs(1.0, 0.0)
    except StencilError as exc:
        assert "больше нуля" in str(exc)
    else:
        raise AssertionError("Zero tolerance must raise StencilError")


if __name__ == "__main__":
    test_circle_segmentation_does_not_divide_by_zero()
    test_zero_tolerance_is_rejected_cleanly()
    print("OK")
