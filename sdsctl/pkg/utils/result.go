package utils

import (
	"encoding/json"
	"k8s.io/apimachinery/pkg/runtime"
)

type StatusMsg struct {
	Code int
	Msg  string
}
type Message struct {
	Result StatusMsg
	Data   runtime.RawExtension
}

func PrintOkJson(msg, data string) {
	message := &Message{
		Result: StatusMsg{
			Code: 0,
			Msg:  msg,
		},
	}
	json.Marshal(message)
}
