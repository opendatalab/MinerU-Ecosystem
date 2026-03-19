export class MinerUError extends Error {
  readonly code: string;
  readonly traceId: string;

  constructor(code: string | number, message: string, traceId = "") {
    const tag = traceId ? ` (trace: ${traceId})` : "";
    super(`[${code}] ${message}${tag}`);
    this.name = "MinerUError";
    this.code = String(code);
    this.traceId = traceId;
  }
}

export class AuthError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "AuthError";
  }
}

export class ParamError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "ParamError";
  }
}

export class FileTooLargeError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "FileTooLargeError";
  }
}

export class PageLimitError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "PageLimitError";
  }
}

export class TaskNotFoundError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "TaskNotFoundError";
  }
}

export class ExtractFailedError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "ExtractFailedError";
  }
}

export class TimeoutError extends MinerUError {
  readonly timeout: number;
  readonly taskId: string;

  constructor(timeout: number, taskId: string) {
    super("TIMEOUT", `Task ${taskId} did not complete within ${timeout}s`);
    this.name = "TimeoutError";
    this.timeout = timeout;
    this.taskId = taskId;
  }
}

export class QuotaExceededError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "QuotaExceededError";
  }
}

// Flash API specific errors

export class FlashFileTooLargeError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "FlashFileTooLargeError";
  }
}

export class FlashUnsupportedTypeError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "FlashUnsupportedTypeError";
  }
}

export class FlashPageLimitError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "FlashPageLimitError";
  }
}

export class FlashParamError extends MinerUError {
  constructor(code: string | number, message: string, traceId = "") {
    super(code, message, traceId);
    this.name = "FlashParamError";
  }
}

export class NoAuthClientError extends MinerUError {
  constructor() {
    super(
      "-1",
      "This operation requires an authenticated client; pass token to MinerU() or set MINERU_TOKEN env var.",
    );
    this.name = "NoAuthClientError";
  }
}

const CODE_TO_ERROR: Record<string, typeof MinerUError> = {
  A0202: AuthError,
  A0211: AuthError,
  "-500": ParamError,
  "-10002": ParamError,
  "-60005": FileTooLargeError,
  "-60006": PageLimitError,
  "-60010": ExtractFailedError,
  "-60012": TaskNotFoundError,
  "-60013": MinerUError,
  "-60018": QuotaExceededError,
  "-60019": QuotaExceededError,
  "-30001": FlashFileTooLargeError,
  "-30002": FlashUnsupportedTypeError,
  "-30003": FlashPageLimitError,
  "-30004": FlashParamError,
};

export function raiseForCode(
  code: number | string,
  msg: string,
  traceId = "",
): never {
  const ErrorClass = CODE_TO_ERROR[String(code)] ?? MinerUError;
  throw new ErrorClass(code, msg, traceId);
}
