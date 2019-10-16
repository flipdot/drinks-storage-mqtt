from drinks_storage.config import ScaleConfig
from drinks_storage.scale_calc import handle_scale_value, ERROR_OUT_OF_RANGE

def test_handle_scale_value():
    crate_raw = -261813
    tare_raw = 8149431

    myScale = ScaleConfig(
        scale_name='apfelschorle',
        tare_raw=tare_raw,
        crate_raw=crate_raw,
        tolerance=0.1,
    )

    # calc one crate
    (error_code, result) = handle_scale_value(myScale, tare_raw)
    assert error_code == 0
    assert result['crate_count'] == 0

    # calc one crate
    (error_code, result) = handle_scale_value(myScale, tare_raw + crate_raw)
    assert error_code == 0
    assert result['crate_count'] == 1

    # calc two crate
    (error_code, result) = handle_scale_value(myScale, tare_raw + 2 * crate_raw)
    assert error_code == 0
    assert result['crate_count'] == 2


    # 9% off should be ok
    (error_code, result) = handle_scale_value(myScale, tare_raw + (0.06 * crate_raw))
    assert error_code == 0
    assert result['crate_count'] == 0

    # 12% off should raise an error
    (error_code, result) = handle_scale_value(myScale, tare_raw + (0.12 * crate_raw))
    assert error_code == ERROR_OUT_OF_RANGE
