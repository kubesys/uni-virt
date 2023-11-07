package utils

import (
	"github.com/satori/go.uuid"
	"strings"
)

func GetUUID() string {
	uuid := uuid.NewV4().String()
	uuid = strings.ReplaceAll(uuid, "-", "")[:16]
	return uuid
}
