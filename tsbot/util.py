from __future__ import annotations


def parse_response_error(input_str: str) -> tuple[int, str]:
    _, error_id, msg = input_str.split(" ")

    return int(error_id.split("=")[-1]), msg.split("=")[-1]
