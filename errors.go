package mineru

import (
	"fmt"
	"time"
)

// APIError is the base error type for all MinerU API errors.
type APIError struct {
	Code    string
	Message string
	TraceID string
}

func (e *APIError) Error() string {
	if e.TraceID != "" {
		return fmt.Sprintf("[%s] %s (trace: %s)", e.Code, e.Message, e.TraceID)
	}
	return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

// Typed errors for specific API error codes.
type (
	AuthError          struct{ APIError }
	ParamError         struct{ APIError }
	FileTooLargeError  struct{ APIError }
	PageLimitError     struct{ APIError }
	TaskNotFoundError  struct{ APIError }
	ExtractFailedError struct{ APIError }
	QuotaExceededError struct{ APIError }
)

// TimeoutError is raised by the SDK when polling exceeds the configured timeout.
type TimeoutError struct {
	APIError
	Timeout time.Duration
	TaskID  string
}

func newTimeoutError(timeout time.Duration, taskID string) *TimeoutError {
	return &TimeoutError{
		APIError: APIError{Code: "TIMEOUT", Message: fmt.Sprintf("task %s did not complete within %s", taskID, timeout)},
		Timeout:  timeout,
		TaskID:   taskID,
	}
}

func errorForCode(code, msg, traceID string) error {
	base := APIError{Code: code, Message: msg, TraceID: traceID}
	switch code {
	case "A0202", "A0211":
		return &AuthError{base}
	case "-500", "-10002":
		return &ParamError{base}
	case "-60005":
		return &FileTooLargeError{base}
	case "-60006":
		return &PageLimitError{base}
	case "-60010":
		return &ExtractFailedError{base}
	case "-60012":
		return &TaskNotFoundError{base}
	case "-60018", "-60019":
		return &QuotaExceededError{base}
	default:
		return &base
	}
}
