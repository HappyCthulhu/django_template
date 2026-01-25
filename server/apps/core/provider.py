from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import requests
from loguru import logger
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping


ResponseBody = dict[str, Any] | list[Any] | str | None


@dataclass(slots=True)
class NormalizedResponse:
    """Нормализованный HTTP-ответ базового провайдера."""

    status_code: int
    headers: dict[str, str]
    body: ResponseBody


class ProviderRequestError(Exception):
    """Represents an error that occurred during an HTTP request in a provider."""

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        status_code: int | None = None,
        response_body: ResponseBody | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize ProviderRequestError.

        Args:
            message: Human-readable error message.
            url: Request URL where the error occurred.
            status_code: HTTP response status code, if available.
            response_body: Parsed response body, if available.
            original_exception: Original exception that caused this error, if any.

        """
        self.url = url
        self.status_code = status_code
        self.response_body = response_body
        self.original_exception = original_exception
        super().__init__(message)


class BaseProvider:
    """Base HTTP provider for external requests with retry and response normalization."""

    DEFAULT_RETRIES: int = 3
    DEFAULT_BACKOFF_FACTOR: float = 0.5
    DEFAULT_STATUS_FORCELIST: tuple[int, ...] = (429, 500, 502, 503, 504)

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | tuple[float, float] | None = 10.0,
        session: Session | None = None,
        retries: int | None = None,
        backoff_factor: float | None = None,
        status_forcelist: tuple[int, ...] | None = None,
    ) -> None:
        """Initialize BaseProvider.

        Args:
            base_url: Optional base URL to be prefixed to all request URLs.
            timeout: Default timeout (in seconds) for requests.
            session: Optional preconfigured requests.Session instance.
            retries: Number of retry attempts for failed requests.
            backoff_factor: Backoff factor for retry delays.
            status_forcelist: HTTP status codes that should trigger a retry.

        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self.session = session or self._create_session(
            retries=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )

    @classmethod
    def _create_session(
        cls,
        *,
        retries: int | None,
        backoff_factor: float | None,
        status_forcelist: tuple[int, ...] | None,
    ) -> Session:
        """Create and configure a requests.Session with retry and backoff."""
        session = requests.Session()

        retry_config = Retry(
            total=retries if retries is not None else cls.DEFAULT_RETRIES,
            read=retries if retries is not None else cls.DEFAULT_RETRIES,
            connect=retries if retries is not None else cls.DEFAULT_RETRIES,
            backoff_factor=backoff_factor if backoff_factor is not None else cls.DEFAULT_BACKOFF_FACTOR,
            status_forcelist=status_forcelist if status_forcelist is not None else cls.DEFAULT_STATUS_FORCELIST,
            allowed_methods=("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_config)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> NormalizedResponse:
        """Perform HTTP GET request."""
        return self._request(method="GET", url=url, params=params, headers=headers)

    def post(
        self,
        url: str,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> NormalizedResponse:
        """Perform HTTP POST request."""
        return self._request(method="POST", url=url, json=json, data=data, headers=headers)

    def put(
        self,
        url: str,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> NormalizedResponse:
        """Perform HTTP PUT request."""
        return self._request(method="PUT", url=url, json=json, data=data, headers=headers)

    def delete(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> NormalizedResponse:
        """Perform HTTP DELETE request."""
        return self._request(method="DELETE", url=url, params=params, headers=headers)

    def _build_url(self, url: str) -> str:
        """Build absolute URL using base_url if provided."""
        if self.base_url and not url.lower().startswith(("http://", "https://")):
            return f"{self.base_url}/{url.lstrip('/')}"
        return url

    def _normalize_response(self, response: Response) -> NormalizedResponse:
        """Normalize HTTP response into a typed structure."""
        status_code = response.status_code
        headers: MutableMapping[str, str] = dict(response.headers)

        body: ResponseBody
        if response.content is None or response.content == b"":
            body = None
        else:
            try:
                body = response.json()
            except ValueError:
                body = response.text

        return NormalizedResponse(
            status_code=status_code,
            headers=headers,
            body=body,
        )

    def _request(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> NormalizedResponse:
        """Core request handler used by all HTTP methods.

        Returns:
            Normalized response as a dictionary with status_code, headers, and body.

        Raises:
            ProviderRequestError: If network error occurs or response status is not OK.

        """
        full_url = self._build_url(url)

        try:
            response = self.session.request(
                method=method,
                url=full_url,
                params=dict(params) if params is not None else None,
                json=dict(json) if json is not None else None,
                data=dict(data) if data is not None else None,
                headers=dict(headers) if headers is not None else None,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error(
                "HTTP request failed: method={method}, url={url}, error={error}",
                method=method,
                url=full_url,
                error=str(exc),
            )
            raise ProviderRequestError(
                "HTTP request failed",
                url=full_url,
                original_exception=exc,
            ) from exc

        normalized = self._normalize_response(response)

        if not response.ok:
            logger.warning(
                "HTTP request returned non-OK status: method={method}, url={url}, "
                "status_code={status_code}, body={body}",
                method=method,
                url=full_url,
                status_code=normalized.status_code,
                body=normalized.body,
            )
            raise ProviderRequestError(
                "HTTP request returned non-OK status",
                url=full_url,
                status_code=normalized.status_code,
                response_body=normalized.body,
            )

        return normalized

