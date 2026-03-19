package main

import "syscall"

var (
	kernel32           = syscall.NewLazyDLL("kernel32.dll")
	setConsoleOutputCP = kernel32.NewProc("SetConsoleOutputCP")
)

func init() {
	// Tell the Windows console that our stdout is UTF-8 (code page 65001).
	// Without this, Chinese/CJK characters appear as mojibake because the
	// default console code page on Chinese Windows is 936 (GBK).
	setConsoleOutputCP.Call(65001)
}
