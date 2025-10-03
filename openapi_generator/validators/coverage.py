"""Coverage and quality reporting for generated specifications."""

from typing import List

from openapi_generator.models.schemas import (
    ConfidenceLevel,
    CoverageReport,
    Endpoint,
)
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class CoverageAnalyzer:
    """Analyzes coverage and quality of extracted endpoints."""

    def analyze(self, endpoints: List[Endpoint]) -> CoverageReport:
        """Analyze endpoint coverage and quality.

        Args:
            endpoints: List of extracted endpoints

        Returns:
            Coverage report
        """
        logger.info(f"Analyzing coverage for {len(endpoints)} endpoints")

        total = len(endpoints)
        if total == 0:
            return CoverageReport(
                total_endpoints=0,
                endpoints_with_parameters=0,
                endpoints_with_request_body=0,
                endpoints_with_responses=0,
                endpoints_with_examples=0,
                confidence_distribution={},
                average_confidence=0.0,
            )

        # Count endpoints with various features
        with_params = sum(1 for e in endpoints if e.parameters)
        with_body = sum(1 for e in endpoints if e.request_body)
        with_responses = sum(1 for e in endpoints if e.responses)

        # Count endpoints with examples
        with_examples = 0
        for endpoint in endpoints:
            has_example = False

            # Check parameter examples
            if any(p.example for p in endpoint.parameters):
                has_example = True

            # Check request body example
            if endpoint.request_body and endpoint.request_body.example:
                has_example = True

            # Check response examples
            if any(r.example for r in endpoint.responses):
                has_example = True

            if has_example:
                with_examples += 1

        # Confidence distribution
        confidence_dist = {
            ConfidenceLevel.HIGH.value: sum(
                1 for e in endpoints if e.confidence == ConfidenceLevel.HIGH
            ),
            ConfidenceLevel.MEDIUM.value: sum(
                1 for e in endpoints if e.confidence == ConfidenceLevel.MEDIUM
            ),
            ConfidenceLevel.LOW.value: sum(
                1 for e in endpoints if e.confidence == ConfidenceLevel.LOW
            ),
        }

        # Calculate average confidence (high=1.0, medium=0.6, low=0.3)
        confidence_scores = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.3,
        }
        avg_confidence = sum(
            confidence_scores[e.confidence] for e in endpoints
        ) / total

        report = CoverageReport(
            total_endpoints=total,
            endpoints_with_parameters=with_params,
            endpoints_with_request_body=with_body,
            endpoints_with_responses=with_responses,
            endpoints_with_examples=with_examples,
            confidence_distribution=confidence_dist,
            average_confidence=avg_confidence,
        )

        logger.info(f"Coverage analysis complete. Quality score: {report.quality_score:.1f}%")

        return report
