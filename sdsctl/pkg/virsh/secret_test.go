package virsh

import (
	"fmt"
	"testing"
)

func TestGetOrCreateCephTypeSecret(t *testing.T) {
	secret, err := GetOrCreateCephTypeSecret("client.admin")
	fmt.Printf("secret:%+v\n", secret)
	fmt.Printf("err:%+v\n", err)
}

func TestGetCephAdminSecret2(t *testing.T) {
	secret, err := GetCephAdminSecret("client.admin")
	fmt.Printf("secret:%+v\n", string(secret))
	fmt.Printf("err:%+v\n", err)
}

func TestSetSecretValue(t *testing.T) {
	err := SetSecretValue("client.admin")
	fmt.Printf("err:%+v\n", err)
}

func TestGetSecretValue(t *testing.T) {
	value, err := GetSecretValue("client.admin")
	fmt.Printf("value:%+v\n", value)
	fmt.Printf("err:%+v\n", err)
}
