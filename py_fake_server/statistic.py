import json
import re
from functools import wraps
from typing import Optional, List, Callable, Dict


class RequestedParams:
    def __init__(self, cookies: Optional[Dict[str, str]], body: Optional[bytes], content_type: Optional[str],
                 files: Optional[Dict[str, bytes]], headers: Optional[Dict[str, str]],
                 query_params: Optional[Dict[str, str]]):
        self.cookies = cookies
        self.body = body
        self.content_type = content_type
        self.files = files
        self.headers = headers
        self.query_params = query_params


class HeaderDoesNotExist:
    def __repr__(self):
        return "<HEADER DOES NOT EXIST>"


def check(method):
    @wraps(method)
    def decorator(self, *args, **kwargs):
        try:
            method(self, *args, **kwargs)
        except AssertionError as error:
            self._error_messages.append(str(error))
        return self
    return decorator


class Statistic:
    def __init__(self, method: str, url: str):
        self.method: str = method
        self.url: str = url
        self.requests: List[RequestedParams] = []
        self._current_request_index: Optional[int] = None
        self._number_of_requests_not_specify: bool = True
        self._error_messages: List[str] = [f"Expect that server was requested with [{method.upper()}] {url}."]

    @property
    def requested_times(self) -> int:
        return len(self.requests)

    @property
    def current_requested_time(self) -> int:
        return self._current_request_index + 1

    def exactly_once(self) -> "Statistic":
        return self.exactly_1_times()

    def exactly_twice(self) -> "Statistic":
        return self.exactly_2_times()

    def for_the_first_time(self) -> "Statistic":
        return self.for_the_1_time()

    def for_the_second_time(self) -> "Statistic":
        return self.for_the_2_time()

    def __getattr__(self, item):
        exactly_times_pattern = r"^exactly_(?P<number>\d+)_times$"
        exactly_times_result = re.match(exactly_times_pattern, item)
        if exactly_times_result:
            number = int(exactly_times_result.groupdict()["number"])
            return self._exactly_times(number)

        for_the_time_pattern = r"^for_the_(?P<number>\d+)_time$"
        for_the_time_result = re.match(for_the_time_pattern, item)
        if for_the_time_result:
            number = int(for_the_time_result.groupdict()["number"])
            return self._for_the_time(number)

        raise AttributeError(f"'Statistic' object has no attribute '{item}'")

    def _exactly_times(self, expected_requested_times: int) -> Callable[[], "Statistic"]:
        self._number_of_requests_not_specify = False
        if expected_requested_times != self.requested_times:
            self._error_messages.append(f" {expected_requested_times} times.\n"
                                        f"But server was requested {self.requested_times} times.")
            self._raise_assertion()
        return lambda: self

    def _for_the_time(self, times: int) -> Callable[[], "Statistic"]:
        if self.requested_times < times:
            self._error_messages.append(f" At least {times} times.\n"
                                        f"But server was requested {self.requested_times} times.")
            self._raise_assertion()
        else:
            self._current_request_index = times - 1
            return lambda: self

    @check
    def with_cookies(self, cookies: Dict[str, str]) -> "Statistic":
        actual_cookies = self.current_request.cookies
        assert cookies == actual_cookies, \
            f"\nFor the {self.current_requested_time} time: with cookies {cookies}.\n" \
            f"But for the {self.current_requested_time} time: cookies was {actual_cookies}."

    @check
    def with_body(self, body: str) -> "Statistic":
        actual_body = self.current_request.body.decode("utf-8", errors="skip")
        assert body == actual_body, \
            f"\nFor the {self.current_requested_time} time: with body {body.__repr__()}.\n" \
            f"But for the {self.current_requested_time} time: body was {actual_body.__repr__()}."

    @check
    def with_json(self, json_dict: dict) -> "Statistic":
        body = json.dumps(json_dict, sort_keys=True)

        actual_body = self.current_request.body.decode("utf-8", errors="skip")
        try:
            actual_json_dict = json.loads(actual_body)
        except json.JSONDecodeError:
            assert False, \
                f"\nFor the {self.current_requested_time} time: with json {body}.\n" \
                f"But for the {self.current_requested_time} time: json was corrupted {actual_body.__repr__()}."

        actual_body = json.dumps(actual_json_dict, sort_keys=True)
        assert body == actual_body, \
            f"\nFor the {self.current_requested_time} time: with json {body}.\n" \
            f"But for the {self.current_requested_time} time: json was {actual_body}."

    @check
    def with_content_type(self, content_type: str) -> "Statistic":
        actual_content_type = self.current_request.content_type
        assert content_type == actual_content_type, \
            f"\nFor the {self.current_requested_time} time: with content type {content_type.__repr__()}.\n" \
            f"But for the {self.current_requested_time} time: content type was {actual_content_type.__repr__()}."

    @check
    def with_files(self, files: Dict[str, bytes]) -> "Statistic":
        actual_files = self.current_request.files
        if files != actual_files:
            self._error_messages.append(
                f"\nFor the {self.current_requested_time} time: with files {files}.\n"
                f"But for the {self.current_requested_time} time: files was {actual_files}."
            )

    @check
    def with_headers(self, headers: Dict[str, str]) -> "Statistic":
        actual_headers = self.current_request.headers
        expected_headers = {name.upper(): value for name, value in headers.items()}

        headers_diff = self._get_headers_diff(expected_headers, actual_headers)
        assert not headers_diff, \
            f"\nFor the {self.current_requested_time} time: with headers contain {expected_headers}.\n" \
            f"But for the {self.current_requested_time} time: headers contained {headers_diff}."

    @staticmethod
    def _get_headers_diff(expected_headers: Dict[str, str], actual_headers: Dict[str, str]) -> Dict[str, str]:
        headers_diff = {}

        for header_name, header_value in expected_headers.items():
            if header_name in actual_headers and header_value != actual_headers[header_name]:
                headers_diff[header_name] = actual_headers[header_name]
            elif header_name not in actual_headers:
                headers_diff[header_name] = HeaderDoesNotExist()

        return headers_diff

    @check
    def with_query_params(self, query_params: Dict[str, str]) -> "Statistic":
        actual_query_params = self.current_request.query_params

        assert query_params == actual_query_params, \
            f"\nFor the {self.current_requested_time} time: with query params {query_params}.\n" \
            f"But for the {self.current_requested_time} time: query params was {actual_query_params}."

    @property
    def current_request(self) -> RequestedParams:
        if self._current_request_index is None:
            raise RuntimeError("You should specify concrete request for check with 'for_the_<any_number>_time'")
        return self.requests[self._current_request_index]

    def check(self) -> bool:
        if not self.requested_times and self._number_of_requests_not_specify:
            self._error_messages.append("\nBut server was requested 0 times.")

        if self.errors_exist:
            self._raise_assertion()
        else:
            self._clean_state()
            return True

    @property
    def errors_exist(self) -> bool:
        return len(self._error_messages) > 1

    def _raise_assertion(self):
        error_message = "".join(self._error_messages)
        self._clean_state()
        raise AssertionError(error_message)

    def _clean_state(self):
        self._error_messages = self._error_messages[0:1]
        self._number_of_requests_not_specify = True
        self._current_request_index = None
