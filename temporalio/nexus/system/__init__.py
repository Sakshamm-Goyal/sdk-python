"""System Nexus operation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import temporalio.api.common.v1
import temporalio.common
import temporalio.converter
from temporalio.bridge._visitor_functions import VisitorFunctions
from temporalio.converter import BinaryProtoPayloadConverter, CompositePayloadConverter

TEMPORAL_SYSTEM_ENDPOINT = "__temporal_system"
_SYSTEM_PAYLOAD_METADATA_KEY = "__temporal_system_payload"
_SYSTEM_PAYLOAD_METADATA_VALUE = b"true"


class SystemNexusPayloadConverter(CompositePayloadConverter):
    """Payload converter for system Nexus outer envelopes."""

    def __init__(self) -> None:
        """Create a payload converter for system Nexus outer envelopes."""
        super().__init__(BinaryProtoPayloadConverter())

    def to_payloads(
        self, values: Sequence[Any]
    ) -> list[temporalio.api.common.v1.Payload]:
        """See base class."""
        payloads = super().to_payloads(values)
        for value, payload in zip(values, payloads):
            if isinstance(value, temporalio.common.RawValue):
                continue
            payload.metadata[_SYSTEM_PAYLOAD_METADATA_KEY] = (
                _SYSTEM_PAYLOAD_METADATA_VALUE
            )
        return payloads


def is_system_endpoint(endpoint: str) -> bool:
    """Return whether a Nexus endpoint is the Temporal system endpoint."""
    return endpoint == TEMPORAL_SYSTEM_ENDPOINT


def _is_system_payload(payload: temporalio.api.common.v1.Payload) -> bool:
    return (
        payload.metadata.get(_SYSTEM_PAYLOAD_METADATA_KEY)
        == _SYSTEM_PAYLOAD_METADATA_VALUE
    )


async def maybe_visit_payload(
    payload: temporalio.api.common.v1.Payload,
    visitor_functions: VisitorFunctions,
    skip_search_attributes: bool,
) -> temporalio.api.common.v1.Payload | None:
    """Visit nested payloads if the payload is a Temporal system Nexus envelope."""
    if not _is_system_payload(payload):
        return None

    payload_converter = get_payload_converter()
    value = payload_converter.from_payload(payload)
    from ._payload_visitor import PayloadVisitor

    await PayloadVisitor(skip_search_attributes=skip_search_attributes).visit(
        visitor_functions, value
    )
    return payload_converter.to_payload(value)


def get_payload_converter() -> temporalio.converter.PayloadConverter:
    """Return the fixed payload converter for system Nexus outer envelopes."""
    return SystemNexusPayloadConverter()


__all__ = [
    "TEMPORAL_SYSTEM_ENDPOINT",
    "get_payload_converter",
    "is_system_endpoint",
    "maybe_visit_payload",
    "SystemNexusPayloadConverter",
]
