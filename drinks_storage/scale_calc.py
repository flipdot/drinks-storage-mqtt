from .config import ScaleConfig

ERROR_OUT_OF_RANGE = -1
ERROR_COUNT_NEGATIVE = -2
ERROR_NONE = 0


def to_crates(config: ScaleConfig, raw_value: int):
    return (raw_value - config.tare_raw) / config.crate_raw


def from_crates(config: ScaleConfig, crates: int):
    return crates * config.crate_raw + config.tare_raw


def handle_scale_value(scale_config, scale_value, auto_tare=False):
    crates_float = to_crates(scale_config, scale_value)
    crates_int = round(crates_float)

    diff = crates_float - crates_int
    accuracy = 1 - abs(diff)

    auto_tared = False

    # Check for negative crate count
    if crates_int < 0:
        return (ERROR_COUNT_NEGATIVE, {
            "crate_count": None,
            "crate_count_float": crates_float,
            "accuracy": accuracy,
            "diff": diff,
            "auto_tared": auto_tared,
        })

    # Check for deviation of crate count's ideal values in kg
    if abs(diff) > scale_config.tolerance:
        return (ERROR_OUT_OF_RANGE, {
            "crate_count": None,
            "crate_count_float": crates_float,
            "accuracy": accuracy,
            "diff": diff,
            "auto_tared": auto_tared
        })

    # Auto tare if enabled
    if auto_tare:
        # Update scale's tare in config
        scale_config.tare_raw -= (
            from_crates(scale_config, round(crates_float)) -
            from_crates(scale_config, crates_float)) / 2.0

        auto_tared = True

    # Everything within limits
    return (ERROR_NONE, {
        "crate_count": crates_int,
        "crate_count_float": crates_float,
        "accuracy": accuracy,
        "diff": diff,
        "auto_tared": auto_tared,
    })
