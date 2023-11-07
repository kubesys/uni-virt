package utils

import (
	"github.com/kube-stack/sdsctl/pkg/constant"
	rotatelogs "github.com/lestrrat-go/file-rotatelogs"
	"github.com/op/go-logging"
	"os"
	"strings"
	"time"
)

var logger *logging.Logger

func GetLogger() *logging.Logger {
	if logger == nil {
		InitLogger(constant.DefualtLogPath, true)
	}
	return logger
}

func InitLogger(logPath string, debug bool) {
	if logPath == "" {
		logPath = constant.DefualtLogPath
	}

	// set rotate log
	prefix := strings.Split(logPath, ".log")[0]

	content, _ := rotatelogs.New(
		// retate log format
		prefix+"_%Y-%m-%d.log",
		// ref to latest log file
		rotatelogs.WithLinkName(logPath),
		//MaxAge and RotationCount cannot be both set
		rotatelogs.WithMaxAge(time.Duration(168)*time.Hour),
		//rotate each day
		rotatelogs.WithRotationTime(time.Duration(24)*time.Hour),
	)

	// set logging format
	logger = logging.MustGetLogger("network-controller")

	// set stdout backend & logger formatter
	stdBackend := logging.NewLogBackend(os.Stdout, "", 0)
	loggerStdFmt := `%{color}[%{time:06-01-02 15:04:05}][%{shortfile}][%{level:.6s}] %{shortfunc}%{color:reset} %{message}`
	stdFormatter, _ := logging.NewStringFormatter(loggerStdFmt)
	stdback := logging.NewBackendFormatter(stdBackend, stdFormatter)

	// set file backend & logger formatter
	fBackend := logging.NewLogBackend(content, "", 0)
	loggerFileFmt := "[%{time:06-01-02 15:04:05}][%{shortfile}][%{level:.6s}] %{shortfunc} %{message}"
	fFormatter, _ := logging.NewStringFormatter(loggerFileFmt)
	fback := logging.NewBackendFormatter(fBackend, fFormatter)

	// set output: stdout & file
	logging.SetBackend(fback, stdback)

	// set log level
	SetLoggerLevel(debug)
}

func SetLoggerLevel(debug bool) {
	if debug {
		logging.SetLevel(logging.DEBUG, "network-controller")
	} else {
		logging.SetLevel(logging.INFO, "network-controller")
	}
}
