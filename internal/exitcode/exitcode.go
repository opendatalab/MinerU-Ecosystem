// Package exitcode maps SDK errors to CLI exit codes.
package exitcode

import (
	"errors"

	mineru "github.com/OpenDataLab/mineru-open-sdk"
)

// Exit codes
const (
	Success       = 0
	GeneralError  = 1
	UsageError    = 2
	AuthError     = 3
	FileError     = 4
	ExtractFailed = 5
	TimeoutError  = 6
	QuotaExceeded = 7
)

// ErrorInfo holds error details for CLI output.
type ErrorInfo struct {
	Code    int
	Message string
	Hint    string
}

// Wrap maps an SDK error to an ErrorInfo with appropriate exit code.
func Wrap(err error) *ErrorInfo {
	if err == nil {
		return nil
	}

	// Check for specific SDK error types
	var authErr *mineru.AuthError
	if errors.As(err, &authErr) {
		return &ErrorInfo{
			Code:    AuthError,
			Message: err.Error(),
			Hint:    "Token is invalid or expired. Run 'mineru-open-api auth' to configure a new token.",
		}
	}

	var fileTooLargeErr *mineru.FileTooLargeError
	if errors.As(err, &fileTooLargeErr) {
		return &ErrorInfo{
			Code:    FileError,
			Message: err.Error(),
			Hint:    "File exceeds size limit. Try splitting the file or contact support for higher limits.",
		}
	}

	var pageLimitErr *mineru.PageLimitError
	if errors.As(err, &pageLimitErr) {
		return &ErrorInfo{
			Code:    FileError,
			Message: err.Error(),
			Hint:    "Document has too many pages. Try using --pages to specify a smaller range.",
		}
	}

	var extractFailedErr *mineru.ExtractFailedError
	if errors.As(err, &extractFailedErr) {
		return &ErrorInfo{
			Code:    ExtractFailed,
			Message: err.Error(),
			Hint:    "Server failed to parse the document. Try again or contact support if the issue persists.",
		}
	}

	var timeoutErr *mineru.TimeoutError
	if errors.As(err, &timeoutErr) {
		return &ErrorInfo{
			Code:    TimeoutError,
			Message: err.Error(),
			Hint:    "Task timed out. You can check status with 'mineru-open-api status <task-id>'.",
		}
	}

	var quotaErr *mineru.QuotaExceededError
	if errors.As(err, &quotaErr) {
		return &ErrorInfo{
			Code:    QuotaExceeded,
			Message: err.Error(),
			Hint:    "Daily quota exceeded. Upgrade your plan or try again tomorrow.",
		}
	}

	var paramErr *mineru.ParamError
	if errors.As(err, &paramErr) {
		return &ErrorInfo{
			Code:    UsageError,
			Message: err.Error(),
			Hint:    "Check your command arguments and try again.",
		}
	}

	var taskNotFoundErr *mineru.TaskNotFoundError
	if errors.As(err, &taskNotFoundErr) {
		return &ErrorInfo{
			Code:    GeneralError,
			Message: err.Error(),
			Hint:    "Task not found. Check the task ID and try again.",
		}
	}

	var flashFileTooLargeErr *mineru.FlashFileTooLargeError
	if errors.As(err, &flashFileTooLargeErr) {
		return &ErrorInfo{
			Code:    FileError,
			Message: err.Error(),
			Hint:    "File exceeds flash mode limit (10MB). Use standard 'extract' command or split the file.",
		}
	}

	var flashUnsupportedErr *mineru.FlashUnsupportedTypeError
	if errors.As(err, &flashUnsupportedErr) {
		return &ErrorInfo{
			Code:    FileError,
			Message: err.Error(),
			Hint:    "Flash mode supports PDF, images, Doc/Docx, PPT/PPTx, and HTML only.",
		}
	}

	var flashPageLimitErr *mineru.FlashPageLimitError
	if errors.As(err, &flashPageLimitErr) {
		return &ErrorInfo{
			Code:    FileError,
			Message: err.Error(),
			Hint:    "File exceeds flash mode page limit (50 pages). Use standard 'extract' command or specify --pages.",
		}
	}

	var flashParamErr *mineru.FlashParamError
	if errors.As(err, &flashParamErr) {
		return &ErrorInfo{
			Code:    UsageError,
			Message: err.Error(),
			Hint:    "Check your command arguments and try again.",
		}
	}

	// Generic API error
	var apiErr *mineru.APIError
	if errors.As(err, &apiErr) {
		return &ErrorInfo{
			Code:    GeneralError,
			Message: err.Error(),
			Hint:    "",
		}
	}

	// Unknown error
	return &ErrorInfo{
		Code:    GeneralError,
		Message: err.Error(),
		Hint:    "",
	}
}

// GetCode returns the exit code for an error.
func GetCode(err error) int {
	info := Wrap(err)
	if info == nil {
		return Success
	}
	return info.Code
}
