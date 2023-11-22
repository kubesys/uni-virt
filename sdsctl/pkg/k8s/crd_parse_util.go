package k8s

import (
	"encoding/json"
	"github.com/tidwall/gjson"
	"github.com/tidwall/sjson"
)

func AddPowerStatus(bytes []byte, message, reason string) ([]byte, error) {
	statusMap := map[string]interface{}{
		"message": message,
		"reason":  reason,
	}
	return UpdateCRDSpec(bytes, "status.conditions.state.waiting", statusMap)
}

func AddPowerStatusForInit(bytes []byte, message, reason string) ([]byte, error) {
	statusMap := map[string]interface{}{
		"message": message,
		"reason":  reason,
	}
	return UpdateCRDSpec(bytes, "spec.status.conditions.state.waiting", statusMap)
}

func UpdateCRDSpec(spec []byte, key string, value interface{}) ([]byte, error) {
	bytes, err := sjson.SetBytes(spec, key, value)
	if err != nil {
		return []byte{}, err
	}
	return bytes, nil
}

func GetCRDSpecNodeName(spec []byte) (string, error) {
	parse := gjson.ParseBytes(spec)
	value := parse.Get("nodeName")
	res := ""
	if err := json.Unmarshal([]byte(value.Raw), &res); err != nil {
		return res, err
	}
	return res, nil
}

func GetCRDSpec(spec []byte, key string) (map[string]string, error) {
	parse := gjson.ParseBytes(spec)
	value := parse.Get(key)
	res := make(map[string]string)
	if err := json.Unmarshal([]byte(value.Raw), &res); err != nil {
		return res, err
	}
	return res, nil
}

func GetNodeName(spec []byte) string {
	parse := gjson.ParseBytes(spec)
	return parse.Get("nodeName").String()
}
