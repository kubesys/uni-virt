package rook

import (
	"fmt"
	"testing"
)

func TestGetSecret(t *testing.T) {
	secret, err := GetSecret()
	fmt.Printf("secret:%+v", secret)
	fmt.Printf("err:%+v", err)
}
